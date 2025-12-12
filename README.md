# ML Agent for Demand Shift Detection and Non-Moving Inventory Identification

An intelligent ML-driven agent that continuously analyzes inventory and sales data to detect demand shifts, identify non-moving inventory, and provide actionable alerts for supply chain optimization.

## Features

- **Demand Shift Detection**: Uses CUSUM, moving average crossover, and Z-score anomaly detection to identify significant changes in demand patterns
- **Non-Moving Inventory Detection**: Configurable thresholds (60/90/180 days) to classify inventory as slow-moving, non-moving, or dead stock
- **ABC-XYZ Segmentation**: Classifies SKUs based on volume (ABC) and demand variability (XYZ)
- **Risk Scoring**: Composite risk scores combining demand shifts, movement status, shelf life, and product lifecycle
- **Alert Generation**: Priority-based alerts with actionable recommendations
- **REST API**: FastAPI endpoints for integration with planning and ERP/SCM systems
- **Interactive Dashboard**: Plotly-based visualizations for analysis results

## Project Structure

```
Hackathon/
├── data/                      # Input data files (CSV)
├── src/
│   ├── config.py              # Configuration settings
│   ├── data/
│   │   ├── loader.py          # Data loading from CSV/Excel
│   │   ├── preprocessor.py    # Feature engineering
│   │   └── schemas.py         # Pydantic data models
│   ├── ml/
│   │   ├── demand_shift.py    # Demand shift detection
│   │   ├── non_moving.py      # Non-moving inventory detection
│   │   ├── segmentation.py    # ABC-XYZ classification
│   │   └── scoring.py         # Risk scoring engine
│   ├── output/
│   │   ├── alerts.py          # Alert generation
│   │   ├── database.py        # SQLite persistence
│   │   ├── exporters.py       # CSV/JSON export
│   │   └── api.py             # FastAPI endpoints
│   └── visualization/
│       ├── charts.py          # Plotly chart generation
│       └── dashboard.py       # HTML dashboard
├── outputs/                   # Generated results
├── main.py                    # Entry point
├── requirements.txt           # Python dependencies
└── README.md
```

## Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Run Analysis Pipeline

```bash
# Run complete analysis
python main.py analyze

# With custom paths
python main.py analyze --data-dir ./data --output-dir ./outputs
```

### Start API Server

```bash
# Start API only
python main.py api

# Run analysis then start API
python main.py api --run-analysis

# Full mode: analyze + API
python main.py full
```

### API Endpoints

Once the API is running, access the documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

Key endpoints:
- `GET /api/demand-shifts` - Get demand shift detection results
- `GET /api/non-moving` - Get non-moving inventory status
- `GET /api/segmentation` - Get ABC-XYZ classification
- `GET /api/alerts` - Get prioritized alerts
- `GET /api/risk-scores` - Get risk scores
- `GET /api/sku/{sku_id}/analysis` - Detailed SKU analysis
- `POST /api/run-analysis` - Trigger new analysis run

## Configuration

Key configuration parameters in `src/config.py`:

```python
# Non-moving thresholds (days)
SLOW_MOVING_DAYS = 60
NON_MOVING_DAYS = 90
DEAD_STOCK_DAYS = 180

# Demand shift detection
CUSUM_THRESHOLD = 2.0  # Standard deviations
MA_SHORT_WINDOW = 4    # weeks
MA_LONG_WINDOW = 12    # weeks

# ABC-XYZ thresholds
ABC_A_PERCENTILE = 0.8  # Top 20% by volume
ABC_B_PERCENTILE = 0.5  # Next 30%
XYZ_X_CV = 0.5          # CV threshold for stable demand
XYZ_Y_CV = 1.0          # CV threshold for variable demand
```

## Data Requirements

### Input Files

| File | Purpose | Required Columns |
|------|---------|-----------------|
| `items.csv` | SKU master | item_id, description, category, uom, shelf_life_days, launch_date |
| `locations.csv` | Location master | location_id, name |
| `sales_history_weekly.csv` | Weekly sales | week_ending, item_id, location_id, qty_sold |
| `inventory_snapshots_weekly.csv` | Weekly inventory | week_ending, item_id, location_id, on_hand_qty |
| `forecasts_weekly.csv` | Weekly forecasts | week_ending, item_id, location_id, forecast_qty |
| `item_reorder_policy.csv` | Min/Max policies | item_id, min_qty, max_qty |

## Output Files

After running analysis, outputs are generated in the `outputs/` directory:

- `demand_shifts.csv` - Detected demand shifts
- `non_moving_inventory.csv` - Non-moving inventory status
- `segmentation.csv` - ABC-XYZ classification
- `risk_scores.csv` - Risk scores and recommendations
- `alerts.csv` - Generated alerts
- `summary_report.csv` - Key metrics summary
- `full_analysis.json` - Complete analysis in JSON format
- `inventory_analysis.db` - SQLite database with all results
- `dashboard.html` - Interactive HTML dashboard

## Key Metrics

### Demand Shift Detection
- **CUSUM Signal**: Detects sustained shifts in mean demand
- **MA Crossover**: Short-term vs long-term trend divergence
- **Z-Score Anomalies**: Sudden spikes or drops

### Movement Categories
- **Active**: Regular movement within 60 days
- **Slow-Moving**: 60-90 days since last movement
- **Non-Moving**: 90-180 days since last movement
- **Dead Stock**: 180+ days since last movement

### Risk Levels
- **Critical** (≥80): Immediate action required
- **High** (≥60): Action within 24 hours
- **Medium** (≥40): Action within 1 week
- **Low** (≥20): Monitor and review
- **Minimal** (<20): No immediate concern

## Technology Stack

- **Python 3.11+**
- **pandas/numpy**: Data processing
- **scipy/statsmodels**: Statistical analysis
- **scikit-learn**: ML segmentation
- **FastAPI**: REST API
- **SQLite**: Data persistence
- **Plotly**: Interactive visualizations
- **Pydantic**: Data validation

## License

MIT License

# Hackathon
