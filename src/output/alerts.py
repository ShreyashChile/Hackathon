"""
Alert generation module.

Generates structured alerts for inventory management based on
analysis results.
"""

import pandas as pd
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field, asdict
import json
import logging

logger = logging.getLogger(__name__)


class AlertPriority(str, Enum):
    """Alert priority levels."""
    P1_CRITICAL = "P1_CRITICAL"  # Immediate action required
    P2_HIGH = "P2_HIGH"  # Action within 24 hours
    P3_MEDIUM = "P3_MEDIUM"  # Action within 1 week
    P4_LOW = "P4_LOW"  # Monitor and review
    P5_INFO = "P5_INFO"  # Informational


class AlertCategory(str, Enum):
    """Categories of alerts."""
    DEMAND_SHIFT = "demand_shift"
    INVENTORY_RISK = "inventory_risk"
    SHELF_LIFE = "shelf_life"
    SUPPLY_RISK = "supply_risk"
    OPTIMIZATION = "optimization"


@dataclass
class Alert:
    """Represents a single alert."""
    alert_id: str
    item_id: str
    location_id: str
    priority: AlertPriority
    category: AlertCategory
    title: str
    description: str
    risk_score: float
    created_at: datetime
    expires_at: Optional[datetime] = None
    acknowledged: bool = False
    resolved: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        result = asdict(self)
        result['priority'] = self.priority.value
        result['category'] = self.category.value
        result['created_at'] = self.created_at.isoformat()
        if self.expires_at:
            result['expires_at'] = self.expires_at.isoformat()
        return result
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), default=str)


class AlertGenerator:
    """Generate alerts from analysis results."""
    
    def __init__(self):
        self._alert_counter = 0
    
    def _generate_alert_id(self) -> str:
        """Generate unique alert ID."""
        self._alert_counter += 1
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"ALT-{timestamp}-{self._alert_counter:05d}"
    
    def _get_priority_from_score(self, score: float) -> AlertPriority:
        """Determine priority from risk score."""
        if score >= 80:
            return AlertPriority.P1_CRITICAL
        elif score >= 60:
            return AlertPriority.P2_HIGH
        elif score >= 40:
            return AlertPriority.P3_MEDIUM
        elif score >= 20:
            return AlertPriority.P4_LOW
        else:
            return AlertPriority.P5_INFO
    
    def generate_demand_shift_alerts(
        self,
        demand_shifts: pd.DataFrame,
        min_confidence: float = 50.0
    ) -> List[Alert]:
        """Generate alerts for detected demand shifts."""
        logger.info("Generating demand shift alerts...")
        
        alerts = []
        
        # Filter significant shifts
        shifts = demand_shifts[
            (demand_shifts['shift_detected']) &
            (demand_shifts['confidence_score'] >= min_confidence)
        ]
        
        for _, row in shifts.iterrows():
            direction = row['shift_direction']
            magnitude = abs(row['shift_magnitude'])
            
            if direction == 'increase':
                title = f"Demand Surge Detected - {row['item_id']}"
                description = (
                    f"Demand for {row['item_id']} at {row['location_id']} has increased "
                    f"by {magnitude:.1f}% compared to baseline. "
                    f"Current weekly demand: {row['current_demand']:.0f}, "
                    f"Baseline: {row['baseline_demand']:.0f}."
                )
                recommendations = [
                    "Review and increase safety stock levels",
                    "Consider expediting pending orders",
                    "Evaluate capacity for higher demand"
                ]
            else:
                title = f"Demand Drop Detected - {row['item_id']}"
                description = (
                    f"Demand for {row['item_id']} at {row['location_id']} has decreased "
                    f"by {magnitude:.1f}% compared to baseline. "
                    f"Current weekly demand: {row['current_demand']:.0f}, "
                    f"Baseline: {row['baseline_demand']:.0f}."
                )
                recommendations = [
                    "Review open purchase orders for reduction",
                    "Reduce future order quantities",
                    "Investigate root cause of demand decline"
                ]
            
            alert = Alert(
                alert_id=self._generate_alert_id(),
                item_id=row['item_id'],
                location_id=row['location_id'],
                priority=self._get_priority_from_score(row['confidence_score']),
                category=AlertCategory.DEMAND_SHIFT,
                title=title,
                description=description,
                risk_score=row['confidence_score'],
                created_at=datetime.now(),
                metadata={
                    'shift_type': row.get('shift_type'),
                    'shift_magnitude': row['shift_magnitude'],
                    'shift_direction': direction,
                    'baseline_demand': row['baseline_demand'],
                    'current_demand': row['current_demand'],
                    'cusum_signal': row.get('cusum_signal', False),
                    'ma_crossover_signal': row.get('ma_crossover_signal', False)
                },
                recommendations=recommendations
            )
            alerts.append(alert)
        
        logger.info(f"Generated {len(alerts)} demand shift alerts")
        return alerts
    
    def generate_non_moving_alerts(
        self,
        non_moving: pd.DataFrame,
        min_risk_score: float = 40.0
    ) -> List[Alert]:
        """Generate alerts for non-moving inventory."""
        logger.info("Generating non-moving inventory alerts...")
        
        alerts = []
        
        # Filter high-risk items
        risky_items = non_moving[
            (non_moving['non_moving_risk_score'] >= min_risk_score) &
            (non_moving['current_inventory'] > 0)
        ]
        
        for _, row in risky_items.iterrows():
            category = row['movement_category']
            days = row['days_since_movement']
            inventory = row['current_inventory']
            
            if category == 'dead_stock':
                title = f"Dead Stock Alert - {row['item_id']}"
                description = (
                    f"{row['item_id']} at {row['location_id']} has had no movement "
                    f"for {days:.0f} days with {inventory:.0f} units on hand. "
                    f"This inventory is at high risk of obsolescence."
                )
                recommendations = [
                    "Evaluate for disposal or write-off",
                    "Consider clearance pricing or markdown",
                    "Stop all pending supply orders"
                ]
                priority = AlertPriority.P1_CRITICAL
            elif category == 'non_moving':
                title = f"Non-Moving Inventory - {row['item_id']}"
                description = (
                    f"{row['item_id']} at {row['location_id']} has had no movement "
                    f"for {days:.0f} days with {inventory:.0f} units on hand."
                )
                recommendations = [
                    "Put supply orders on hold",
                    "Review for promotional opportunities",
                    "Consider stock transfers to other locations"
                ]
                priority = AlertPriority.P2_HIGH
            else:  # slow_moving
                title = f"Slow-Moving Inventory - {row['item_id']}"
                description = (
                    f"{row['item_id']} at {row['location_id']} is moving slowly "
                    f"({days:.0f} days since last movement) with {inventory:.0f} units on hand."
                )
                recommendations = [
                    "Review pricing strategy",
                    "Consider promotional activities",
                    "Reduce reorder quantities"
                ]
                priority = AlertPriority.P3_MEDIUM
            
            alert = Alert(
                alert_id=self._generate_alert_id(),
                item_id=row['item_id'],
                location_id=row['location_id'],
                priority=priority,
                category=AlertCategory.INVENTORY_RISK,
                title=title,
                description=description,
                risk_score=row['non_moving_risk_score'],
                created_at=datetime.now(),
                metadata={
                    'movement_category': category,
                    'days_since_movement': days,
                    'current_inventory': inventory,
                    'shelf_life_at_risk': row.get('shelf_life_at_risk', False),
                    'product_category': row.get('category')
                },
                recommendations=recommendations
            )
            alerts.append(alert)
        
        logger.info(f"Generated {len(alerts)} non-moving inventory alerts")
        return alerts
    
    def generate_risk_alerts(
        self,
        risk_scores: pd.DataFrame,
        min_score: float = 50.0
    ) -> List[Alert]:
        """Generate alerts from risk scores."""
        logger.info("Generating risk-based alerts...")
        
        alerts = []
        
        high_risk = risk_scores[risk_scores['overall_score'] >= min_score]
        
        for _, row in high_risk.iterrows():
            primary_factor = row['primary_risk_factor']
            alert_list = row.get('alerts', [])
            
            # Create title based on primary risk
            factor_titles = {
                'demand_shift': 'Demand Pattern Change',
                'non_moving': 'Inventory Movement Risk',
                'shelf_life': 'Shelf Life Concern',
                'lifecycle': 'Product Lifecycle Risk',
                'inventory': 'Inventory Level Issue'
            }
            
            title = f"{factor_titles.get(primary_factor, 'Risk Alert')} - {row['item_id']}"
            
            description = (
                f"{row['item_id']} at {row['location_id']} has an overall risk score of "
                f"{row['overall_score']:.1f}. Primary concern: {primary_factor}. "
                f"Current inventory: {row['on_hand_qty']:.0f} units."
            )
            
            # Add specific details based on alerts
            if 'shelf_life_risk' in alert_list:
                description += " WARNING: Shelf life at risk."
            if 'dead_stock' in alert_list:
                description += " Item classified as dead stock."
            
            alert = Alert(
                alert_id=self._generate_alert_id(),
                item_id=row['item_id'],
                location_id=row['location_id'],
                priority=self._get_priority_from_score(row['overall_score']),
                category=AlertCategory.INVENTORY_RISK,
                title=title,
                description=description,
                risk_score=row['overall_score'],
                created_at=datetime.now(),
                metadata={
                    'primary_risk_factor': primary_factor,
                    'demand_shift_score': row['demand_shift_score'],
                    'non_moving_score': row['non_moving_score'],
                    'shelf_life_score': row['shelf_life_score'],
                    'lifecycle_score': row['lifecycle_score'],
                    'inventory_score': row['inventory_score'],
                    'alerts': alert_list,
                    'category': row.get('category')
                },
                recommendations=row.get('recommendations', [])
            )
            alerts.append(alert)
        
        logger.info(f"Generated {len(alerts)} risk alerts")
        return alerts
    
    def consolidate_alerts(self, *alert_lists: List[Alert]) -> List[Alert]:
        """Consolidate and deduplicate alerts from multiple sources."""
        all_alerts = []
        seen_keys = set()
        
        for alert_list in alert_lists:
            for alert in alert_list:
                # Create unique key for deduplication
                key = (alert.item_id, alert.location_id, alert.category.value)
                
                if key not in seen_keys:
                    all_alerts.append(alert)
                    seen_keys.add(key)
        
        # Sort by priority and score
        priority_order = {
            AlertPriority.P1_CRITICAL: 0,
            AlertPriority.P2_HIGH: 1,
            AlertPriority.P3_MEDIUM: 2,
            AlertPriority.P4_LOW: 3,
            AlertPriority.P5_INFO: 4
        }
        
        all_alerts.sort(key=lambda x: (priority_order[x.priority], -x.risk_score))
        
        return all_alerts
    
    def alerts_to_dataframe(self, alerts: List[Alert]) -> pd.DataFrame:
        """Convert alerts to DataFrame."""
        if not alerts:
            return pd.DataFrame()
        
        records = [alert.to_dict() for alert in alerts]
        df = pd.DataFrame(records)
        
        # Convert recommendations list to string for easier viewing
        df['recommendations_text'] = df['recommendations'].apply(
            lambda x: '; '.join(x) if x else ''
        )
        
        return df
    
    def get_alert_summary(self, alerts: List[Alert]) -> Dict:
        """Get summary statistics for alerts."""
        if not alerts:
            return {'total': 0}
        
        df = self.alerts_to_dataframe(alerts)
        
        return {
            'total': len(alerts),
            'by_priority': df['priority'].value_counts().to_dict(),
            'by_category': df['category'].value_counts().to_dict(),
            'critical_count': len(df[df['priority'] == 'P1_CRITICAL']),
            'high_count': len(df[df['priority'] == 'P2_HIGH']),
            'unique_items': df['item_id'].nunique(),
            'unique_locations': df['location_id'].nunique()
        }

