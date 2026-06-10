import os
import sys
import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv

# Add project root to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.pipeline import run_pipeline

load_dotenv()

# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)

# Configure logging
os.makedirs("logs", exist_ok=True)
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

# File handler
file_handler = logging.FileHandler("logs/scheduler.log")
file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
root_logger.addHandler(file_handler)

# Stdout handler
stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
root_logger.addHandler(stdout_handler)

logger = logging.getLogger(__name__)

# Configure Scheduler
scheduler = BlockingScheduler(timezone="Asia/Kolkata")

day_of_week = os.getenv("SCHEDULER_DAY_OF_WEEK", "mon")
try:
    hour = int(os.getenv("SCHEDULER_HOUR", 8))
except ValueError:
    hour = 8

@scheduler.scheduled_job(
    CronTrigger(
        day_of_week=day_of_week,
        hour=hour,
        minute=0
    )
)
def weekly_job():
    logger.info("Scheduler triggered: starting weekly pipeline run")
    try:
        # Scheduler runs in background / cloud, so force headless approval gates
        os.environ["REQUIRE_TERMINAL_APPROVAL"] = "false"
        result = run_pipeline()
        logger.info(f"Pipeline completed successfully. Result status: {result.get('status')}")
    except Exception as e:
        logger.error(f"Pipeline failed with exception: {e}", exc_info=True)

if __name__ == "__main__":
    logger.info(f"Scheduler started. Timezone: Asia/Kolkata. Schedule: Every {day_of_week.upper()} at {hour:02d}:00 IST")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped.")
