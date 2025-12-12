"""
SKU Segmentation module.

Implements ABC-XYZ classification:
- ABC: Based on sales volume/value (Pareto principle)
- XYZ: Based on demand variability (coefficient of variation)
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, List
from enum import Enum
from dataclasses import dataclass
import logging

from ..config import get_config, SegmentationConfig
from ..data.schemas import AnalysisDataset

logger = logging.getLogger(__name__)


class ABCClass(str, Enum):
    """ABC classification based on volume/value."""
    A = "A"  # Top 20% - High volume
    B = "B"  # Next 30% - Medium volume
    C = "C"  # Bottom 50% - Low volume


class XYZClass(str, Enum):
    """XYZ classification based on demand variability."""
    X = "X"  # CV < 0.5 - Stable/predictable
    Y = "Y"  # 0.5 <= CV < 1.0 - Variable
    Z = "Z"  # CV >= 1.0 - Erratic/unpredictable


@dataclass
class SegmentationResult:
    """Result of SKU segmentation."""
    item_id: str
    location_id: Optional[str]
    abc_class: ABCClass
    xyz_class: XYZClass
    segment: str  # Combined e.g., "AX", "BY", "CZ"
    total_quantity: float
    avg_weekly_demand: float
    demand_std: float
    coefficient_of_variation: float
    cumulative_volume_pct: float
    weeks_with_sales: int
    total_weeks: int


class SKUSegmentation:
    """ABC-XYZ SKU classification engine."""
    
    def __init__(self, config: Optional[SegmentationConfig] = None):
        self.config = config or get_config().segmentation
    
    def _calculate_abc_class(
        self,
        cumulative_pct: float
    ) -> ABCClass:
        """Classify based on cumulative volume percentage."""
        if cumulative_pct <= (1 - self.config.abc_a_percentile):
            return ABCClass.A  # Top performers (first 20% of cumulative)
        elif cumulative_pct <= (1 - self.config.abc_b_percentile):
            return ABCClass.B  # Middle performers (next 30%)
        else:
            return ABCClass.C  # Low performers (bottom 50%)
    
    def _calculate_xyz_class(
        self,
        cv: float
    ) -> XYZClass:
        """Classify based on coefficient of variation."""
        if np.isnan(cv) or cv < self.config.xyz_x_cv:
            return XYZClass.X  # Stable demand
        elif cv < self.config.xyz_y_cv:
            return XYZClass.Y  # Variable demand
        else:
            return XYZClass.Z  # Erratic demand
    
    def segment_by_location(
        self,
        dataset: AnalysisDataset,
        location_id: str
    ) -> pd.DataFrame:
        """Segment SKUs for a specific location."""
        
        # Filter sales data for location
        sales = dataset.sales_history[
            dataset.sales_history['location_id'] == location_id
        ].copy()
        
        if len(sales) == 0:
            return pd.DataFrame()
        
        # Calculate metrics per item
        item_metrics = sales.groupby('item_id').agg({
            'qty_sold': ['sum', 'mean', 'std', 'count'],
            'week_ending': 'nunique'
        }).reset_index()
        
        item_metrics.columns = [
            'item_id', 'total_qty', 'avg_qty', 'std_qty', 
            'data_points', 'weeks_with_data'
        ]
        
        # Calculate coefficient of variation
        item_metrics['cv'] = item_metrics['std_qty'] / item_metrics['avg_qty'].replace(0, np.nan)
        item_metrics['cv'] = item_metrics['cv'].fillna(0)
        
        # Calculate weeks with actual sales (qty > 0)
        weeks_with_sales = sales[sales['qty_sold'] > 0].groupby('item_id')[
            'week_ending'
        ].nunique().reset_index()
        weeks_with_sales.columns = ['item_id', 'weeks_with_sales']
        
        item_metrics = item_metrics.merge(weeks_with_sales, on='item_id', how='left')
        item_metrics['weeks_with_sales'] = item_metrics['weeks_with_sales'].fillna(0)
        
        # Sort by total quantity descending for ABC
        item_metrics = item_metrics.sort_values('total_qty', ascending=False)
        
        # Calculate cumulative percentage
        total_volume = item_metrics['total_qty'].sum()
        item_metrics['volume_pct'] = item_metrics['total_qty'] / total_volume if total_volume > 0 else 0
        item_metrics['cumulative_pct'] = item_metrics['volume_pct'].cumsum()
        
        # Apply classifications
        item_metrics['abc_class'] = item_metrics['cumulative_pct'].apply(
            self._calculate_abc_class
        )
        item_metrics['xyz_class'] = item_metrics['cv'].apply(
            self._calculate_xyz_class
        )
        
        # Create combined segment
        item_metrics['segment'] = (
            item_metrics['abc_class'].apply(lambda x: x.value) + 
            item_metrics['xyz_class'].apply(lambda x: x.value)
        )
        
        item_metrics['location_id'] = location_id
        
        return item_metrics
    
    def segment_all(
        self,
        dataset: AnalysisDataset,
        by_location: bool = True
    ) -> pd.DataFrame:
        """
        Segment all SKUs.
        
        Args:
            dataset: Analysis dataset
            by_location: If True, segment separately per location.
                        If False, aggregate across all locations.
        """
        logger.info(f"Segmenting SKUs (by_location={by_location})...")
        
        if by_location:
            results = []
            for location_id in dataset.location_list:
                location_result = self.segment_by_location(dataset, location_id)
                if len(location_result) > 0:
                    results.append(location_result)
            
            if results:
                df = pd.concat(results, ignore_index=True)
            else:
                df = pd.DataFrame()
        else:
            # Aggregate across all locations
            sales = dataset.sales_history.copy()
            
            item_metrics = sales.groupby('item_id').agg({
                'qty_sold': ['sum', 'mean', 'std'],
                'week_ending': 'nunique'
            }).reset_index()
            
            item_metrics.columns = [
                'item_id', 'total_qty', 'avg_qty', 'std_qty', 'weeks_with_data'
            ]
            
            item_metrics['cv'] = item_metrics['std_qty'] / item_metrics['avg_qty'].replace(0, np.nan)
            item_metrics['cv'] = item_metrics['cv'].fillna(0)
            
            weeks_with_sales = sales[sales['qty_sold'] > 0].groupby('item_id')[
                'week_ending'
            ].nunique().reset_index()
            weeks_with_sales.columns = ['item_id', 'weeks_with_sales']
            
            item_metrics = item_metrics.merge(weeks_with_sales, on='item_id', how='left')
            item_metrics['weeks_with_sales'] = item_metrics['weeks_with_sales'].fillna(0)
            
            item_metrics = item_metrics.sort_values('total_qty', ascending=False)
            
            total_volume = item_metrics['total_qty'].sum()
            item_metrics['volume_pct'] = item_metrics['total_qty'] / total_volume if total_volume > 0 else 0
            item_metrics['cumulative_pct'] = item_metrics['volume_pct'].cumsum()
            
            item_metrics['abc_class'] = item_metrics['cumulative_pct'].apply(
                self._calculate_abc_class
            )
            item_metrics['xyz_class'] = item_metrics['cv'].apply(
                self._calculate_xyz_class
            )
            
            item_metrics['segment'] = (
                item_metrics['abc_class'].apply(lambda x: x.value) + 
                item_metrics['xyz_class'].apply(lambda x: x.value)
            )
            
            item_metrics['location_id'] = 'ALL'
            df = item_metrics
        
        # Add item category info
        if len(df) > 0:
            df = df.merge(
                dataset.items[['item_id', 'category', 'description']],
                on='item_id',
                how='left'
            )
        
        logger.info(f"Segmentation complete. Processed {len(df)} item-location combinations")
        
        return df
    
    def get_segment_summary(self, segmentation_result: pd.DataFrame) -> pd.DataFrame:
        """Get summary statistics by segment."""
        if len(segmentation_result) == 0:
            return pd.DataFrame()
        
        summary = segmentation_result.groupby('segment').agg({
            'item_id': 'count',
            'total_qty': 'sum',
            'avg_qty': 'mean',
            'cv': 'mean'
        }).reset_index()
        
        summary.columns = ['segment', 'sku_count', 'total_volume', 'avg_demand', 'avg_cv']
        
        # Calculate percentage of SKUs
        total_skus = summary['sku_count'].sum()
        summary['sku_pct'] = round(summary['sku_count'] / total_skus * 100, 2)
        
        # Calculate percentage of volume
        total_volume = summary['total_volume'].sum()
        summary['volume_pct'] = round(summary['total_volume'] / total_volume * 100, 2)
        
        return summary.sort_values('segment')
    
    def get_segment_matrix(self, segmentation_result: pd.DataFrame) -> pd.DataFrame:
        """Get ABC-XYZ matrix showing count per segment."""
        if len(segmentation_result) == 0:
            return pd.DataFrame()
        
        matrix = pd.crosstab(
            segmentation_result['abc_class'].apply(lambda x: x.value if isinstance(x, ABCClass) else x),
            segmentation_result['xyz_class'].apply(lambda x: x.value if isinstance(x, XYZClass) else x)
        )
        
        # Ensure all classes are present
        for abc in ['A', 'B', 'C']:
            if abc not in matrix.index:
                matrix.loc[abc] = 0
        for xyz in ['X', 'Y', 'Z']:
            if xyz not in matrix.columns:
                matrix[xyz] = 0
        
        matrix = matrix.loc[['A', 'B', 'C'], ['X', 'Y', 'Z']]
        
        return matrix
    
    def get_segment_recommendations(self, segment: str) -> Dict:
        """Get recommendations for inventory management based on segment."""
        recommendations = {
            'AX': {
                'priority': 'Critical',
                'reorder_strategy': 'Continuous review with tight safety stock',
                'forecast_method': 'Advanced time-series (high accuracy needed)',
                'inventory_policy': 'Low safety stock, frequent replenishment',
                'attention': 'High - revenue drivers with predictable demand'
            },
            'AY': {
                'priority': 'High',
                'reorder_strategy': 'Periodic review with moderate safety stock',
                'forecast_method': 'Statistical methods with demand sensing',
                'inventory_policy': 'Moderate safety stock',
                'attention': 'High - revenue drivers with some variability'
            },
            'AZ': {
                'priority': 'High',
                'reorder_strategy': 'Careful management, higher safety stock',
                'forecast_method': 'Collaborative forecasting',
                'inventory_policy': 'Higher safety stock or supplier flexibility',
                'attention': 'High - revenue drivers but unpredictable'
            },
            'BX': {
                'priority': 'Medium',
                'reorder_strategy': 'Periodic review',
                'forecast_method': 'Simple statistical methods',
                'inventory_policy': 'Standard safety stock',
                'attention': 'Medium - stable moderate movers'
            },
            'BY': {
                'priority': 'Medium',
                'reorder_strategy': 'Periodic review with some buffer',
                'forecast_method': 'Moving averages',
                'inventory_policy': 'Moderate safety stock',
                'attention': 'Medium - typical B items'
            },
            'BZ': {
                'priority': 'Medium-Low',
                'reorder_strategy': 'Higher reorder points',
                'forecast_method': 'Simple methods, focus on safety stock',
                'inventory_policy': 'Higher safety stock',
                'attention': 'Medium - erratic B items need buffer'
            },
            'CX': {
                'priority': 'Low',
                'reorder_strategy': 'Simple min-max or kanban',
                'forecast_method': 'Simple average',
                'inventory_policy': 'Minimal investment',
                'attention': 'Low - stable but low volume'
            },
            'CY': {
                'priority': 'Low',
                'reorder_strategy': 'Larger lot sizes, less frequent orders',
                'forecast_method': 'Simple methods',
                'inventory_policy': 'Balance carrying cost vs ordering',
                'attention': 'Low - review for rationalization'
            },
            'CZ': {
                'priority': 'Minimal',
                'reorder_strategy': 'Make to order or discontinue',
                'forecast_method': 'Not recommended - order based',
                'inventory_policy': 'Consider not stocking',
                'attention': 'Review for discontinuation'
            }
        }
        
        return recommendations.get(segment, {
            'priority': 'Unknown',
            'recommendation': 'Segment not recognized'
        })

