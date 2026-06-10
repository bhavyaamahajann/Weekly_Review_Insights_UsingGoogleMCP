import os
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
AUDIT_FILE = os.path.join(PROJECT_ROOT, "logs/audit.jsonl")

def log_run(product: str, iso_week: str, generated_report: dict, doc_section_id: str, email_draft_id: str):
    """
    Appends a complete audit log entry to logs/audit.jsonl.
    """
    entry = {
        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "product": product,
        "iso_week": iso_week,
        "doc_section_id": doc_section_id,
        "email_draft_id": email_draft_id,
        "generated_report": generated_report
    }
    
    try:
        os.makedirs(os.path.dirname(AUDIT_FILE), exist_ok=True)
        with open(AUDIT_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        logger.info(f"Appended audit log entry for {product} - {iso_week}")
    except Exception as e:
        logger.error(f"Failed to write audit log entry: {e}")

def query_log(product: str, iso_week: str) -> dict | None:
    """
    Searches the audit log for a specific (product, iso_week) entry.
    Returns the latest matching entry or None.
    """
    if not os.path.exists(AUDIT_FILE):
        return None
        
    matching_entry = None
    try:
        with open(AUDIT_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    if entry.get("product") == product and entry.get("iso_week") == iso_week:
                        matching_entry = entry
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        logger.error(f"Failed to query audit log: {e}")
        
    return matching_entry
