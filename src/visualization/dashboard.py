"""
Dashboard generation module.

Creates an HTML dashboard with all analysis visualizations.
"""

import pandas as pd
from pathlib import Path
from typing import List, Optional
from datetime import datetime
import logging

from .charts import ChartGenerator
from ..output.alerts import Alert

logger = logging.getLogger(__name__)


class DashboardGenerator:
    """Generate HTML dashboard for analysis results."""
    
    def __init__(self, output_dir: Path | str = "outputs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.chart_gen = ChartGenerator()
    
    def generate_dashboard(
        self,
        demand_shifts: pd.DataFrame,
        non_moving: pd.DataFrame,
        segmentation: pd.DataFrame,
        risk_scores: pd.DataFrame,
        alerts: List[Alert],
        run_id: str = "",
        filename: str = "dashboard.html"
    ) -> Path:
        """Generate complete HTML dashboard."""
        logger.info("Generating dashboard...")
        
        # Generate all charts
        charts = {}
        
        # Demand shift charts
        charts['shift_dist'] = self.chart_gen.demand_shift_distribution(demand_shifts)
        charts['shift_category'] = self.chart_gen.demand_shift_by_category(demand_shifts)
        charts['shift_magnitude'] = self.chart_gen.shift_magnitude_histogram(demand_shifts)
        
        # Non-moving charts
        charts['nm_location'] = self.chart_gen.non_moving_by_location(non_moving)
        charts['nm_scatter'] = self.chart_gen.non_moving_risk_scatter(non_moving)
        
        # Segmentation charts
        charts['abc_xyz_heatmap'] = self.chart_gen.abc_xyz_heatmap(segmentation)
        charts['segment_sunburst'] = self.chart_gen.segment_sunburst(segmentation)
        
        # Risk score charts
        charts['risk_dist'] = self.chart_gen.risk_score_distribution(risk_scores)
        
        # Alerts chart
        if alerts:
            from ..output.alerts import AlertGenerator
            alert_gen = AlertGenerator()
            alerts_df = alert_gen.alerts_to_dataframe(alerts)
            charts['alerts_priority'] = self.chart_gen.alerts_by_priority(alerts_df)
        
        # Calculate summary stats
        summary = self._calculate_summary(
            demand_shifts, non_moving, segmentation, risk_scores, alerts
        )
        
        # Generate HTML
        html_content = self._generate_html(charts, summary, run_id)
        
        # Save to file
        filepath = self.output_dir / filename
        with open(filepath, 'w') as f:
            f.write(html_content)
        
        logger.info(f"Dashboard saved to {filepath}")
        return filepath
    
    def _calculate_summary(
        self,
        demand_shifts: pd.DataFrame,
        non_moving: pd.DataFrame,
        segmentation: pd.DataFrame,
        risk_scores: pd.DataFrame,
        alerts: List[Alert]
    ) -> dict:
        """Calculate summary statistics for dashboard."""
        return {
            'total_sku_locations': len(demand_shifts),
            'unique_skus': demand_shifts['item_id'].nunique(),
            'unique_locations': demand_shifts['location_id'].nunique(),
            'shifts_detected': int(demand_shifts['shift_detected'].sum()),
            'shift_increases': int((demand_shifts['shift_detected'] & 
                                   (demand_shifts['shift_direction'] == 'increase')).sum()),
            'shift_decreases': int((demand_shifts['shift_detected'] & 
                                   (demand_shifts['shift_direction'] == 'decrease')).sum()),
            'dead_stock_count': int((non_moving['movement_category'].astype(str) == 'dead_stock').sum()),
            'non_moving_count': int((non_moving['movement_category'].astype(str) == 'non_moving').sum()),
            'slow_moving_count': int((non_moving['movement_category'].astype(str) == 'slow_moving').sum()),
            'active_count': int((non_moving['movement_category'].astype(str) == 'active').sum()),
            'critical_risk': int((risk_scores['risk_level'] == 'critical').sum()),
            'high_risk': int((risk_scores['risk_level'] == 'high').sum()),
            'medium_risk': int((risk_scores['risk_level'] == 'medium').sum()),
            'low_risk': int((risk_scores['risk_level'] == 'low').sum()),
            'total_alerts': len(alerts),
            'critical_alerts': len([a for a in alerts if a.priority.value == 'P1_CRITICAL']),
            'high_alerts': len([a for a in alerts if a.priority.value == 'P2_HIGH']),
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def _generate_html(
        self,
        charts: dict,
        summary: dict,
        run_id: str
    ) -> str:
        """Generate HTML content for dashboard."""
        
        # Convert charts to HTML divs
        chart_divs = {}
        for name, fig in charts.items():
            chart_divs[name] = fig.to_html(full_html=False, include_plotlyjs=False)
        
        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ML Inventory Agent - Analysis Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        :root {{
            --bg-primary: #0f172a;
            --bg-secondary: #1e293b;
            --bg-card: #334155;
            --text-primary: #f1f5f9;
            --text-secondary: #94a3b8;
            --accent-blue: #3b82f6;
            --accent-green: #22c55e;
            --accent-yellow: #eab308;
            --accent-red: #ef4444;
            --accent-orange: #f97316;
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 1600px;
            margin: 0 auto;
            padding: 2rem;
        }}
        
        header {{
            background: linear-gradient(135deg, var(--bg-secondary), var(--bg-card));
            padding: 2rem;
            border-radius: 12px;
            margin-bottom: 2rem;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        
        h1 {{
            font-size: 2.5rem;
            font-weight: 700;
            background: linear-gradient(90deg, var(--accent-blue), var(--accent-green));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
        }}
        
        .subtitle {{
            color: var(--text-secondary);
            font-size: 1rem;
        }}
        
        .run-info {{
            display: flex;
            gap: 2rem;
            margin-top: 1rem;
            color: var(--text-secondary);
            font-size: 0.875rem;
        }}
        
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }}
        
        .kpi-card {{
            background: var(--bg-secondary);
            border-radius: 12px;
            padding: 1.5rem;
            border: 1px solid rgba(255,255,255,0.1);
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        
        .kpi-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.3);
        }}
        
        .kpi-value {{
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 0.25rem;
        }}
        
        .kpi-label {{
            color: var(--text-secondary);
            font-size: 0.875rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        
        .kpi-critical {{ color: var(--accent-red); }}
        .kpi-high {{ color: var(--accent-orange); }}
        .kpi-medium {{ color: var(--accent-yellow); }}
        .kpi-success {{ color: var(--accent-green); }}
        .kpi-info {{ color: var(--accent-blue); }}
        
        .section {{
            margin-bottom: 2rem;
        }}
        
        .section-title {{
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid var(--accent-blue);
            display: inline-block;
        }}
        
        .chart-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 1.5rem;
        }}
        
        .chart-card {{
            background: var(--bg-secondary);
            border-radius: 12px;
            padding: 1.5rem;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        
        .chart-title {{
            font-size: 1.125rem;
            font-weight: 600;
            margin-bottom: 1rem;
            color: var(--text-primary);
        }}
        
        .alert-section {{
            background: var(--bg-secondary);
            border-radius: 12px;
            padding: 1.5rem;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        
        .alert-list {{
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
            max-height: 400px;
            overflow-y: auto;
        }}
        
        .alert-item {{
            display: flex;
            align-items: flex-start;
            gap: 1rem;
            padding: 1rem;
            background: var(--bg-card);
            border-radius: 8px;
            border-left: 4px solid;
        }}
        
        .alert-p1 {{ border-color: var(--accent-red); }}
        .alert-p2 {{ border-color: var(--accent-orange); }}
        .alert-p3 {{ border-color: var(--accent-yellow); }}
        .alert-p4 {{ border-color: var(--accent-green); }}
        
        .alert-priority {{
            font-size: 0.75rem;
            font-weight: 600;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            text-transform: uppercase;
        }}
        
        .priority-p1 {{ background: var(--accent-red); color: white; }}
        .priority-p2 {{ background: var(--accent-orange); color: white; }}
        .priority-p3 {{ background: var(--accent-yellow); color: black; }}
        .priority-p4 {{ background: var(--accent-green); color: white; }}
        
        .alert-content {{
            flex: 1;
        }}
        
        .alert-title {{
            font-weight: 600;
            margin-bottom: 0.25rem;
        }}
        
        .alert-description {{
            color: var(--text-secondary);
            font-size: 0.875rem;
        }}
        
        footer {{
            text-align: center;
            padding: 2rem;
            color: var(--text-secondary);
            font-size: 0.875rem;
        }}
        
        @media (max-width: 768px) {{
            .container {{
                padding: 1rem;
            }}
            
            .chart-grid {{
                grid-template-columns: 1fr;
            }}
            
            .kpi-grid {{
                grid-template-columns: repeat(2, 1fr);
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>ML Inventory Agent Dashboard</h1>
            <p class="subtitle">Demand Shift Detection & Non-Moving Inventory Analysis</p>
            <div class="run-info">
                <span>Run ID: {run_id or 'N/A'}</span>
                <span>Generated: {summary['generated_at']}</span>
                <span>SKUs: {summary['unique_skus']} | Locations: {summary['unique_locations']}</span>
            </div>
        </header>
        
        <!-- KPI Cards -->
        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-value kpi-info">{summary['total_sku_locations']}</div>
                <div class="kpi-label">Total SKU-Locations</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-value kpi-high">{summary['shifts_detected']}</div>
                <div class="kpi-label">Demand Shifts Detected</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-value kpi-critical">{summary['dead_stock_count']}</div>
                <div class="kpi-label">Dead Stock Items</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-value kpi-medium">{summary['non_moving_count']}</div>
                <div class="kpi-label">Non-Moving Items</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-value kpi-critical">{summary['critical_risk']}</div>
                <div class="kpi-label">Critical Risk Items</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-value kpi-high">{summary['high_risk']}</div>
                <div class="kpi-label">High Risk Items</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-value kpi-critical">{summary['critical_alerts']}</div>
                <div class="kpi-label">Critical Alerts</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-value kpi-success">{summary['active_count']}</div>
                <div class="kpi-label">Active Items</div>
            </div>
        </div>
        
        <!-- Demand Shifts Section -->
        <div class="section">
            <h2 class="section-title">Demand Shift Analysis</h2>
            <div class="chart-grid">
                <div class="chart-card">
                    <h3 class="chart-title">Shift Distribution</h3>
                    {chart_divs.get('shift_dist', '<p>No data available</p>')}
                </div>
                <div class="chart-card">
                    <h3 class="chart-title">Shifts by Category</h3>
                    {chart_divs.get('shift_category', '<p>No data available</p>')}
                </div>
                <div class="chart-card">
                    <h3 class="chart-title">Shift Magnitude Distribution</h3>
                    {chart_divs.get('shift_magnitude', '<p>No data available</p>')}
                </div>
            </div>
        </div>
        
        <!-- Non-Moving Inventory Section -->
        <div class="section">
            <h2 class="section-title">Non-Moving Inventory</h2>
            <div class="chart-grid">
                <div class="chart-card">
                    <h3 class="chart-title">Movement Status by Location</h3>
                    {chart_divs.get('nm_location', '<p>No data available</p>')}
                </div>
                <div class="chart-card">
                    <h3 class="chart-title">Risk vs Days Since Movement</h3>
                    {chart_divs.get('nm_scatter', '<p>No data available</p>')}
                </div>
            </div>
        </div>
        
        <!-- Segmentation Section -->
        <div class="section">
            <h2 class="section-title">ABC-XYZ Segmentation</h2>
            <div class="chart-grid">
                <div class="chart-card">
                    <h3 class="chart-title">Segmentation Matrix</h3>
                    {chart_divs.get('abc_xyz_heatmap', '<p>No data available</p>')}
                </div>
                <div class="chart-card">
                    <h3 class="chart-title">Segment Distribution</h3>
                    {chart_divs.get('segment_sunburst', '<p>No data available</p>')}
                </div>
            </div>
        </div>
        
        <!-- Risk Scores Section -->
        <div class="section">
            <h2 class="section-title">Risk Analysis</h2>
            <div class="chart-grid">
                <div class="chart-card">
                    <h3 class="chart-title">Risk Score Distribution</h3>
                    {chart_divs.get('risk_dist', '<p>No data available</p>')}
                </div>
                <div class="chart-card">
                    <h3 class="chart-title">Alerts by Priority</h3>
                    {chart_divs.get('alerts_priority', '<p>No data available</p>')}
                </div>
            </div>
        </div>
        
        <footer>
            <p>ML Inventory Agent v1.0.0 | Generated on {summary['generated_at']}</p>
        </footer>
    </div>
</body>
</html>'''
        
        return html

