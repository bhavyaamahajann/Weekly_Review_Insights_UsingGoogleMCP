import os
import sys
import unittest
import shutil
import json

# Add project root to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.state.state_store import check_existing_run, save_run_state, STATE_FILE
from src.state.audit_logger import log_run, query_log, AUDIT_FILE

class TestStateAndAudit(unittest.TestCase):
    
    def setUp(self):
        # Backup existing files if they exist
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

    def test_state_store_upsert_lookup(self):
        product = "TestProduct"
        iso_week = "2026-W99"
        
        # 1. Check lookup on non-existing entry
        res = check_existing_run(product, iso_week)
        self.assertIsNone(res)
        
        # 2. Save state (Insert)
        save_run_state(product, iso_week, "sec_123", "draft_456", "completed")
        
        # 3. Lookup and verify
        res2 = check_existing_run(product, iso_week)
        self.assertIsNotNone(res2)
        self.assertEqual(res2["doc_section_id"], "sec_123")
        self.assertEqual(res2["email_draft_id"], "draft_456")
        self.assertEqual(res2["status"], "completed")
        self.assertIn("last_updated", res2)
        
        # 4. Upsert (Update)
        save_run_state(product, iso_week, "sec_789", "draft_999", "updated")
        
        # 5. Lookup and verify update occurred
        res3 = check_existing_run(product, iso_week)
        self.assertIsNotNone(res3)
        self.assertEqual(res3["doc_section_id"], "sec_789")
        self.assertEqual(res3["email_draft_id"], "draft_999")
        self.assertEqual(res3["status"], "updated")

    def test_audit_logger_append_query(self):
        product = "TestProductAudit"
        iso_week = "2026-W99"
        report = {"summary": "some summary test info", "sentiment": {"positive": 100}}
        
        # 1. Check query on non-existing entry
        res = query_log(product, iso_week)
        self.assertIsNone(res)
        
        # 2. Log run
        log_run(product, iso_week, report, "sec_123", "draft_456")
        
        # 3. Query and verify
        res2 = query_log(product, iso_week)
        self.assertIsNotNone(res2)
        self.assertEqual(res2["product"], product)
        self.assertEqual(res2["iso_week"], iso_week)
        self.assertEqual(res2["doc_section_id"], "sec_123")
        self.assertEqual(res2["email_draft_id"], "draft_456")
        self.assertEqual(res2["generated_report"]["summary"], "some summary test info")
        self.assertIn("timestamp", res2)
        
        # 4. Log second run (same week) to simulate multiple attempts
        report_updated = {"summary": "updated summary"}
        log_run(product, iso_week, report_updated, "sec_789", "draft_999")
        
        # 5. Query and verify it returns the latest matching run
        res3 = query_log(product, iso_week)
        self.assertIsNotNone(res3)
        self.assertEqual(res3["doc_section_id"], "sec_789")
        self.assertEqual(res3["generated_report"]["summary"], "updated summary")

if __name__ == "__main__":
    unittest.main()
