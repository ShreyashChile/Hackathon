"""
PostgreSQL database module for persisting analysis results.
"""

import os
import pandas as pd
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import logging

import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_values, RealDictCursor
from dotenv import load_dotenv

from .alerts import Alert, AlertPriority, AlertCategory
from ..config import get_config, DatabaseConfig

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class DatabaseManager:
    """Manage PostgreSQL database for analysis results."""
    
    def __init__(self, db_config: Optional[DatabaseConfig] = None):
        """
        Initialize database manager.
        
        Args:
            db_config: Database configuration. If None, loads from environment.
        """
        if db_config is None:
            db_config = DatabaseConfig.from_env()
        
        self.db_config = db_config
        self.schema_name = db_config.schema_name
        self._initialize_database()
    
    def _get_connection(self):
        """Get database connection."""
        return psycopg2.connect(
            host=self.db_config.host,
            database=self.db_config.database,
            user=self.db_config.user,
            password=self.db_config.password,
            port=self.db_config.port
        )
    
    def _initialize_database(self):
        """Initialize database tables for analysis results."""
        logger.info(f"Initializing database at {self.db_config.host}/{self.db_config.database}")
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Create schema if not exists
            cursor.execute(sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(
                sql.Identifier(self.schema_name)
            ))
            
            # Analysis runs table
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS {self.schema_name}.analysis_runs (
                    run_id VARCHAR(50) PRIMARY KEY,
                    run_timestamp TIMESTAMP NOT NULL,
                    data_start_date DATE,
                    data_end_date DATE,
                    total_skus INTEGER,
                    total_locations INTEGER,
                    status VARCHAR(20),
                    metadata JSONB
                )
            ''')
            
            # Demand shifts table
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS {self.schema_name}.demand_shifts (
                    id SERIAL PRIMARY KEY,
                    run_id VARCHAR(50) NOT NULL,
                    item_id VARCHAR(20) NOT NULL,
                    location_id VARCHAR(20) NOT NULL,
                    shift_detected BOOLEAN,
                    shift_type VARCHAR(50),
                    shift_direction VARCHAR(20),
                    shift_magnitude NUMERIC(10, 2),
                    confidence_score NUMERIC(10, 2),
                    baseline_demand NUMERIC(10, 2),
                    current_demand NUMERIC(10, 2),
                    category VARCHAR(50),
                    created_at TIMESTAMP,
                    FOREIGN KEY (run_id) REFERENCES {self.schema_name}.analysis_runs(run_id) ON DELETE CASCADE
                )
            ''')
            
            # Non-moving inventory table (updated with new columns)
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS {self.schema_name}.non_moving_inventory (
                    id SERIAL PRIMARY KEY,
                    run_id VARCHAR(50) NOT NULL,
                    item_id VARCHAR(20) NOT NULL,
                    location_id VARCHAR(20) NOT NULL,
                    movement_status VARCHAR(20),
                    movement_category VARCHAR(20),
                    days_since_movement NUMERIC(10, 2),
                    weeks_since_movement INTEGER,
                    current_inventory NUMERIC(10, 2),
                    non_moving_risk_score NUMERIC(10, 2),
                    has_open_po BOOLEAN,
                    open_po_qty INTEGER,
                    recommended_action TEXT,
                    recommended_actions JSONB,
                    shelf_life_at_risk BOOLEAN,
                    category VARCHAR(50),
                    threshold_weeks_used INTEGER,
                    created_at TIMESTAMP,
                    FOREIGN KEY (run_id) REFERENCES {self.schema_name}.analysis_runs(run_id) ON DELETE CASCADE
                )
            ''')
            
            # Segmentation table
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS {self.schema_name}.segmentation (
                    id SERIAL PRIMARY KEY,
                    run_id VARCHAR(50) NOT NULL,
                    item_id VARCHAR(20) NOT NULL,
                    location_id VARCHAR(20),
                    abc_class VARCHAR(1),
                    xyz_class VARCHAR(1),
                    segment VARCHAR(2),
                    total_qty NUMERIC(12, 2),
                    avg_qty NUMERIC(10, 2),
                    cv NUMERIC(10, 4),
                    category VARCHAR(50),
                    created_at TIMESTAMP,
                    FOREIGN KEY (run_id) REFERENCES {self.schema_name}.analysis_runs(run_id) ON DELETE CASCADE
                )
            ''')
            
            # Risk scores table
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS {self.schema_name}.risk_scores (
                    id SERIAL PRIMARY KEY,
                    run_id VARCHAR(50) NOT NULL,
                    item_id VARCHAR(20) NOT NULL,
                    location_id VARCHAR(20) NOT NULL,
                    overall_score NUMERIC(10, 2),
                    risk_level VARCHAR(20),
                    demand_shift_score NUMERIC(10, 2),
                    non_moving_score NUMERIC(10, 2),
                    shelf_life_score NUMERIC(10, 2),
                    lifecycle_score NUMERIC(10, 2),
                    inventory_score NUMERIC(10, 2),
                    primary_risk_factor VARCHAR(50),
                    on_hand_qty NUMERIC(12, 2),
                    category VARCHAR(50),
                    created_at TIMESTAMP,
                    FOREIGN KEY (run_id) REFERENCES {self.schema_name}.analysis_runs(run_id) ON DELETE CASCADE
                )
            ''')
            
            # Alerts table
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS {self.schema_name}.alerts (
                    alert_id VARCHAR(100) PRIMARY KEY,
                    run_id VARCHAR(50) NOT NULL,
                    item_id VARCHAR(20) NOT NULL,
                    location_id VARCHAR(20) NOT NULL,
                    priority VARCHAR(20),
                    category VARCHAR(50),
                    title VARCHAR(255),
                    description TEXT,
                    risk_score NUMERIC(10, 2),
                    created_at TIMESTAMP,
                    expires_at TIMESTAMP,
                    acknowledged BOOLEAN DEFAULT FALSE,
                    resolved BOOLEAN DEFAULT FALSE,
                    metadata JSONB,
                    recommendations JSONB,
                    FOREIGN KEY (run_id) REFERENCES {self.schema_name}.analysis_runs(run_id) ON DELETE CASCADE
                )
            ''')
            
            # Create indexes
            cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_demand_shifts_item ON {self.schema_name}.demand_shifts(item_id)')
            cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_demand_shifts_run ON {self.schema_name}.demand_shifts(run_id)')
            cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_non_moving_item ON {self.schema_name}.non_moving_inventory(item_id)')
            cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_non_moving_run ON {self.schema_name}.non_moving_inventory(run_id)')
            cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_non_moving_status ON {self.schema_name}.non_moving_inventory(movement_status)')
            cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_risk_scores_item ON {self.schema_name}.risk_scores(item_id)')
            cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_risk_scores_run ON {self.schema_name}.risk_scores(run_id)')
            cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_alerts_run ON {self.schema_name}.alerts(run_id)')
            cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_alerts_priority ON {self.schema_name}.alerts(priority)')
            
            conn.commit()
            logger.info("Database initialized successfully")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error initializing database: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
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
        run_timestamp = datetime.now()
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(f'''
                INSERT INTO {self.schema_name}.analysis_runs 
                (run_id, run_timestamp, data_start_date, data_end_date, 
                 total_skus, total_locations, status, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                run_id, run_timestamp, data_start_date, data_end_date,
                total_skus, total_locations, 'running',
                json.dumps(metadata) if metadata else None
            ))
            
            conn.commit()
            logger.info(f"Created analysis run: {run_id}")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error creating run: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
        
        return run_id
    
    def complete_run(self, run_id: str, status: str = 'completed'):
        """Mark an analysis run as complete."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(f'''
                UPDATE {self.schema_name}.analysis_runs SET status = %s WHERE run_id = %s
            ''', (status, run_id))
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Error completing run: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def save_demand_shifts(self, run_id: str, df: pd.DataFrame):
        """Save demand shift results."""
        if len(df) == 0:
            return
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            df_to_save = df.copy()
            df_to_save['run_id'] = run_id
            df_to_save['created_at'] = datetime.now()
            
            columns = [
                'run_id', 'item_id', 'location_id', 'shift_detected',
                'shift_type', 'shift_direction', 'shift_magnitude',
                'confidence_score', 'baseline_demand', 'current_demand',
                'category', 'created_at'
            ]
            
            # Filter to only existing columns
            columns = [c for c in columns if c in df_to_save.columns]
            
            # Prepare data for insertion
            data = df_to_save[columns].values.tolist()
            
            # Build insert query
            insert_query = f'''
                INSERT INTO {self.schema_name}.demand_shifts 
                ({', '.join(columns)})
                VALUES %s
            '''
            
            execute_values(cursor, insert_query, data)
            conn.commit()
            
            logger.info(f"Saved {len(df)} demand shift records")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error saving demand shifts: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def save_non_moving(self, run_id: str, df: pd.DataFrame):
        """Save non-moving inventory results."""
        if len(df) == 0:
            return
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            df_to_save = df.copy()
            df_to_save['run_id'] = run_id
            df_to_save['created_at'] = datetime.now()
            
            # Convert movement_category to string
            if 'movement_category' in df_to_save.columns:
                df_to_save['movement_category'] = df_to_save['movement_category'].astype(str)
            
            # Convert recommended_actions list to JSON
            if 'recommended_actions' in df_to_save.columns:
                df_to_save['recommended_actions'] = df_to_save['recommended_actions'].apply(
                    lambda x: json.dumps(x) if isinstance(x, list) else x
                )
            
            columns = [
                'run_id', 'item_id', 'location_id', 'movement_status', 'movement_category',
                'days_since_movement', 'weeks_since_movement', 'current_inventory', 
                'non_moving_risk_score', 'has_open_po', 'open_po_qty',
                'recommended_action', 'recommended_actions', 'shelf_life_at_risk', 
                'category', 'threshold_weeks_used', 'created_at'
            ]
            
            columns = [c for c in columns if c in df_to_save.columns]
            
            # Prepare data for insertion
            data = df_to_save[columns].values.tolist()
            
            insert_query = f'''
                INSERT INTO {self.schema_name}.non_moving_inventory 
                ({', '.join(columns)})
                VALUES %s
            '''
            
            execute_values(cursor, insert_query, data)
            conn.commit()
            
            logger.info(f"Saved {len(df)} non-moving inventory records")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error saving non-moving inventory: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def save_segmentation(self, run_id: str, df: pd.DataFrame):
        """Save segmentation results."""
        if len(df) == 0:
            return
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            df_to_save = df.copy()
            df_to_save['run_id'] = run_id
            df_to_save['created_at'] = datetime.now()
            
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
            
            data = df_to_save[columns].values.tolist()
            
            insert_query = f'''
                INSERT INTO {self.schema_name}.segmentation 
                ({', '.join(columns)})
                VALUES %s
            '''
            
            execute_values(cursor, insert_query, data)
            conn.commit()
            
            logger.info(f"Saved {len(df)} segmentation records")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error saving segmentation: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def save_risk_scores(self, run_id: str, df: pd.DataFrame):
        """Save risk score results."""
        if len(df) == 0:
            return
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            df_to_save = df.copy()
            df_to_save['run_id'] = run_id
            df_to_save['created_at'] = datetime.now()
            
            columns = [
                'run_id', 'item_id', 'location_id', 'overall_score',
                'risk_level', 'demand_shift_score', 'non_moving_score',
                'shelf_life_score', 'lifecycle_score', 'inventory_score',
                'primary_risk_factor', 'on_hand_qty', 'category', 'created_at'
            ]
            
            columns = [c for c in columns if c in df_to_save.columns]
            
            data = df_to_save[columns].values.tolist()
            
            insert_query = f'''
                INSERT INTO {self.schema_name}.risk_scores 
                ({', '.join(columns)})
                VALUES %s
            '''
            
            execute_values(cursor, insert_query, data)
            conn.commit()
            
            logger.info(f"Saved {len(df)} risk score records")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error saving risk scores: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def save_alerts(self, run_id: str, alerts: List[Alert]):
        """Save alert records."""
        if not alerts:
            return
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            for alert in alerts:
                cursor.execute(f'''
                    INSERT INTO {self.schema_name}.alerts
                    (alert_id, run_id, item_id, location_id, priority, category,
                     title, description, risk_score, created_at, expires_at,
                     acknowledged, resolved, metadata, recommendations)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (alert_id) DO UPDATE SET
                        priority = EXCLUDED.priority,
                        description = EXCLUDED.description,
                        risk_score = EXCLUDED.risk_score,
                        metadata = EXCLUDED.metadata,
                        recommendations = EXCLUDED.recommendations
                ''', (
                    alert.alert_id, run_id, alert.item_id, alert.location_id,
                    alert.priority.value, alert.category.value,
                    alert.title, alert.description, alert.risk_score,
                    alert.created_at,
                    alert.expires_at if alert.expires_at else None,
                    alert.acknowledged, alert.resolved,
                    json.dumps(alert.metadata),
                    json.dumps(alert.recommendations)
                ))
            
            conn.commit()
            logger.info(f"Saved {len(alerts)} alerts")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error saving alerts: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def get_latest_run(self) -> Optional[Dict]:
        """Get the most recent analysis run."""
        conn = self._get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            cursor.execute(f'''
                SELECT * FROM {self.schema_name}.analysis_runs 
                ORDER BY run_timestamp DESC LIMIT 1
            ''')
            
            row = cursor.fetchone()
            return dict(row) if row else None
            
        finally:
            cursor.close()
            conn.close()
    
    def get_demand_shifts(
        self,
        run_id: Optional[str] = None,
        item_id: Optional[str] = None
    ) -> pd.DataFrame:
        """Get demand shift results."""
        conn = self._get_connection()
        
        query = f"SELECT * FROM {self.schema_name}.demand_shifts WHERE 1=1"
        params = []
        
        if run_id:
            query += " AND run_id = %s"
            params.append(run_id)
        if item_id:
            query += " AND item_id = %s"
            params.append(item_id)
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        return df
    
    def get_non_moving(
        self,
        run_id: Optional[str] = None,
        location_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> pd.DataFrame:
        """Get non-moving inventory results."""
        conn = self._get_connection()
        
        query = f"SELECT * FROM {self.schema_name}.non_moving_inventory WHERE 1=1"
        params = []
        
        if run_id:
            query += " AND run_id = %s"
            params.append(run_id)
        if location_id:
            query += " AND location_id = %s"
            params.append(location_id)
        if status:
            query += " AND movement_status = %s"
            params.append(status)
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        return df
    
    def get_items_on_hold(self, run_id: Optional[str] = None) -> pd.DataFrame:
        """Get items with status 'on_hold' (non-moving with open PO)."""
        return self.get_non_moving(run_id=run_id, status='on_hold')
    
    def get_alerts(
        self,
        run_id: Optional[str] = None,
        priority: Optional[str] = None,
        resolved: Optional[bool] = None
    ) -> pd.DataFrame:
        """Get alerts."""
        conn = self._get_connection()
        
        query = f"SELECT * FROM {self.schema_name}.alerts WHERE 1=1"
        params = []
        
        if run_id:
            query += " AND run_id = %s"
            params.append(run_id)
        if priority:
            query += " AND priority = %s"
            params.append(priority)
        if resolved is not None:
            query += " AND resolved = %s"
            params.append(resolved)
        
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
        
        query = f"SELECT * FROM {self.schema_name}.risk_scores WHERE overall_score >= %s"
        params = [min_score]
        
        if run_id:
            query += " AND run_id = %s"
            params.append(run_id)
        
        query += " ORDER BY overall_score DESC"
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        return df
    
    def get_segmentation(
        self,
        run_id: Optional[str] = None,
        segment: Optional[str] = None
    ) -> pd.DataFrame:
        """Get segmentation results."""
        conn = self._get_connection()
        
        query = f"SELECT * FROM {self.schema_name}.segmentation WHERE 1=1"
        params = []
        
        if run_id:
            query += " AND run_id = %s"
            params.append(run_id)
        if segment:
            query += " AND segment = %s"
            params.append(segment)
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        return df
    
    def get_analysis_summary(self, run_id: str) -> Dict:
        """Get summary statistics for an analysis run."""
        conn = self._get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            # Get run info
            cursor.execute(f'''
                SELECT * FROM {self.schema_name}.analysis_runs WHERE run_id = %s
            ''', (run_id,))
            run_info = cursor.fetchone()
            
            # Get non-moving summary
            cursor.execute(f'''
                SELECT 
                    movement_status,
                    COUNT(*) as count,
                    SUM(current_inventory) as total_inventory,
                    AVG(non_moving_risk_score) as avg_risk_score
                FROM {self.schema_name}.non_moving_inventory 
                WHERE run_id = %s
                GROUP BY movement_status
            ''', (run_id,))
            non_moving_summary = cursor.fetchall()
            
            # Get demand shift summary
            cursor.execute(f'''
                SELECT 
                    shift_direction,
                    COUNT(*) as count,
                    AVG(shift_magnitude) as avg_magnitude
                FROM {self.schema_name}.demand_shifts 
                WHERE run_id = %s AND shift_detected = TRUE
                GROUP BY shift_direction
            ''', (run_id,))
            shift_summary = cursor.fetchall()
            
            # Get risk summary
            cursor.execute(f'''
                SELECT 
                    risk_level,
                    COUNT(*) as count,
                    AVG(overall_score) as avg_score
                FROM {self.schema_name}.risk_scores 
                WHERE run_id = %s
                GROUP BY risk_level
            ''', (run_id,))
            risk_summary = cursor.fetchall()
            
            return {
                'run_info': dict(run_info) if run_info else None,
                'non_moving_summary': [dict(r) for r in non_moving_summary],
                'shift_summary': [dict(r) for r in shift_summary],
                'risk_summary': [dict(r) for r in risk_summary]
            }
            
        finally:
            cursor.close()
            conn.close()
    
    def delete_run(self, run_id: str):
        """Delete an analysis run and all associated data."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(f'''
                DELETE FROM {self.schema_name}.analysis_runs WHERE run_id = %s
            ''', (run_id,))
            
            conn.commit()
            logger.info(f"Deleted run: {run_id}")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error deleting run: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
