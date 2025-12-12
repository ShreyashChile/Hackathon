"""
Non-moving inventory detection module.

Identifies slow-moving, non-moving, and dead stock based on 
configurable time thresholds.
"""

import pandas as pd
import numpy as np
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum
import logging

from ..config import get_config, NonMovingConfig
from ..data.schemas import AnalysisDataset

logger = logging.getLogger(__name__)


class MovementCategory(str, Enum):
    """Inventory movement categories."""
    ACTIVE = "active"
    SLOW_MOVING = "slow_moving"
    NON_MOVING = "non_moving"
    DEAD_STOCK = "dead_stock"


class NonMovingDetector:
    """Detect non-moving inventory based on movement thresholds."""
    
    def __init__(self, config: Optional[NonMovingConfig] = None):
        self.config = config or get_config().non_moving
    
    def _calculate_days_since_last_movement(
        self,
        sales_history: pd.DataFrame,
        analysis_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """Calculate days since last movement for each item-location."""
        
        if analysis_date is None:
            analysis_date = sales_history['week_ending'].max()
        
        # Find last sale date for each item-location
        movement_data = sales_history[sales_history['qty_sold'] > 0].groupby(
            ['item_id', 'location_id']
        ).agg({
            'week_ending': 'max',
            'qty_sold': 'sum'
        }).reset_index()
        
        movement_data.columns = ['item_id', 'location_id', 'last_movement_date', 'total_qty_sold']
        
        # Get all item-location combinations
        all_combinations = sales_history[['item_id', 'location_id']].drop_duplicates()
        
        # Merge to get all combinations
        result = all_combinations.merge(movement_data, on=['item_id', 'location_id'], how='left')
        
        # Calculate days since last movement
        result['days_since_movement'] = (
            pd.Timestamp(analysis_date) - result['last_movement_date']
        ).dt.days
        
        # Items that never moved
        result['days_since_movement'] = result['days_since_movement'].fillna(9999)
        result['total_qty_sold'] = result['total_qty_sold'].fillna(0)
        
        return result
    
    def _categorize_movement(self, days: float) -> MovementCategory:
        """Categorize inventory based on days since movement."""
        if days <= self.config.slow_moving_days:
            return MovementCategory.ACTIVE
        elif days <= self.config.non_moving_days:
            return MovementCategory.SLOW_MOVING
        elif days <= self.config.dead_stock_days:
            return MovementCategory.NON_MOVING
        else:
            return MovementCategory.DEAD_STOCK
    
    def detect(
        self,
        dataset: AnalysisDataset,
        analysis_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        Detect non-moving inventory.
        
        Returns DataFrame with columns:
        - item_id, location_id
        - last_movement_date
        - days_since_movement
        - movement_category
        - total_qty_sold
        - current_inventory
        - recommended_action
        """
        logger.info("Detecting non-moving inventory...")
        
        if analysis_date is None:
            analysis_date = dataset.sales_history['week_ending'].max()
        
        # Calculate movement metrics
        result = self._calculate_days_since_last_movement(
            dataset.sales_history, 
            analysis_date
        )
        
        # Categorize each item-location
        result['movement_category'] = result['days_since_movement'].apply(
            self._categorize_movement
        )
        
        # Get current inventory levels
        latest_inventory = dataset.inventory_snapshots[
            dataset.inventory_snapshots['week_ending'] == 
            dataset.inventory_snapshots['week_ending'].max()
        ][['item_id', 'location_id', 'on_hand_qty']]
        
        result = result.merge(
            latest_inventory,
            on=['item_id', 'location_id'],
            how='left'
        )
        result.rename(columns={'on_hand_qty': 'current_inventory'}, inplace=True)
        
        # Add item details
        result = result.merge(
            dataset.items[['item_id', 'category', 'shelf_life_days', 'obsolete_date']],
            on='item_id',
            how='left'
        )
        
        # Calculate shelf life risk
        result['shelf_life_at_risk'] = (
            (result['days_since_movement'] > result['shelf_life_days'] * 0.5) &
            (result['current_inventory'] > 0)
        )
        
        # Add recommended actions
        result['recommended_action'] = result.apply(
            self._get_recommended_action, axis=1
        )
        
        # Calculate risk score (0-100)
        result['non_moving_risk_score'] = result.apply(
            self._calculate_risk_score, axis=1
        )
        
        logger.info(f"Detection complete. Found {len(result)} item-location combinations")
        logger.info(f"Movement category breakdown:\n{result['movement_category'].value_counts()}")
        
        return result.sort_values('non_moving_risk_score', ascending=False)
    
    def _get_recommended_action(self, row: pd.Series) -> str:
        """Get recommended action based on movement category and inventory."""
        category = row['movement_category']
        has_inventory = row['current_inventory'] > 0 if pd.notna(row['current_inventory']) else False
        shelf_life_risk = row.get('shelf_life_at_risk', False)
        
        if category == MovementCategory.ACTIVE:
            return "Monitor - Normal movement"
        elif category == MovementCategory.SLOW_MOVING:
            if has_inventory:
                return "Review pricing / Promote to accelerate movement"
            return "Reduce reorder quantities"
        elif category == MovementCategory.NON_MOVING:
            if shelf_life_risk:
                return "URGENT: Clear stock before expiry"
            if has_inventory:
                return "Put supply orders on hold / Consider markdowns"
            return "Review demand patterns / Consider discontinuation"
        else:  # DEAD_STOCK
            if has_inventory:
                return "Evaluate disposal / Write-off candidate"
            return "Discontinue SKU / Remove from catalog"
    
    def _calculate_risk_score(self, row: pd.Series) -> float:
        """Calculate a composite risk score (0-100) for non-moving inventory."""
        score = 0.0
        
        # Days since movement component (40% weight)
        days = row['days_since_movement']
        if days >= self.config.dead_stock_days:
            score += 40
        elif days >= self.config.non_moving_days:
            score += 30
        elif days >= self.config.slow_moving_days:
            score += 15
        
        # Inventory level component (30% weight)
        inventory = row['current_inventory'] if pd.notna(row['current_inventory']) else 0
        if inventory > 0:
            score += 30  # Having inventory increases risk
        
        # Shelf life risk component (20% weight)
        if row.get('shelf_life_at_risk', False):
            score += 20
        
        # Product lifecycle component (10% weight)
        if row.get('category') == 'Declining':
            score += 10
        elif row.get('category') == 'SlowMover':
            score += 5
        
        return min(score, 100)
    
    def get_summary_by_location(self, detection_result: pd.DataFrame) -> pd.DataFrame:
        """Get summary statistics by location."""
        summary = detection_result.groupby(['location_id', 'movement_category']).agg({
            'item_id': 'count',
            'current_inventory': 'sum',
            'non_moving_risk_score': 'mean'
        }).reset_index()
        
        summary.columns = ['location_id', 'movement_category', 'sku_count', 
                          'total_inventory', 'avg_risk_score']
        return summary
    
    def get_summary_by_category(self, detection_result: pd.DataFrame) -> pd.DataFrame:
        """Get summary statistics by product category."""
        summary = detection_result.groupby(['category', 'movement_category']).agg({
            'item_id': 'count',
            'current_inventory': 'sum',
            'non_moving_risk_score': 'mean'
        }).reset_index()
        
        summary.columns = ['category', 'movement_category', 'sku_count',
                          'total_inventory', 'avg_risk_score']
        return summary
    
    def get_high_risk_items(
        self, 
        detection_result: pd.DataFrame,
        risk_threshold: float = 50.0
    ) -> pd.DataFrame:
        """Get items with risk score above threshold."""
        return detection_result[
            detection_result['non_moving_risk_score'] >= risk_threshold
        ].copy()

