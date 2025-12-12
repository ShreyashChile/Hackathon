"""
Risk/Confidence Scoring module.

Calculates composite risk scores for SKUs based on multiple factors:
- Demand shift magnitude and persistence
- Non-moving inventory status
- Shelf life remaining
- Product lifecycle stage
- Inventory value at risk
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, List
from dataclasses import dataclass
from enum import Enum
import logging

from ..config import get_config, ScoringConfig
from ..data.schemas import AnalysisDataset

logger = logging.getLogger(__name__)


class RiskLevel(str, Enum):
    """Risk level categories."""
    CRITICAL = "critical"  # Score >= 80
    HIGH = "high"  # Score >= 60
    MEDIUM = "medium"  # Score >= 40
    LOW = "low"  # Score >= 20
    MINIMAL = "minimal"  # Score < 20


class AlertType(str, Enum):
    """Types of alerts to generate."""
    DEMAND_SURGE = "demand_surge"
    DEMAND_DROP = "demand_drop"
    DEAD_STOCK = "dead_stock"
    SLOW_MOVING = "slow_moving"
    SHELF_LIFE_RISK = "shelf_life_risk"
    OVERSTOCK = "overstock"
    UNDERSTOCK = "understock"


@dataclass
class RiskScore:
    """Composite risk score for an item-location."""
    item_id: str
    location_id: str
    overall_score: float
    risk_level: RiskLevel
    demand_shift_score: float
    non_moving_score: float
    shelf_life_score: float
    lifecycle_score: float
    inventory_score: float
    primary_risk_factor: str
    alerts: List[AlertType]
    recommendations: List[str]


class RiskScorer:
    """Calculate composite risk scores for inventory items."""
    
    def __init__(self, config: Optional[ScoringConfig] = None):
        self.config = config or get_config().scoring
    
    def _calculate_demand_shift_score(
        self,
        shift_detected: bool,
        shift_magnitude: float,
        confidence: float,
        direction: str
    ) -> float:
        """Calculate score based on demand shift detection."""
        if not shift_detected:
            return 0.0
        
        # Base score from magnitude
        magnitude_score = min(abs(shift_magnitude) / 100 * 50, 50)
        
        # Add confidence component
        confidence_score = confidence / 100 * 30
        
        # Direction adjustment (drops are riskier than surges)
        direction_multiplier = 1.2 if direction == 'decrease' else 1.0
        
        return min((magnitude_score + confidence_score) * direction_multiplier, 100)
    
    def _calculate_non_moving_score(
        self,
        days_since_movement: float,
        movement_category: str,
        has_inventory: bool
    ) -> float:
        """Calculate score based on non-moving status."""
        config = get_config().non_moving
        
        if not has_inventory:
            return 0.0
        
        if movement_category == 'dead_stock':
            return 100.0
        elif movement_category == 'non_moving':
            return 75.0
        elif movement_category == 'slow_moving':
            return 40.0
        else:
            # Active - score based on days
            return min(days_since_movement / config.slow_moving_days * 20, 20)
    
    def _calculate_shelf_life_score(
        self,
        shelf_life_days: float,
        days_since_launch: float,
        has_inventory: bool
    ) -> float:
        """Calculate score based on shelf life risk."""
        if not has_inventory or shelf_life_days <= 0:
            return 0.0
        
        consumed_pct = days_since_launch / shelf_life_days
        
        if consumed_pct >= 1.0:
            return 100.0  # Expired
        elif consumed_pct >= 0.75:
            return 80.0  # Critical
        elif consumed_pct >= 0.5:
            return 50.0  # Warning
        elif consumed_pct >= 0.25:
            return 20.0  # Monitor
        else:
            return 0.0
    
    def _calculate_lifecycle_score(
        self,
        category: str,
        has_obsolete_date: bool
    ) -> float:
        """Calculate score based on product lifecycle."""
        scores = {
            'Declining': 80.0,
            'SlowMover': 60.0,
            'Seasonal': 30.0,  # Depends on timing
            'Staple': 10.0,
            'NewLaunch': 20.0  # Some risk due to uncertainty
        }
        
        base_score = scores.get(category, 25.0)
        
        # Add if obsolete date is set
        if has_obsolete_date:
            base_score = min(base_score + 20, 100)
        
        return base_score
    
    def _calculate_inventory_score(
        self,
        on_hand_qty: float,
        min_qty: float,
        max_qty: float,
        weeks_of_supply: float
    ) -> float:
        """Calculate score based on inventory position."""
        if on_hand_qty <= 0:
            return 0.0
        
        # Overstock risk
        if on_hand_qty > max_qty:
            overstock_pct = (on_hand_qty - max_qty) / max_qty if max_qty > 0 else 1
            overstock_score = min(overstock_pct * 50, 50)
        else:
            overstock_score = 0
        
        # Weeks of supply risk
        if weeks_of_supply > 26:  # More than 6 months
            wos_score = min((weeks_of_supply - 26) / 26 * 50, 50)
        else:
            wos_score = 0
        
        return min(overstock_score + wos_score, 100)
    
    def _get_risk_level(self, score: float) -> RiskLevel:
        """Determine risk level from score."""
        if score >= 80:
            return RiskLevel.CRITICAL
        elif score >= 60:
            return RiskLevel.HIGH
        elif score >= 40:
            return RiskLevel.MEDIUM
        elif score >= 20:
            return RiskLevel.LOW
        else:
            return RiskLevel.MINIMAL
    
    def _get_alerts(
        self,
        demand_shift_score: float,
        non_moving_score: float,
        shelf_life_score: float,
        shift_direction: str,
        stock_position: str
    ) -> List[AlertType]:
        """Determine which alerts to generate."""
        alerts = []
        
        if demand_shift_score >= 50:
            if shift_direction == 'increase':
                alerts.append(AlertType.DEMAND_SURGE)
            elif shift_direction == 'decrease':
                alerts.append(AlertType.DEMAND_DROP)
        
        if non_moving_score >= 75:
            alerts.append(AlertType.DEAD_STOCK)
        elif non_moving_score >= 40:
            alerts.append(AlertType.SLOW_MOVING)
        
        if shelf_life_score >= 50:
            alerts.append(AlertType.SHELF_LIFE_RISK)
        
        if stock_position == 'overstocked':
            alerts.append(AlertType.OVERSTOCK)
        elif stock_position == 'understocked':
            alerts.append(AlertType.UNDERSTOCK)
        
        return alerts
    
    def _get_recommendations(
        self,
        alerts: List[AlertType],
        risk_level: RiskLevel,
        category: str
    ) -> List[str]:
        """Generate recommendations based on alerts."""
        recommendations = []
        
        for alert in alerts:
            if alert == AlertType.DEMAND_SURGE:
                recommendations.append("Increase reorder quantity and review safety stock")
            elif alert == AlertType.DEMAND_DROP:
                recommendations.append("Reduce reorder quantities and pause open orders if possible")
            elif alert == AlertType.DEAD_STOCK:
                recommendations.append("Evaluate for disposal, markdown, or write-off")
            elif alert == AlertType.SLOW_MOVING:
                recommendations.append("Review pricing and promotions to accelerate movement")
            elif alert == AlertType.SHELF_LIFE_RISK:
                recommendations.append("URGENT: Clear inventory before expiry - consider markdowns")
            elif alert == AlertType.OVERSTOCK:
                recommendations.append("Reduce incoming supply and consider stock transfers")
            elif alert == AlertType.UNDERSTOCK:
                recommendations.append("Expedite replenishment orders")
        
        # Category-specific recommendations
        if category == 'Declining' and risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            recommendations.append("Consider SKU discontinuation planning")
        
        if category == 'Seasonal':
            recommendations.append("Review seasonal patterns and adjust forecasts")
        
        return recommendations
    
    def score(
        self,
        demand_shifts: pd.DataFrame,
        non_moving: pd.DataFrame,
        dataset: AnalysisDataset
    ) -> pd.DataFrame:
        """
        Calculate composite risk scores for all item-locations.
        
        Args:
            demand_shifts: Output from DemandShiftDetector
            non_moving: Output from NonMovingDetector
            dataset: Analysis dataset
        
        Returns:
            DataFrame with risk scores and recommendations
        """
        logger.info("Calculating risk scores...")
        
        # Merge demand shifts and non-moving data
        merged = demand_shifts.merge(
            non_moving[[
                'item_id', 'location_id', 'days_since_movement', 
                'movement_category', 'current_inventory', 'non_moving_risk_score'
            ]],
            on=['item_id', 'location_id'],
            how='outer'
        )
        
        # Add item details
        merged = merged.merge(
            dataset.items[['item_id', 'category', 'shelf_life_days', 'launch_date', 'obsolete_date']],
            on='item_id',
            how='left'
        )
        
        # Add reorder policy
        merged = merged.merge(
            dataset.reorder_policies,
            on='item_id',
            how='left'
        )
        
        # Get latest inventory snapshot
        latest_date = dataset.inventory_snapshots['week_ending'].max()
        latest_inv = dataset.inventory_snapshots[
            dataset.inventory_snapshots['week_ending'] == latest_date
        ][['item_id', 'location_id', 'on_hand_qty']]
        
        merged = merged.merge(
            latest_inv,
            on=['item_id', 'location_id'],
            how='left'
        )
        
        # Fill missing values
        merged['shift_detected'] = merged['shift_detected'].fillna(False)
        merged['shift_magnitude'] = merged['shift_magnitude'].fillna(0)
        merged['confidence_score'] = merged['confidence_score'].fillna(0)
        merged['shift_direction'] = merged['shift_direction'].fillna('stable')
        merged['days_since_movement'] = merged['days_since_movement'].fillna(0)
        merged['movement_category'] = merged['movement_category'].fillna('active')
        merged['current_inventory'] = merged['current_inventory'].fillna(0)
        merged['on_hand_qty'] = merged['on_hand_qty'].fillna(0)
        
        # Calculate days since launch
        merged['days_since_launch'] = (
            pd.Timestamp.now() - pd.to_datetime(merged['launch_date'])
        ).dt.days
        
        # Calculate component scores
        results = []
        
        for _, row in merged.iterrows():
            # Calculate individual scores
            demand_score = self._calculate_demand_shift_score(
                row['shift_detected'],
                row['shift_magnitude'],
                row['confidence_score'],
                row['shift_direction']
            )
            
            non_moving_score = self._calculate_non_moving_score(
                row['days_since_movement'],
                str(row['movement_category']),
                row['on_hand_qty'] > 0
            )
            
            shelf_life_score = self._calculate_shelf_life_score(
                row.get('shelf_life_days', 365),
                row.get('days_since_launch', 0),
                row['on_hand_qty'] > 0
            )
            
            lifecycle_score = self._calculate_lifecycle_score(
                row.get('category', 'Staple'),
                pd.notna(row.get('obsolete_date'))
            )
            
            # Calculate weeks of supply (using current demand as proxy)
            current_demand = row.get('current_demand', 0)
            weeks_of_supply = (
                row['on_hand_qty'] / current_demand 
                if current_demand > 0 else float('inf')
            )
            
            inventory_score = self._calculate_inventory_score(
                row['on_hand_qty'],
                row.get('min_qty', 0),
                row.get('max_qty', float('inf')),
                weeks_of_supply
            )
            
            # Calculate weighted overall score
            overall_score = (
                demand_score * self.config.demand_shift_weight +
                non_moving_score * self.config.non_moving_weight +
                shelf_life_score * self.config.shelf_life_weight +
                lifecycle_score * self.config.lifecycle_weight +
                inventory_score * self.config.inventory_value_weight
            )
            
            # Determine primary risk factor
            scores = {
                'demand_shift': demand_score,
                'non_moving': non_moving_score,
                'shelf_life': shelf_life_score,
                'lifecycle': lifecycle_score,
                'inventory': inventory_score
            }
            primary_factor = max(scores, key=scores.get)
            
            # Determine stock position
            if row['on_hand_qty'] > row.get('max_qty', float('inf')):
                stock_position = 'overstocked'
            elif row['on_hand_qty'] < row.get('min_qty', 0):
                stock_position = 'understocked'
            else:
                stock_position = 'optimal'
            
            # Get alerts and recommendations
            risk_level = self._get_risk_level(overall_score)
            alerts = self._get_alerts(
                demand_score, non_moving_score, shelf_life_score,
                row['shift_direction'], stock_position
            )
            recommendations = self._get_recommendations(
                alerts, risk_level, row.get('category', 'Staple')
            )
            
            results.append({
                'item_id': row['item_id'],
                'location_id': row['location_id'],
                'overall_score': round(overall_score, 2),
                'risk_level': risk_level.value,
                'demand_shift_score': round(demand_score, 2),
                'non_moving_score': round(non_moving_score, 2),
                'shelf_life_score': round(shelf_life_score, 2),
                'lifecycle_score': round(lifecycle_score, 2),
                'inventory_score': round(inventory_score, 2),
                'primary_risk_factor': primary_factor,
                'alerts': [a.value for a in alerts],
                'recommendations': recommendations,
                'on_hand_qty': row['on_hand_qty'],
                'category': row.get('category'),
                'shift_detected': row['shift_detected'],
                'shift_magnitude': row['shift_magnitude'],
                'movement_category': str(row['movement_category']),
                'days_since_movement': row['days_since_movement']
            })
        
        result_df = pd.DataFrame(results)
        result_df = result_df.sort_values('overall_score', ascending=False)
        
        logger.info(f"Scoring complete. Risk level breakdown:")
        logger.info(f"\n{result_df['risk_level'].value_counts()}")
        
        return result_df
    
    def get_risk_summary(self, scores: pd.DataFrame) -> Dict:
        """Get summary of risk scores."""
        return {
            'total_items': len(scores),
            'by_risk_level': scores['risk_level'].value_counts().to_dict(),
            'by_primary_factor': scores['primary_risk_factor'].value_counts().to_dict(),
            'avg_score': round(scores['overall_score'].mean(), 2),
            'critical_items': len(scores[scores['risk_level'] == 'critical']),
            'high_risk_items': len(scores[scores['risk_level'].isin(['critical', 'high'])])
        }
    
    def get_priority_items(
        self,
        scores: pd.DataFrame,
        top_n: int = 20
    ) -> pd.DataFrame:
        """Get top priority items requiring attention."""
        return scores.nlargest(top_n, 'overall_score')

