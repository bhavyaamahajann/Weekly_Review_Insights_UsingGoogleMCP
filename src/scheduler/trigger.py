import os
import sys
import threading
import logging
from flask import Flask, jsonify
from dotenv import load_dotenv

# Add project root to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.pipeline import run_pipeline

load_dotenv()

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

app = Flask(__name__)

def run_pipeline_async():
    logger.info("Manual HTTP trigger started pipeline run in background thread")
    try:
        # Force headless mode since trigger is run from cloud/service call
        os.environ["REQUIRE_TERMINAL_APPROVAL"] = "false"
        result = run_pipeline()
        logger.info(f"Manual HTTP trigger pipeline run finished. Result status: {result.get('status')}")
    except Exception as e:
        logger.error(f"Manual HTTP trigger pipeline failed with exception: {e}", exc_info=True)

@app.route("/trigger", methods=["POST"])
def trigger_pipeline():
    """Manually trigger the pipeline in a background thread."""
    thread = threading.Thread(target=run_pipeline_async)
    thread.daemon = True
    thread.start()
    return jsonify({
        "status": "triggered",
        "message": "Pipeline run started in background thread."
    }), 202

@app.route("/health", methods=["GET"])
def health():
    """Simple health check endpoint."""
    return jsonify({
        "status": "ok",
        "message": "Scheduler trigger service is running."
    }), 200

if __name__ == "__main__":
    port = int(os.getenv("SCHEDULER_TRIGGER_PORT", 5050))
    logger.info(f"Starting trigger HTTP server on port {port}...")
    app.run(host="127.0.0.1", port=port)
