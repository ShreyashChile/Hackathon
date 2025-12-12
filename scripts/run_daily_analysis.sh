#!/bin/bash
#
# Daily Analysis Cron Job Script
#
# This script runs the ML inventory analysis pipeline using PostgreSQL as the data source.
# Designed for automated daily runs via cron.
#
# Usage:
#   ./scripts/run_daily_analysis.sh
#
# Cron Example (run daily at 2 AM):
#   0 2 * * * /path/to/Hackathon/scripts/run_daily_analysis.sh >> /path/to/logs/analysis.log 2>&1
#

set -e  # Exit on any error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$PROJECT_DIR/venv"
LOG_DIR="$PROJECT_DIR/logs"

# Create logs directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Log file with timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="$LOG_DIR/analysis_$TIMESTAMP.log"

echo "========================================" | tee -a "$LOG_FILE"
echo "ML Inventory Analysis - Daily Run" | tee -a "$LOG_FILE"
echo "Started: $(date)" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"

# Change to project directory
cd "$PROJECT_DIR"

# Activate virtual environment
if [ -f "$VENV_DIR/bin/activate" ]; then
    source "$VENV_DIR/bin/activate"
    echo "Activated virtual environment: $VENV_DIR" | tee -a "$LOG_FILE"
else
    echo "ERROR: Virtual environment not found at $VENV_DIR" | tee -a "$LOG_FILE"
    exit 1
fi

# Check for .env file
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo "WARNING: .env file not found. Ensure PostgreSQL credentials are set." | tee -a "$LOG_FILE"
fi

# Run analysis with PostgreSQL source
echo "Running analysis with PostgreSQL data source..." | tee -a "$LOG_FILE"
python main.py analyze --source postgres 2>&1 | tee -a "$LOG_FILE"

# Capture exit code
EXIT_CODE=${PIPESTATUS[0]}

echo "========================================" | tee -a "$LOG_FILE"
echo "Completed: $(date)" | tee -a "$LOG_FILE"
echo "Exit Code: $EXIT_CODE" | tee -a "$LOG_FILE"
echo "Log File: $LOG_FILE" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"

# Cleanup old logs (keep last 30 days)
find "$LOG_DIR" -name "analysis_*.log" -type f -mtime +30 -delete 2>/dev/null || true

exit $EXIT_CODE

