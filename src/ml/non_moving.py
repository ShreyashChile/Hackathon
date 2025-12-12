"""
Non-moving inventory detection module.

Identifies non-moving items based on:
- Sales/Receipt = 0 for configurable duration (12/26/52 weeks)
- Open PO status determines "on_hold" vs "non_moving"

Recommended actions include:
- Sales strategy
- Interplant transfer
- Forecast check
- Mark obsolete
"""

import pandas as pd
import numpy as np
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from enum import Enum
import logging

from ..config import get_config, NonMovingConfig
from ..data.schemas import AnalysisDataset

logger = logging.getLogger(__name__)


class MovementStatus(str, Enum):
    """Status for non-moving items."""
    ACTIVE = "active"
    NON_MOVING = "non_moving"
    ON_HOLD = "on_hold"  # Non-moving with open PO


class RecommendedAction(str, Enum):
    """Recommended actions for non-moving items."""
    MONITOR = "monitor"
    SALES_STRATEGY = "sales_strategy"
    INTERPLANT_TRANSFER = "interplant_transfer"
    CHECK_FORECAST = "check_forecast"
    MARK_OBSOLETE = "mark_obsolete"


# Legacy enum for backwards compatibility
class MovementCategory(str, Enum):
    """Inventory movement categories (legacy)."""
    ACTIVE = "active"
    SLOW_MOVING = "slow_moving"
    NON_MOVING = "non_moving"
    DEAD_STOCK = "dead_stock"


class NonMovingDetector:
    """Detect non-moving inventory based on configurable thresholds."""
    
    def __init__(self, config: Optional[NonMovingConfig] = None):
        self.config = config or get_config().non_moving
    
    def _get_open_pos(
        self,
        purchase_orders: pd.DataFrame,
        analysis_date: datetime
    ) -> pd.DataFrame:
        """
        Get open POs (expected_week >= analysis_date means not yet received).
        
        Args:
            purchase_orders: DataFrame with PO data
            analysis_date: Current analysis date
            
        Returns:
            DataFrame with open PO summary per item-location
        """
        if purchase_orders is None or purchase_orders.empty:
            return pd.DataFrame(columns=['item_id', 'location_id', 'has_open_po', 'open_po_qty', 'open_po_count'])
        
        # Consider PO as "open" if expected_week hasn't passed
        open_pos = purchase_orders[
            purchase_orders['expected_week'] >= pd.Timestamp(analysis_date)
        ].copy()
        
        if open_pos.empty:
            return pd.DataFrame(columns=['item_id', 'location_id', 'has_open_po', 'open_po_qty', 'open_po_count'])
        
        # Aggregate by item-location
        open_po_summary = open_pos.groupby(['item_id', 'location_id']).agg({
            'qty_ordered': 'sum',
            'po_id': 'count'
        }).reset_index()
        
        open_po_summary.columns = ['item_id', 'location_id', 'open_po_qty', 'open_po_count']
        open_po_summary['has_open_po'] = True
        
        return open_po_summary
    
    def _calculate_weeks_since_last_activity(
        self,
        dataset: AnalysisDataset,
        analysis_date: datetime
    ) -> pd.DataFrame:
        """
        Calculate weeks since last sale OR receipt for each item-location.
        Non-moving if BOTH sale and receipt are >= threshold weeks.
        
        Args:
            dataset: Analysis dataset
            analysis_date: Current analysis date
            
        Returns:
            DataFrame with activity metrics per item-location
        """
        sales = dataset.sales_history.copy()
        
        # Get last sale date (where qty_sold > 0)
        last_sales = sales[sales['qty_sold'] > 0].groupby(
            ['item_id', 'location_id']
        )['week_ending'].max().reset_index()
        last_sales.columns = ['item_id', 'location_id', 'last_sale_week']
        
        # Get all item-location combinations
        all_combinations = sales[['item_id', 'location_id']].drop_duplicates()
        
        result = all_combinations.merge(last_sales, on=['item_id', 'location_id'], how='left')
        
        # Calculate weeks since last sale
        result['weeks_since_sale'] = (
            (pd.Timestamp(analysis_date) - result['last_sale_week']).dt.days / 7
        ).fillna(9999).astype(int)
        
        # If we have receipt data in non_moving_candidates, use it
        if hasattr(dataset, 'non_moving_candidates') and not dataset.non_moving_candidates.empty:
            if 'last_receipt_week' in dataset.non_moving_candidates.columns:
                receipt_data = dataset.non_moving_candidates[
                    ['item_id', 'location_id', 'last_receipt_week']
                ].copy()
                result = result.merge(receipt_data, on=['item_id', 'location_id'], how='left')
                
                result['weeks_since_receipt'] = (
                    (pd.Timestamp(analysis_date) - result['last_receipt_week']).dt.days / 7
                ).fillna(9999).astype(int)
            else:
                result['last_receipt_week'] = pd.NaT
                result['weeks_since_receipt'] = 9999
        else:
            result['last_receipt_week'] = pd.NaT
            result['weeks_since_receipt'] = 9999
        
        # Last movement = min of sale and receipt (most recent activity)
        result['weeks_since_movement'] = result[['weeks_since_sale', 'weeks_since_receipt']].min(axis=1)
        
        # Also track days for legacy compatibility
        result['days_since_movement'] = result['weeks_since_movement'] * 7
        
        return result
    
    def _check_forecast_is_zero(
        self,
        forecasts: pd.DataFrame,
        item_id: str,
        location_id: str,
        analysis_date: datetime,
        weeks_ahead: int = 12
    ) -> Dict:
        """
        Check if forecast is zero for the next N weeks.
        
        Args:
            forecasts: Forecast DataFrame
            item_id: Item to check
            location_id: Location to check
            analysis_date: Current analysis date
            weeks_ahead: Number of weeks to look ahead
            
        Returns:
            Dict with forecast_is_zero flag and total forecast qty
        """
        if forecasts is None or forecasts.empty:
            return {'forecast_is_zero': True, 'total_forecast': 0}
        
        future_forecasts = forecasts[
            (forecasts['item_id'] == item_id) &
            (forecasts['location_id'] == location_id) &
            (forecasts['week_ending'] >= pd.Timestamp(analysis_date)) &
            (forecasts['week_ending'] <= pd.Timestamp(analysis_date) + timedelta(weeks=weeks_ahead))
        ]
        
        if future_forecasts.empty:
            return {'forecast_is_zero': True, 'total_forecast': 0}
        
        total_forecast = future_forecasts['forecast_qty'].sum()
        return {
            'forecast_is_zero': total_forecast == 0,
            'total_forecast': total_forecast
        }
    
    def _check_interplant_demand(
        self,
        dataset: AnalysisDataset,
        item_id: str,
        current_location: str,
        threshold_weeks: int
    ) -> Dict:
        """
        Check if other locations have recent demand for this item.
        
        Args:
            dataset: Analysis dataset
            item_id: Item to check
            current_location: Current location ID
            threshold_weeks: Weeks to consider as "recent"
            
        Returns:
            Dict with demand info from other locations
        """
        sales = dataset.sales_history
        
        other_location_sales = sales[
            (sales['item_id'] == item_id) &
            (sales['location_id'] != current_location) &
            (sales['qty_sold'] > 0)
        ]
        
        if other_location_sales.empty:
            return {
                'has_demand_elsewhere': False, 
                'locations_with_demand': [],
                'total_qty_elsewhere': 0
            }
        
        # Group by location and check recent activity
        recent_sales = other_location_sales.groupby('location_id').agg({
            'week_ending': 'max',
            'qty_sold': 'sum'
        }).reset_index()
        
        # Filter to locations with recent activity
        max_date = sales['week_ending'].max()
        threshold_date = max_date - timedelta(weeks=threshold_weeks)
        
        active_locations = recent_sales[
            recent_sales['week_ending'] >= threshold_date
        ]
        
        return {
            'has_demand_elsewhere': len(active_locations) > 0,
            'locations_with_demand': active_locations['location_id'].tolist(),
            'total_qty_elsewhere': active_locations['qty_sold'].sum() if len(active_locations) > 0 else 0
        }
    
    def _get_recommended_actions(
        self,
        row: pd.Series,
        dataset: AnalysisDataset,
        analysis_date: datetime,
        threshold_weeks: int
    ) -> List[str]:
        """
        Generate recommended actions for a non-moving item.
        
        Actions:
        - Sales Strategy: Consider promotions/discounts
        - Interplant Transfer: Move to locations with demand
        - Check Forecast: If forecast is 0, consider discontinuation
        - Mark Obsolete: If inactive for extended period
        
        Args:
            row: Row of data for the item-location
            dataset: Analysis dataset
            analysis_date: Current analysis date
            threshold_weeks: Weeks threshold used
            
        Returns:
            List of recommended action strings
        """
        actions = []
        
        if row['movement_status'] == MovementStatus.ACTIVE.value:
            return [RecommendedAction.MONITOR.value]
        
        # 1. Check forecast
        forecast_info = self._check_forecast_is_zero(
            dataset.forecasts,
            row['item_id'],
            row['location_id'],
            analysis_date
        )
        
        if forecast_info['forecast_is_zero']:
            actions.append(f"{RecommendedAction.CHECK_FORECAST.value}: Forecast is 0 - consider discontinuation")
        else:
            actions.append(f"{RecommendedAction.CHECK_FORECAST.value}: Forecast exists ({forecast_info['total_forecast']} units) - review demand patterns")
        
        # 2. Check interplant transfer opportunity
        interplant = self._check_interplant_demand(
            dataset, row['item_id'], row['location_id'], threshold_weeks
        )
        
        if interplant['has_demand_elsewhere']:
            locations = ', '.join(interplant['locations_with_demand'])
            actions.append(f"{RecommendedAction.INTERPLANT_TRANSFER.value}: Demand exists at {locations} ({interplant['total_qty_elsewhere']} units)")
        
        # 3. Sales strategy suggestion
        if row['current_inventory'] > 0:
            actions.append(f"{RecommendedAction.SALES_STRATEGY.value}: Consider promotions/discounts to clear {int(row['current_inventory'])} units")
        
        # 4. Mark obsolete suggestion
        weeks_inactive = row['weeks_since_movement']
        if weeks_inactive >= 52 and forecast_info['forecast_is_zero']:
            actions.append(f"{RecommendedAction.MARK_OBSOLETE.value}: Item inactive for {weeks_inactive} weeks with zero forecast - mark as obsolete")
        elif weeks_inactive >= 26 and forecast_info['forecast_is_zero']:
            actions.append(f"{RecommendedAction.MARK_OBSOLETE.value}: Review for obsolescence ({weeks_inactive} weeks inactive)")
        
        return actions if actions else [RecommendedAction.MONITOR.value]
    
    def _calculate_risk_score(self, row: pd.Series) -> float:
        """
        Calculate risk score (0-100) for non-moving inventory.
        
        Args:
            row: Row of data for the item-location
            
        Returns:
            Risk score between 0 and 100
        """
        if row['movement_status'] == MovementStatus.ACTIVE.value:
            return 0.0
        
        score = 0.0
        
        # Weeks since movement (40% weight)
        weeks = row['weeks_since_movement']
        if weeks >= 52:
            score += 40
        elif weeks >= 26:
            score += 30
        elif weeks >= 12:
            score += 20
        
        # Has inventory (30% weight)
        if row['current_inventory'] > 0:
            score += 30
        
        # Status modifier (20% weight)
        if row['movement_status'] == MovementStatus.ON_HOLD.value:
            score += 10  # Less critical - already being addressed with open PO
        else:
            score += 20  # More critical - no action taken
        
        # Category (10% weight)
        if row.get('category') == 'Declining':
            score += 10
        elif row.get('category') == 'SlowMover':
            score += 5
        
        return min(score, 100)
    
    def _get_legacy_movement_category(self, row: pd.Series) -> str:
        """
        Get legacy movement category for backwards compatibility.
        
        Args:
            row: Row of data
            
        Returns:
            Legacy movement category string
        """
        days = row['days_since_movement']
        
        if days <= self.config.slow_moving_days:
            return MovementCategory.ACTIVE.value
        elif days <= self.config.non_moving_days:
            return MovementCategory.SLOW_MOVING.value
        elif days <= self.config.dead_stock_days:
            return MovementCategory.NON_MOVING.value
        else:
            return MovementCategory.DEAD_STOCK.value
    
    def detect(
        self,
        dataset: AnalysisDataset,
        threshold_weeks: Optional[int] = None,
        analysis_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        Detect non-moving inventory based on configurable threshold.
        
        Args:
            dataset: Analysis dataset
            threshold_weeks: Weeks of inactivity to consider non-moving (12, 26, or 52)
                           Defaults to config.default_threshold_weeks (12 weeks)
            analysis_date: Date to analyze from (defaults to latest date in data)
        
        Returns:
            DataFrame with non-moving detection results including:
            - movement_status: 'active', 'non_moving', or 'on_hold'
            - recommended_actions: List of suggested actions
            - has_open_po: Whether item has open purchase orders
        """
        threshold_weeks = threshold_weeks or self.config.default_threshold_weeks
        
        if analysis_date is None:
            analysis_date = dataset.sales_history['week_ending'].max()
        
        logger.info(f"Detecting non-moving inventory (threshold: {threshold_weeks} weeks)...")
        
        # Step 1: Calculate weeks since last activity
        result = self._calculate_weeks_since_last_activity(dataset, analysis_date)
        
        # Step 2: Determine if non-moving (sales/receipt >= threshold)
        result['is_non_moving'] = result['weeks_since_movement'] >= threshold_weeks
        
        # Step 3: Check for open POs
        open_pos = self._get_open_pos(dataset.purchase_orders, analysis_date)
        result = result.merge(open_pos, on=['item_id', 'location_id'], how='left')
        result['has_open_po'] = result['has_open_po'].fillna(False)
        result['open_po_qty'] = result['open_po_qty'].fillna(0).astype(int)
        result['open_po_count'] = result['open_po_count'].fillna(0).astype(int)
        
        # Step 4: Determine movement status
        # - ACTIVE: Not non-moving
        # - ON_HOLD: Non-moving but has open PO
        # - NON_MOVING: Non-moving and no open PO
        def get_status(row):
            if not row['is_non_moving']:
                return MovementStatus.ACTIVE.value
            elif row['has_open_po']:
                return MovementStatus.ON_HOLD.value  # Non-moving but has open PO
            else:
                return MovementStatus.NON_MOVING.value
        
        result['movement_status'] = result.apply(get_status, axis=1)
        
        # Step 5: Get current inventory
        latest_inventory = dataset.inventory_snapshots[
            dataset.inventory_snapshots['week_ending'] == 
            dataset.inventory_snapshots['week_ending'].max()
        ][['item_id', 'location_id', 'on_hand_qty']]
        
        result = result.merge(latest_inventory, on=['item_id', 'location_id'], how='left')
        result.rename(columns={'on_hand_qty': 'current_inventory'}, inplace=True)
        result['current_inventory'] = result['current_inventory'].fillna(0)
        
        # Step 6: Add item details
        result = result.merge(
            dataset.items[['item_id', 'category', 'shelf_life_days', 'obsolete_date']],
            on='item_id',
            how='left'
        )
        
        # Step 7: Calculate shelf life risk
        result['shelf_life_at_risk'] = (
            (result['days_since_movement'] > result['shelf_life_days'] * 0.5) &
            (result['current_inventory'] > 0)
        )
        
        # Step 8: Generate recommended actions
        logger.info("Generating recommended actions...")
        result['recommended_actions'] = result.apply(
            lambda row: self._get_recommended_actions(row, dataset, analysis_date, threshold_weeks),
            axis=1
        )
        
        # Step 9: Create recommended_action string (legacy format)
        def format_legacy_action(actions_list):
            if not actions_list:
                return "Monitor - Normal movement"
            return " | ".join(actions_list)
        
        result['recommended_action'] = result['recommended_actions'].apply(format_legacy_action)
        
        # Step 10: Calculate risk score
        result['non_moving_risk_score'] = result.apply(
            self._calculate_risk_score, axis=1
        )
        
        # Step 11: Add legacy movement_category for backwards compatibility
        result['movement_category'] = result.apply(self._get_legacy_movement_category, axis=1)
        
        # Add threshold used
        result['threshold_weeks_used'] = threshold_weeks
        
        # Add total qty sold for reference
        total_sales = dataset.sales_history.groupby(
            ['item_id', 'location_id']
        )['qty_sold'].sum().reset_index()
        total_sales.columns = ['item_id', 'location_id', 'total_qty_sold']
        result = result.merge(total_sales, on=['item_id', 'location_id'], how='left')
        result['total_qty_sold'] = result['total_qty_sold'].fillna(0)
        
        logger.info("Detection complete. Status breakdown:")
        logger.info(f"\n{result['movement_status'].value_counts()}")
        logger.info(f"\nItems with open POs: {result['has_open_po'].sum()}")
        
        return result.sort_values('non_moving_risk_score', ascending=False)
    
    def get_summary(self, detection_result: pd.DataFrame) -> Dict:
        """Get summary statistics."""
        return {
            'total_items': len(detection_result),
            'active': len(detection_result[detection_result['movement_status'] == MovementStatus.ACTIVE.value]),
            'non_moving': len(detection_result[detection_result['movement_status'] == MovementStatus.NON_MOVING.value]),
            'on_hold': len(detection_result[detection_result['movement_status'] == MovementStatus.ON_HOLD.value]),
            'with_open_po': len(detection_result[detection_result['has_open_po'] == True]),
            'with_inventory_at_risk': len(detection_result[
                (detection_result['movement_status'] != MovementStatus.ACTIVE.value) &
                (detection_result['current_inventory'] > 0)
            ]),
            'threshold_weeks': detection_result['threshold_weeks_used'].iloc[0] if len(detection_result) > 0 else None
        }
    
    # Legacy methods for backwards compatibility
    def get_summary_by_location(self, detection_result: pd.DataFrame) -> pd.DataFrame:
        """Get summary statistics by location."""
        summary = detection_result.groupby(['location_id', 'movement_status']).agg({
            'item_id': 'count',
            'current_inventory': 'sum',
            'non_moving_risk_score': 'mean'
        }).reset_index()
        
        summary.columns = ['location_id', 'movement_status', 'sku_count', 
                          'total_inventory', 'avg_risk_score']
        return summary
    
    def get_summary_by_category(self, detection_result: pd.DataFrame) -> pd.DataFrame:
        """Get summary statistics by product category."""
        summary = detection_result.groupby(['category', 'movement_status']).agg({
            'item_id': 'count',
            'current_inventory': 'sum',
            'non_moving_risk_score': 'mean'
        }).reset_index()
        
        summary.columns = ['category', 'movement_status', 'sku_count',
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
    
    def get_items_with_open_po(
        self,
        detection_result: pd.DataFrame
    ) -> pd.DataFrame:
        """Get non-moving items that have open POs (on_hold status)."""
        return detection_result[
            detection_result['movement_status'] == MovementStatus.ON_HOLD.value
        ].copy()
    
    def get_items_for_transfer(
        self,
        detection_result: pd.DataFrame
    ) -> pd.DataFrame:
        """Get items recommended for interplant transfer."""
        return detection_result[
            detection_result['recommended_action'].str.contains(
                RecommendedAction.INTERPLANT_TRANSFER.value, 
                na=False
            )
        ].copy()
    
    def get_items_for_obsolete(
        self,
        detection_result: pd.DataFrame
    ) -> pd.DataFrame:
        """Get items recommended to be marked obsolete."""
        return detection_result[
            detection_result['recommended_action'].str.contains(
                RecommendedAction.MARK_OBSOLETE.value, 
                na=False
            )
        ].copy()
