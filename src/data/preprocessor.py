"""
Data preprocessing and feature engineering module.
"""

import pandas as pd
import numpy as np
from typing import Optional
from datetime import datetime, timedelta
import logging

from .schemas import AnalysisDataset
from ..config import get_config

logger = logging.getLogger(__name__)


class DataPreprocessor:
    """Preprocess and engineer features for analysis."""
    
    def __init__(self, dataset: AnalysisDataset):
        self.dataset = dataset
        self.config = get_config()
    
    def merge_data(self) -> pd.DataFrame:
        """Merge sales, inventory, and forecast data."""
        logger.info("Merging sales, inventory, and forecast data...")
        
        # Start with sales history
        merged = self.dataset.sales_history.copy()
        
        # Merge inventory snapshots
        merged = merged.merge(
            self.dataset.inventory_snapshots[['week_ending', 'item_id', 'location_id', 'on_hand_qty']],
            on=['week_ending', 'item_id', 'location_id'],
            how='left'
        )
        
        # Merge forecasts
        merged = merged.merge(
            self.dataset.forecasts[['week_ending', 'item_id', 'location_id', 'forecast_qty']],
            on=['week_ending', 'item_id', 'location_id'],
            how='left'
        )
        
        # Merge item master data
        merged = merged.merge(
            self.dataset.items[['item_id', 'category', 'shelf_life_days', 'launch_date', 'obsolete_date']],
            on='item_id',
            how='left'
        )
        
        # Merge reorder policies
        merged = merged.merge(
            self.dataset.reorder_policies,
            on='item_id',
            how='left'
        )
        
        logger.info(f"Merged data shape: {merged.shape}")
        return merged
    
    def add_time_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add time-based features."""
        logger.info("Adding time features...")
        
        df = df.copy()
        df['year'] = df['week_ending'].dt.year
        df['month'] = df['week_ending'].dt.month
        df['week_of_year'] = df['week_ending'].dt.isocalendar().week
        df['quarter'] = df['week_ending'].dt.quarter
        
        # Days since launch
        df['days_since_launch'] = (df['week_ending'] - df['launch_date']).dt.days
        
        # Days until obsolete (if applicable)
        df['days_until_obsolete'] = np.where(
            df['obsolete_date'].notna(),
            (df['obsolete_date'] - df['week_ending']).dt.days,
            np.nan
        )
        
        return df
    
    def add_rolling_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add rolling window features for demand analysis."""
        logger.info("Adding rolling features...")
        
        df = df.copy()
        df = df.sort_values(['item_id', 'location_id', 'week_ending'])
        
        # Group by item-location for rolling calculations
        grouped = df.groupby(['item_id', 'location_id'])
        
        # Short-term moving average (4 weeks)
        df['ma_4w'] = grouped['qty_sold'].transform(
            lambda x: x.rolling(window=4, min_periods=1).mean()
        )
        
        # Long-term moving average (12 weeks)
        df['ma_12w'] = grouped['qty_sold'].transform(
            lambda x: x.rolling(window=12, min_periods=1).mean()
        )
        
        # Rolling standard deviation (12 weeks)
        df['std_12w'] = grouped['qty_sold'].transform(
            lambda x: x.rolling(window=12, min_periods=2).std()
        )
        
        # Coefficient of variation
        df['cv_12w'] = df['std_12w'] / df['ma_12w'].replace(0, np.nan)
        
        # Week-over-week change
        df['wow_change'] = grouped['qty_sold'].transform(lambda x: x.diff())
        df['wow_pct_change'] = grouped['qty_sold'].transform(lambda x: x.pct_change())
        
        # Cumulative sum
        df['cumsum_qty'] = grouped['qty_sold'].transform('cumsum')
        
        return df
    
    def add_movement_features(self, df: pd.DataFrame, analysis_date: Optional[datetime] = None) -> pd.DataFrame:
        """Add features related to inventory movement."""
        logger.info("Adding movement features...")
        
        df = df.copy()
        
        if analysis_date is None:
            analysis_date = df['week_ending'].max()
        
        # Calculate last sale date for each item-location
        last_sales = df[df['qty_sold'] > 0].groupby(['item_id', 'location_id'])['week_ending'].max()
        last_sales = last_sales.reset_index()
        last_sales.columns = ['item_id', 'location_id', 'last_sale_date']
        
        df = df.merge(last_sales, on=['item_id', 'location_id'], how='left')
        
        # Days since last sale
        df['days_since_last_sale'] = (df['week_ending'] - df['last_sale_date']).dt.days
        df['days_since_last_sale'] = df['days_since_last_sale'].fillna(9999)
        
        # Has movement flag
        df['has_recent_movement'] = df['days_since_last_sale'] <= self.config.non_moving.slow_moving_days
        
        return df
    
    def add_forecast_accuracy_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add features comparing actuals to forecasts."""
        logger.info("Adding forecast accuracy features...")
        
        df = df.copy()
        
        # Forecast error
        df['forecast_error'] = df['qty_sold'] - df['forecast_qty']
        df['forecast_error_pct'] = np.where(
            df['forecast_qty'] > 0,
            df['forecast_error'] / df['forecast_qty'],
            np.nan
        )
        
        # Absolute percentage error
        df['ape'] = np.abs(df['forecast_error_pct'])
        
        return df
    
    def add_inventory_health_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add inventory health indicators."""
        logger.info("Adding inventory health features...")
        
        df = df.copy()
        
        # Weeks of supply (inventory / avg weekly demand)
        df['weeks_of_supply'] = np.where(
            df['ma_4w'] > 0,
            df['on_hand_qty'] / df['ma_4w'],
            np.inf
        )
        
        # Stock status relative to min/max
        df['below_min'] = df['on_hand_qty'] < df['min_qty']
        df['above_max'] = df['on_hand_qty'] > df['max_qty']
        df['stock_position'] = np.where(
            df['below_min'], 'understocked',
            np.where(df['above_max'], 'overstocked', 'optimal')
        )
        
        # Shelf life remaining percentage
        df['shelf_life_consumed_pct'] = np.where(
            df['shelf_life_days'] > 0,
            df['days_since_launch'] / df['shelf_life_days'],
            0
        )
        
        return df
    
    def preprocess(self) -> AnalysisDataset:
        """Run full preprocessing pipeline."""
        logger.info("Starting preprocessing pipeline...")
        
        # Merge all data
        merged = self.merge_data()
        
        # Add all features
        merged = self.add_time_features(merged)
        merged = self.add_rolling_features(merged)
        merged = self.add_movement_features(merged)
        merged = self.add_forecast_accuracy_features(merged)
        merged = self.add_inventory_health_features(merged)
        
        # Store in dataset
        self.dataset.merged_data = merged
        
        logger.info(f"Preprocessing complete. Final shape: {merged.shape}")
        return self.dataset
    
    def get_latest_snapshot(self) -> pd.DataFrame:
        """Get the latest data snapshot for each item-location."""
        if self.dataset.merged_data is None:
            self.preprocess()
        
        latest_date = self.dataset.merged_data['week_ending'].max()
        return self.dataset.merged_data[
            self.dataset.merged_data['week_ending'] == latest_date
        ].copy()
    
    def get_time_series(self, item_id: str, location_id: str) -> pd.DataFrame:
        """Get time series data for a specific item-location combination."""
        if self.dataset.merged_data is None:
            self.preprocess()
        
        mask = (
            (self.dataset.merged_data['item_id'] == item_id) &
            (self.dataset.merged_data['location_id'] == location_id)
        )
        return self.dataset.merged_data[mask].sort_values('week_ending').copy()

