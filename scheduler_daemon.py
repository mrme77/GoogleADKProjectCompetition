#!/usr/bin/env python3
"""
MANIS Scheduler Daemon
Runs the MANIS pipeline at scheduled times using Python schedule library

Schedule:
- 07:00 AM (Morning briefing)
- 12:30 PM (Midday update)
- 20:30 PM (Evening digest)
"""

import os
import sys
import time
import logging
import schedule
import subprocess
from datetime import datetime
from pathlib import Path

# Configure logging
log_dir = Path(__file__).parent / "logs"
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "scheduler.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Path to the main runner script
RUNNER_SCRIPT = Path(__file__).parent / "run_manis.py"
PYTHON_EXECUTABLE = sys.executable


def run_manis_job():
    """Execute the MANIS pipeline as a subprocess"""
    logger.info("=" * 80)
    logger.info(f"Scheduled job triggered at {datetime.now()}")
    logger.info("=" * 80)

    try:
        # Run the pipeline in a subprocess
        result = subprocess.run(
            [PYTHON_EXECUTABLE, str(RUNNER_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout
        )

        if result.returncode == 0:
            logger.info("✓ Pipeline executed successfully")
            logger.info(f"Output: {result.stdout}")
        else:
            logger.error(f"✗ Pipeline failed with exit code {result.returncode}")
            logger.error(f"Error: {result.stderr}")

    except subprocess.TimeoutExpired:
        logger.error("✗ Pipeline execution timed out after 1 hour")
    except Exception as e:
        logger.error(f"✗ Unexpected error: {str(e)}", exc_info=True)


def main():
    """Main scheduler loop"""
    logger.info("=" * 80)
    logger.info("MANIS Scheduler Daemon Started")
    logger.info(f"PID: {os.getpid()}")
    logger.info("=" * 80)

    # Schedule jobs
    schedule.every().day.at("07:00").do(run_manis_job)
    schedule.every().day.at("12:30").do(run_manis_job)
    schedule.every().day.at("20:30").do(run_manis_job)

    logger.info("Scheduled jobs:")
    logger.info("  - 07:00 AM (Morning briefing)")
    logger.info("  - 12:30 PM (Midday update)")
    logger.info("  - 20:30 PM (Evening digest)")
    logger.info("")
    logger.info("Scheduler is now running. Press Ctrl+C to exit.")
    logger.info("")

    # Run the scheduler
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
    except Exception as e:
        logger.error(f"Scheduler crashed: {str(e)}", exc_info=True)


if __name__ == "__main__":
    main()
