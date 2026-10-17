import sqlite3
import pandas as pd
import os

# Define our database filename
db_name = "supply_chain_data.db"

def initialize_database():
    """Sets up the SQLite connection and creates our relational tables."""
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    # 1. Create Suppliers Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS suppliers (
        supplier_id INTEGER PRIMARY KEY,
        supplier_name TEXT NOT NULL,
        country TEXT NOT NULL,
        risk_rating TEXT NOT NULL
    );
    """)
    
    # 2. Create Products Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        product_id INTEGER PRIMARY KEY,
        product_name TEXT NOT NULL,
        category TEXT NOT NULL,
        unit_cost_usd REAL NOT NULL,
        supplier_id INTEGER,
        FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id)
    );
    """)
    
    # 3. Create Shipments Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS shipments (
        shipment_id INTEGER PRIMARY KEY,
        product_id INTEGER,
        destination_region TEXT NOT NULL,
        order_date TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        shipping_cost_usd REAL NOT NULL,
        status TEXT NOT NULL,
        FOREIGN KEY (product_id) REFERENCES products(product_id)
    );
    """)
    
    conn.commit()
    conn.close()
    print(f"[INFO] Successfully created relational database schema in {db_name}")

def populate_mock_data():
    """Inserts sample enterprise supply chain data into our relational tables."""
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    # 1. Insert Sample Suppliers
    suppliers_data = [
        (1, "Global Logistics Corp", "USA", "Low"),
        (2, "Apex Manufacturing", "Germany", "Medium"),
        (3, "Pacific Trade Partners", "Singapore", "Low"),
        (4, "Andes Logistics", "Chile", "High")
    ]
    cursor.executemany("""
    INSERT OR IGNORE INTO suppliers (supplier_id, supplier_name, country, risk_rating)
    VALUES (?, ?, ?, ?);
    """, suppliers_data)
    
    # 2. Insert Sample Products
    products_data = [
        (101, "Industrial Robotic Arm", "Hardware", 12500.00, 1),
        (102, "Precision Sensor Node", "Electronics", 340.50, 2),
        (103, "High-Grade Steel Valve", "Raw Materials", 120.00, 3),
        (104, "Solar Inverter Unit", "Energy", 2400.00, 2),
        (105, "Lithium Battery Cell", "Energy", 85.00, 4)
    ]
    cursor.executemany("""
    INSERT OR IGNORE INTO products (product_id, product_name, category, unit_cost_usd, supplier_id)
    VALUES (?, ?, ?, ?, ?);
    """, products_data)
    
    # 3. Insert Sample Shipments
    shipments_data = [
        (1001, 101, "North America", "2026-05-01", 10, 4500.00, "Completed"),
        (1002, 102, "Europe", "2026-05-03", 150, 1200.00, "Completed"),
        (1003, 103, "Asia-Pacific", "2026-05-05", 500, 3100.00, "In Transit"),
        (1004, 104, "North America", "2026-05-08", 25, 2200.00, "Completed"),
        (1005, 105, "Latin America", "2026-05-10", 1200, 5400.00, "Delayed")
    ]
    cursor.executemany("""
    INSERT OR IGNORE INTO shipments (shipment_id, product_id, destination_region, order_date, quantity, shipping_cost_usd, status)
    VALUES (?, ?, ?, ?, ?, ?, ?);
    """, shipments_data)
    
    conn.commit()
    conn.close()
    print("[INFO] Successfully populated database with mock enterprise supply chain data!")

if __name__ == "__main__":
    initialize_database()
    populate_mock_data()