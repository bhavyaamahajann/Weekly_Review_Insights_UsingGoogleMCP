import os
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Use absolute path or relative path to project root
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
STATE_FILE = os.path.join(PROJECT_ROOT, "state/run_state.json")

def _load_all_state() -> dict:
    """Helper to load all states from the state file."""
    if not os.path.exists(STATE_FILE):
        return {}
    
    try:
        with open(STATE_FILE, "r") as f:
            content = f.read().strip()
            if not content:
                return {}
            return json.loads(content)
    except Exception as e:
        logger.warning(f"Failed to load state file: {e}. Returning empty state.")
        return {}

def _save_all_state(state: dict):
    """Helper to save the entire state dict back to the state file."""
    try:
        os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to write to state file: {e}")

def check_existing_run(product: str, iso_week: str) -> dict | None:
    """
    Returns the existing state record for (product, iso_week) if it exists,
    otherwise returns None.
    """
    state = _load_all_state()
    product_state = state.get(product, {})
    return product_state.get(iso_week)

def save_run_state(product: str, iso_week: str, doc_section_id: str, email_draft_id: str, status: str):
    """
    Upserts the state record for (product, iso_week).
    """
    state = _load_all_state()
    
    if product not in state:
        state[product] = {}
        
    state[product][iso_week] = {
        "doc_section_id": doc_section_id,
        "email_draft_id": email_draft_id,
        "status": status,
        "last_updated": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    }
    
    _save_all_state(state)
    logger.info(f"Saved run state for {product} - {iso_week}: status={status}")
