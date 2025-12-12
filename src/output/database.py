"""
SQLite database module for persisting analysis results.
"""

import sqlite3
import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import logging

from .alerts import Alert, AlertPriority, AlertCategory

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manage SQLite database for analysis results."""
    
    def __init__(self, db_path: Path | str = "outputs/inventory_analysis.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_database()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _initialize_database(self):
        """Initialize database tables."""
        logger.info(f"Initializing database at {self.db_path}")
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Analysis runs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analysis_runs (
                run_id TEXT PRIMARY KEY,
                run_timestamp TEXT NOT NULL,
                data_start_date TEXT,
                data_end_date TEXT,
                total_skus INTEGER,
                total_locations INTEGER,
                status TEXT,
                metadata TEXT
            )
        ''')
        
        # Demand shifts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS demand_shifts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                item_id TEXT NOT NULL,
                location_id TEXT NOT NULL,
                shift_detected INTEGER,
                shift_type TEXT,
                shift_direction TEXT,
                shift_magnitude REAL,
                confidence_score REAL,
                baseline_demand REAL,
                current_demand REAL,
                category TEXT,
                created_at TEXT,
                FOREIGN KEY (run_id) REFERENCES analysis_runs(run_id)
            )
        ''')
        
        # Non-moving inventory table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS non_moving_inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                item_id TEXT NOT NULL,
                location_id TEXT NOT NULL,
                movement_category TEXT,
                days_since_movement REAL,
                current_inventory REAL,
                non_moving_risk_score REAL,
                recommended_action TEXT,
                shelf_life_at_risk INTEGER,
                category TEXT,
                created_at TEXT,
                FOREIGN KEY (run_id) REFERENCES analysis_runs(run_id)
            )
        ''')
        
        # Segmentation table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS segmentation (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                item_id TEXT NOT NULL,
                location_id TEXT,
                abc_class TEXT,
                xyz_class TEXT,
                segment TEXT,
                total_qty REAL,
                avg_qty REAL,
                cv REAL,
                category TEXT,
                created_at TEXT,
                FOREIGN KEY (run_id) REFERENCES analysis_runs(run_id)
            )
        ''')
        
        # Risk scores table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS risk_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                item_id TEXT NOT NULL,
                location_id TEXT NOT NULL,
                overall_score REAL,
                risk_level TEXT,
                demand_shift_score REAL,
                non_moving_score REAL,
                shelf_life_score REAL,
                lifecycle_score REAL,
                inventory_score REAL,
                primary_risk_factor TEXT,
                on_hand_qty REAL,
                category TEXT,
                created_at TEXT,
                FOREIGN KEY (run_id) REFERENCES analysis_runs(run_id)
            )
        ''')
        
        # Alerts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                alert_id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                item_id TEXT NOT NULL,
                location_id TEXT NOT NULL,
                priority TEXT,
                category TEXT,
                title TEXT,
                description TEXT,
                risk_score REAL,
                created_at TEXT,
                expires_at TEXT,
                acknowledged INTEGER DEFAULT 0,
                resolved INTEGER DEFAULT 0,
                metadata TEXT,
                recommendations TEXT,
                FOREIGN KEY (run_id) REFERENCES analysis_runs(run_id)
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_demand_shifts_item ON demand_shifts(item_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_demand_shifts_run ON demand_shifts(run_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_non_moving_item ON non_moving_inventory(item_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_non_moving_run ON non_moving_inventory(run_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_risk_scores_item ON risk_scores(item_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_risk_scores_run ON risk_scores(run_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_alerts_run ON alerts(run_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_alerts_priority ON alerts(priority)')
        
        conn.commit()
        conn.close()
        
        logger.info("Database initialized successfully")
    
    def create_run(
        self,
        total_skus: int,
        total_locations: int,
        data_start_date: Optional[str] = None,
        data_end_date: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """Create a new analysis run record."""
        run_id = datetime.now().strftime("RUN_%Y%m%d_%H%M%S")
        run_timestamp = datetime.now().isoformat()
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO analysis_runs 
            (run_id, run_timestamp, data_start_date, data_end_date, 
             total_skus, total_locations, status, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            run_id, run_timestamp, data_start_date, data_end_date,
            total_skus, total_locations, 'running',
            json.dumps(metadata) if metadata else None
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Created analysis run: {run_id}")
        return run_id
    
    def complete_run(self, run_id: str, status: str = 'completed'):
        """Mark an analysis run as complete."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE analysis_runs SET status = ? WHERE run_id = ?
        ''', (status, run_id))
        
        conn.commit()
        conn.close()
    
    def save_demand_shifts(self, run_id: str, df: pd.DataFrame):
        """Save demand shift results."""
        if len(df) == 0:
            return
        
        conn = self._get_connection()
        
        df_to_save = df.copy()
        df_to_save['run_id'] = run_id
        df_to_save['created_at'] = datetime.now().isoformat()
        
        columns = [
            'run_id', 'item_id', 'location_id', 'shift_detected',
            'shift_type', 'shift_direction', 'shift_magnitude',
            'confidence_score', 'baseline_demand', 'current_demand',
            'category', 'created_at'
        ]
        
        # Filter to only existing columns
        columns = [c for c in columns if c in df_to_save.columns]
        
        df_to_save[columns].to_sql(
            'demand_shifts', conn, if_exists='append', index=False
        )
        
        conn.close()
        logger.info(f"Saved {len(df)} demand shift records")
    
    def save_non_moving(self, run_id: str, df: pd.DataFrame):
        """Save non-moving inventory results."""
        if len(df) == 0:
            return
        
        conn = self._get_connection()
        
        df_to_save = df.copy()
        df_to_save['run_id'] = run_id
        df_to_save['created_at'] = datetime.now().isoformat()
        
        # Convert movement_category to string
        df_to_save['movement_category'] = df_to_save['movement_category'].astype(str)
        
        columns = [
            'run_id', 'item_id', 'location_id', 'movement_category',
            'days_since_movement', 'current_inventory', 'non_moving_risk_score',
            'recommended_action', 'shelf_life_at_risk', 'category', 'created_at'
        ]
        
        columns = [c for c in columns if c in df_to_save.columns]
        
        df_to_save[columns].to_sql(
            'non_moving_inventory', conn, if_exists='append', index=False
        )
        
        conn.close()
        logger.info(f"Saved {len(df)} non-moving inventory records")
    
    def save_segmentation(self, run_id: str, df: pd.DataFrame):
        """Save segmentation results."""
        if len(df) == 0:
            return
        
        conn = self._get_connection()
        
        df_to_save = df.copy()
        df_to_save['run_id'] = run_id
        df_to_save['created_at'] = datetime.now().isoformat()
        
        # Convert enum values to strings
        if 'abc_class' in df_to_save.columns:
            df_to_save['abc_class'] = df_to_save['abc_class'].apply(
                lambda x: x.value if hasattr(x, 'value') else str(x)
            )
        if 'xyz_class' in df_to_save.columns:
            df_to_save['xyz_class'] = df_to_save['xyz_class'].apply(
                lambda x: x.value if hasattr(x, 'value') else str(x)
            )
        
        columns = [
            'run_id', 'item_id', 'location_id', 'abc_class', 'xyz_class',
            'segment', 'total_qty', 'avg_qty', 'cv', 'category', 'created_at'
        ]
        
        columns = [c for c in columns if c in df_to_save.columns]
        
        df_to_save[columns].to_sql(
            'segmentation', conn, if_exists='append', index=False
        )
        
        conn.close()
        logger.info(f"Saved {len(df)} segmentation records")
    
    def save_risk_scores(self, run_id: str, df: pd.DataFrame):
        """Save risk score results."""
        if len(df) == 0:
            return
        
        conn = self._get_connection()
        
        df_to_save = df.copy()
        df_to_save['run_id'] = run_id
        df_to_save['created_at'] = datetime.now().isoformat()
        
        columns = [
            'run_id', 'item_id', 'location_id', 'overall_score',
            'risk_level', 'demand_shift_score', 'non_moving_score',
            'shelf_life_score', 'lifecycle_score', 'inventory_score',
            'primary_risk_factor', 'on_hand_qty', 'category', 'created_at'
        ]
        
        columns = [c for c in columns if c in df_to_save.columns]
        
        df_to_save[columns].to_sql(
            'risk_scores', conn, if_exists='append', index=False
        )
        
        conn.close()
        logger.info(f"Saved {len(df)} risk score records")
    
    def save_alerts(self, run_id: str, alerts: List[Alert]):
        """Save alert records."""
        if not alerts:
            return
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        for alert in alerts:
            cursor.execute('''
                INSERT OR REPLACE INTO alerts
                (alert_id, run_id, item_id, location_id, priority, category,
                 title, description, risk_score, created_at, expires_at,
                 acknowledged, resolved, metadata, recommendations)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                alert.alert_id, run_id, alert.item_id, alert.location_id,
                alert.priority.value, alert.category.value,
                alert.title, alert.description, alert.risk_score,
                alert.created_at.isoformat(),
                alert.expires_at.isoformat() if alert.expires_at else None,
                int(alert.acknowledged), int(alert.resolved),
                json.dumps(alert.metadata),
                json.dumps(alert.recommendations)
            ))
        
        conn.commit()
        conn.close()
        logger.info(f"Saved {len(alerts)} alerts")
    
    def get_latest_run(self) -> Optional[Dict]:
        """Get the most recent analysis run."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM analysis_runs 
            ORDER BY run_timestamp DESC LIMIT 1
        ''')
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def get_demand_shifts(
        self,
        run_id: Optional[str] = None,
        item_id: Optional[str] = None
    ) -> pd.DataFrame:
        """Get demand shift results."""
        conn = self._get_connection()
        
        query = "SELECT * FROM demand_shifts WHERE 1=1"
        params = []
        
        if run_id:
            query += " AND run_id = ?"
            params.append(run_id)
        if item_id:
            query += " AND item_id = ?"
            params.append(item_id)
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        return df
    
    def get_non_moving(
        self,
        run_id: Optional[str] = None,
        location_id: Optional[str] = None
    ) -> pd.DataFrame:
        """Get non-moving inventory results."""
        conn = self._get_connection()
        
        query = "SELECT * FROM non_moving_inventory WHERE 1=1"
        params = []
        
        if run_id:
            query += " AND run_id = ?"
            params.append(run_id)
        if location_id:
            query += " AND location_id = ?"
            params.append(location_id)
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        return df
    
    def get_alerts(
        self,
        run_id: Optional[str] = None,
        priority: Optional[str] = None,
        resolved: Optional[bool] = None
    ) -> pd.DataFrame:
        """Get alerts."""
        conn = self._get_connection()
        
        query = "SELECT * FROM alerts WHERE 1=1"
        params = []
        
        if run_id:
            query += " AND run_id = ?"
            params.append(run_id)
        if priority:
            query += " AND priority = ?"
            params.append(priority)
        if resolved is not None:
            query += " AND resolved = ?"
            params.append(int(resolved))
        
        query += " ORDER BY priority, risk_score DESC"
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        return df
    
    def get_risk_scores(
        self,
        run_id: Optional[str] = None,
        min_score: float = 0.0
    ) -> pd.DataFrame:
        """Get risk scores."""
        conn = self._get_connection()
        
        query = "SELECT * FROM risk_scores WHERE overall_score >= ?"
        params = [min_score]
        
        if run_id:
            query += " AND run_id = ?"
            params.append(run_id)
        
        query += " ORDER BY overall_score DESC"
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        return df

