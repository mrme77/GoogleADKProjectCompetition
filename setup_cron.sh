#!/bin/bash
# MANIS Cron Setup Script
# Automatically configures cron job to run MANIS at 8:00 AM daily

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

# Create cron job entry
CRON_JOBS="# MANIS - Multi-Agent News Intelligence System
# Runs at 8:00 AM daily

0 8 * * * cd '$PROJECT_DIR' && '$RUNNER_SCRIPT' >> '$PROJECT_DIR/logs/cron.log' 2>&1
"

# Create logs directory
mkdir -p "$PROJECT_DIR/logs"

# Backup existing crontab
echo "Backing up existing crontab..."
crontab -l > "$PROJECT_DIR/crontab_backup_$(date +%Y%m%d_%H%M%S).txt" 2>/dev/null || echo "No existing crontab found"

# Add new cron job
echo ""
echo "Adding MANIS cron job..."
echo ""
echo "Cron schedule:"
echo "  - 08:00 AM daily (Morning briefing)"
echo ""

# Get current crontab, remove any old MANIS jobs, and add new ones
(crontab -l 2>/dev/null | grep -v "MANIS" || true; echo "$CRON_JOBS") | crontab -

echo "✓ Cron job installed successfully!"
echo ""
echo "To view your cron jobs, run:"
echo "  crontab -l"
echo ""
echo "To remove MANIS cron job, run:"
echo "  crontab -e"
echo "  (then delete the MANIS lines)"
echo ""
echo "Logs will be saved to: $PROJECT_DIR/logs/"
echo ""
