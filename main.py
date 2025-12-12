#!/usr/bin/env python3
"""
ML Agent for Demand Shift Detection and Non-Moving Inventory Identification

Main entry point for running analysis and starting the API server.
"""

import argparse
import logging
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_analysis(data_dir: str = "data", output_dir: str = "outputs", source: str = "csv"):
    """
    Run the complete analysis pipeline.
    
    Args:
        data_dir: Path to data directory (used when source='csv')
        output_dir: Path to output directory
        source: Data source - 'csv' for CSV files, 'postgres' for PostgreSQL
    """
    from src.config import update_config
    from src.data.loader import DataLoader
    from src.data.postgres_loader import PostgresDataLoader
    from src.data.preprocessor import DataPreprocessor
    from src.ml.demand_shift import DemandShiftDetector
    from src.ml.non_moving import NonMovingDetector
    from src.ml.segmentation import SKUSegmentation
    from src.ml.scoring import RiskScorer
    from src.output.alerts import AlertGenerator
    from src.output.database import DatabaseManager
    from src.output.exporters import CSVExporter, JSONExporter
    from src.visualization.dashboard import DashboardGenerator
    
    # Update config with paths
    update_config(data_dir=Path(data_dir), output_dir=Path(output_dir))
    
    logger.info("=" * 60)
    logger.info("ML INVENTORY AGENT - ANALYSIS PIPELINE")
    logger.info("=" * 60)
    
    # Step 1: Load data
    logger.info("\n[1/7] Loading data...")
    
    if source == "postgres":
        logger.info("Data source: PostgreSQL")
        loader = PostgresDataLoader()
    else:
        logger.info(f"Data source: CSV files from {data_dir}")
        loader = DataLoader(data_dir)
    
    dataset = loader.load_all()
    logger.info(f"Loaded {len(dataset.sku_list)} SKUs across {len(dataset.location_list)} locations")
    
    # Step 2: Preprocess
    logger.info("\n[2/7] Preprocessing data...")
    preprocessor = DataPreprocessor(dataset)
    dataset = preprocessor.preprocess()
    
    # Step 3: Initialize PostgreSQL database
    logger.info("\n[3/7] Initializing PostgreSQL database...")
    db = DatabaseManager()  # Uses environment variables for PostgreSQL connection
    run_id = db.create_run(
        total_skus=len(dataset.sku_list),
        total_locations=len(dataset.location_list),
        data_start_date=str(dataset.date_range[0]),
        data_end_date=str(dataset.date_range[1])
    )
    
    # Step 4: Demand shift detection
    logger.info("\n[4/7] Detecting demand shifts...")
    shift_detector = DemandShiftDetector()
    demand_shifts = shift_detector.detect(dataset)
    shift_summary = shift_detector.get_shift_summary(demand_shifts)
    logger.info(f"Found {shift_summary['shifts_detected']} demand shifts "
                f"({shift_summary['shift_rate']}% of combinations)")
    db.save_demand_shifts(run_id, demand_shifts)
    
    # Step 5: Non-moving inventory detection
    logger.info("\n[5/7] Detecting non-moving inventory...")
    nm_detector = NonMovingDetector()
    non_moving = nm_detector.detect(dataset)
    nm_summary = nm_detector.get_summary(non_moving)
    logger.info("Movement status breakdown:")
    logger.info(f"  - Active: {nm_summary['active']}")
    logger.info(f"  - Non-moving: {nm_summary['non_moving']}")
    logger.info(f"  - On Hold (has open PO): {nm_summary['on_hold']}")
    logger.info(f"  - Items with inventory at risk: {nm_summary['with_inventory_at_risk']}")
    db.save_non_moving(run_id, non_moving)
    
    # Step 6: ABC-XYZ Segmentation
    logger.info("\n[6/7] Performing ABC-XYZ segmentation...")
    segmenter = SKUSegmentation()
    segmentation = segmenter.segment_all(dataset, by_location=True)
    seg_summary = segmenter.get_segment_summary(segmentation)
    logger.info(f"Segment distribution:\n{seg_summary.to_string()}")
    db.save_segmentation(run_id, segmentation)
    
    # Step 7: Risk scoring
    logger.info("\n[7/7] Calculating risk scores...")
    scorer = RiskScorer()
    risk_scores = scorer.score(demand_shifts, non_moving, dataset)
    risk_summary = scorer.get_risk_summary(risk_scores)
    logger.info(f"Risk level distribution: {risk_summary['by_risk_level']}")
    db.save_risk_scores(run_id, risk_scores)
    
    # Generate alerts
    logger.info("\nGenerating alerts...")
    alert_gen = AlertGenerator()
    shift_alerts = alert_gen.generate_demand_shift_alerts(demand_shifts)
    nm_alerts = alert_gen.generate_non_moving_alerts(non_moving)
    risk_alerts = alert_gen.generate_risk_alerts(risk_scores)
    all_alerts = alert_gen.consolidate_alerts(shift_alerts, nm_alerts, risk_alerts)
    alert_summary = alert_gen.get_alert_summary(all_alerts)
    logger.info(f"Generated {alert_summary['total']} alerts")
    db.save_alerts(run_id, all_alerts)
    
    # Export results
    logger.info("\nExporting results...")
    csv_exporter = CSVExporter(output_dir)
    csv_exporter.export_demand_shifts(demand_shifts)
    csv_exporter.export_non_moving(non_moving)
    csv_exporter.export_segmentation(segmentation)
    csv_exporter.export_risk_scores(risk_scores)
    csv_exporter.export_alerts(all_alerts)
    csv_exporter.export_summary_report(demand_shifts, non_moving, segmentation, risk_scores)
    
    json_exporter = JSONExporter(output_dir)
    json_exporter.export_full_analysis(
        demand_shifts, non_moving, segmentation, risk_scores, all_alerts
    )
    
    # Generate dashboard
    logger.info("\nGenerating dashboard...")
    dashboard_gen = DashboardGenerator(output_dir)
    dashboard_path = dashboard_gen.generate_dashboard(
        demand_shifts, non_moving, segmentation, risk_scores, all_alerts, run_id
    )
    logger.info(f"Dashboard saved to: {dashboard_path}")
    
    # Mark run as complete
    db.complete_run(run_id)
    
    # Print summary
    logger.info("\n" + "=" * 60)
    logger.info("ANALYSIS COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Run ID: {run_id}")
    logger.info("\nKEY FINDINGS:")
    logger.info(f"  - Demand shifts detected: {shift_summary['shifts_detected']}")
    logger.info(f"  - Non-moving items: {nm_summary['non_moving']}")
    logger.info(f"  - Items on hold (with open PO): {nm_summary['on_hold']}")
    logger.info(f"  - High risk items: {risk_summary['high_risk_items']}")
    logger.info(f"  - Critical alerts: {alert_summary.get('critical_count', 0)}")
    logger.info(f"\nOutputs saved to: {output_dir}/")
    logger.info("=" * 60)
    
    return {
        'run_id': run_id,
        'demand_shifts': demand_shifts,
        'non_moving': non_moving,
        'segmentation': segmentation,
        'risk_scores': risk_scores,
        'alerts': all_alerts
    }


def start_api(host: str = "0.0.0.0", port: int = 8000):
    """Start the FastAPI server."""
    import uvicorn
    from src.output.api import app
    
    logger.info(f"Starting API server at http://{host}:{port}")
    logger.info(f"API Documentation: http://{host}:{port}/docs")
    
    uvicorn.run(app, host=host, port=port)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="ML Agent for Demand Shift Detection and Non-Moving Inventory"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Run analysis pipeline")
    analyze_parser.add_argument(
        "--source",
        choices=["csv", "postgres"],
        default="csv",
        help="Data source: 'csv' for CSV files, 'postgres' for PostgreSQL (default: csv)"
    )
    analyze_parser.add_argument(
        "--data-dir", 
        default="data",
        help="Path to data directory, used when source=csv (default: data)"
    )
    analyze_parser.add_argument(
        "--output-dir",
        default="outputs",
        help="Path to output directory (default: outputs)"
    )
    
    # API command
    api_parser = subparsers.add_parser("api", help="Start the API server")
    api_parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)"
    )
    api_parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to (default: 8000)"
    )
    api_parser.add_argument(
        "--run-analysis",
        action="store_true",
        help="Run analysis before starting API"
    )
    
    # Full command (analyze + api)
    full_parser = subparsers.add_parser("full", help="Run analysis and start API")
    full_parser.add_argument(
        "--source",
        choices=["csv", "postgres"],
        default="csv",
        help="Data source: 'csv' for CSV files, 'postgres' for PostgreSQL (default: csv)"
    )
    full_parser.add_argument(
        "--data-dir",
        default="data",
        help="Path to data directory, used when source=csv"
    )
    full_parser.add_argument(
        "--output-dir",
        default="outputs",
        help="Path to output directory"
    )
    full_parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="API host"
    )
    full_parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="API port"
    )
    
    args = parser.parse_args()
    
    if args.command == "analyze":
        run_analysis(args.data_dir, args.output_dir, args.source)
    elif args.command == "api":
        if args.run_analysis:
            run_analysis()
        start_api(args.host, args.port)
    elif args.command == "full":
        run_analysis(args.data_dir, args.output_dir, args.source)
        start_api(args.host, args.port)
    else:
        # Default: show help
        parser.print_help()
        print("\n" + "=" * 60)
        print("Quick Start:")
        print("  python main.py analyze                 # Run analysis (CSV source)")
        print("  python main.py analyze --source postgres  # Run analysis (PostgreSQL)")
        print("  python main.py api                     # Start API server")
        print("  python main.py full                    # Run analysis + start API")
        print("  python main.py full --source postgres  # Cron job mode")
        print("=" * 60)


if __name__ == "__main__":
    main()

