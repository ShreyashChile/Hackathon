"""
Export modules for CSV and JSON output.
"""

import pandas as pd
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from .alerts import Alert

logger = logging.getLogger(__name__)


class CSVExporter:
    """Export analysis results to CSV files."""
    
    def __init__(self, output_dir: Path | str = "outputs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_filename(self, base_name: str, timestamp: bool = True) -> Path:
        """Generate output filename."""
        if timestamp:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            return self.output_dir / f"{base_name}_{ts}.csv"
        return self.output_dir / f"{base_name}.csv"
    
    def export_demand_shifts(
        self,
        df: pd.DataFrame,
        filename: Optional[str] = None,
        include_timestamp: bool = False
    ) -> Path:
        """Export demand shift results to CSV."""
        if filename:
            filepath = self.output_dir / filename
        else:
            filepath = self._get_filename("demand_shifts", include_timestamp)
        
        df.to_csv(filepath, index=False)
        logger.info(f"Exported demand shifts to {filepath}")
        return filepath
    
    def export_non_moving(
        self,
        df: pd.DataFrame,
        filename: Optional[str] = None,
        include_timestamp: bool = False
    ) -> Path:
        """Export non-moving inventory results to CSV."""
        if filename:
            filepath = self.output_dir / filename
        else:
            filepath = self._get_filename("non_moving_inventory", include_timestamp)
        
        # Convert enum values to strings
        df_export = df.copy()
        if 'movement_category' in df_export.columns:
            df_export['movement_category'] = df_export['movement_category'].astype(str)
        
        df_export.to_csv(filepath, index=False)
        logger.info(f"Exported non-moving inventory to {filepath}")
        return filepath
    
    def export_segmentation(
        self,
        df: pd.DataFrame,
        filename: Optional[str] = None,
        include_timestamp: bool = False
    ) -> Path:
        """Export segmentation results to CSV."""
        if filename:
            filepath = self.output_dir / filename
        else:
            filepath = self._get_filename("segmentation", include_timestamp)
        
        # Convert enum values to strings
        df_export = df.copy()
        for col in ['abc_class', 'xyz_class']:
            if col in df_export.columns:
                df_export[col] = df_export[col].apply(
                    lambda x: x.value if hasattr(x, 'value') else str(x)
                )
        
        df_export.to_csv(filepath, index=False)
        logger.info(f"Exported segmentation to {filepath}")
        return filepath
    
    def export_risk_scores(
        self,
        df: pd.DataFrame,
        filename: Optional[str] = None,
        include_timestamp: bool = False
    ) -> Path:
        """Export risk scores to CSV."""
        if filename:
            filepath = self.output_dir / filename
        else:
            filepath = self._get_filename("risk_scores", include_timestamp)
        
        # Handle list columns
        df_export = df.copy()
        for col in ['alerts', 'recommendations']:
            if col in df_export.columns:
                df_export[col] = df_export[col].apply(
                    lambda x: '; '.join(x) if isinstance(x, list) else str(x)
                )
        
        df_export.to_csv(filepath, index=False)
        logger.info(f"Exported risk scores to {filepath}")
        return filepath
    
    def export_alerts(
        self,
        alerts: List[Alert],
        filename: Optional[str] = None,
        include_timestamp: bool = False
    ) -> Path:
        """Export alerts to CSV."""
        if filename:
            filepath = self.output_dir / filename
        else:
            filepath = self._get_filename("alerts", include_timestamp)
        
        if not alerts:
            # Create empty file with headers
            pd.DataFrame(columns=[
                'alert_id', 'item_id', 'location_id', 'priority',
                'category', 'title', 'description', 'risk_score',
                'created_at', 'recommendations'
            ]).to_csv(filepath, index=False)
        else:
            records = []
            for alert in alerts:
                record = alert.to_dict()
                record['recommendations'] = '; '.join(record['recommendations'])
                records.append(record)
            
            pd.DataFrame(records).to_csv(filepath, index=False)
        
        logger.info(f"Exported {len(alerts)} alerts to {filepath}")
        return filepath
    
    def export_summary_report(
        self,
        demand_shifts: pd.DataFrame,
        non_moving: pd.DataFrame,
        segmentation: pd.DataFrame,
        risk_scores: pd.DataFrame,
        filename: Optional[str] = None
    ) -> Path:
        """Export a summary report combining key metrics."""
        if filename:
            filepath = self.output_dir / filename
        else:
            filepath = self._get_filename("summary_report", timestamp=False)
        
        # Create summary statistics
        summary_data = []
        
        # Demand shift summary
        shifts_detected = len(demand_shifts[demand_shifts['shift_detected'] == True])
        summary_data.append({
            'metric': 'Total SKU-Location Combinations',
            'value': len(demand_shifts)
        })
        summary_data.append({
            'metric': 'Demand Shifts Detected',
            'value': shifts_detected
        })
        summary_data.append({
            'metric': 'Demand Shift Rate (%)',
            'value': round(shifts_detected / len(demand_shifts) * 100, 2) if len(demand_shifts) > 0 else 0
        })
        
        # Non-moving summary
        for category in ['dead_stock', 'non_moving', 'slow_moving', 'active']:
            count = len(non_moving[non_moving['movement_category'].astype(str) == category])
            summary_data.append({
                'metric': f'Items - {category.replace("_", " ").title()}',
                'value': count
            })
        
        # Risk summary
        for level in ['critical', 'high', 'medium', 'low', 'minimal']:
            count = len(risk_scores[risk_scores['risk_level'] == level])
            summary_data.append({
                'metric': f'Risk Level - {level.title()}',
                'value': count
            })
        
        # Segmentation summary
        if 'segment' in segmentation.columns:
            for segment in segmentation['segment'].unique():
                count = len(segmentation[segmentation['segment'] == segment])
                summary_data.append({
                    'metric': f'Segment - {segment}',
                    'value': count
                })
        
        pd.DataFrame(summary_data).to_csv(filepath, index=False)
        logger.info(f"Exported summary report to {filepath}")
        return filepath


class JSONExporter:
    """Export analysis results to JSON files."""
    
    def __init__(self, output_dir: Path | str = "outputs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_filename(self, base_name: str, timestamp: bool = True) -> Path:
        """Generate output filename."""
        if timestamp:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            return self.output_dir / f"{base_name}_{ts}.json"
        return self.output_dir / f"{base_name}.json"
    
    def _dataframe_to_json_records(self, df: pd.DataFrame) -> List[Dict]:
        """Convert DataFrame to JSON-serializable records."""
        df_copy = df.copy()
        
        # Convert datetime columns
        for col in df_copy.columns:
            if pd.api.types.is_datetime64_any_dtype(df_copy[col]):
                df_copy[col] = df_copy[col].astype(str)
            elif df_copy[col].dtype == 'object':
                # Try to convert enum-like values
                df_copy[col] = df_copy[col].apply(
                    lambda x: x.value if hasattr(x, 'value') else x
                )
        
        return df_copy.to_dict(orient='records')
    
    def export_full_analysis(
        self,
        demand_shifts: pd.DataFrame,
        non_moving: pd.DataFrame,
        segmentation: pd.DataFrame,
        risk_scores: pd.DataFrame,
        alerts: List[Alert],
        metadata: Optional[Dict] = None,
        filename: Optional[str] = None
    ) -> Path:
        """Export complete analysis results to a single JSON file."""
        if filename:
            filepath = self.output_dir / filename
        else:
            filepath = self._get_filename("full_analysis", timestamp=False)
        
        output = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'total_item_locations': len(demand_shifts),
                **(metadata or {})
            },
            'demand_shifts': {
                'summary': {
                    'total': len(demand_shifts),
                    'shifts_detected': int(demand_shifts['shift_detected'].sum()),
                    'by_direction': demand_shifts['shift_direction'].value_counts().to_dict()
                },
                'data': self._dataframe_to_json_records(
                    demand_shifts[demand_shifts['shift_detected'] == True].head(100)
                )
            },
            'non_moving_inventory': {
                'summary': {
                    'total': len(non_moving),
                    'by_category': non_moving['movement_category'].astype(str).value_counts().to_dict()
                },
                'data': self._dataframe_to_json_records(
                    non_moving.nlargest(100, 'non_moving_risk_score')
                )
            },
            'segmentation': {
                'summary': {
                    'total': len(segmentation),
                    'by_segment': segmentation['segment'].value_counts().to_dict() if 'segment' in segmentation else {}
                },
                'data': self._dataframe_to_json_records(segmentation.head(100))
            },
            'risk_scores': {
                'summary': {
                    'total': len(risk_scores),
                    'by_level': risk_scores['risk_level'].value_counts().to_dict(),
                    'avg_score': round(risk_scores['overall_score'].mean(), 2)
                },
                'data': self._dataframe_to_json_records(
                    risk_scores.nlargest(100, 'overall_score')
                )
            },
            'alerts': {
                'summary': {
                    'total': len(alerts),
                    'by_priority': {},
                    'by_category': {}
                },
                'data': [alert.to_dict() for alert in alerts[:100]]
            }
        }
        
        # Calculate alert summaries
        for alert in alerts:
            priority = alert.priority.value
            category = alert.category.value
            output['alerts']['summary']['by_priority'][priority] = \
                output['alerts']['summary']['by_priority'].get(priority, 0) + 1
            output['alerts']['summary']['by_category'][category] = \
                output['alerts']['summary']['by_category'].get(category, 0) + 1
        
        with open(filepath, 'w') as f:
            json.dump(output, f, indent=2, default=str)
        
        logger.info(f"Exported full analysis to {filepath}")
        return filepath
    
    def export_alerts(
        self,
        alerts: List[Alert],
        filename: Optional[str] = None
    ) -> Path:
        """Export alerts to JSON."""
        if filename:
            filepath = self.output_dir / filename
        else:
            filepath = self._get_filename("alerts", timestamp=False)
        
        output = {
            'generated_at': datetime.now().isoformat(),
            'total_alerts': len(alerts),
            'alerts': [alert.to_dict() for alert in alerts]
        }
        
        with open(filepath, 'w') as f:
            json.dump(output, f, indent=2, default=str)
        
        logger.info(f"Exported {len(alerts)} alerts to {filepath}")
        return filepath

