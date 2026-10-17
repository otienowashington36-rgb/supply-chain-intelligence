
import sqlite3
import pandas as pd
from pathlib import Path

# Database and output configuration
DB_NAME = "supply_chain_data.db"
OUTPUT_DIR = Path("supply_chain_reports")


def run_supply_chain_analysis():
    """Generate detailed supply chain intelligence reports."""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    query = """
    SELECT
        s.destination_region,
        p.category,
        sup.supplier_id,
        sup.supplier_name,
        sup.risk_rating,

        COUNT(s.shipment_id) AS total_shipments,
        COUNT(DISTINCT s.product_id) AS distinct_products,
        SUM(COALESCE(s.quantity, 0)) AS total_units_shipped,

        ROUND(SUM(COALESCE(s.shipping_cost_usd, 0)), 2)
            AS total_shipping_cost_usd,

        ROUND(
            AVG(s.shipping_cost_usd), 2
        ) AS avg_shipping_cost_per_shipment_usd,

        ROUND(
            SUM(COALESCE(s.shipping_cost_usd, 0))
            / NULLIF(SUM(COALESCE(s.quantity, 0)), 0),
            2
        ) AS shipping_cost_per_unit_usd,

        ROUND(
            SUM(COALESCE(s.quantity, 0) * p.unit_cost_usd)
            / NULLIF(SUM(
                CASE WHEN p.unit_cost_usd IS NOT NULL
                     THEN COALESCE(s.quantity, 0)
                     ELSE 0 END
            ), 0),
            2
        ) AS weighted_avg_unit_cost_usd,

        ROUND(
            SUM(COALESCE(s.quantity, 0) * p.unit_cost_usd),
            2
        ) AS estimated_product_value_usd,

        ROUND(
            100.0 * SUM(COALESCE(s.shipping_cost_usd, 0))
            / NULLIF(
                SUM(COALESCE(s.quantity, 0) * p.unit_cost_usd),
                0
            ),
            2
        ) AS shipping_cost_pct_of_product_value

    FROM shipments s
    INNER JOIN products p
        ON s.product_id = p.product_id
    INNER JOIN suppliers sup
        ON p.supplier_id = sup.supplier_id

    GROUP BY
        s.destination_region,
        p.category,
        sup.supplier_id,
        sup.supplier_name,
        sup.risk_rating

    ORDER BY total_shipping_cost_usd DESC;
    """

    try:
        with sqlite3.connect(DB_NAME) as conn:
            # Confirm that the required tables exist
            tables = pd.read_sql_query(
                """
                SELECT name FROM sqlite_master
                WHERE type = 'table'
                """,
                conn
            )["name"].tolist()

            required = {"shipments", "products", "suppliers"}
            missing = required - set(tables)

            if missing:
                raise ValueError(
                    f"Missing required database tables: {sorted(missing)}"
                )

            # Load detailed analysis
            df = pd.read_sql_query(query, conn)

    except (sqlite3.Error, ValueError) as exc:
        print(f"[ERROR] Analysis failed: {exc}")
        return

    if df.empty:
        print("[WARNING] No matching shipment records found.")
        return

    # Clean up incomplete or invalid report records
    df["total_shipping_cost_usd"] = pd.to_numeric(
        df["total_shipping_cost_usd"], errors="coerce"
    )
    df["total_units_shipped"] = pd.to_numeric(
        df["total_units_shipped"], errors="coerce"
    )

    # Identify missing key dimensions
    missing_dimensions = df[
        ["destination_region", "category", "supplier_name"]
    ].isna().sum()

    # Executive summary
    total_shipments = int(df["total_shipments"].sum())
    total_units = df["total_units_shipped"].sum()
    total_shipping = df["total_shipping_cost_usd"].sum()
    total_product_value = df["estimated_product_value_usd"].sum()

    summary = pd.DataFrame([
        {"metric": "Report groups", "value": len(df)},
        {"metric": "Total shipments", "value": total_shipments},
        {"metric": "Total units shipped", "value": total_units},
        {
            "metric": "Total shipping cost (USD)",
            "value": round(total_shipping, 2)
        },
        {
            "metric": "Estimated product value (USD)",
            "value": round(total_product_value, 2)
        },
        {
            "metric": "Shipping cost per unit (USD)",
            "value": round(total_shipping / total_units, 2)
            if total_units else None
        },
        {
            "metric": "Shipping cost as % of product value",
            "value": round(100 * total_shipping / total_product_value, 2)
            if total_product_value else None
        }
    ])

    # Regional performance
    regional = (
        df.groupby("destination_region", dropna=False)
        .agg(
            total_shipments=("total_shipments", "sum"),
            total_units=("total_units_shipped", "sum"),
            total_shipping_cost_usd=("total_shipping_cost_usd", "sum"),
            estimated_product_value_usd=("estimated_product_value_usd", "sum")
        )
        .reset_index()
    )

    regional["shipping_cost_per_unit_usd"] = (
        regional["total_shipping_cost_usd"]
        / regional["total_units"].replace(0, float("nan"))
    ).round(2)

    regional["shipping_cost_share_pct"] = (
        100 * regional["total_shipping_cost_usd"]
        / total_shipping if total_shipping else 0
    ).round(2)

    regional = regional.sort_values(
        "total_shipping_cost_usd", ascending=False
    )

    # Supplier risk and cost exposure
    supplier = (
        df.groupby(
            ["supplier_id", "supplier_name", "risk_rating"],
            dropna=False
        )
        .agg(
            total_shipments=("total_shipments", "sum"),
            total_units_shipped=("total_units_shipped", "sum"),
            total_shipping_cost_usd=("total_shipping_cost_usd", "sum"),
            estimated_product_value_usd=("estimated_product_value_usd", "sum")
        )
        .reset_index()
    )

    supplier["shipping_cost_share_pct"] = (
        100 * supplier["total_shipping_cost_usd"]
        / total_shipping if total_shipping else 0
    ).round(2)

    supplier = supplier.sort_values(
        "total_shipping_cost_usd", ascending=False
    )

    # Category performance
    category = (
        df.groupby("category", dropna=False)
        .agg(
            total_shipments=("total_shipments", "sum"),
            total_units_shipped=("total_units_shipped", "sum"),
            total_shipping_cost_usd=("total_shipping_cost_usd", "sum"),
            estimated_product_value_usd=("estimated_product_value_usd", "sum")
        )
        .reset_index()
        .sort_values("total_shipping_cost_usd", ascending=False)
    )

    category["shipping_cost_share_pct"] = (
        100 * category["total_shipping_cost_usd"]
        / total_shipping if total_shipping else 0
    ).round(2)

    # Export reports
    reports = {
        "detailed_supply_chain_report.csv": df,
        "executive_summary.csv": summary,
        "regional_performance.csv": regional,
        "supplier_risk_analysis.csv": supplier,
        "category_performance.csv": category,
        "data_quality_checks.csv": missing_dimensions.rename(
            "missing_group_values"
        ).rename_axis("dimension").reset_index()
    }

    for filename, report_df in reports.items():
        report_df.to_csv(OUTPUT_DIR / filename, index=False)

    # Console dashboard
    print("\n" + "=" * 70)
    print("       GLOBAL SUPPLY CHAIN INTELLIGENCE REPORT")
    print("=" * 70)

    print("\nEXECUTIVE SUMMARY")
    print(summary.to_string(index=False))

    print("\nTOP 5 REGIONS BY SHIPPING COST")
    print(regional.head(5).to_string(index=False))

    print("\nTOP 5 SUPPLIERS BY SHIPPING COST")
    print(supplier.head(5).to_string(index=False))

    print("\nPRODUCT CATEGORY PERFORMANCE")
    print(category.to_string(index=False))

    print("\nDATA QUALITY CHECKS")
    print(missing_dimensions.to_string())

    print(f"\n[INFO] {len(reports)} reports exported to: {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    run_supply_chain_analysis()
