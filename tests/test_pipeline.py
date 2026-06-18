import os
import sys
import unittest
import shutil
import numpy as np
from unittest.mock import patch

# Add project root to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.pipeline import run_pipeline, PRODUCT
from src.state.state_store import STATE_FILE, check_existing_run
from src.state.audit_logger import AUDIT_FILE, query_log
from src.analysis.pulse_generator import get_iso_week_key

class TestPipelineEndToEnd(unittest.TestCase):
    server_proc = None

    @classmethod
    def setUpClass(cls):
        # Locate external server.py path
        mcp_server_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../Bhavya_MCP_Server/server.py"))
        print(f"Starting MCP server subprocess on port 3010 from {mcp_server_path}...")
        import subprocess
        import time
        cls.server_proc = subprocess.Popen(
            ["./venv/bin/python", mcp_server_path, "--port", "3010", "--host", "127.0.0.1", "--transport", "sse"]
        )
        time.sleep(3)

    @classmethod
    def tearDownClass(cls):
        if cls.server_proc:
            print("Terminating MCP server subprocess...")
            cls.server_proc.terminate()
            try:
                cls.server_proc.wait(timeout=5)
            except Exception:
                cls.server_proc.kill()
    
    def setUp(self):
        # We backup state and audit files before running the E2E test
        self.state_backup = None
        if os.path.exists(STATE_FILE):
            self.state_backup = STATE_FILE + ".bak"
            shutil.copy2(STATE_FILE, self.state_backup)
            os.remove(STATE_FILE)
            
        self.audit_backup = None
        if os.path.exists(AUDIT_FILE):
            self.audit_backup = AUDIT_FILE + ".bak"
            shutil.copy2(AUDIT_FILE, self.audit_backup)
            os.remove(AUDIT_FILE)
            
        # Point pipeline to local server
        self.orig_gdoc_url = os.environ.get("MCP_GDOC_SERVER_URL")
        self.orig_gmail_url = os.environ.get("MCP_GMAIL_SERVER_URL")
        os.environ["MCP_GDOC_SERVER_URL"] = "http://127.0.0.1:3010"
        os.environ["MCP_GMAIL_SERVER_URL"] = "http://127.0.0.1:3010"
        
        # Ensure we are in mock mode for Google Docs/Gmail writes if we want to run safely,
        # but the test env can also run with actual MCP server depending on USE_MOCK_GOOGLE.
        # Let's set USE_MOCK_GOOGLE=true to make the tests fast and independent of OAuth creds.
        self.orig_mock_env = os.environ.get("USE_MOCK_GOOGLE")
        os.environ["USE_MOCK_GOOGLE"] = "true"
        
        # Setup API Key and disable terminal approval
        self.orig_api_key = os.environ.get("API_SECRET_KEY")
        self.orig_term_app = os.environ.get("REQUIRE_TERMINAL_APPROVAL")
        os.environ["API_SECRET_KEY"] = "test-secret-key"
        os.environ["REQUIRE_TERMINAL_APPROVAL"] = "false"
        
    def tearDown(self):
        # Restore backup files
        if os.path.exists(STATE_FILE):
            os.remove(STATE_FILE)
        if self.state_backup:
            shutil.copy2(self.state_backup, STATE_FILE)
            os.remove(self.state_backup)
            
        if os.path.exists(AUDIT_FILE):
            os.remove(AUDIT_FILE)
        if self.audit_backup:
            shutil.copy2(self.audit_backup, AUDIT_FILE)
            os.remove(self.audit_backup)
            
        if self.orig_mock_env is not None:
            os.environ["USE_MOCK_GOOGLE"] = self.orig_mock_env
        else:
            os.environ.pop("USE_MOCK_GOOGLE", None)

        if self.orig_gdoc_url is not None:
            os.environ["MCP_GDOC_SERVER_URL"] = self.orig_gdoc_url
        else:
            os.environ.pop("MCP_GDOC_SERVER_URL", None)

        if self.orig_gmail_url is not None:
            os.environ["MCP_GMAIL_SERVER_URL"] = self.orig_gmail_url
        else:
            os.environ.pop("MCP_GMAIL_SERVER_URL", None)

        if self.orig_api_key is not None:
            os.environ["API_SECRET_KEY"] = self.orig_api_key
        else:
            os.environ.pop("API_SECRET_KEY", None)

        if self.orig_term_app is not None:
            os.environ["REQUIRE_TERMINAL_APPROVAL"] = self.orig_term_app
        else:
            os.environ.pop("REQUIRE_TERMINAL_APPROVAL", None)

    @patch("src.pipeline.generate_fee_explainer")
    @patch("src.pipeline.generate_weekly_pulse")
    @patch("builtins.input", return_value="A")
    def test_pipeline_full_run_and_idempotency(self, mock_input, mock_pulse, mock_fee):
        """
        Runs the pipeline end-to-end.
        Verifies:
        1. Pipeline executes successfully and returns success status.
        2. State file is updated.
        3. Audit log contains a valid entry.
        4. Re-running the pipeline for the same week runs in update mode and successfully completes.
        """
        mock_pulse.return_value = {
            "weekly_summary": "Test weekly pulse summary.",
            "sentiment": {
                "positive": 50,
                "negative": 30,
                "neutral": 20
            },
            "action_ideas": [
                "Test Action 1",
                "Test Action 2",
                "Test Action 3"
            ]
        }
        mock_fee.return_value = {
            "scenario": "Mutual Fund Exit Load",
            "bullets": [
                "Exit load is a fee charged when you sell MF units.",
                "Typically 1% if redeemed within 1 year."
            ],
            "sources": [
                "Groww MF Rules"
            ],
            "last_checked": "June 2026"
        }
        iso_week = get_iso_week_key()
        
        # --- FIRST RUN (Insert Mode) ---
        logger_name = "src.pipeline"
        import logging
        logging.getLogger(logger_name).info("Starting E2E First Run Test...")
        
        result = run_pipeline()
        
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("iso_week"), iso_week)
        self.assertIsNotNone(result.get("doc_section_id"))
        self.assertIsNotNone(result.get("email_draft_id"))
        
        # Check that state store was updated
        state_record = check_existing_run(PRODUCT, iso_week)
        self.assertIsNotNone(state_record)
        self.assertEqual(state_record["status"], "completed")
        self.assertEqual(state_record["doc_section_id"], result["doc_section_id"])
        self.assertEqual(state_record["email_draft_id"], result["email_draft_id"])
        
        # Check that audit log was written
        audit_record = query_log(PRODUCT, iso_week)
        self.assertIsNotNone(audit_record)
        self.assertEqual(audit_record["doc_section_id"], result["doc_section_id"])
        self.assertEqual(audit_record["email_draft_id"], result["email_draft_id"])
        self.assertIn("weekly_pulse", audit_record["generated_report"])
        self.assertIn("fee_explainer", audit_record["generated_report"])
        
        # Keep track of first run section/draft IDs
        first_doc_sec_id = result["doc_section_id"]
        first_email_draft_id = result["email_draft_id"]
        
        # --- SECOND RUN (Update / Idempotency Mode) ---
        logging.getLogger(logger_name).info("Starting E2E Second Run (Idempotency) Test...")
        
        result_update = run_pipeline()
        
        self.assertEqual(result_update.get("status"), "success")
        self.assertEqual(result_update.get("iso_week"), iso_week)
        # In update mode, the section ID should remain identical (mock section ID stays same)
        self.assertEqual(result_update.get("doc_section_id"), first_doc_sec_id)
        
        # Check that state store was updated (last_updated timestamp should be updated, status completed)
        state_record_updated = check_existing_run(PRODUCT, iso_week)
        self.assertIsNotNone(state_record_updated)
        self.assertEqual(state_record_updated["status"], "completed")
        
        # Check that audit log contains the updated run
        audit_record_updated = query_log(PRODUCT, iso_week)
        self.assertIsNotNone(audit_record_updated)
        self.assertEqual(audit_record_updated["doc_section_id"], first_doc_sec_id)

if __name__ == "__main__":
    unittest.main()
