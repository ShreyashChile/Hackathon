"""
Pydantic schemas for data validation.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date
from enum import Enum
import pandas as pd


class ProductCategory(str, Enum):
    """Product lifecycle categories."""
    DECLINING = "Declining"
    STAPLE = "Staple"
    SEASONAL = "Seasonal"
    NEW_LAUNCH = "NewLaunch"
    SLOW_MOVER = "SlowMover"


class UnitOfMeasure(str, Enum):
    """Units of measure."""
    EA = "EA"
    CASE = "CASE"
    BOX = "BOX"


class ItemSchema(BaseModel):
    """Schema for item master data."""
    item_id: str
    description: str
    category: ProductCategory
    uom: UnitOfMeasure
    shelf_life_days: int
    launch_date: date
    obsolete_date: Optional[date] = None


class LocationSchema(BaseModel):
    """Schema for location data."""
    location_id: str
    name: str


class SalesHistorySchema(BaseModel):
    """Schema for weekly sales history."""
    week_ending: date
    item_id: str
    location_id: str
    qty_sold: int


class InventorySnapshotSchema(BaseModel):
    """Schema for weekly inventory snapshots."""
    week_ending: date
    item_id: str
    location_id: str
    on_hand_qty: int


class ForecastSchema(BaseModel):
    """Schema for weekly forecasts."""
    week_ending: date
    item_id: str
    location_id: str
    forecast_qty: int


class ReorderPolicySchema(BaseModel):
    """Schema for item reorder policies."""
    item_id: str
    min_qty: int
    max_qty: int


class SupplierSchema(BaseModel):
    """Schema for supplier data."""
    supplier_id: str
    supplier_name: str
    base_lead_time_days: int
    on_time_delivery_rate: float
    defect_rate_pct: float


class PurchaseOrderSchema(BaseModel):
    """Schema for purchase orders."""
    po_id: str
    order_week: date
    expected_week: date
    item_id: str
    location_id: str
    supplier_id: str
    qty_ordered: int


class AnalysisDataset:
    """Container for all analysis data."""
    
    def __init__(
        self,
        items: pd.DataFrame,
        locations: pd.DataFrame,
        sales_history: pd.DataFrame,
        inventory_snapshots: pd.DataFrame,
        forecasts: pd.DataFrame,
        reorder_policies: pd.DataFrame,
        suppliers: pd.DataFrame,
        non_moving_candidates: pd.DataFrame,
        purchase_orders: Optional[pd.DataFrame] = None,
        merged_data: Optional[pd.DataFrame] = None
    ):
        self.items = items
        self.locations = locations
        self.sales_history = sales_history
        self.inventory_snapshots = inventory_snapshots
        self.forecasts = forecasts
        self.reorder_policies = reorder_policies
        self.suppliers = suppliers
        self.non_moving_candidates = non_moving_candidates
        self.purchase_orders = purchase_orders if purchase_orders is not None else pd.DataFrame()
        self.merged_data = merged_data
    
    @property
    def sku_list(self) -> List[str]:
        """Get list of all SKU IDs."""
        return self.items['item_id'].unique().tolist()
    
    @property
    def location_list(self) -> List[str]:
        """Get list of all location IDs."""
        return self.locations['location_id'].unique().tolist()
    
    @property
    def date_range(self) -> tuple:
        """Get the date range of the sales data."""
        return (
            self.sales_history['week_ending'].min(),
            self.sales_history['week_ending'].max()
        )
    
    def get_sku_sales(self, item_id: str, location_id: Optional[str] = None) -> pd.DataFrame:
        """Get sales history for a specific SKU."""
        mask = self.sales_history['item_id'] == item_id
        if location_id:
            mask &= self.sales_history['location_id'] == location_id
        return self.sales_history[mask].sort_values('week_ending')
    
    def get_sku_inventory(self, item_id: str, location_id: Optional[str] = None) -> pd.DataFrame:
        """Get inventory history for a specific SKU."""
        mask = self.inventory_snapshots['item_id'] == item_id
        if location_id:
            mask &= self.inventory_snapshots['location_id'] == location_id
        return self.inventory_snapshots[mask].sort_values('week_ending')
    
    def get_item_details(self, item_id: str) -> Optional[pd.Series]:
        """Get item master details."""
        item = self.items[self.items['item_id'] == item_id]
        if len(item) > 0:
            return item.iloc[0]
        return None

