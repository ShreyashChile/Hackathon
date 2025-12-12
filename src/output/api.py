"""
FastAPI REST API for the ML Inventory Agent.
"""

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path
import logging

import json
import numpy as np
import pandas as pd

from ..config import get_config
from ..data.loader import DataLoader
from ..data.preprocessor import DataPreprocessor


def convert_to_serializable(obj):
    """Convert numpy/pandas types to JSON-serializable Python types."""
    if isinstance(obj, dict):
        return {k: convert_to_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_serializable(item) for item in obj]
    elif isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj) if not np.isnan(obj) else None
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif hasattr(obj, 'isoformat'):  # datetime-like
        return obj.isoformat()
    elif hasattr(obj, 'value'):  # Enum
        return obj.value
    elif pd.isna(obj):
        return None
    else:
        return obj


def df_to_records(df: pd.DataFrame) -> list:
    """Convert DataFrame to JSON-serializable list of dicts."""
    records = df.to_dict(orient='records')
    return [convert_to_serializable(r) for r in records]
from ..ml.demand_shift import DemandShiftDetector
from ..ml.non_moving import NonMovingDetector
from ..ml.segmentation import SKUSegmentation
from ..ml.scoring import RiskScorer
from .alerts import AlertGenerator
from .database import DatabaseManager
from .exporters import CSVExporter, JSONExporter

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="ML Inventory Agent API",
    description="API for demand shift detection and non-moving inventory identification",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state for analysis results
_analysis_state = {
    'last_run_id': None,
    'demand_shifts': None,
    'non_moving': None,
    'segmentation': None,
    'risk_scores': None,
    'alerts': None,
    'dataset': None
}


# Pydantic models for API responses
class AnalysisStatus(BaseModel):
    status: str
    last_run_id: Optional[str]
    last_run_time: Optional[str]
    total_items: Optional[int]
    total_locations: Optional[int]


class DemandShiftItem(BaseModel):
    item_id: str
    location_id: str
    shift_detected: bool
    shift_type: Optional[str]
    shift_direction: str
    shift_magnitude: float
    confidence_score: float
    baseline_demand: float
    current_demand: float
    category: Optional[str]


class NonMovingItem(BaseModel):
    item_id: str
    location_id: str
    movement_category: str
    days_since_movement: float
    current_inventory: float
    non_moving_risk_score: float
    recommended_action: str
    category: Optional[str]


class SegmentationItem(BaseModel):
    item_id: str
    location_id: Optional[str]
    abc_class: str
    xyz_class: str
    segment: str
    total_qty: float
    avg_qty: float
    cv: float
    category: Optional[str]


class RiskScoreItem(BaseModel):
    item_id: str
    location_id: str
    overall_score: float
    risk_level: str
    demand_shift_score: float
    non_moving_score: float
    shelf_life_score: float
    primary_risk_factor: str
    on_hand_qty: float
    category: Optional[str]
    recommendations: List[str]


class AlertItem(BaseModel):
    alert_id: str
    item_id: str
    location_id: str
    priority: str
    category: str
    title: str
    description: str
    risk_score: float
    created_at: str
    recommendations: List[str]


class AnalysisResponse(BaseModel):
    success: bool
    run_id: str
    message: str
    summary: Dict[str, Any]


class SKUAnalysis(BaseModel):
    item_id: str
    locations: List[str]
    demand_shifts: List[Dict]
    non_moving_status: List[Dict]
    segmentation: List[Dict]
    risk_scores: List[Dict]
    overall_status: str


# Helper functions
def ensure_analysis_run():
    """Ensure analysis has been run."""
    if _analysis_state['demand_shifts'] is None:
        raise HTTPException(
            status_code=400,
            detail="No analysis has been run yet. Call POST /api/run-analysis first."
        )


def run_full_analysis():
    """Run complete analysis pipeline."""
    logger.info("Starting full analysis pipeline...")
    config = get_config()
    
    # Load data
    loader = DataLoader(config.data_dir)
    dataset = loader.load_all()
    _analysis_state['dataset'] = dataset
    
    # Preprocess
    preprocessor = DataPreprocessor(dataset)
    dataset = preprocessor.preprocess()
    
    # Initialize database
    db = DatabaseManager()
    
    # Create run record
    run_id = db.create_run(
        total_skus=len(dataset.sku_list),
        total_locations=len(dataset.location_list),
        data_start_date=str(dataset.date_range[0]),
        data_end_date=str(dataset.date_range[1])
    )
    _analysis_state['last_run_id'] = run_id
    
    # Run analyses
    logger.info("Running demand shift detection...")
    shift_detector = DemandShiftDetector()
    demand_shifts = shift_detector.detect(dataset)
    _analysis_state['demand_shifts'] = demand_shifts
    db.save_demand_shifts(run_id, demand_shifts)
    
    logger.info("Running non-moving detection...")
    nm_detector = NonMovingDetector()
    non_moving = nm_detector.detect(dataset)
    _analysis_state['non_moving'] = non_moving
    db.save_non_moving(run_id, non_moving)
    
    logger.info("Running segmentation...")
    segmenter = SKUSegmentation()
    segmentation = segmenter.segment_all(dataset, by_location=True)
    _analysis_state['segmentation'] = segmentation
    db.save_segmentation(run_id, segmentation)
    
    logger.info("Calculating risk scores...")
    scorer = RiskScorer()
    risk_scores = scorer.score(demand_shifts, non_moving, dataset)
    _analysis_state['risk_scores'] = risk_scores
    db.save_risk_scores(run_id, risk_scores)
    
    logger.info("Generating alerts...")
    alert_gen = AlertGenerator()
    shift_alerts = alert_gen.generate_demand_shift_alerts(demand_shifts)
    nm_alerts = alert_gen.generate_non_moving_alerts(non_moving)
    risk_alerts = alert_gen.generate_risk_alerts(risk_scores)
    all_alerts = alert_gen.consolidate_alerts(shift_alerts, nm_alerts, risk_alerts)
    _analysis_state['alerts'] = all_alerts
    db.save_alerts(run_id, all_alerts)
    
    # Export results
    csv_exporter = CSVExporter()
    csv_exporter.export_demand_shifts(demand_shifts)
    csv_exporter.export_non_moving(non_moving)
    csv_exporter.export_segmentation(segmentation)
    csv_exporter.export_risk_scores(risk_scores)
    csv_exporter.export_alerts(all_alerts)
    
    json_exporter = JSONExporter()
    json_exporter.export_full_analysis(
        demand_shifts, non_moving, segmentation, risk_scores, all_alerts
    )
    
    db.complete_run(run_id)
    
    logger.info(f"Analysis complete. Run ID: {run_id}")
    
    return {
        'run_id': run_id,
        'shifts_detected': int(demand_shifts['shift_detected'].sum()),
        'non_moving_items': len(non_moving[non_moving['movement_category'].astype(str) != 'active']),
        'high_risk_items': len(risk_scores[risk_scores['risk_level'].isin(['critical', 'high'])]),
        'total_alerts': len(all_alerts)
    }


# API Endpoints
@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint."""
    return {"status": "healthy", "service": "ML Inventory Agent API", "version": "1.0.0"}


@app.get("/api/status", response_model=AnalysisStatus, tags=["Status"])
async def get_status():
    """Get current analysis status."""
    db = DatabaseManager()
    latest_run = db.get_latest_run()
    
    if latest_run:
        return AnalysisStatus(
            status="ready" if _analysis_state['demand_shifts'] is not None else "no_analysis",
            last_run_id=latest_run['run_id'],
            last_run_time=latest_run['run_timestamp'],
            total_items=latest_run['total_skus'],
            total_locations=latest_run['total_locations']
        )
    
    return AnalysisStatus(
        status="no_analysis",
        last_run_id=None,
        last_run_time=None,
        total_items=None,
        total_locations=None
    )


@app.post("/api/run-analysis", response_model=AnalysisResponse, tags=["Analysis"])
async def trigger_analysis(background_tasks: BackgroundTasks):
    """Trigger a full analysis run."""
    try:
        summary = run_full_analysis()
        
        return AnalysisResponse(
            success=True,
            run_id=summary['run_id'],
            message="Analysis completed successfully",
            summary=summary
        )
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/demand-shifts", tags=["Demand Shifts"])
async def get_demand_shifts(
    shift_detected: Optional[bool] = None,
    direction: Optional[str] = Query(None, regex="^(increase|decrease|stable)$"),
    min_confidence: float = 0.0,
    category: Optional[str] = None,
    location_id: Optional[str] = None,
    limit: int = Query(100, le=1000)
):
    """Get demand shift detection results."""
    ensure_analysis_run()
    
    df = _analysis_state['demand_shifts'].copy()
    
    if shift_detected is not None:
        df = df[df['shift_detected'] == shift_detected]
    if direction:
        df = df[df['shift_direction'] == direction]
    if min_confidence > 0:
        df = df[df['confidence_score'] >= min_confidence]
    if category:
        df = df[df['category'] == category]
    if location_id:
        df = df[df['location_id'] == location_id]
    
    df = df.head(limit)
    
    return {
        "total": len(df),
        "data": df.to_dict(orient='records')
    }


@app.get("/api/non-moving", tags=["Non-Moving Inventory"])
async def get_non_moving(
    movement_category: Optional[str] = Query(
        None, 
        regex="^(active|slow_moving|non_moving|dead_stock)$"
    ),
    min_risk_score: float = 0.0,
    location_id: Optional[str] = None,
    has_inventory: Optional[bool] = None,
    limit: int = Query(100, le=1000)
):
    """Get non-moving inventory results."""
    ensure_analysis_run()
    
    df = _analysis_state['non_moving'].copy()
    
    if movement_category:
        df = df[df['movement_category'].astype(str) == movement_category]
    if min_risk_score > 0:
        df = df[df['non_moving_risk_score'] >= min_risk_score]
    if location_id:
        df = df[df['location_id'] == location_id]
    if has_inventory is not None:
        if has_inventory:
            df = df[df['current_inventory'] > 0]
        else:
            df = df[df['current_inventory'] == 0]
    
    df = df.head(limit)
    
    # Convert enum values
    df['movement_category'] = df['movement_category'].astype(str)
    
    return {
        "total": len(df),
        "data": df.to_dict(orient='records')
    }


@app.get("/api/segmentation", tags=["Segmentation"])
async def get_segmentation(
    segment: Optional[str] = Query(None, regex="^[ABC][XYZ]$"),
    abc_class: Optional[str] = Query(None, regex="^[ABC]$"),
    xyz_class: Optional[str] = Query(None, regex="^[XYZ]$"),
    location_id: Optional[str] = None,
    limit: int = Query(100, le=1000)
):
    """Get ABC-XYZ segmentation results."""
    ensure_analysis_run()
    
    df = _analysis_state['segmentation'].copy()
    
    if segment:
        df = df[df['segment'] == segment]
    if abc_class:
        df = df[df['abc_class'].apply(lambda x: x.value if hasattr(x, 'value') else x) == abc_class]
    if xyz_class:
        df = df[df['xyz_class'].apply(lambda x: x.value if hasattr(x, 'value') else x) == xyz_class]
    if location_id:
        df = df[df['location_id'] == location_id]
    
    # Convert enum values
    for col in ['abc_class', 'xyz_class']:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: x.value if hasattr(x, 'value') else x)
    
    df = df.head(limit)
    
    return {
        "total": len(df),
        "data": df.to_dict(orient='records')
    }


@app.get("/api/segmentation/matrix", tags=["Segmentation"])
async def get_segmentation_matrix(location_id: Optional[str] = None):
    """Get ABC-XYZ segmentation matrix."""
    ensure_analysis_run()
    
    segmenter = SKUSegmentation()
    df = _analysis_state['segmentation'].copy()
    
    if location_id:
        df = df[df['location_id'] == location_id]
    
    matrix = segmenter.get_segment_matrix(df)
    
    return {
        "matrix": matrix.to_dict(),
        "total_items": len(df)
    }


@app.get("/api/alerts", tags=["Alerts"])
async def get_alerts(
    priority: Optional[str] = Query(
        None,
        regex="^(P1_CRITICAL|P2_HIGH|P3_MEDIUM|P4_LOW|P5_INFO)$"
    ),
    category: Optional[str] = Query(
        None,
        regex="^(demand_shift|inventory_risk|shelf_life|supply_risk|optimization)$"
    ),
    limit: int = Query(100, le=500)
):
    """Get alerts."""
    ensure_analysis_run()
    
    alerts = _analysis_state['alerts']
    
    if priority:
        alerts = [a for a in alerts if a.priority.value == priority]
    if category:
        alerts = [a for a in alerts if a.category.value == category]
    
    alerts = alerts[:limit]
    
    return {
        "total": len(alerts),
        "data": [a.to_dict() for a in alerts]
    }


@app.get("/api/alerts/summary", tags=["Alerts"])
async def get_alerts_summary():
    """Get alerts summary."""
    ensure_analysis_run()
    
    alert_gen = AlertGenerator()
    return alert_gen.get_alert_summary(_analysis_state['alerts'])


@app.get("/api/risk-scores", tags=["Risk Scores"])
async def get_risk_scores(
    risk_level: Optional[str] = Query(
        None,
        regex="^(critical|high|medium|low|minimal)$"
    ),
    min_score: float = 0.0,
    primary_factor: Optional[str] = None,
    location_id: Optional[str] = None,
    limit: int = Query(100, le=1000)
):
    """Get risk scores."""
    ensure_analysis_run()
    
    df = _analysis_state['risk_scores'].copy()
    
    if risk_level:
        df = df[df['risk_level'] == risk_level]
    if min_score > 0:
        df = df[df['overall_score'] >= min_score]
    if primary_factor:
        df = df[df['primary_risk_factor'] == primary_factor]
    if location_id:
        df = df[df['location_id'] == location_id]
    
    df = df.head(limit)
    
    return {
        "total": len(df),
        "data": df.to_dict(orient='records')
    }


@app.get("/api/risk-scores/summary", tags=["Risk Scores"])
async def get_risk_summary():
    """Get risk score summary."""
    ensure_analysis_run()
    
    scorer = RiskScorer()
    return scorer.get_risk_summary(_analysis_state['risk_scores'])


@app.get("/api/sku/{sku_id}/analysis", tags=["SKU Analysis"])
async def get_sku_analysis(sku_id: str):
    """Get detailed analysis for a specific SKU."""
    ensure_analysis_run()
    
    # Get data for this SKU
    demand_shifts = _analysis_state['demand_shifts']
    non_moving = _analysis_state['non_moving']
    segmentation = _analysis_state['segmentation']
    risk_scores = _analysis_state['risk_scores']
    
    sku_shifts = demand_shifts[demand_shifts['item_id'] == sku_id]
    sku_nm = non_moving[non_moving['item_id'] == sku_id]
    sku_seg = segmentation[segmentation['item_id'] == sku_id]
    sku_risk = risk_scores[risk_scores['item_id'] == sku_id]
    
    if len(sku_shifts) == 0:
        raise HTTPException(status_code=404, detail=f"SKU {sku_id} not found")
    
    # Determine overall status
    max_risk = float(sku_risk['overall_score'].max()) if len(sku_risk) > 0 else 0
    if max_risk >= 60:
        overall_status = "requires_attention"
    elif max_risk >= 40:
        overall_status = "monitor"
    else:
        overall_status = "healthy"
    
    # Convert enums in copies
    sku_nm_copy = sku_nm.copy()
    sku_nm_copy['movement_category'] = sku_nm_copy['movement_category'].astype(str)
    
    sku_seg_copy = sku_seg.copy()
    for col in ['abc_class', 'xyz_class']:
        if col in sku_seg_copy.columns:
            sku_seg_copy[col] = sku_seg_copy[col].apply(
                lambda x: x.value if hasattr(x, 'value') else str(x)
            )
    
    return {
        "item_id": sku_id,
        "locations": sku_shifts['location_id'].unique().tolist(),
        "demand_shifts": df_to_records(sku_shifts),
        "non_moving_status": df_to_records(sku_nm_copy),
        "segmentation": df_to_records(sku_seg_copy),
        "risk_scores": df_to_records(sku_risk),
        "overall_status": overall_status
    }


@app.get("/api/locations", tags=["Reference Data"])
async def get_locations():
    """Get list of locations."""
    ensure_analysis_run()
    
    dataset = _analysis_state['dataset']
    return {
        "locations": dataset.locations.to_dict(orient='records')
    }


@app.get("/api/items", tags=["Reference Data"])
async def get_items(category: Optional[str] = None):
    """Get list of items."""
    ensure_analysis_run()
    
    dataset = _analysis_state['dataset']
    items = dataset.items.copy()
    
    if category:
        items = items[items['category'] == category]
    
    # Convert dates to strings
    for col in ['launch_date', 'obsolete_date']:
        if col in items.columns:
            items[col] = items[col].astype(str)
    
    return {
        "total": len(items),
        "data": items.to_dict(orient='records')
    }


@app.get("/api/dashboard/summary", tags=["Dashboard"])
async def get_dashboard_summary():
    """Get summary data for dashboard."""
    ensure_analysis_run()
    
    demand_shifts = _analysis_state['demand_shifts']
    non_moving = _analysis_state['non_moving']
    risk_scores = _analysis_state['risk_scores']
    alerts = _analysis_state['alerts']
    
    return {
        "overview": {
            "total_sku_locations": len(demand_shifts),
            "unique_skus": demand_shifts['item_id'].nunique(),
            "unique_locations": demand_shifts['location_id'].nunique()
        },
        "demand_shifts": {
            "total_shifts": int(demand_shifts['shift_detected'].sum()),
            "increases": int((demand_shifts['shift_detected'] & (demand_shifts['shift_direction'] == 'increase')).sum()),
            "decreases": int((demand_shifts['shift_detected'] & (demand_shifts['shift_direction'] == 'decrease')).sum())
        },
        "non_moving": {
            "dead_stock": int((non_moving['movement_category'].astype(str) == 'dead_stock').sum()),
            "non_moving": int((non_moving['movement_category'].astype(str) == 'non_moving').sum()),
            "slow_moving": int((non_moving['movement_category'].astype(str) == 'slow_moving').sum()),
            "active": int((non_moving['movement_category'].astype(str) == 'active').sum())
        },
        "risk_levels": risk_scores['risk_level'].value_counts().to_dict(),
        "alerts": {
            "total": len(alerts),
            "critical": len([a for a in alerts if a.priority.value == 'P1_CRITICAL']),
            "high": len([a for a in alerts if a.priority.value == 'P2_HIGH'])
        }
    }


def create_app():
    """Create and configure the FastAPI application."""
    return app

