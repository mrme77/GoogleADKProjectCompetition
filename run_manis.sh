#!/bin/bash
# MANIS Pipeline Runner
# Executes the complete Multi-Agent News Intelligence System pipeline using ADK

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Load environment variables from .env file
# (Now handled by manis_agent/__init__.py, but we keep the comment for clarity)
# set -a
# source manis_agent/.env
# set +a

# Path to ADK in virtual environment
ADK_CMD="$SCRIPT_DIR/adk-env/bin/adk"

# Create logs directory
mkdir -p logs

# Set log file
LOG_FILE="logs/manis_$(date +%Y%m%d_%H%M%S).log"

echo "========================================" | tee -a "$LOG_FILE"
echo "MANIS Pipeline Started: $(date)" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"

# Run MANIS using ADK with piped input (non-interactive)
echo "Collect, analyze, and deliver today's news intelligence report" | "$ADK_CMD" run manis_agent --save_session 2>&1 | tee -a "$LOG_FILE"

EXIT_CODE=${PIPESTATUS[0]}

if [ $EXIT_CODE -eq 0 ]; then
    echo "✓ Pipeline completed successfully" | tee -a "$LOG_FILE"
else
    echo "✗ Pipeline failed with exit code $EXIT_CODE" | tee -a "$LOG_FILE"
fi

exit $EXIT_CODE
