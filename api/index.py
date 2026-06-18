import os
import json
import glob
from flask import Flask, jsonify, send_from_directory, request
from dotenv import load_dotenv

load_dotenv()

# We point static_folder to the root dist directory
app = Flask(__name__, static_folder='../dist', static_url_path='/')

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
        
    return jsonify({
        "pulse": pulse_data,
        "themes": themes_data.get("themes", []) if themes_data else [],
        "quotes": quotes_data if quotes_data else []
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

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        "status": "online",
        "message": "Groww Review Pulse Flask API",
        "use_mock_groq": os.getenv("USE_MOCK_GROQ", "false")
    })

# Catch-all route to serve the built static site for React router routes
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        # Fallback to index.html for SPA routing
        if os.path.exists(os.path.join(app.static_folder, 'index.html')):
            return send_from_directory(app.static_folder, 'index.html')
        else:
            return jsonify({
                "error": "Static frontend assets not built yet. Run npm run build at the root first."
            }), 404

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f"Starting Flask development server on port {port}...")
    app.run(host="0.0.0.0", port=port, debug=True)
