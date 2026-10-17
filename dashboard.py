
import pandas as pd
from pathlib import Path

REPORT_DIR = Path("supply_chain_reports")

REPORTS = {
    "1": ("Executive Summary", "executive_summary.csv"),
    "2": ("Regional Performance", "regional_performance.csv"),
    "3": ("Supplier Risk Analysis", "supplier_risk_analysis.csv"),
    "4": ("Category Performance", "category_performance.csv"),
    "5": ("Anomaly Alerts", "supply_chain_anomaly_alerts.csv"),
    "6": ("Anomaly Summary", "supply_chain_anomaly_summary.csv"),
}


def load_report(filename):
    """Safely load a CSV report."""
    path = REPORT_DIR / filename

    if not path.exists():
        print(f"\n[WARNING] Missing report: {path}")
        print("Run the relevant analysis script first.")
        return None

    try:
        return pd.read_csv(path)
    except (OSError, pd.errors.EmptyDataError, pd.errors.ParserError) as exc:
        print(f"\n[ERROR] Could not read {filename}: {exc}")
        return None


def display_menu():
    print("\n" + "=" * 66)
    print("          GLOBAL SUPPLY CHAIN EXECUTIVE DASHBOARD")
    print("=" * 66)
    print("1. Executive Summary Metrics")
    print("2. Regional Performance")
    print("3. Supplier Risk & Cost Exposure")
    print("4. Product Category Performance")
    print("5. Automated Anomaly Alerts")
    print("6. Anomaly Summary")
    print("7. Search and Filter a Report")
    print("8. Export a Filtered Report")
    print("9. Refresh Reports")
    print("0. Exit")
    print("=" * 66)


def show_report(title, filename):
    df = load_report(filename)

    if df is None:
        return None

    print(f"\n--- {title.upper()} ---")

    if df.empty:
        print("No records found.")
    else:
        with pd.option_context(
            "display.max_columns", None,
            "display.width", 180,
            "display.max_colwidth", 35
        ):
            print(df.to_string(index=False))

    print(f"\nRecords: {len(df)}")
    return df


def show_alerts():
    df = load_report("supply_chain_anomaly_alerts.csv")

    if df is None:
        return

    if df.empty:
        print("\nNo anomalies are currently flagged.")
        return

    if "severity" not in df.columns:
        print("[ERROR] The alert report has no severity column.")
        print(df.to_string(index=False))
        return

    print("\nSeverity levels available:")
    print(df["severity"].fillna("Unknown").value_counts().to_string())

    severity = input(
        "\nFilter by severity (High/Medium/Low/All): "
    ).strip().lower()

    if severity and severity != "all":
        df = df[
            df["severity"].fillna("").str.lower() == severity
        ]

    if df.empty:
        print("No alerts match that severity.")
        return

    preferred = [
        "shipment_id", "supplier_name", "destination_region",
        "alert_type", "severity", "recommended_action"
    ]
    columns = [col for col in preferred if col in df.columns]

    print("\n--- FILTERED ANOMALY ALERTS ---")
    print(df[columns].to_string(index=False))
    print(f"\nMatching alert records: {len(df)}")


def filter_report():
    """Search a selected report by column and text."""
    filename = choose_report()
    if filename is None:
        return

    df = load_report(filename)
    if df is None or df.empty:
        return

    print("\nAvailable columns:")
    print(", ".join(df.columns))

    column = input("Column to search: ").strip()

    if column not in df.columns:
        print("[ERROR] Unknown column.")
        return

    term = input("Search text: ").strip()

    if not term:
        print("[WARNING] Enter a search term.")
        return

    mask = df[column].astype("string").str.contains(
        term, case=False, na=False, regex=False
    )
    results = df[mask]

    if results.empty:
        print("No matching records found.")
    else:
        print(f"\nFound {len(results)} matching records:")
        print(results.to_string(index=False))


def choose_report():
    print("\nSelect a report:")

    for key, (title, filename) in REPORTS.items():
        print(f"{key}. {title} ({filename})")

    choice = input("Report number: ").strip()

    if choice not in REPORTS:
        print("[ERROR] Invalid report selection.")
        return None

    return REPORTS[choice][1]


def export_filtered_report():
    """Filter a report and export the matching rows."""
    filename = choose_report()
    if filename is None:
        return

    df = load_report(filename)
    if df is None or df.empty:
        return

    print("\nAvailable columns:")
    print(", ".join(df.columns))

    column = input("Column to filter: ").strip()

    if column not in df.columns:
        print("[ERROR] Unknown column.")
        return

    term = input("Value contains: ").strip()

    if not term:
        print("[WARNING] Filter text cannot be empty.")
        return

    mask = df[column].astype("string").str.contains(
        term, case=False, na=False, regex=False
    )
    filtered = df[mask]

    if filtered.empty:
        print("No matching records to export.")
        return

    output_name = input(
        "Output filename (without extension): "
    ).strip()

    if not output_name:
        output_name = "filtered_supply_chain_report"

    # Prevent path traversal and force CSV output inside REPORT_DIR.
    safe_name = Path(output_name).name
    if safe_name.lower().endswith(".csv"):
        safe_name = safe_name[:-4]

    if not safe_name or safe_name in {".", ".."}:
        print("[ERROR] Invalid output filename.")
        return

    output_path = REPORT_DIR / f"{safe_name}.csv"

    if output_path.exists():
        overwrite = input("File exists. Overwrite? (y/n): ").strip().lower()
        if overwrite != "y":
            print("Export cancelled.")
            return

    try:
        filtered.to_csv(output_path, index=False)
        print(f"[INFO] Exported {len(filtered)} rows to {output_path}")
    except OSError as exc:
        print(f"[ERROR] Export failed: {exc}")


def main():
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    while True:
        display_menu()
        choice = input("Select an option (0-9): ").strip()

        if choice == "0":
            print("\n[INFO] Exiting Supply Chain Dashboard.")
            break

        elif choice in REPORTS:
            title, filename = REPORTS[choice]

            if choice == "5":
                show_alerts()
            else:
                show_report(title, filename)

        elif choice == "7":
            filter_report()

        elif choice == "8":
            export_filtered_report()

        elif choice == "9":
            print("\n[INFO] Report directory:")
            print(REPORT_DIR.resolve())
            print("Reports are read from disk when selected.")

        else:
            print("[ERROR] Invalid choice. Enter a number from 0 to 9.")


if __name__ == "__main__":
    main()