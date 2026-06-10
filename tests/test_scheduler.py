import os
import sys
import unittest
import time
from unittest.mock import patch, MagicMock

# Add project root to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.scheduler.trigger import app
from src.scheduler.scheduler import scheduler

class TestSchedulerAndTrigger(unittest.TestCase):
    
    def setUp(self):
        # Create a Flask test client
        self.client = app.test_client()
        self.client.testing = True

    def test_health_endpoint(self):
        """Verify the health check endpoint returns 200 OK."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "ok")
        self.assertIn("running", data["message"])

    @patch("src.scheduler.trigger.run_pipeline")
    def test_trigger_endpoint(self, mock_run_pipeline):
        """Verify that POST /trigger starts the pipeline in the background and returns 202."""
        response = self.client.post("/trigger")
        self.assertEqual(response.status_code, 202)
        data = response.get_json()
        self.assertEqual(data["status"], "triggered")
        
        # Wait a small moment to let the background thread run
        time.sleep(0.5)
        
        # Check that run_pipeline was called
        mock_run_pipeline.assert_called_once()

    def test_scheduler_configuration(self):
        """Verify scheduler jobs configuration defaults are read correctly."""
        jobs = scheduler.get_jobs()
        self.assertEqual(len(jobs), 1)
        job = jobs[0]
        
        # Verify it has a CronTrigger trigger
        trigger_str = str(job.trigger)
        self.assertIn("cron", trigger_str)

if __name__ == "__main__":
    unittest.main()
