#!/bin/bash
# MANIS Cron Setup Script
# Automatically configures cron jobs to run MANIS at 7:00 AM, 12:30 PM, and 8:30 PM

set -e

# Get the absolute path to the project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNNER_SCRIPT="$PROJECT_DIR/run_manis.sh"

echo "========================================"
echo "MANIS Cron Setup"
echo "========================================"
echo "Project Directory: $PROJECT_DIR"
echo "Runner Script: $RUNNER_SCRIPT"
echo ""

# Make runner script executable
chmod +x "$RUNNER_SCRIPT"

# Create cron job entries
CRON_JOBS="# MANIS - Multi-Agent News Intelligence System
# Runs at 7:30 AM, 12:30 PM, and 4:30 PM daily

30 7 * * * cd '$PROJECT_DIR' && '$RUNNER_SCRIPT' >> '$PROJECT_DIR/logs/cron.log' 2>&1
30 12 * * * cd '$PROJECT_DIR' && '$RUNNER_SCRIPT' >> '$PROJECT_DIR/logs/cron.log' 2>&1
30 16 * * * cd '$PROJECT_DIR' && '$RUNNER_SCRIPT' >> '$PROJECT_DIR/logs/cron.log' 2>&1
"

# Create logs directory
mkdir -p "$PROJECT_DIR/logs"

# Backup existing crontab
echo "Backing up existing crontab..."
crontab -l > "$PROJECT_DIR/crontab_backup_$(date +%Y%m%d_%H%M%S).txt" 2>/dev/null || echo "No existing crontab found"

# Add new cron jobs
echo ""
echo "Adding MANIS cron jobs..."
echo ""
echo "Cron schedule:"
echo "  - 07:30 AM daily (Morning briefing)"
echo "  - 12:30 PM daily (Midday update)"
echo "  - 04:30 PM daily (Afternoon digest)"
echo ""

# Get current crontab, remove any old MANIS jobs, and add new ones
(crontab -l 2>/dev/null | grep -v "MANIS" | grep -v "run_manis.py" || true; echo "$CRON_JOBS") | crontab -

echo "✓ Cron jobs installed successfully!"
echo ""
echo "To view your cron jobs, run:"
echo "  crontab -l"
echo ""
echo "To remove MANIS cron jobs, run:"
echo "  crontab -e"
echo "  (then delete the MANIS lines)"
echo ""
echo "Logs will be saved to: $PROJECT_DIR/logs/"
echo ""
