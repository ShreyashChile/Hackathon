"""
Demand shift detection module.

Implements multiple techniques to detect significant changes in demand patterns:
- CUSUM (Cumulative Sum) for sustained shifts
- Moving Average Crossover for trend changes
- Z-Score anomaly detection for sudden spikes/drops
- Seasonal decomposition for pattern changes
"""

import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Tuple
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
import logging
from scipy import stats

from ..config import get_config, DemandShiftConfig
from ..data.schemas import AnalysisDataset

logger = logging.getLogger(__name__)


class ShiftDirection(str, Enum):
    """Direction of demand shift."""
    INCREASE = "increase"
    DECREASE = "decrease"
    STABLE = "stable"


class ShiftType(str, Enum):
    """Type of demand shift detected."""
    SUSTAINED = "sustained"  # Long-term trend change
    SPIKE = "spike"  # Sudden increase
    DROP = "drop"  # Sudden decrease
    SEASONAL_ANOMALY = "seasonal_anomaly"
    TREND_CHANGE = "trend_change"


@dataclass
class DemandShiftResult:
    """Result of demand shift detection for a single item-location."""
    item_id: str
    location_id: str
    shift_detected: bool
    shift_type: Optional[ShiftType]
    shift_direction: ShiftDirection
    shift_magnitude: float  # Percentage change
    confidence_score: float  # 0-100
    detection_date: datetime
    baseline_demand: float
    current_demand: float
    cusum_signal: bool
    ma_crossover_signal: bool
    zscore_signal: bool
    details: Dict


class DemandShiftDetector:
    """Detect demand shifts using multiple statistical techniques."""
    
    def __init__(self, config: Optional[DemandShiftConfig] = None):
        self.config = config or get_config().demand_shift
    
    def _calculate_cusum(
        self,
        series: pd.Series,
        threshold: Optional[float] = None
    ) -> Tuple[pd.Series, pd.Series, bool]:
        """
        Calculate CUSUM (Cumulative Sum) for detecting sustained shifts.
        
        Returns:
        - cusum_pos: Positive CUSUM values
        - cusum_neg: Negative CUSUM values
        - signal: Whether shift is detected
        """
        threshold = threshold or self.config.cusum_threshold
        
        # Calculate mean and std from first half of data (baseline)
        n = len(series)
        baseline_period = max(n // 2, self.config.min_data_points)
        baseline = series.iloc[:baseline_period]
        
        mean = baseline.mean()
        std = baseline.std()
        
        if std == 0 or np.isnan(std):
            return pd.Series([0] * n), pd.Series([0] * n), False
        
        # Standardize the series
        z = (series - mean) / std
        
        # Calculate CUSUM
        cusum_pos = np.zeros(n)
        cusum_neg = np.zeros(n)
        
        for i in range(1, n):
            cusum_pos[i] = max(0, cusum_pos[i-1] + z.iloc[i] - 0.5)
            cusum_neg[i] = min(0, cusum_neg[i-1] + z.iloc[i] + 0.5)
        
        # Check for signal
        signal = (
            np.max(cusum_pos) > threshold * std or 
            np.min(cusum_neg) < -threshold * std
        )
        
        return pd.Series(cusum_pos), pd.Series(cusum_neg), signal
    
    def _calculate_ma_crossover(
        self,
        series: pd.Series
    ) -> Tuple[pd.Series, pd.Series, bool, ShiftDirection]:
        """
        Detect trend changes using moving average crossover.
        
        Returns:
        - ma_short: Short-term moving average
        - ma_long: Long-term moving average
        - signal: Whether crossover detected
        - direction: Direction of crossover
        """
        ma_short = series.rolling(
            window=self.config.ma_short_window, 
            min_periods=1
        ).mean()
        
        ma_long = series.rolling(
            window=self.config.ma_long_window, 
            min_periods=1
        ).mean()
        
        # Check recent values for crossover
        recent_short = ma_short.iloc[-3:].mean() if len(ma_short) >= 3 else ma_short.iloc[-1]
        recent_long = ma_long.iloc[-3:].mean() if len(ma_long) >= 3 else ma_long.iloc[-1]
        
        # Compare with baseline (first 12 weeks or available data)
        baseline_period = min(self.config.ma_long_window, len(series) // 2)
        baseline_avg = series.iloc[:baseline_period].mean() if baseline_period > 0 else series.mean()
        
        # Determine direction and signal
        if recent_short > 0 and baseline_avg > 0:
            pct_change = (recent_short - baseline_avg) / baseline_avg
        else:
            pct_change = 0
        
        signal = abs(pct_change) > 0.25  # 25% change threshold
        
        if pct_change > 0.1:
            direction = ShiftDirection.INCREASE
        elif pct_change < -0.1:
            direction = ShiftDirection.DECREASE
        else:
            direction = ShiftDirection.STABLE
        
        return ma_short, ma_long, signal, direction
    
    def _detect_zscore_anomalies(
        self,
        series: pd.Series,
        threshold: Optional[float] = None
    ) -> Tuple[pd.Series, bool, List[int]]:
        """
        Detect anomalies using Z-score method.
        
        Returns:
        - zscores: Z-scores for each point
        - has_anomalies: Whether anomalies detected
        - anomaly_positions: List of positional indices of anomalies
        """
        threshold = threshold or self.config.zscore_threshold
        
        mean = series.mean()
        std = series.std()
        
        if std == 0 or np.isnan(std):
            return pd.Series([0] * len(series), index=series.index), False, []
        
        zscores = (series - mean) / std
        anomalies = zscores.abs() > threshold
        
        # Get positional indices (not index values) for anomalies
        anomaly_positions = [i for i, is_anomaly in enumerate(anomalies) if is_anomaly]
        
        return zscores, len(anomaly_positions) > 0, anomaly_positions
    
    def _detect_trend_change(
        self,
        series: pd.Series
    ) -> Tuple[float, float, bool]:
        """
        Detect significant trend change using linear regression.
        
        Returns:
        - slope_first_half: Slope of first half
        - slope_second_half: Slope of second half
        - trend_changed: Whether trend direction changed significantly
        """
        n = len(series)
        if n < self.config.min_data_points * 2:
            return 0, 0, False
        
        mid = n // 2
        
        # First half regression
        x1 = np.arange(mid)
        y1 = series.iloc[:mid].values
        if len(y1) > 1:
            slope1, _, _, _, _ = stats.linregress(x1, y1)
        else:
            slope1 = 0
        
        # Second half regression
        x2 = np.arange(n - mid)
        y2 = series.iloc[mid:].values
        if len(y2) > 1:
            slope2, _, _, _, _ = stats.linregress(x2, y2)
        else:
            slope2 = 0
        
        # Check for significant trend change
        # Sign change or magnitude change > 50%
        trend_changed = (
            (slope1 > 0 and slope2 < 0) or
            (slope1 < 0 and slope2 > 0) or
            (slope1 != 0 and abs(slope2 - slope1) / abs(slope1) > 0.5)
        )
        
        return slope1, slope2, trend_changed
    
    def detect_for_item_location(
        self,
        sales_data: pd.DataFrame,
        item_id: str,
        location_id: str
    ) -> DemandShiftResult:
        """Detect demand shifts for a specific item-location combination."""
        
        # Filter data
        mask = (sales_data['item_id'] == item_id) & (sales_data['location_id'] == location_id)
        item_data = sales_data[mask].sort_values('week_ending')
        
        if len(item_data) < self.config.min_data_points:
            return DemandShiftResult(
                item_id=item_id,
                location_id=location_id,
                shift_detected=False,
                shift_type=None,
                shift_direction=ShiftDirection.STABLE,
                shift_magnitude=0,
                confidence_score=0,
                detection_date=datetime.now(),
                baseline_demand=0,
                current_demand=0,
                cusum_signal=False,
                ma_crossover_signal=False,
                zscore_signal=False,
                details={"error": "Insufficient data"}
            )
        
        series = item_data['qty_sold']
        detection_date = item_data['week_ending'].max()
        
        # Run detection methods
        cusum_pos, cusum_neg, cusum_signal = self._calculate_cusum(series)
        ma_short, ma_long, ma_signal, ma_direction = self._calculate_ma_crossover(series)
        zscores, zscore_signal, anomaly_indices = self._detect_zscore_anomalies(series)
        slope1, slope2, trend_changed = self._detect_trend_change(series)
        
        # Calculate baseline and current demand
        baseline_period = min(self.config.ma_long_window, len(series) // 2)
        baseline_demand = series.iloc[:baseline_period].mean() if baseline_period > 0 else 0
        current_demand = series.iloc[-self.config.ma_short_window:].mean()
        
        # Calculate shift magnitude
        if baseline_demand > 0:
            shift_magnitude = ((current_demand - baseline_demand) / baseline_demand) * 100
        else:
            shift_magnitude = 100 if current_demand > 0 else 0
        
        # Determine overall shift detection and type
        shift_detected = cusum_signal or ma_signal or zscore_signal or trend_changed
        
        # Determine shift type
        shift_type = None
        if shift_detected:
            if cusum_signal and abs(shift_magnitude) > 25:
                shift_type = ShiftType.SUSTAINED
            elif zscore_signal and len(anomaly_indices) > 0:
                # anomaly_indices are positional indices
                n = len(series)
                recent_anomalies = [i for i in anomaly_indices if i >= n - 4]
                if recent_anomalies:
                    # Use iloc with positional indices
                    recent_zscores = [zscores.iloc[i] for i in recent_anomalies]
                    if np.mean(recent_zscores) > 0:
                        shift_type = ShiftType.SPIKE
                    else:
                        shift_type = ShiftType.DROP
            elif trend_changed:
                shift_type = ShiftType.TREND_CHANGE
            else:
                shift_type = ShiftType.SUSTAINED if abs(shift_magnitude) > 20 else None
        
        # Determine direction
        if shift_magnitude > 10:
            direction = ShiftDirection.INCREASE
        elif shift_magnitude < -10:
            direction = ShiftDirection.DECREASE
        else:
            direction = ShiftDirection.STABLE
        
        # Calculate confidence score
        signals_count = sum([cusum_signal, ma_signal, zscore_signal, trend_changed])
        confidence_score = min(signals_count * 25 + abs(shift_magnitude) * 0.5, 100)
        
        return DemandShiftResult(
            item_id=item_id,
            location_id=location_id,
            shift_detected=shift_detected,
            shift_type=shift_type,
            shift_direction=direction,
            shift_magnitude=round(shift_magnitude, 2),
            confidence_score=round(confidence_score, 2),
            detection_date=detection_date,
            baseline_demand=round(baseline_demand, 2),
            current_demand=round(current_demand, 2),
            cusum_signal=cusum_signal,
            ma_crossover_signal=ma_signal,
            zscore_signal=zscore_signal,
            details={
                "trend_slope_first_half": round(slope1, 4),
                "trend_slope_second_half": round(slope2, 4),
                "trend_changed": trend_changed,
                "num_anomalies": len(anomaly_indices),
                "data_points": len(series)
            }
        )
    
    def detect(self, dataset: AnalysisDataset) -> pd.DataFrame:
        """
        Detect demand shifts for all item-location combinations.
        
        Returns DataFrame with shift detection results.
        """
        logger.info("Detecting demand shifts...")
        
        results = []
        
        # Get unique item-location combinations
        combinations = dataset.sales_history[
            ['item_id', 'location_id']
        ].drop_duplicates()
        
        total = len(combinations)
        for idx, (_, row) in enumerate(combinations.iterrows()):
            if (idx + 1) % 50 == 0:
                logger.info(f"Processing {idx + 1}/{total}")
            
            result = self.detect_for_item_location(
                dataset.sales_history,
                row['item_id'],
                row['location_id']
            )
            results.append(result)
        
        # Convert to DataFrame
        df = pd.DataFrame([
            {
                'item_id': r.item_id,
                'location_id': r.location_id,
                'shift_detected': r.shift_detected,
                'shift_type': r.shift_type.value if r.shift_type else None,
                'shift_direction': r.shift_direction.value,
                'shift_magnitude': r.shift_magnitude,
                'confidence_score': r.confidence_score,
                'detection_date': r.detection_date,
                'baseline_demand': r.baseline_demand,
                'current_demand': r.current_demand,
                'cusum_signal': r.cusum_signal,
                'ma_crossover_signal': r.ma_crossover_signal,
                'zscore_signal': r.zscore_signal,
                **r.details
            }
            for r in results
        ])
        
        # Add item category info
        df = df.merge(
            dataset.items[['item_id', 'category']],
            on='item_id',
            how='left'
        )
        
        logger.info(f"Detection complete. Found {df['shift_detected'].sum()} shifts out of {len(df)} combinations")
        
        return df.sort_values('confidence_score', ascending=False)
    
    def get_shift_summary(self, detection_result: pd.DataFrame) -> Dict:
        """Get summary statistics of detected shifts."""
        shifts = detection_result[detection_result['shift_detected']]
        
        return {
            'total_combinations': len(detection_result),
            'shifts_detected': len(shifts),
            'shift_rate': round(len(shifts) / len(detection_result) * 100, 2),
            'by_direction': shifts['shift_direction'].value_counts().to_dict(),
            'by_type': shifts['shift_type'].value_counts().to_dict() if 'shift_type' in shifts else {},
            'by_category': shifts.groupby('category')['shift_detected'].count().to_dict(),
            'avg_magnitude': round(shifts['shift_magnitude'].mean(), 2) if len(shifts) > 0 else 0,
            'avg_confidence': round(shifts['confidence_score'].mean(), 2) if len(shifts) > 0 else 0
        }
    
    def get_significant_shifts(
        self,
        detection_result: pd.DataFrame,
        min_confidence: float = 50.0,
        min_magnitude: float = 20.0
    ) -> pd.DataFrame:
        """Get significant shifts above thresholds."""
        return detection_result[
            (detection_result['shift_detected']) &
            (detection_result['confidence_score'] >= min_confidence) &
            (detection_result['shift_magnitude'].abs() >= min_magnitude)
        ].copy()

