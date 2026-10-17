Global Supply Chain & Regional Price Intelligence Platform
Project Overview
An end-to-end Python and SQL analytics platform designed to analyze global shipment logistics, monitor supplier risk exposure, and detect unusual shipping costs and shipment volumes.

The platform uses a relational SQLite database, automated SQL analytics, statistical anomaly detection, and an interactive command-line dashboard to transform supply chain data into actionable business insights.

Key Features
1. Relational Database Management
SQLite database with suppliers, products, and shipments tables.
Relational data analysis using SQL joins.
Structured database initialization and sample data generation.
2. Supply Chain Analytics
Total shipment and unit-volume analysis.
Regional shipping expenditure comparisons.
Supplier risk and cost exposure analysis.
Product category performance reporting.
Shipping cost per unit and estimated product value calculations.
3. Automated Anomaly Detection
Flags large shipments from high-risk suppliers.
Identifies unusually high shipping costs.
Applies the Interquartile Range (IQR) method to detect statistical outliers.
Assigns alert severity and recommended follow-up actions.
Exports anomaly reports to CSV.
4. Executive Dashboard
Menu-driven command-line interface.
View executive summary metrics and detailed reports.
Search and filter report records.
Review anomaly alerts by severity.
Export filtered datasets to CSV.
Technology Stack
Programming: Python
Database: SQLite
Query Language: SQL
Data Analysis: Pandas
File Management: pathlib
Statistical Analysis: Interquartile Range (IQR)
Development Environment: Visual Studio Code
Project Structure

SupplyChainProject/
├── global_supply_pipeline.py
├── analyze_supply_chain.py
├── detect_anomalies.py
├── dashboard.py
├── README.md
├── requirements.txt
├── .gitignore
└── supply_chain_reports/
The database and report files are generated locally by the application and may be excluded from the public repository.

Installation and Usage
Prerequisites
Python 3.10 or later
Git
Pandas
1. Install dependencies

python -m pip install pandas
2. Initialize the database and sample data

python global_supply_pipeline.py
3. Generate analytical reports

python analyze_supply_chain.py
4. Run anomaly detection

python detect_anomalies.py
5. Launch the dashboard

python dashboard.py
Run these commands from the project directory. Ensure that the script filenames match those in your actual project.

Business Value
This project demonstrates practical applications of data engineering and analytics for:

Monitoring shipping expenditure across regions.
Evaluating supplier risk exposure.
Identifying unusual shipment costs and quantities.
Producing structured reports for management decisions.
Supporting data-driven supply chain investigations.
Future Enhancements
Interactive web dashboard using Streamlit.
Historical shipping cost trend analysis.
Regional price comparisons and supplier performance trends.
Automated data-quality validation.
Scheduled report generation and alert notifications.
Project Status
A Python-based supply chain analytics portfolio project demonstrating relational database design, SQL reporting, statistical anomaly detection, and command-line dashboard development.