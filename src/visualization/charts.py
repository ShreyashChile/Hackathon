"""
Chart generation module using Plotly.
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, List
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import logging

logger = logging.getLogger(__name__)


class ChartGenerator:
    """Generate interactive charts for analysis results."""
    
    def __init__(self, template: str = "plotly_white"):
        self.template = template
        self.color_palette = px.colors.qualitative.Set2
    
    def demand_shift_distribution(
        self,
        demand_shifts: pd.DataFrame,
        title: str = "Demand Shift Distribution"
    ) -> go.Figure:
        """Create a pie chart of demand shift distribution."""
        shifts = demand_shifts[demand_shifts['shift_detected'] == True]
        
        direction_counts = shifts['shift_direction'].value_counts()
        
        fig = go.Figure(data=[go.Pie(
            labels=direction_counts.index,
            values=direction_counts.values,
            hole=0.4,
            marker_colors=['#2ecc71', '#e74c3c', '#95a5a6']
        )])
        
        fig.update_layout(
            title=title,
            template=self.template,
            annotations=[dict(text=f'{len(shifts)}<br>Shifts', x=0.5, y=0.5, 
                             font_size=16, showarrow=False)]
        )
        
        return fig
    
    def demand_shift_by_category(
        self,
        demand_shifts: pd.DataFrame,
        title: str = "Demand Shifts by Product Category"
    ) -> go.Figure:
        """Create a grouped bar chart of shifts by category."""
        shifts = demand_shifts[demand_shifts['shift_detected'] == True]
        
        summary = shifts.groupby(['category', 'shift_direction']).size().unstack(fill_value=0)
        
        fig = go.Figure()
        
        colors = {'increase': '#2ecc71', 'decrease': '#e74c3c', 'stable': '#95a5a6'}
        
        for direction in summary.columns:
            fig.add_trace(go.Bar(
                name=direction.title(),
                x=summary.index,
                y=summary[direction],
                marker_color=colors.get(direction, '#3498db')
            ))
        
        fig.update_layout(
            title=title,
            barmode='group',
            xaxis_title="Category",
            yaxis_title="Count",
            template=self.template,
            legend_title="Shift Direction"
        )
        
        return fig
    
    def shift_magnitude_histogram(
        self,
        demand_shifts: pd.DataFrame,
        title: str = "Demand Shift Magnitude Distribution"
    ) -> go.Figure:
        """Create histogram of shift magnitudes."""
        shifts = demand_shifts[demand_shifts['shift_detected'] == True]
        
        fig = px.histogram(
            shifts,
            x='shift_magnitude',
            nbins=30,
            title=title,
            labels={'shift_magnitude': 'Shift Magnitude (%)'},
            color='shift_direction',
            color_discrete_map={
                'increase': '#2ecc71',
                'decrease': '#e74c3c',
                'stable': '#95a5a6'
            }
        )
        
        fig.update_layout(template=self.template)
        
        return fig
    
    def non_moving_by_location(
        self,
        non_moving: pd.DataFrame,
        title: str = "Non-Moving Inventory by Location"
    ) -> go.Figure:
        """Create stacked bar chart of movement categories by location."""
        summary = non_moving.groupby(
            ['location_id', 'movement_category']
        ).size().unstack(fill_value=0)
        
        # Convert movement_category to string if needed
        summary.columns = [str(c) for c in summary.columns]
        
        fig = go.Figure()
        
        colors = {
            'active': '#2ecc71',
            'slow_moving': '#f39c12',
            'non_moving': '#e67e22',
            'dead_stock': '#e74c3c'
        }
        
        for category in ['active', 'slow_moving', 'non_moving', 'dead_stock']:
            if category in summary.columns:
                fig.add_trace(go.Bar(
                    name=category.replace('_', ' ').title(),
                    x=summary.index,
                    y=summary[category],
                    marker_color=colors.get(category, '#3498db')
                ))
        
        fig.update_layout(
            title=title,
            barmode='stack',
            xaxis_title="Location",
            yaxis_title="SKU Count",
            template=self.template,
            legend_title="Movement Category"
        )
        
        return fig
    
    def non_moving_risk_scatter(
        self,
        non_moving: pd.DataFrame,
        title: str = "Non-Moving Risk vs Days Since Movement"
    ) -> go.Figure:
        """Create scatter plot of risk score vs days since movement."""
        df = non_moving[non_moving['days_since_movement'] < 500].copy()  # Filter outliers
        
        fig = px.scatter(
            df,
            x='days_since_movement',
            y='non_moving_risk_score',
            color='movement_category',
            size='current_inventory',
            hover_data=['item_id', 'location_id'],
            title=title,
            labels={
                'days_since_movement': 'Days Since Last Movement',
                'non_moving_risk_score': 'Risk Score',
                'current_inventory': 'Inventory'
            },
            color_discrete_map={
                'active': '#2ecc71',
                'slow_moving': '#f39c12',
                'non_moving': '#e67e22',
                'dead_stock': '#e74c3c'
            }
        )
        
        fig.update_layout(template=self.template)
        
        return fig
    
    def abc_xyz_heatmap(
        self,
        segmentation: pd.DataFrame,
        title: str = "ABC-XYZ Segmentation Matrix"
    ) -> go.Figure:
        """Create heatmap of ABC-XYZ segmentation."""
        # Convert enum values to strings
        seg = segmentation.copy()
        for col in ['abc_class', 'xyz_class']:
            if col in seg.columns:
                seg[col] = seg[col].apply(
                    lambda x: x.value if hasattr(x, 'value') else str(x)
                )
        
        matrix = pd.crosstab(seg['abc_class'], seg['xyz_class'])
        
        # Ensure proper ordering
        abc_order = ['A', 'B', 'C']
        xyz_order = ['X', 'Y', 'Z']
        
        for abc in abc_order:
            if abc not in matrix.index:
                matrix.loc[abc] = 0
        for xyz in xyz_order:
            if xyz not in matrix.columns:
                matrix[xyz] = 0
        
        matrix = matrix.loc[abc_order, xyz_order]
        
        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=matrix.values,
            x=xyz_order,
            y=abc_order,
            colorscale='RdYlGn_r',
            text=matrix.values,
            texttemplate="%{text}",
            textfont={"size": 20}
        ))
        
        fig.update_layout(
            title=title,
            xaxis_title="Demand Variability (XYZ)",
            yaxis_title="Volume (ABC)",
            template=self.template
        )
        
        return fig
    
    def segment_sunburst(
        self,
        segmentation: pd.DataFrame,
        title: str = "SKU Segmentation Sunburst"
    ) -> go.Figure:
        """Create sunburst chart of segmentation."""
        seg = segmentation.copy()
        for col in ['abc_class', 'xyz_class']:
            if col in seg.columns:
                seg[col] = seg[col].apply(
                    lambda x: x.value if hasattr(x, 'value') else str(x)
                )
        
        fig = px.sunburst(
            seg,
            path=['abc_class', 'xyz_class'],
            title=title,
            color='abc_class',
            color_discrete_map={'A': '#27ae60', 'B': '#f39c12', 'C': '#e74c3c'}
        )
        
        fig.update_layout(template=self.template)
        
        return fig
    
    def risk_score_distribution(
        self,
        risk_scores: pd.DataFrame,
        title: str = "Risk Score Distribution"
    ) -> go.Figure:
        """Create histogram of risk scores."""
        fig = px.histogram(
            risk_scores,
            x='overall_score',
            nbins=20,
            title=title,
            labels={'overall_score': 'Risk Score'},
            color='risk_level',
            color_discrete_map={
                'critical': '#e74c3c',
                'high': '#e67e22',
                'medium': '#f39c12',
                'low': '#27ae60',
                'minimal': '#2ecc71'
            }
        )
        
        fig.update_layout(template=self.template)
        
        return fig
    
    def risk_factors_radar(
        self,
        risk_scores: pd.DataFrame,
        item_id: str,
        location_id: str,
        title: Optional[str] = None
    ) -> go.Figure:
        """Create radar chart of risk factors for a specific item."""
        item = risk_scores[
            (risk_scores['item_id'] == item_id) & 
            (risk_scores['location_id'] == location_id)
        ]
        
        if len(item) == 0:
            return go.Figure()
        
        item = item.iloc[0]
        
        categories = [
            'Demand Shift',
            'Non-Moving',
            'Shelf Life',
            'Lifecycle',
            'Inventory'
        ]
        
        values = [
            item['demand_shift_score'],
            item['non_moving_score'],
            item['shelf_life_score'],
            item['lifecycle_score'],
            item['inventory_score']
        ]
        
        fig = go.Figure(data=go.Scatterpolar(
            r=values + [values[0]],  # Close the polygon
            theta=categories + [categories[0]],
            fill='toself',
            name=f'{item_id} @ {location_id}'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 100])
            ),
            title=title or f'Risk Profile: {item_id} @ {location_id}',
            template=self.template
        )
        
        return fig
    
    def alerts_by_priority(
        self,
        alerts_df: pd.DataFrame,
        title: str = "Alerts by Priority"
    ) -> go.Figure:
        """Create bar chart of alerts by priority."""
        priority_counts = alerts_df['priority'].value_counts()
        
        # Define order and colors
        priority_order = ['P1_CRITICAL', 'P2_HIGH', 'P3_MEDIUM', 'P4_LOW', 'P5_INFO']
        colors = ['#e74c3c', '#e67e22', '#f39c12', '#27ae60', '#3498db']
        
        # Reorder
        priority_counts = priority_counts.reindex(priority_order).fillna(0)
        
        fig = go.Figure(data=go.Bar(
            x=priority_counts.index,
            y=priority_counts.values,
            marker_color=colors
        ))
        
        fig.update_layout(
            title=title,
            xaxis_title="Priority",
            yaxis_title="Count",
            template=self.template
        )
        
        return fig
    
    def time_series_demand(
        self,
        sales_data: pd.DataFrame,
        item_id: str,
        location_id: str,
        title: Optional[str] = None
    ) -> go.Figure:
        """Create time series chart of demand for an item."""
        mask = (sales_data['item_id'] == item_id) & (sales_data['location_id'] == location_id)
        data = sales_data[mask].sort_values('week_ending')
        
        if len(data) == 0:
            return go.Figure()
        
        fig = make_subplots(rows=2, cols=1, 
                           shared_xaxes=True,
                           vertical_spacing=0.1,
                           subplot_titles=('Weekly Sales', 'Moving Averages'))
        
        # Weekly sales
        fig.add_trace(
            go.Scatter(x=data['week_ending'], y=data['qty_sold'],
                      mode='lines', name='Weekly Sales',
                      line=dict(color='#3498db')),
            row=1, col=1
        )
        
        # Moving averages
        ma_4w = data['qty_sold'].rolling(4).mean()
        ma_12w = data['qty_sold'].rolling(12).mean()
        
        fig.add_trace(
            go.Scatter(x=data['week_ending'], y=ma_4w,
                      mode='lines', name='4-Week MA',
                      line=dict(color='#2ecc71')),
            row=2, col=1
        )
        
        fig.add_trace(
            go.Scatter(x=data['week_ending'], y=ma_12w,
                      mode='lines', name='12-Week MA',
                      line=dict(color='#e74c3c')),
            row=2, col=1
        )
        
        fig.update_layout(
            title=title or f'Demand Analysis: {item_id} @ {location_id}',
            template=self.template,
            height=500
        )
        
        return fig
    
    def save_chart(
        self,
        fig: go.Figure,
        filepath: str,
        format: str = "html"
    ):
        """Save chart to file."""
        if format == "html":
            fig.write_html(filepath)
        elif format == "png":
            fig.write_image(filepath)
        elif format == "json":
            fig.write_json(filepath)
        
        logger.info(f"Chart saved to {filepath}")

