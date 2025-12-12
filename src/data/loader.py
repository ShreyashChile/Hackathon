"""
Data loading module for CSV and Excel files.
"""

import pandas as pd
from pathlib import Path
from typing import Optional
import logging

from .schemas import AnalysisDataset

logger = logging.getLogger(__name__)


class DataLoader:
    """Load data from CSV and Excel files."""
    
    def __init__(self, data_dir: Path | str = "data"):
        self.data_dir = Path(data_dir)
        if not self.data_dir.exists():
            raise FileNotFoundError(f"Data directory not found: {self.data_dir}")
    
    def _load_csv(self, filename: str, parse_dates: Optional[list] = None) -> pd.DataFrame:
        """Load a CSV file from the data directory."""
        filepath = self.data_dir / filename
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        logger.info(f"Loading {filename}...")
        df = pd.read_csv(filepath, parse_dates=parse_dates)
        logger.info(f"Loaded {len(df)} rows from {filename}")
        return df
    
    def load_items(self) -> pd.DataFrame:
        """Load item master data."""
        df = self._load_csv("items.csv", parse_dates=['launch_date', 'obsolete_date'])
        return df
    
    def load_locations(self) -> pd.DataFrame:
        """Load location data."""
        return self._load_csv("locations.csv")
    
    def load_sales_history(self) -> pd.DataFrame:
        """Load weekly sales history."""
        df = self._load_csv("sales_history_weekly.csv", parse_dates=['week_ending'])
        return df
    
    def load_inventory_snapshots(self) -> pd.DataFrame:
        """Load weekly inventory snapshots."""
        df = self._load_csv("inventory_snapshots_weekly.csv", parse_dates=['week_ending'])
        return df
    
    def load_forecasts(self) -> pd.DataFrame:
        """Load weekly forecasts."""
        df = self._load_csv("forecasts_weekly.csv", parse_dates=['week_ending'])
        return df
    
    def load_reorder_policies(self) -> pd.DataFrame:
        """Load item reorder policies."""
        return self._load_csv("item_reorder_policy.csv")
    
    def load_suppliers(self) -> pd.DataFrame:
        """Load supplier data."""
        return self._load_csv("suppliers.csv")
    
    def load_non_moving_candidates(self) -> pd.DataFrame:
        """Load pre-computed non-moving candidates."""
        df = self._load_csv(
            "non_moving_candidates.csv",
            parse_dates=['last_sale_week', 'last_receipt_week', 'last_movement_week']
        )
        return df
    
    def load_supplier_sourcing(self) -> pd.DataFrame:
        """Load item-supplier sourcing data."""
        return self._load_csv("item_supplier_sourcing.csv")
    
    def load_calendar(self) -> pd.DataFrame:
        """Load calendar weeks."""
        df = self._load_csv("calendar_weeks.csv", parse_dates=['week_ending'])
        return df
    
    def load_purchase_orders(self) -> pd.DataFrame:
        """Load purchase orders data."""
        df = self._load_csv(
            "purchase_orders.csv",
            parse_dates=['order_week', 'expected_week']
        )
        return df
    
    def load_all(self) -> AnalysisDataset:
        """Load all data files into an AnalysisDataset."""
        logger.info("Loading all data files...")
        
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

