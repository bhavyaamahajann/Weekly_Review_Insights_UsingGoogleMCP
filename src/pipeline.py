import os
import sys
import logging
import json
import numpy as np
from datetime import datetime
from dotenv import load_dotenv

# Add project root to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.utils.exceptions import PipelineAbortError
from src.ingestion.fetch_reviews import fetch_and_sync_reviews
from src.processing.cleaner import clean_corpus
from src.processing.embedder import embed_reviews
from src.processing.clusterer import cluster_reviews
from src.processing.quote_extractor import extract_quotes
from src.analysis.pulse_generator import generate_weekly_pulse, get_iso_week_key
from src.analysis.fee_explainer import generate_fee_explainer
from src.delivery.approval_gates import approval_gate
from src.delivery.gdoc_mcp import append_to_gdoc
from src.delivery.gmail_mcp import create_gmail_draft
from src.state.state_store import check_existing_run, save_run_state
from src.state.audit_logger import log_run

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

PRODUCT = "Groww"

def run_pipeline() -> dict:
    load_dotenv()
    
    # Set default Document ID if not configured in environment
    if not os.getenv("GDOC_DOCUMENT_ID") or os.getenv("GDOC_DOCUMENT_ID") == "your_google_doc_id":
        os.environ["GDOC_DOCUMENT_ID"] = "126paEr1-SJpFx7P2RWkzq6rPRUHfYjgqvhcXrNK21M0"
        logger.info(f"Using default Google Doc ID: {os.environ['GDOC_DOCUMENT_ID']}")

    # 1. Compute ISO week
    iso_week = get_iso_week_key()
    logger.info(f"Starting Weekly Product Review Pulse & Fee Explainer pipeline for week {iso_week}")
    
    # 2. Check idempotency state
    existing_run = check_existing_run(PRODUCT, iso_week)
    is_update_mode = False
    doc_section_id = None
    email_draft_id = None
    
    if existing_run:
        is_update_mode = True
        doc_section_id = existing_run.get("doc_section_id")
        email_draft_id = existing_run.get("email_draft_id")
        logger.info(f"Existing run found for week {iso_week} (status: {existing_run.get('status')}). Running in UPDATE mode.")
    else:
        logger.info(f"No existing run found for week {iso_week}. Running in INSERT mode.")
        
    # Define directory paths
    raw_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data/raw"))
    cleaned_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data/cleaned"))
    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(cleaned_dir, exist_ok=True)
    
    raw_csv = os.path.join(raw_dir, "reviews.csv")
    clean_csv = os.path.join(cleaned_dir, "reviews_clean.csv")
    clean_json = os.path.join(cleaned_dir, "reviews_clean.json")
    
    try:
        # 3. Fetch & clean reviews
        logger.info("--- Step 3: Fetching and Cleaning Reviews ---")
        fetch_and_sync_reviews()
        
        min_threshold = int(os.getenv("MIN_REVIEWS_THRESHOLD", 50))
        cleaned_df = clean_corpus(raw_csv, clean_csv, clean_json, min_threshold)
        
        # 4. Embed, cluster, extract quotes
        logger.info("--- Step 4: Generating Embeddings, Clusters, and Quotes ---")
        texts = cleaned_df["review_text"].tolist()
        embeddings = embed_reviews(texts)
        
        # Save embeddings
        embeddings_path = os.path.join(cleaned_dir, f"embeddings_{iso_week}.npy")
        np.save(embeddings_path, embeddings)
        
        # Cluster reviews
        cluster_result = cluster_reviews(embeddings, cleaned_df, max_clusters=5)
        
        # Save cluster results
        themes_metadata_path = os.path.join(cleaned_dir, f"themes_metadata_{iso_week}.json")
        with open(themes_metadata_path, "w") as f:
            json.dump(cluster_result, f, indent=2)
            
        themes = cluster_result["themes"]
        
        # Extract verbatim quotes
        quotes = extract_quotes(cleaned_df, themes, embeddings)
        
        # Save quotes
        quotes_path = os.path.join(cleaned_dir, f"quotes_{iso_week}.json")
        with open(quotes_path, "w") as f:
            json.dump(quotes, f, indent=2)
            
        # 5/6. Generate summaries via Groq with Human Approval Gates (Gates 1 & 2)
        logger.info("--- Step 5 & 6: Generating Analysis and Running Gates 1 & 2 ---")
        
        # Gate 1: Weekly Pulse Summary
        weekly_pulse = None
        pulse_feedback = None
        gate1_approved = False
        
        while not gate1_approved:
            weekly_pulse = generate_weekly_pulse(themes, quotes, iso_week=iso_week, feedback=pulse_feedback)
            
            # Format payload for Gate 1 preview
            gate1_payload = {
                "themes": [t["label"] for t in themes],
                "quotes": [q["quote"] for q in quotes],
                "weekly_summary": weekly_pulse["weekly_summary"],
                "sentiment": weekly_pulse["sentiment"],
                "action_ideas": weekly_pulse["action_ideas"]
            }
            
            if approval_gate(1, iso_week, gate1_payload):
                gate1_approved = True
            else:
                pulse_feedback = gate1_payload.get("feedback")
                logger.info("Gate 1 rejected. Regenerating weekly pulse summary...")
                
        # Gate 2: Fee Explainer Summary
        fee_explainer = None
        fee_feedback = None
        gate2_approved = False
        
        while not gate2_approved:
            fee_explainer = generate_fee_explainer(iso_week=iso_week, feedback=fee_feedback)
            
            # Format payload for Gate 2 preview
            gate2_payload = {
                "scenario": fee_explainer["scenario"],
                "bullets": fee_explainer["bullets"],
                "sources": fee_explainer["sources"],
                "last_checked": fee_explainer["last_checked"]
            }
            
            if approval_gate(2, iso_week, gate2_payload):
                gate2_approved = True
            else:
                fee_feedback = gate2_payload.get("feedback")
                logger.info("Gate 2 rejected. Regenerating fee explainer...")
                
        # 7. Gate 3: Google Doc write via MCP
        logger.info("--- Step 7: Running Gate 3 and Writing to Google Doc ---")
        gdoc_payload = {
            "date": datetime.utcnow().strftime("%Y-%m-%d"),
            "iso_week": iso_week,
            "weekly_pulse": weekly_pulse,
            "fee_scenario": fee_explainer["scenario"],
            "explanation_bullets": fee_explainer["bullets"],
            "source_links": fee_explainer["sources"],
            "last_checked": fee_explainer["last_checked"],
            "document_id": os.getenv("GDOC_DOCUMENT_ID"),
            "is_update": is_update_mode
        }
        
        if not approval_gate(3, iso_week, gdoc_payload):
            logger.warning("Gate 3 rejected by user. Aborting pipeline before external writes.")
            save_run_state(PRODUCT, iso_week, doc_section_id, email_draft_id, "failed_gdoc_rejected")
            return {"status": "aborted", "reason": "gdoc_rejected"}
            
        # If approved, perform write
        new_doc_section_id = append_to_gdoc(gdoc_payload, doc_section_id=doc_section_id if is_update_mode else None)
        logger.info(f"Google Doc write completed. Section ID: {new_doc_section_id}")
        
        # Save state with GDoc write complete
        save_run_state(PRODUCT, iso_week, new_doc_section_id, email_draft_id, "gdoc_written")
        
        # 8. Gate 4: Gmail draft creation via MCP
        logger.info("--- Step 8: Running Gate 4 and Creating Gmail Draft ---")
        doc_link = f"https://docs.google.com/document/d/{os.getenv('GDOC_DOCUMENT_ID')}/edit"
        
        # Format summaries for email body
        pulse_summary = weekly_pulse["weekly_summary"] + "\nSentiment: " + \
            f"Positive {weekly_pulse['sentiment']['positive']}%, " + \
            f"Negative {weekly_pulse['sentiment']['negative']}%, " + \
            f"Neutral {weekly_pulse['sentiment']['neutral']}%\n" + \
            "Action Ideas:\n" + "\n".join([f"- {idea}" for idea in weekly_pulse["action_ideas"]])
            
        fee_summary = "\n".join([f"- {bullet}" for bullet in fee_explainer["bullets"]])
        
        gmail_recipient = os.getenv("GMAIL_RECIPIENT", "team@groww.in")
        gmail_subject = f"Weekly Pulse + Fee Explainer — Groww ({iso_week})"
        
        email_body = f"Hi Team,\n\n" \
                     f"Here is the Weekly Product Review Pulse and Fee Explainer for Groww ({iso_week}).\n\n" \
                     f"WEEKLY PULSE SUMMARY:\n{pulse_summary}\n\n" \
                     f"FEE EXPLAINER: Mutual Fund Exit Load\n{fee_summary}\n\n" \
                     f"The full report and historical logs have been appended to the Google Doc:\n{doc_link}\n\n" \
                     f"Best regards,\n" \
                     f"Product Review Pulse Automator\n"

        gate4_payload = {
            "recipient": gmail_recipient,
            "subject": gmail_subject,
            "body": email_body
        }
        
        if not approval_gate(4, iso_week, gate4_payload):
            logger.warning("Gate 4 rejected by user. Pipeline finished with partial completion (GDoc written, no Gmail draft).")
            save_run_state(PRODUCT, iso_week, new_doc_section_id, email_draft_id, "completed_no_gmail")
            
            # Log audit trail
            generated_report = {
                "weekly_pulse": weekly_pulse,
                "fee_explainer": fee_explainer
            }
            log_run(PRODUCT, iso_week, generated_report, new_doc_section_id, email_draft_id)
            return {"status": "completed_partial", "doc_section_id": new_doc_section_id, "email_draft_id": email_draft_id}
            
        # If approved, perform draft creation
        new_email_draft_id = create_gmail_draft(pulse_summary, fee_summary, doc_link, iso_week)
        logger.info(f"Gmail draft creation completed. Draft ID: {new_email_draft_id}")
        
        # 9. Final state save and audit logging
        save_run_state(PRODUCT, iso_week, new_doc_section_id, new_email_draft_id, "completed")
        
        generated_report = {
            "weekly_pulse": weekly_pulse,
            "fee_explainer": fee_explainer
        }
        log_run(PRODUCT, iso_week, generated_report, new_doc_section_id, new_email_draft_id)
        
        # 10. Write clean deliverable report to docs/weekly_pulse_report.md
        try:
            report_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../docs"))
            os.makedirs(report_dir, exist_ok=True)
            report_file = os.path.join(report_dir, "weekly_pulse_report.md")
            
            # Map input themes & quotes
            theme_list = "\n".join([f"{i+1}. {t['label']} ({t['size']} reviews)" for i, t in enumerate(themes[:5])])
            quote_list = "\n".join([f"- **Theme '{q['theme']}':** \"{q['quote']}\"" for q in quotes[:5]])
            bullets_list = "\n".join([f"- {b}" for b in fee_explainer["bullets"]])
            sources_list = "\n".join([
                f"- [{s['name']}]({s['url']})" if isinstance(s, dict) else f"- {s}"
                for s in fee_explainer["sources"]
            ])
            
            report_content = (
                f"# Groww — Weekly Product Review Pulse & Fee Explainer\n\n"
                f"**Report Period:** {iso_week}\n"
                f"**Generated Date:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
                f"---\n\n"
                f"## Part A — Weekly Product Pulse\n\n"
                f"### Top Themes\n{theme_list}\n\n"
                f"### Real User Quotes\n{quote_list}\n\n"
                f"### Weekly Summary\n{weekly_pulse['weekly_summary']}\n\n"
                f"### Action Ideas\n"
                f"1. {weekly_pulse['action_ideas'][0]}\n"
                f"2. {weekly_pulse['action_ideas'][1]}\n"
                f"3. {weekly_pulse['action_ideas'][2]}\n\n"
                f"---\n\n"
                f"## Part B — Fee Explainer: Mutual Fund Exit Load\n\n"
                f"### Key Facts\n{bullets_list}\n\n"
                f"**Last Checked:** {fee_explainer['last_checked']}\n\n"
                f"### Official Sources\n{sources_list}\n"
            )
            
            with open(report_file, "w") as rf:
                rf.write(report_content)
            logger.info(f"Clean weekly pulse report saved to {report_file}")
        except Exception as re_err:
            logger.warning(f"Could not write weekly pulse report file: {re_err}")
        
        logger.info(f"Pipeline finished successfully for week {iso_week}!")
        
        # Keep history of just 4 weeks
        try:
            prune_old_runs(keep_weeks=4)
        except Exception as prune_err:
            logger.warning(f"Failed to prune old runs: {prune_err}")

        return {
            "status": "success",
            "iso_week": iso_week,
            "doc_section_id": new_doc_section_id,
            "email_draft_id": new_email_draft_id
        }
        
    except PipelineAbortError as e:
        logger.error(f"Pipeline aborted: {e.message} (Code: {e.error_code})")
        # Save failed state
        save_run_state(PRODUCT, iso_week, doc_section_id, email_draft_id, f"failed_aborted_{e.error_code}")
        return {"status": "aborted", "code": e.error_code, "reason": e.message}
    except Exception as e:
        logger.error(f"Pipeline execution encountered unexpected error: {e}", exc_info=True)
        save_run_state(PRODUCT, iso_week, doc_section_id, email_draft_id, "failed_unexpected_error")
        return {"status": "failed", "reason": str(e)}

def prune_old_runs(keep_weeks: int = 4):
    """
    Deletes generated output and cleaned files for weeks older than the keep_weeks newest weeks.
    Also prunes logs/audit.jsonl and state/run_state.json.
    """
    import glob
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    outputs_dir = os.path.join(project_root, "data/outputs")
    cleaned_dir = os.path.join(project_root, "data/cleaned")
    
    # 1. Identify all weeks
    pulse_files = glob.glob(os.path.join(outputs_dir, "pulse_*.json"))
    weeks = []
    for pf in pulse_files:
        week = os.path.basename(pf).replace("pulse_", "").replace(".json", "")
        weeks.append(week)
        
    weeks = sorted(weeks)
    if len(weeks) <= keep_weeks:
        return
        
    # Weeks to delete
    to_delete = weeks[:-keep_weeks]
    logger.info(f"Pruning old runs data. Keeping the newest {keep_weeks} weeks. Deleting weeks: {to_delete}")
    
    for week in to_delete:
        # Delete output files
        for fpath in [
            os.path.join(outputs_dir, f"pulse_{week}.json"),
            os.path.join(outputs_dir, f"fee_explainer_{week}.json"),
            os.path.join(cleaned_dir, f"themes_metadata_{week}.json"),
            os.path.join(cleaned_dir, f"quotes_{week}.json"),
            os.path.join(cleaned_dir, f"embeddings_{week}.npy")
        ]:
            if os.path.exists(fpath):
                try:
                    os.remove(fpath)
                    logger.info(f"Pruned file: {os.path.basename(fpath)}")
                except Exception as e:
                    logger.warning(f"Failed to prune file {fpath}: {e}")
                    
    # 2. Prune logs/audit.jsonl
    audit_file = os.path.join(project_root, "logs/audit.jsonl")
    if os.path.exists(audit_file):
        kept_weeks_set = set(weeks[-keep_weeks:])
        pruned_lines = []
        try:
            with open(audit_file, "r", encoding="utf-8") as f:
                for line in f:
                    line_str = line.strip()
                    if not line_str:
                        continue
                    try:
                        entry = json.loads(line_str)
                        if entry.get("iso_week") in kept_weeks_set:
                            pruned_lines.append(line_str)
                    except json.JSONDecodeError:
                        continue
            with open(audit_file, "w", encoding="utf-8") as f:
                for line in pruned_lines:
                    f.write(line + "\n")
            logger.info(f"Pruned logs/audit.jsonl to keep only weeks: {kept_weeks_set}")
        except Exception as e:
            logger.warning(f"Failed to prune audit log file: {e}")
            
    # 3. Prune state/run_state.json
    state_file = os.path.join(project_root, "state/run_state.json")
    if os.path.exists(state_file):
        kept_weeks_set = set(weeks[-keep_weeks:])
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                state_data = json.load(f)
            modified = False
            for product in list(state_data.keys()):
                for week in list(state_data[product].keys()):
                    if week not in kept_weeks_set:
                        del state_data[product][week]
                        modified = True
            if modified:
                with open(state_file, "w", encoding="utf-8") as f:
                    json.dump(state_data, f, indent=2)
                logger.info("Pruned state/run_state.json")
        except Exception as e:
            logger.warning(f"Failed to prune run state file: {e}")

if __name__ == "__main__":
    result = run_pipeline()
    if result.get("status") in ("failed", "aborted"):
        import sys
        sys.exit(1)
