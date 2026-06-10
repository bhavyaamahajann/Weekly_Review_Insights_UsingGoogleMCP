import os
import sys
import time
import subprocess
import unittest
import urllib.request
import json
from unittest.mock import patch

# Add project root to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.delivery.gdoc_mcp import append_to_gdoc
from src.delivery.gmail_mcp import create_gmail_draft
from src.delivery.approval_gates import approval_gate

class TestDeliveryMCP(unittest.TestCase):
    server_proc = None
    
    @classmethod
    def setUpClass(cls):
        # Configure env variables to point to test port 3010
        os.environ["MCP_GDOC_SERVER_URL"] = "http://127.0.0.1:3010"
        os.environ["MCP_GMAIL_SERVER_URL"] = "http://127.0.0.1:3010"
        os.environ["GDOC_DOCUMENT_ID"] = "test_doc_id"
        os.environ["GMAIL_RECIPIENT"] = "test_team@groww.in"
        os.environ["USE_MOCK_GOOGLE"] = "true"
        
        # Ensure test directory exists
        os.makedirs("data/outputs", exist_ok=True)
        
        # Clean previous simulation outputs
        for f in ["data/outputs/gdoc_simulation.md", "data/outputs/gmail_simulation.txt"]:
            if os.path.exists(f):
                os.remove(f)
                
        # Start server subprocess in background (decoupled sibling folder)
        mcp_server_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../Bhavya_MCP_Server/server.py"))
        print(f"Starting MCP server subprocess on port 3010 from {mcp_server_path}...")
        cls.server_proc = subprocess.Popen(
            ["./venv/bin/python", mcp_server_path, "--port", "3010", "--host", "127.0.0.1", "--transport", "sse"]
        )
        # Bounded sleep to wait for server start
        time.sleep(3)
        
    @classmethod
    def tearDownClass(cls):
        if cls.server_proc:
            print("Terminating MCP server subprocess...")
            cls.server_proc.terminate()
            try:
                cls.server_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                cls.server_proc.kill()
                
    def test_01_server_health_check(self):
        """Verify the health check endpoint returns 200 and matches expected structure."""
        url = "http://127.0.0.1:3010/"
        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                status = response.getcode()
                self.assertEqual(status, 200)
                body = json.loads(response.read().decode('utf-8'))
                self.assertEqual(body["status"], "ok")
                self.assertEqual(body["server"], "Groww Workspace MCP Server")
                self.assertEqual(body["port"], 3010)
        except Exception as e:
            self.fail(f"Could not connect to health check endpoint: {e}")
            
    def test_02_append_to_gdoc_simulation(self):
        """Test append_to_gdoc client writing a new section and then updating it (idempotency)."""
        payload = {
            "date": "2026-06-09",
            "iso_week": "2026-W23",
            "weekly_pulse": {
                "weekly_summary": "Initial summary content here.",
                "sentiment": {"positive": 15, "negative": 60, "neutral": 25},
                "action_ideas": ["Action 1", "Action 2", "Action 3"]
            },
            "fee_scenario": "Mutual Fund Exit Load",
            "explanation_bullets": ["Bullet 1", "Bullet 2"],
            "source_links": ["http://source1.com"],
            "last_checked": "June 2026"
        }
        
        # 1. Test Insert
        section_id = append_to_gdoc(payload)
        self.assertEqual(section_id, "mock_sec_2026-W23")
        
        # Verify file contents
        self.assertTrue(os.path.exists("data/outputs/gdoc_simulation.md"))
        with open("data/outputs/gdoc_simulation.md", "r") as f:
            content = f.read()
        self.assertIn("[Start Week: 2026-W23]", content)
        self.assertIn("Initial summary content here.", content)
        
        # 2. Test Update (Idempotency)
        payload["weekly_pulse"]["weekly_summary"] = "Updated summary content."
        section_id_2 = append_to_gdoc(payload, doc_section_id="2026-W23")
        self.assertEqual(section_id_2, "mock_sec_2026-W23")
        
        # Verify file updated, not duplicated
        with open("data/outputs/gdoc_simulation.md", "r") as f:
            updated_content = f.read()
        self.assertIn("Updated summary content.", updated_content)
        self.assertNotIn("Initial summary content here.", updated_content)
        # Should only have one start marker
        self.assertEqual(updated_content.count("[Start Week: 2026-W23]"), 1)
        
    def test_03_create_gmail_draft_simulation(self):
        """Test create_gmail_draft client creating and updating a mock email draft."""
        pulse_summary = "Weekly review pulse summary."
        fee_summary = "Factual exit load fee explainer summary."
        doc_link = "http://docs.google.com/document/d/test_doc_id/edit"
        iso_week = "2026-W23"
        
        # 1. Create Draft
        draft_id = create_gmail_draft(pulse_summary, fee_summary, doc_link, iso_week)
        self.assertEqual(draft_id, "mock_draft_2026-W23")
        
        # Verify file contents
        self.assertTrue(os.path.exists("data/outputs/gmail_simulation.txt"))
        with open("data/outputs/gmail_simulation.txt", "r") as f:
            content = f.read()
        self.assertIn("[Start Draft: 2026-W23]", content)
        self.assertIn("Weekly review pulse summary.", content)
        
        # 2. Update Draft (Idempotency)
        updated_pulse = "An updated pulse summary."
        draft_id_2 = create_gmail_draft(updated_pulse, fee_summary, doc_link, iso_week)
        self.assertEqual(draft_id_2, "mock_draft_2026-W23")
        
        # Verify updated, not duplicated
        with open("data/outputs/gmail_simulation.txt", "r") as f:
            updated_content = f.read()
        self.assertIn("An updated pulse summary.", updated_content)
        self.assertNotIn("Weekly review pulse summary.", updated_content)
        self.assertEqual(updated_content.count("[Start Draft: 2026-W23]"), 1)

    def test_04_approval_gates_approve(self):
        """Test approval_gate returns True on Approve choice."""
        payload = {
            "weekly_summary": "Test Summary",
            "sentiment": {"positive": 50, "negative": 50, "neutral": 0},
            "action_ideas": ["Idea 1"]
        }
        
        # Mock input to return "A" (Approve)
        with patch("builtins.input", return_value="A"):
            result = approval_gate(1, "Test Label", payload)
            self.assertTrue(result)
            
        # Mock input to return "R" (Reject)
        with patch("builtins.input", return_value="R"):
            result = approval_gate(3, "Test Label", {"document_id": "doc123"})
            self.assertFalse(result)

if __name__ == "__main__":
    unittest.main()
