#!/usr/bin/env python3
"""
Excel to PostgreSQL Import Script

Imports data from dynamic_inventory_dataset.xlsx into PostgreSQL database
with proper schemas and foreign key constraints.
"""

import os
import sys
from pathlib import Path

import pandas as pd
import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_values
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv(Path(__file__).parent.parent / '.env')

# Database configuration
DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST'),
    'database': os.getenv('POSTGRES_DATABASE'),
    'user': os.getenv('POSTGRES_USER'),
    'password': os.getenv('POSTGRES_PASSWORD'),
    'port': os.getenv('POSTGRES_PORT', '5432')
}

# Schema name for all tables
SCHEMA_NAME = 'inventory'

# Excel file path
EXCEL_FILE = Path(__file__).parent.parent / 'data' / 'dynamic_inventory_dataset.xlsx'

# Sheet name to table name mapping
SHEET_TO_TABLE = {
    'CalendarWeeks': 'calendar_weeks',
    'Items': 'items',
    'Suppliers': 'suppliers',
    'Locations': 'locations',
    'ItemSupplierSourcing': 'item_supplier_sourcing',
    'ReorderPolicy': 'reorder_policy',
    'LeadTimeHistory': 'lead_time_history',
    'SalesWeekly': 'sales_weekly',
    'ForecastsWeekly': 'forecasts_weekly',
    'PurchaseOrders': 'purchase_orders',
    'Receipts': 'receipts',
    'InventorySnapshots': 'inventory_snapshots',
    'NonMovingCandidates': 'non_moving_candidates',
}

# Table creation order (respecting foreign key dependencies)
TABLE_ORDER = [
    'calendar_weeks',
    'items',
    'suppliers',
    'locations',
    'item_supplier_sourcing',
    'reorder_policy',
    'lead_time_history',
    'sales_weekly',
    'forecasts_weekly',
    'purchase_orders',
    'receipts',
    'inventory_snapshots',
    'non_moving_candidates',
    'item_weekly_metrics',  # Derived table populated from JOINs
]

# SQL schema definitions (using inventory schema)
SCHEMA_SQL = {
    'calendar_weeks': """
        CREATE TABLE inventory.calendar_weeks (
            week_ending DATE PRIMARY KEY,
            fiscal_week INTEGER NOT NULL,
            fiscal_year INTEGER NOT NULL
        );
    """,
    
    'items': """
        CREATE TABLE inventory.items (
            item_id VARCHAR(20) PRIMARY KEY,
            description VARCHAR(255),
            category VARCHAR(50),
            uom VARCHAR(20),
            shelf_life_days INTEGER,
            launch_date DATE,
            obsolete_date DATE
        );
    """,
    
    'suppliers': """
        CREATE TABLE inventory.suppliers (
            supplier_id VARCHAR(20) PRIMARY KEY,
            supplier_name VARCHAR(100) NOT NULL,
            base_lead_time_days INTEGER,
            on_time_delivery_rate NUMERIC(5, 3),
            defect_rate_pct NUMERIC(5, 2)
        );
    """,
    
    'locations': """
        CREATE TABLE inventory.locations (
            location_id VARCHAR(20) PRIMARY KEY,
            name VARCHAR(100) NOT NULL
        );
    """,
    
    'item_supplier_sourcing': """
        CREATE TABLE inventory.item_supplier_sourcing (
            item_id VARCHAR(20) NOT NULL,
            supplier_id VARCHAR(20) NOT NULL,
            sourcing_split_pct NUMERIC(6, 2),
            PRIMARY KEY (item_id, supplier_id),
            FOREIGN KEY (item_id) REFERENCES inventory.items(item_id) ON DELETE CASCADE,
            FOREIGN KEY (supplier_id) REFERENCES inventory.suppliers(supplier_id) ON DELETE CASCADE
        );
    """,
    
    'reorder_policy': """
        CREATE TABLE inventory.reorder_policy (
            item_id VARCHAR(20) PRIMARY KEY,
            min_qty INTEGER,
            max_qty INTEGER,
            FOREIGN KEY (item_id) REFERENCES inventory.items(item_id) ON DELETE CASCADE
        );
    """,
    
    'lead_time_history': """
        CREATE TABLE inventory.lead_time_history (
            supplier_id VARCHAR(20) NOT NULL,
            month DATE NOT NULL,
            avg_lead_time_days INTEGER,
            PRIMARY KEY (supplier_id, month),
            FOREIGN KEY (supplier_id) REFERENCES inventory.suppliers(supplier_id) ON DELETE CASCADE
        );
    """,
    
    'sales_weekly': """
        CREATE TABLE inventory.sales_weekly (
            week_ending DATE NOT NULL,
            item_id VARCHAR(20) NOT NULL,
            location_id VARCHAR(20) NOT NULL,
            qty_sold INTEGER,
            PRIMARY KEY (week_ending, item_id, location_id),
            FOREIGN KEY (item_id) REFERENCES inventory.items(item_id) ON DELETE CASCADE,
            FOREIGN KEY (location_id) REFERENCES inventory.locations(location_id) ON DELETE CASCADE
        );
    """,
    
    'forecasts_weekly': """
        CREATE TABLE inventory.forecasts_weekly (
            week_ending DATE NOT NULL,
            item_id VARCHAR(20) NOT NULL,
            location_id VARCHAR(20) NOT NULL,
            forecast_qty INTEGER,
            PRIMARY KEY (week_ending, item_id, location_id),
            FOREIGN KEY (item_id) REFERENCES inventory.items(item_id) ON DELETE CASCADE,
            FOREIGN KEY (location_id) REFERENCES inventory.locations(location_id) ON DELETE CASCADE
        );
    """,
    
    'purchase_orders': """
        CREATE TABLE inventory.purchase_orders (
            po_id VARCHAR(20) PRIMARY KEY,
            order_week DATE,
            expected_week DATE,
            item_id VARCHAR(20) NOT NULL,
            location_id VARCHAR(20) NOT NULL,
            supplier_id VARCHAR(20) NOT NULL,
            qty_ordered INTEGER,
            FOREIGN KEY (item_id) REFERENCES inventory.items(item_id) ON DELETE CASCADE,
            FOREIGN KEY (location_id) REFERENCES inventory.locations(location_id) ON DELETE CASCADE,
            FOREIGN KEY (supplier_id) REFERENCES inventory.suppliers(supplier_id) ON DELETE CASCADE
        );
    """,
    
    'receipts': """
        CREATE TABLE inventory.receipts (
            receipt_id VARCHAR(20) PRIMARY KEY,
            po_id VARCHAR(20),
            receipt_week DATE,
            item_id VARCHAR(20) NOT NULL,
            location_id VARCHAR(20) NOT NULL,
            supplier_id VARCHAR(20) NOT NULL,
            qty_received INTEGER,
            FOREIGN KEY (po_id) REFERENCES inventory.purchase_orders(po_id) ON DELETE SET NULL,
            FOREIGN KEY (item_id) REFERENCES inventory.items(item_id) ON DELETE CASCADE,
            FOREIGN KEY (location_id) REFERENCES inventory.locations(location_id) ON DELETE CASCADE,
            FOREIGN KEY (supplier_id) REFERENCES inventory.suppliers(supplier_id) ON DELETE CASCADE
        );
    """,
    
    'inventory_snapshots': """
        CREATE TABLE inventory.inventory_snapshots (
            week_ending DATE NOT NULL,
            item_id VARCHAR(20) NOT NULL,
            location_id VARCHAR(20) NOT NULL,
            on_hand_qty INTEGER,
            PRIMARY KEY (week_ending, item_id, location_id),
            FOREIGN KEY (item_id) REFERENCES inventory.items(item_id) ON DELETE CASCADE,
            FOREIGN KEY (location_id) REFERENCES inventory.locations(location_id) ON DELETE CASCADE
        );
    """,
    
    'non_moving_candidates': """
        CREATE TABLE inventory.non_moving_candidates (
            item_id VARCHAR(20) NOT NULL,
            location_id VARCHAR(20) NOT NULL,
            last_sale_week DATE,
            last_receipt_week DATE,
            last_movement_week DATE,
            weeks_since_last_movement INTEGER,
            non_moving_flag BOOLEAN,
            recommended_action VARCHAR(255),
            PRIMARY KEY (item_id, location_id),
            FOREIGN KEY (item_id) REFERENCES inventory.items(item_id) ON DELETE CASCADE,
            FOREIGN KEY (location_id) REFERENCES inventory.locations(location_id) ON DELETE CASCADE
        );
    """,
    
    'item_weekly_metrics': """
        CREATE TABLE inventory.item_weekly_metrics (
            item_id VARCHAR(20) NOT NULL,
            location_id VARCHAR(20) NOT NULL,
            week_ending DATE NOT NULL,
            qty_sold INTEGER,
            on_hand INTEGER,
            forecast_qty INTEGER,
            category VARCHAR(50),
            shelf_life_days INTEGER,
            launch_date DATE,
            obsolete_date DATE,
            PRIMARY KEY (item_id, location_id, week_ending),
            FOREIGN KEY (item_id) REFERENCES inventory.items(item_id) ON DELETE CASCADE,
            FOREIGN KEY (location_id) REFERENCES inventory.locations(location_id) ON DELETE CASCADE
        );
        CREATE INDEX idx_item_weekly_metrics_week ON inventory.item_weekly_metrics(week_ending);
        CREATE INDEX idx_item_weekly_metrics_category ON inventory.item_weekly_metrics(category);
    """,
}

# Column name mappings (Excel column -> PostgreSQL column)
COLUMN_MAPPINGS = {
    'calendar_weeks': {
        'week_ending': 'week_ending',
        'fiscal_week': 'fiscal_week',
        'fiscal_year': 'fiscal_year',
    },
    'items': {
        'item_id': 'item_id',
        'description': 'description',
        'category': 'category',
        'uom': 'uom',
        'shelf_life_days': 'shelf_life_days',
        'launch_date': 'launch_date',
        'obsolete_date': 'obsolete_date',
    },
    'suppliers': {
        'supplier_id': 'supplier_id',
        'supplier_name': 'supplier_name',
        'base_lead_time_days': 'base_lead_time_days',
        'on_time_delivery_rate': 'on_time_delivery_rate',
        'defect_rate_pct': 'defect_rate_pct',
    },
    'locations': {
        'location_id': 'location_id',
        'name': 'name',
    },
    'item_supplier_sourcing': {
        'item_id': 'item_id',
        'supplier_id': 'supplier_id',
        'sourcing_split_pct': 'sourcing_split_pct',
    },
    'reorder_policy': {
        'item_id': 'item_id',
        'min_qty': 'min_qty',
        'max_qty': 'max_qty',
    },
    'lead_time_history': {
        'supplier_id': 'supplier_id',
        'month': 'month',
        'avg_lead_time_days': 'avg_lead_time_days',
    },
    'sales_weekly': {
        'week_ending': 'week_ending',
        'item_id': 'item_id',
        'location_id': 'location_id',
        'qty_sold': 'qty_sold',
    },
    'forecasts_weekly': {
        'week_ending': 'week_ending',
        'item_id': 'item_id',
        'location_id': 'location_id',
        'forecast_qty': 'forecast_qty',
    },
    'purchase_orders': {
        'po_id': 'po_id',
        'order_week': 'order_week',
        'expected_week': 'expected_week',
        'item_id': 'item_id',
        'location_id': 'location_id',
        'supplier_id': 'supplier_id',
        'qty_ordered': 'qty_ordered',
    },
    'receipts': {
        'receipt_id': 'receipt_id',
        'po_id': 'po_id',
        'receipt_week': 'receipt_week',
        'item_id': 'item_id',
        'location_id': 'location_id',
        'supplier_id': 'supplier_id',
        'qty_received': 'qty_received',
    },
    'inventory_snapshots': {
        'week_ending': 'week_ending',
        'item_id': 'item_id',
        'location_id': 'location_id',
        'on_hand_qty': 'on_hand_qty',
    },
    'non_moving_candidates': {
        'item_id': 'item_id',
        'location_id': 'location_id',
        'last_sale_week': 'last_sale_week',
        'last_receipt_week': 'last_receipt_week',
        'last_movement_week': 'last_movement_week',
        'weeks_since_last_movement': 'weeks_since_last_movement',
        'non_moving_flag': 'non_moving_flag',
        'recommended_action': 'recommended_action',
    },
}


def get_connection():
    """Create and return a database connection."""
    return psycopg2.connect(**DB_CONFIG)


def create_schema(cursor):
    """Create the inventory schema if it doesn't exist."""
    print(f"Creating schema '{SCHEMA_NAME}' if not exists...")
    cursor.execute(sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(sql.Identifier(SCHEMA_NAME)))
    print(f"  Schema '{SCHEMA_NAME}' ready.")


def drop_all_tables(cursor):
    """Drop all tables in reverse order to respect FK constraints."""
    print("Dropping existing tables...")
    for table in reversed(TABLE_ORDER):
        cursor.execute(sql.SQL("DROP TABLE IF EXISTS {}.{} CASCADE").format(
            sql.Identifier(SCHEMA_NAME),
            sql.Identifier(table)
        ))
        print(f"  Dropped: {SCHEMA_NAME}.{table}")


def create_all_tables(cursor):
    """Create all tables in order."""
    print(f"\nCreating tables in schema '{SCHEMA_NAME}'...")
    for table in TABLE_ORDER:
        cursor.execute(SCHEMA_SQL[table])
        print(f"  Created: {SCHEMA_NAME}.{table}")


def clean_value(val):
    """Convert a value to a proper Python type, handling NaN/NaT."""
    if pd.isna(val):
        return None
    if isinstance(val, pd.Timestamp):
        return val.date()
    if isinstance(val, float) and val != val:  # NaN check
        return None
    return val


def clean_dataframe(df, table_name):
    """Clean and prepare dataframe for insertion."""
    # Convert column names to lowercase and snake_case
    df.columns = df.columns.str.lower().str.replace(' ', '_')
    
    # Get expected columns for this table
    expected_cols = list(COLUMN_MAPPINGS[table_name].keys())
    
    # Select only expected columns that exist
    available_cols = [col for col in expected_cols if col in df.columns]
    df = df[available_cols].copy()
    
    # Convert datetime columns to date first
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].apply(lambda x: x.date() if pd.notnull(x) else None)
    
    # Handle boolean conversion for non_moving_flag
    if 'non_moving_flag' in df.columns:
        df['non_moving_flag'] = df['non_moving_flag'].apply(
            lambda x: True if x in [True, 'True', 'true', 1, '1'] else 
                     (False if x in [False, 'False', 'false', 0, '0'] else None)
        )
    
    # Replace all NaN/NaT with None for proper NULL handling
    # Apply clean_value to each cell
    df = df.applymap(clean_value)
    
    return df


def insert_data(cursor, table_name, df, batch_size=5000):
    """Insert data into table using batch inserts."""
    if df.empty:
        print(f"  No data to insert for {table_name}")
        return 0
    
    columns = list(df.columns)
    
    # Convert dataframe to list of tuples
    data = [tuple(row) for row in df.values]
    
    # Create insert query with schema
    insert_query = sql.SQL("INSERT INTO {}.{} ({}) VALUES %s").format(
        sql.Identifier(SCHEMA_NAME),
        sql.Identifier(table_name),
        sql.SQL(', ').join(map(sql.Identifier, columns))
    )
    
    # Insert in batches
    total_inserted = 0
    for i in range(0, len(data), batch_size):
        batch = data[i:i + batch_size]
        execute_values(cursor, insert_query, batch)
        total_inserted += len(batch)
        if len(data) > batch_size:
            print(f"    Inserted {total_inserted}/{len(data)} rows...")
    
    return total_inserted


def populate_item_weekly_metrics(cursor):
    """Populate item_weekly_metrics table by joining existing tables."""
    print("\n  [item_weekly_metrics]")
    print("    Populating from existing tables (sales, inventory, forecasts, items)...")
    
    insert_query = """
        INSERT INTO inventory.item_weekly_metrics (
            item_id, location_id, week_ending, qty_sold, on_hand,
            forecast_qty, category, shelf_life_days, launch_date, obsolete_date
        )
        SELECT 
            COALESCE(s.item_id, inv.item_id, f.item_id) AS item_id,
            COALESCE(s.location_id, inv.location_id, f.location_id) AS location_id,
            COALESCE(s.week_ending, inv.week_ending, f.week_ending) AS week_ending,
            COALESCE(s.qty_sold, 0) AS qty_sold,
            COALESCE(inv.on_hand_qty, 0) AS on_hand,
            COALESCE(f.forecast_qty, 0) AS forecast_qty,
            i.category,
            i.shelf_life_days,
            i.launch_date,
            i.obsolete_date
        FROM inventory.sales_weekly s
        FULL OUTER JOIN inventory.inventory_snapshots inv 
            ON s.item_id = inv.item_id 
            AND s.location_id = inv.location_id 
            AND s.week_ending = inv.week_ending
        FULL OUTER JOIN inventory.forecasts_weekly f 
            ON COALESCE(s.item_id, inv.item_id) = f.item_id 
            AND COALESCE(s.location_id, inv.location_id) = f.location_id 
            AND COALESCE(s.week_ending, inv.week_ending) = f.week_ending
        JOIN inventory.items i 
            ON i.item_id = COALESCE(s.item_id, inv.item_id, f.item_id)
        ORDER BY item_id, location_id, week_ending;
    """
    
    cursor.execute(insert_query)
    rows_inserted = cursor.rowcount
    print(f"    Inserted {rows_inserted} rows [OK]")
    return rows_inserted


def import_excel_to_postgres():
    """Main function to import Excel data to PostgreSQL."""
    print("=" * 60)
    print("Excel to PostgreSQL Import")
    print("=" * 60)
    
    # Validate configuration
    missing = [k for k, v in DB_CONFIG.items() if not v]
    if missing:
        print(f"\nError: Missing environment variables: {missing}")
        print("Please check your .env file.")
        sys.exit(1)
    
    print(f"\nDatabase: {DB_CONFIG['host']}/{DB_CONFIG['database']}")
    print(f"Schema: {SCHEMA_NAME}")
    print(f"Excel file: {EXCEL_FILE}")
    
    if not EXCEL_FILE.exists():
        print(f"\nError: Excel file not found: {EXCEL_FILE}")
        sys.exit(1)
    
    # Load Excel file
    print("\nLoading Excel file...")
    excel = pd.ExcelFile(EXCEL_FILE)
    print(f"  Found sheets: {excel.sheet_names}")
    
    # Connect to database
    print("\nConnecting to database...")
    try:
        conn = get_connection()
        conn.autocommit = False
        cursor = conn.cursor()
        print("  Connected successfully!")
    except Exception as e:
        print(f"\nError connecting to database: {e}")
        sys.exit(1)
    
    try:
        # Create schema and drop/recreate tables
        create_schema(cursor)
        drop_all_tables(cursor)
        create_all_tables(cursor)
        # Don't commit yet - wait until data is inserted
        
        # Import data for each table
        print("\nImporting data...")
        total_rows = 0
        
        for sheet_name, table_name in SHEET_TO_TABLE.items():
            print(f"\n  [{table_name}]")
            
            # Read sheet
            df = pd.read_excel(excel, sheet_name=sheet_name)
            print(f"    Read {len(df)} rows from sheet '{sheet_name}'")
            
            # Clean data
            df = clean_dataframe(df, table_name)
            
            # Insert data
            rows_inserted = insert_data(cursor, table_name, df)
            conn.commit()  # Commit after each table to save progress
            total_rows += rows_inserted
            print(f"    Inserted {rows_inserted} rows [OK]")
        
        # Populate derived table from existing data (using JOINs)
        rows_inserted = populate_item_weekly_metrics(cursor)
        conn.commit()
        total_rows += rows_inserted
        
        # Final commit
        conn.commit()
        print("\n" + "=" * 60)
        print(f"SUCCESS! Imported {total_rows:,} total rows")
        print("=" * 60)
        
        # Print summary
        print(f"\nTable row counts in schema '{SCHEMA_NAME}':")
        for table in TABLE_ORDER:
            cursor.execute(sql.SQL("SELECT COUNT(*) FROM {}.{}").format(
                sql.Identifier(SCHEMA_NAME),
                sql.Identifier(table)
            ))
            count = cursor.fetchone()[0]
            print(f"  {SCHEMA_NAME}.{table}: {count:,} rows")
        
    except Exception as e:
        conn.rollback()
        print(f"\nError during import: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()
        print("\nDatabase connection closed.")


if __name__ == '__main__':
    import_excel_to_postgres()

