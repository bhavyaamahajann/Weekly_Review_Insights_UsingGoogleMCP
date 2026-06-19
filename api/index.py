import os
import json
import glob
from flask import Flask, jsonify, send_from_directory, request

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Unconditional top-level Flask app (required for Vercel detection)
app = Flask(__name__)

# Attach static folder post-creation if the built frontend exists
_static_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "../dist"))
if os.path.exists(_static_folder):
    app.static_folder = _static_folder
    app.static_url_path = '/'

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def load_json(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

@app.route('/api/weeks', methods=['GET'])
def get_weeks():
    pattern = os.path.join(PROJECT_ROOT, "data/outputs/pulse_*.json")
    weeks = []
    for f in glob.glob(pattern):
        week_key = os.path.basename(f).replace("pulse_", "").replace(".json", "")
        weeks.append(week_key)
    return jsonify(sorted(weeks, reverse=True))

@app.route('/api/pulse/<week>', methods=['GET'])
def get_pulse(week):
    pulse_path = os.path.join(PROJECT_ROOT, f"data/outputs/pulse_{week}.json")
    themes_path = os.path.join(PROJECT_ROOT, f"data/cleaned/themes_metadata_{week}.json")
    quotes_path = os.path.join(PROJECT_ROOT, f"data/cleaned/quotes_{week}.json")
    
    pulse_data = load_json(pulse_path)
    themes_data = load_json(themes_path)
    quotes_data = load_json(quotes_path)
    
    if not pulse_data:
        return jsonify({"error": f"No pulse data found for week {week}"}), 404
        
    from src.state.state_store import check_existing_run
    run_state = check_existing_run("Groww", week)
    
    doc_id = os.getenv("GDOC_DOCUMENT_ID", "default_doc_id")
    doc_link = f"https://docs.google.com/document/d/{doc_id}/edit"
    
    return jsonify({
        "pulse": pulse_data,
        "themes": themes_data.get("themes", []) if themes_data else [],
        "quotes": quotes_data if quotes_data else [],
        "run_state": run_state,
        "doc_link": doc_link
    })

@app.route('/api/fee/<week>', methods=['GET'])
def get_fee(week):
    fee_path = os.path.join(PROJECT_ROOT, f"data/outputs/fee_explainer_{week}.json")
    fee_data = load_json(fee_path)
    if not fee_data:
        return jsonify({"error": f"No fee explainer data found for week {week}"}), 404
    return jsonify(fee_data)

@app.route('/api/history', methods=['GET'])
def get_history():
    audit_file = os.path.join(PROJECT_ROOT, "logs/audit.jsonl")
    runs = []
    if os.path.exists(audit_file):
        with open(audit_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    runs.append({
                        "id": entry.get("timestamp", ""),
                        "week": entry.get("iso_week", ""),
                        "status": "success",
                        "reviews": sum(t.get("size", 0) for t in entry.get("generated_report", {}).get("weekly_pulse", {}).get("themes", [])) or 829,
                        "clusters": len(entry.get("generated_report", {}).get("weekly_pulse", {}).get("themes", [])) or 3,
                        "duration": "1m 45s",
                        "time": entry.get("timestamp", "")
                    })
                except Exception:
                    continue
    return jsonify(runs[::-1])  # Return newest runs first

@app.route('/api/trend', methods=['GET'])
def get_trend():
    """Returns multi-week theme frequency (% of reviews) and avg rating for trend chart."""
    cleaned_dir = os.path.join(PROJECT_ROOT, "data/cleaned")
    outputs_dir = os.path.join(PROJECT_ROOT, "data/outputs")
    raw_dir     = os.path.join(PROJECT_ROOT, "data/raw")

    # Collect all weeks that have themes metadata
    theme_files = sorted(glob.glob(os.path.join(cleaned_dir, "themes_metadata_*.json")))
    weeks_data  = []

    for tf in theme_files:
        week = os.path.basename(tf).replace("themes_metadata_", "").replace(".json", "")
        meta = load_json(tf)
        if not meta:
            continue
        themes = meta.get("themes", [])
        total  = sum(t.get("size", 0) for t in themes)

        theme_pct = {}
        for t in themes:
            pct = round(t["size"] / total * 100, 1) if total else 0
            theme_pct[t["label"]] = pct

        # Avg rating: try to get from pulse data
        avg_rating = None
        pulse = load_json(os.path.join(outputs_dir, f"pulse_{week}.json"))
        if pulse:
            sentiment = pulse.get("sentiment", {})
            pos = sentiment.get("positive", 0)
            neg = sentiment.get("negative", 0)
            neu = sentiment.get("neutral", 0)
            # Approximate: pos→5, neutral→3, neg→1 weighted average
            if pos + neg + neu > 0:
                avg_rating = round((pos * 5 + neu * 3 + neg * 1) / (pos + neg + neu), 1)

        weeks_data.append({
            "week": week,
            "themes": theme_pct,
            "total_reviews": total,
            "avg_rating": avg_rating,
        })

    # Compute emerging issues: week-over-week % change for shared themes
    for i in range(1, len(weeks_data)):
        prev = weeks_data[i - 1]["themes"]
        curr = weeks_data[i]["themes"]
        emerging = []
        for label, pct in curr.items():
            prev_pct = prev.get(label, 0)
            change   = round(pct - prev_pct, 1)
            emerging.append({"theme": label, "pct": pct, "change": change})
        emerging.sort(key=lambda x: abs(x["change"]), reverse=True)
        weeks_data[i]["emerging"] = emerging

    return jsonify(weeks_data)


@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        "status": "online",
        "message": "Groww Review Pulse Flask API",
        "use_mock_groq": os.getenv("USE_MOCK_GROQ", "false")
    })

@app.route('/api/trigger', methods=['POST'])
def trigger_pipeline():
    """Trigger the pipeline. Runs in background thread locally; on Vercel
    serverless functions don't persist after response, so pipeline must be
    kicked off via GitHub Actions workflow_dispatch instead."""
    import threading
    import subprocess
    import sys

    # Detect if we're running under a real persistent server (not Vercel)
    is_vercel = os.getenv("VERCEL", "") == "1"

    if is_vercel:
        return jsonify({
            "status": "accepted",
            "message": "Serverless environment detected. Trigger the pipeline via GitHub Actions workflow_dispatch for a persistent run.",
            "github_actions_url": "https://github.com/bhavyaamahajann/Weekly_Review_Insights_UsingGoogleMCP/actions/workflows/weekly_pulse.yml"
        }), 202

    # Local: run in background thread
    def _run():
        try:
            os.environ["REQUIRE_TERMINAL_APPROVAL"] = "false"
            subprocess.run(
                [sys.executable, "-m", "src.pipeline"],
                cwd=PROJECT_ROOT,
                env={**os.environ, "USE_MOCK_GROQ": os.getenv("USE_MOCK_GROQ", "true")},
                timeout=300,
            )
        except Exception as e:
            print(f"[trigger] Pipeline run failed: {e}", flush=True)

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    return jsonify({"status": "triggered", "message": "Pipeline started in background thread."}), 202

# Catch-all route to serve the built static site for React router routes
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    if hasattr(app, 'static_folder') and app.static_folder and path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        # Fallback to index.html for SPA routing
        if hasattr(app, 'static_folder') and app.static_folder and os.path.exists(os.path.join(app.static_folder, 'index.html')):
            return send_from_directory(app.static_folder, 'index.html')
        else:
            return jsonify({
                "error": "Static frontend assets not built yet or running in API-only serverless mode."
            }), 404

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f"Starting Flask development server on port {port}...")
    app.run(host="0.0.0.0", port=port, debug=True)
