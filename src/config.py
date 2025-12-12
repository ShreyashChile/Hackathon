"""
Configuration settings for the ML Inventory Agent.
"""

from pathlib import Path
from pydantic import BaseModel
from typing import Optional
from datetime import date


class NonMovingConfig(BaseModel):
    """Configuration for non-moving inventory detection."""
    # Duration thresholds (in weeks) - configurable
    non_moving_weeks_3m: int = 12   # 3 months
    non_moving_weeks_6m: int = 26   # 6 months  
    non_moving_weeks_1y: int = 52   # 1 year
    
    # Default threshold to use (in weeks)
    default_threshold_weeks: int = 12  # 12 weeks as per requirement
    
    # Legacy thresholds (keeping for backwards compatibility)
    slow_moving_days: int = 60
    non_moving_days: int = 90
    dead_stock_days: int = 180


class DemandShiftConfig(BaseModel):
    """Configuration for demand shift detection."""
    cusum_threshold: float = 2.0  # Standard deviations
    ma_short_window: int = 4  # weeks
    ma_long_window: int = 12  # weeks
    zscore_threshold: float = 2.5  # For anomaly detection
    min_data_points: int = 12  # Minimum weeks of data required


class SegmentationConfig(BaseModel):
    """Configuration for ABC-XYZ segmentation."""
    abc_a_percentile: float = 0.8  # Top 20% by volume
    abc_b_percentile: float = 0.5  # Next 30%
    xyz_x_cv: float = 0.5  # CV threshold for X (stable)
    xyz_y_cv: float = 1.0  # CV threshold for Y (variable)


class ScoringConfig(BaseModel):
    """Configuration for confidence/risk scoring."""
    demand_shift_weight: float = 0.25
    non_moving_weight: float = 0.30
    shelf_life_weight: float = 0.20
    lifecycle_weight: float = 0.15
    inventory_value_weight: float = 0.10


class DatabaseConfig(BaseModel):
    """Configuration for PostgreSQL database connection."""
    host: str = "localhost"
    database: str = "inventory_db"
    user: str = "postgres"
    password: str = ""
    port: int = 5432
    schema_name: str = "inventory"
    
    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """Load database configuration from environment variables."""
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        return cls(
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            database=os.getenv('POSTGRES_DATABASE', 'inventory_db'),
            user=os.getenv('POSTGRES_USER', 'postgres'),
            password=os.getenv('POSTGRES_PASSWORD', ''),
            port=int(os.getenv('POSTGRES_PORT', '5432')),
            schema_name=os.getenv('POSTGRES_SCHEMA', 'inventory')
        )


class Config(BaseModel):
    """Main configuration class."""
    # Paths
    data_dir: Path = Path("data")
    output_dir: Path = Path("outputs")
    
    # Sub-configurations
    non_moving: NonMovingConfig = NonMovingConfig()
    demand_shift: DemandShiftConfig = DemandShiftConfig()
    segmentation: SegmentationConfig = SegmentationConfig()
    scoring: ScoringConfig = ScoringConfig()
    database: DatabaseConfig = DatabaseConfig()
    
    # Analysis settings
    analysis_date: Optional[date] = None  # If None, use latest date in data
    
    # API settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    class Config:
        arbitrary_types_allowed = True


# Global config instance
config = Config()


def get_config() -> Config:
    """Get the global configuration instance."""
    return config


def update_config(**kwargs) -> Config:
    """Update configuration with new values."""
    global config
    config = Config(**{**config.model_dump(), **kwargs})
    return config

