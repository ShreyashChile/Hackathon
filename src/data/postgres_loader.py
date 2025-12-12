"""
PostgreSQL data loader module.

Loads analysis data directly from PostgreSQL tables instead of CSV files.
Ideal for cron job scenarios where data is already in the database.
"""

import pandas as pd
from typing import Optional
import logging

import psycopg2
from dotenv import load_dotenv

from .schemas import AnalysisDataset
from ..config import get_config, DatabaseConfig

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class PostgresDataLoader:
    """Load analysis data directly from PostgreSQL tables."""
    
    def __init__(self, db_config: Optional[DatabaseConfig] = None):
        """
        Initialize PostgreSQL data loader.
        
        Args:
            db_config: Database configuration. If None, loads from environment.
        """
        if db_config is None:
            db_config = DatabaseConfig.from_env()
        
        self.db_config = db_config
        self.schema_name = db_config.schema_name
    
    def _get_connection(self):
        """Get database connection."""
        return psycopg2.connect(
            host=self.db_config.host,
            database=self.db_config.database,
            user=self.db_config.user,
            password=self.db_config.password,
            port=self.db_config.port
        )
    
    def _load_table(self, table_name: str, parse_dates: Optional[list] = None) -> pd.DataFrame:
        """
        Load a table from PostgreSQL.
        
        Args:
            table_name: Name of the table (without schema prefix)
            parse_dates: List of columns to parse as dates
            
        Returns:
            DataFrame with table data
        """
        conn = self._get_connection()
        
        query = f"SELECT * FROM {self.schema_name}.{table_name}"
        
        logger.info(f"Loading {self.schema_name}.{table_name}...")
        
        df = pd.read_sql_query(query, conn, parse_dates=parse_dates)
        
        conn.close()
        
        logger.info(f"Loaded {len(df)} rows from {self.schema_name}.{table_name}")
        
        return df
    
    def load_items(self) -> pd.DataFrame:
        """Load item master data."""
        df = self._load_table("items", parse_dates=['launch_date', 'obsolete_date'])
        return df
    
    def load_locations(self) -> pd.DataFrame:
        """Load location data."""
        return self._load_table("locations")
    
    def load_sales_history(self) -> pd.DataFrame:
        """Load weekly sales history."""
        # PostgreSQL table is 'sales_weekly', map to expected column names
        df = self._load_table("sales_weekly", parse_dates=['week_ending'])
        return df
    
    def load_inventory_snapshots(self) -> pd.DataFrame:
        """Load weekly inventory snapshots."""
        df = self._load_table("inventory_snapshots", parse_dates=['week_ending'])
        return df
    
    def load_forecasts(self) -> pd.DataFrame:
        """Load weekly forecasts."""
        df = self._load_table("forecasts_weekly", parse_dates=['week_ending'])
        return df
    
    def load_reorder_policies(self) -> pd.DataFrame:
        """Load item reorder policies."""
        # PostgreSQL table is 'reorder_policy', singular
        return self._load_table("reorder_policy")
    
    def load_suppliers(self) -> pd.DataFrame:
        """Load supplier data."""
        return self._load_table("suppliers")
    
    def load_non_moving_candidates(self) -> pd.DataFrame:
        """Load pre-computed non-moving candidates."""
        df = self._load_table(
            "non_moving_candidates",
            parse_dates=['last_sale_week', 'last_receipt_week', 'last_movement_week']
        )
        return df
    
    def load_purchase_orders(self) -> pd.DataFrame:
        """Load purchase orders data."""
        df = self._load_table(
            "purchase_orders",
            parse_dates=['order_week', 'expected_week']
        )
        return df
    
    def load_all(self) -> AnalysisDataset:
        """
        Load all data from PostgreSQL into an AnalysisDataset.
        
        Returns:
            AnalysisDataset with all required data loaded from PostgreSQL
        """
        logger.info("Loading all data from PostgreSQL...")
        
        dataset = AnalysisDataset(
            items=self.load_items(),
            locations=self.load_locations(),
            sales_history=self.load_sales_history(),
            inventory_snapshots=self.load_inventory_snapshots(),
            forecasts=self.load_forecasts(),
            reorder_policies=self.load_reorder_policies(),
            suppliers=self.load_suppliers(),
            non_moving_candidates=self.load_non_moving_candidates(),
            purchase_orders=self.load_purchase_orders()
        )
        
        logger.info(f"Loaded data for {len(dataset.sku_list)} SKUs across {len(dataset.location_list)} locations")
        logger.info(f"Date range: {dataset.date_range[0]} to {dataset.date_range[1]}")
        
        return dataset

