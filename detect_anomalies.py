
import sqlite3
import pandas as pd
from pathlib import Path

DB_NAME = "supply_chain_data.db"
OUTPUT_DIR = Path("supply_chain_reports")

HIGH_RISK_VOLUME_THRESHOLD = 100
HIGH_SHIPPING_COST_THRESHOLD = 4000
HIGH_COST_PER_UNIT_THRESHOLD = 10.00
IQR_MULTIPLIER = 1.5


def flag_iqr_outliers(series):
    """Return a Boolean mask for upper IQR outliers."""
    values = pd.to_numeric(series, errors="coerce")
    valid = values.dropna()

    result = pd.Series(False, index=series.index)

    if len(valid) < 4:
        return result

    q1 = valid.quantile(0.25)
    q3 = valid.quantile(0.75)
    iqr = q3 - q1

    if iqr == 0:
        return result

    upper_bound = q3 + IQR_MULTIPLIER * iqr
    result.loc[valid.index] = valid > upper_bound

    return result


def run_anomaly_detection():
    """Detect supply chain risk and shipment cost/volume anomalies."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    query = """
    SELECT
        s.shipment_id,
        s.order_date,
        s.destination_region,
        p.product_name,
        p.category,
        sup.supplier_id,
        sup.supplier_name,
        sup.risk_rating,
        s.quantity,
        s.shipping_cost_usd,
        CASE
            WHEN s.quantity > 0
            THEN 1.0 * s.shipping_cost_usd / s.quantity
            ELSE NULL
        END AS cost_per_unit
    FROM shipments s
    INNER JOIN products p
        ON s.product_id = p.product_id
    INNER JOIN suppliers sup
        ON p.supplier_id = sup.supplier_id;
    """

    try:
        with sqlite3.connect(DB_NAME) as conn:
            df = pd.read_sql_query(query, conn)
    except (sqlite3.Error, pd.errors.DatabaseError) as exc:
        print(f"[ERROR] Could not read shipment data: {exc}")
        return

    if df.empty:
        print("[WARNING] No shipment data found for anomaly screening.")
        return

    # Convert numeric fields safely.
    for col in ["quantity", "shipping_cost_usd", "cost_per_unit"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Normalize supplier risk labels.
    risk = df["risk_rating"].astype("string").str.strip().str.lower()

    # Each alert has a consistent structure.
    alerts = []

    def add_alert(mask, alert_type, severity, recommendation):
        """Append matching shipment rows to the alert log."""
        matching = df.loc[mask.fillna(False)].copy()

        if matching.empty:
            return

        matching["alert_type"] = alert_type
        matching["severity"] = severity
        matching["recommended_action"] = recommendation
        alerts.append(matching)

    # Rule 1: High-risk suppliers handling large shipments.
    add_alert(
        risk.eq("high") & df["quantity"].gt(
            HIGH_RISK_VOLUME_THRESHOLD
        ),
        "High-risk supplier / large shipment",
        "High",
        "Review supplier continuity plans and shipment exposure."
    )

    # Rule 2: Excessive total shipping costs.
    add_alert(
        df["shipping_cost_usd"].gt(HIGH_SHIPPING_COST_THRESHOLD),
        "High total shipping cost",
        "High",
        "Verify freight invoice, route, and carrier charges."
    )

    # Rule 3: Excessive shipping cost per unit.
    add_alert(
        df["cost_per_unit"].gt(HIGH_COST_PER_UNIT_THRESHOLD),
        "High shipping cost per unit",
        "Medium",
        "Compare with similar products, routes, and shipment sizes."
    )

    # Rule 4: Statistically unusual shipping costs.
    cost_outlier_mask = flag_iqr_outliers(df["shipping_cost_usd"])

    add_alert(
        cost_outlier_mask,
        "Statistical shipping cost outlier",
        "Medium",
        "Investigate why shipping cost is unusually high."
    )

    # Rule 5: Statistically unusual shipment quantities.
    volume_outlier_mask = flag_iqr_outliers(df["quantity"])

    add_alert(
        volume_outlier_mask,
        "Statistical shipment volume outlier",
        "Medium",
        "Validate shipment quantity against order records."
    )

    # Rule 6: Data-quality issues.
    add_alert(
        df["quantity"].isna() | df["quantity"].le(0),
        "Invalid or missing quantity",
        "High",
        "Correct the shipment quantity before cost analysis."
    )

    add_alert(
        df["shipping_cost_usd"].isna()
        | df["shipping_cost_usd"].lt(0),
        "Missing or negative shipping cost",
        "High",
        "Validate the freight charge against source records."
    )

    add_alert(
        df["cost_per_unit"].isna()
        & df["quantity"].gt(0)
        & df["shipping_cost_usd"].notna(),
        "Unavailable unit shipping cost",
        "Low",
        "Review the shipment cost and quantity fields."
    )

    # Combine alerts and remove duplicate shipment/type combinations.
    if alerts:
        alert_log = pd.concat(alerts, ignore_index=True)

        alert_log = alert_log.drop_duplicates(
            subset=["shipment_id", "alert_type"]
        )

        severity_order = {"High": 0, "Medium": 1, "Low": 2}
        alert_log["_severity_order"] = (
            alert_log["severity"].map(severity_order)
        )

        alert_log = alert_log.sort_values(
            ["_severity_order", "shipping_cost_usd"],
            ascending=[True, False],
            na_position="last"
        ).drop(columns="_severity_order")
    else:
        alert_log = pd.DataFrame(columns=[
            *df.columns,
            "alert_type",
            "severity",
            "recommended_action"
        ])

    # Export full alert log.
    alert_path = OUTPUT_DIR / "supply_chain_anomaly_alerts.csv"
    alert_log.to_csv(alert_path, index=False)

    # Export a summary by alert type.
    if not alert_log.empty:
        summary = (
            alert_log.groupby(
                ["alert_type", "severity"], dropna=False
            )
            .agg(
                affected_shipments=("shipment_id", "nunique"),
                alert_records=("shipment_id", "size"),
                shipping_cost_usd=("shipping_cost_usd", "sum")
            )
            .reset_index()
            .sort_values(
                ["severity", "affected_shipments"],
                ascending=[True, False]
            )
        )
    else:
        summary = pd.DataFrame(columns=[
            "alert_type", "severity", "affected_shipments",
            "alert_records", "shipping_cost_usd"
        ])

    summary_path = OUTPUT_DIR / "supply_chain_anomaly_summary.csv"
    summary.to_csv(summary_path, index=False)

    # Console report.
    print("\n" + "=" * 72)
    print("       AUTOMATED SUPPLY CHAIN ANOMALY & RISK MONITOR")
    print("=" * 72)
    print(f"Shipment records screened: {len(df)}")
    print(f"Total alert records: {len(alert_log)}")
    print(
        "Unique shipments flagged: "
        f"{alert_log['shipment_id'].nunique() if not alert_log.empty else 0}"
    )

    if alert_log.empty:
        print("\nNo anomalies detected by the configured rules.")
    else:
        print("\nALERT SUMMARY")
        print(summary.to_string(index=False))

        print("\nHIGHEST-PRIORITY ALERTS")
        columns = [
            "shipment_id",
            "supplier_name",
            "destination_region",
            "alert_type",
            "severity",
            "recommended_action"
        ]
        print(alert_log[columns].head(20).to_string(index=False))

    print(f"\n[INFO] Full alert log: {alert_path.resolve()}")
    print(f"[INFO] Alert summary: {summary_path.resolve()}")
    print("=" * 72)


if __name__ == "__main__":
    run_anomaly_detection()
