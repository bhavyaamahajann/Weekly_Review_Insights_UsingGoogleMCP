# Phase-Wise Implementation Plan
## Groww — Weekly Product Review Pulse & Fee Explainer

---

## Overview

This plan organizes the full system build into **8 sequential phases**, from project scaffolding to final delivery. Each phase has clear inputs, outputs, tasks, file targets, dependencies, and acceptance criteria. The plan is designed so that each phase is independently testable before proceeding to the next.

| Phase | Name | Focus Area | Est. Effort |
|---|---|---|---|
| **Phase 1** | Project Scaffolding & Environment Setup | Repo structure, dependencies, config | 0.5 day |
| **Phase 2** | Data Ingestion & Cleaning Pipeline | Review fetching, cleaning, PII scrubbing | 1 day |
| **Phase 3** | Embedding, Clustering & Quote Extraction | BAAI embeddings, k-means, verbatim quotes | 1.5 days |
| **Phase 4** | LLM Analysis via Groq | Pulse generation, fee explainer, prompt engineering | 1 day |
| **Phase 5** | MCP Delivery & Approval Gates | Google Doc append, Gmail draft via MCP | 1.5 days |
| **Phase 6** | State Management, Audit Logging & Final Wiring | Idempotency, audit trail, end-to-end test | 0.5 day |
| **Phase 7** | Scheduler | APScheduler weekly cron, manual trigger, run history | 1 day |
| **Phase 8** | Dashboard UI | Streamlit dashboard — themes, pulse, audit history | 1.5 days |

---

## Phase 1 — Project Scaffolding & Environment Setup

### Goal
Establish the project directory structure, install all dependencies (including language filters), and configure credentials so every subsequent phase can plug in cleanly.

### Directory Structure

```
groww-review-pulse/
│
├── docs/                          # Project documentation
│   ├── problemstatement.txt
│   ├── context.md
│   ├── architecture.md
│   ├── edge_cases.md
│   └── implementation_plan.md
│
├── src/
│   ├── ingestion/
│   │   └── fetch_reviews.py       # Play Store scraper (master sync)
│   │
│   ├── processing/
│   │   ├── cleaner.py             # De-dup, PII scrub, strict English/emoji filter
│   │   ├── embedder.py            # BAAI/bge-large-en-v1.5 embedding
│   │   ├── clusterer.py           # k-means / DBSCAN clustering
│   │   └── quote_extractor.py     # Verbatim quote extraction & validation
│   │
│   ├── analysis/
│   │   ├── pulse_generator.py     # Groq LLM — weekly pulse
│   │   └── fee_explainer.py       # Groq LLM — fee explanation
│   │
│   ├── delivery/
│   │   ├── approval_gates.py      # Gate 1–4 approval flow
│   │   ├── gdoc_mcp.py            # MCP action: Google Doc append
│   │   └── gmail_mcp.py           # MCP action: Gmail draft creation
│   │
│   ├── state/
│   │   ├── state_store.py         # Idempotency state management
│   │   └── audit_logger.py        # Audit log writer/reader
│   │
│   ├── scheduler/
│   │   ├── scheduler.py           # APScheduler weekly cron job
│   │   └── trigger.py             # Manual trigger CLI / HTTP endpoint
│   │
│   ├── dashboard/
│   │   ├── app.py                 # Streamlit dashboard entry point
│   │   ├── pages/
│   │   │   ├── weekly_pulse.py    # Pulse viewer page
│   │   │   ├── fee_explainer.py   # Fee explainer viewer page
│   │   │   └── audit_history.py   # Run history & audit log page
│   │   └── components/
│   │       ├── theme_chart.py     # Theme distribution bar chart
│   │       ├── quote_card.py      # Quote display card component
│   │       └── sentiment_gauge.py # Sentiment donut chart
│   │
│   └── pipeline.py                # Main orchestrator — runs full flow
│
├── data/
│   ├── raw/
│   │   ├── reviews.csv            # Master raw actual reviews file
│   │   └── reviews.json           # Master raw actual reviews JSON
│   ├── cleaned/
│   │   ├── reviews_clean.csv      # Master cleaned normalized reviews file
│   │   └── reviews_clean.json     # Master cleaned normalized reviews JSON
│   └── outputs/                   # Generated pulse + fee explainer JSONs
│
├── state/
│   └── run_state.json             # Idempotency state store
│
├── logs/
│   ├── audit.jsonl                # Append-only audit log
│   └── scheduler.log              # Scheduler run logs
│
├── tests/
│   ├── test_cleaner.py
│   ├── test_embedder.py
│   ├── test_clusterer.py
│   ├── test_quote_extractor.py
│   ├── test_pulse_generator.py
│   ├── test_fee_explainer.py
│   └── test_scheduler.py
│
├── .env                           # API keys (Groq, MCP config, scraper rules)
├── .env.example                   # Template for .env
├── requirements.txt               # All Python dependencies
└── README.md
```

### Dependencies (`requirements.txt`)

```
# Review Ingestion
google-play-scraper>=1.2.4

# NLP & Embeddings
sentence-transformers>=2.7.0       # Runs BAAI/bge-large-en-v1.5 locally
torch>=2.0.0                       # Required by sentence-transformers

# Clustering
scikit-learn>=1.4.0                # k-means, DBSCAN

# LLM via Groq
groq>=0.9.0                        # Official Groq Python SDK

# PII Scrubbing
presidio-analyzer>=2.2.0
presidio-anonymizer>=2.2.0

# Utilities & Filters
python-dotenv>=1.0.0
pandas>=2.2.0
numpy>=1.26.0
tqdm>=4.66.0
langdetect>=1.0.9                  # Language identification
ftfy>=6.1.0                        # Encoding fixer

# MCP
mcp>=1.0.0                         # Model Context Protocol SDK

# Scheduler (Phase 7)
APScheduler>=3.10.0                # Cron-based pipeline scheduler
Flask>=3.0.0                       # Lightweight HTTP trigger endpoint

# Dashboard UI (Phase 8)
streamlit>=1.35.0                  # Dashboard framework
plotly>=5.22.0                     # Interactive charts
altair>=5.3.0                      # Declarative charts for Streamlit
```

### Environment Variables (`.env`)

```
GROQ_API_KEY=your_groq_api_key_here
MCP_GDOC_SERVER_URL=https://bhavyamcpserver.up.railway.app
MCP_GMAIL_SERVER_URL=https://bhavyamcpserver.up.railway.app
GDOC_DOCUMENT_ID=your_google_doc_id
GMAIL_RECIPIENT=team@groww.in

# Scraper Configurations
MAX_REVIEWS_THRESHOLD=5000         # Upper limit of reviews to fetch
REVIEW_WINDOW_WEEKS=10             # Time window in weeks (rolling)

# Scheduler (Phase 7)
SCHEDULER_DAY_OF_WEEK=mon          # Day to run weekly pipeline (mon–sun)
SCHEDULER_HOUR=8                   # Hour to run (24h, IST)
SCHEDULER_TRIGGER_PORT=5050        # Port for manual HTTP trigger

# Dashboard (Phase 8)
DASHBOARD_PORT=8501                # Streamlit default port
```

### Tasks

- [x] Create full directory and file skeleton
- [x] Create `requirements.txt` and install all packages
- [x] Create `.env` and `.env.example` with all required keys
- [x] Verify `sentence-transformers` can load `BAAI/bge-large-en-v1.5` locally
- [x] Verify Groq API key is valid with a simple test call
- [x] Confirm MCP servers are accessible at configured URLs (verified config and connection check)

### Acceptance Criteria
- `python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-large-en-v1.5')"` runs without error
- `python -c "from groq import Groq"` imports successfully
- Directory structure matches the layout above

---

## Phase 2 — Data Ingestion & Cleaning Pipeline

### Goal
Fetch raw Google Play Store reviews for Groww, synchronizing them incrementally into a single master raw file, and clean/sanitize them into a single master clean corpus.

### Modules

#### `src/ingestion/fetch_reviews.py`

**Responsibilities:**
- Use `google-play-scraper` to fetch public reviews for Groww (`com.nextbillion.groww`).
- Filter reviews by rolling window (`REVIEW_WINDOW_WEEKS`).
- Target up to `MAX_REVIEWS_THRESHOLD` reviews.
- **Incremental sync**: Scrape starting from page 1 and stop immediately when an existing review is encountered in the master file or the date boundary is reached.
- **Schema Mapping**: Retains only: `review_text`, `rating`, `thumbs_up_count`, `app_version`, and `source`.
- Store output as `data/raw/reviews.csv` and `data/raw/reviews.json`.

---

#### `src/processing/cleaner.py`

**Responsibilities:**
- **De-duplication:** SHA-256 hash de-duplication of review texts.
- **Strict Emoji Presence Check:** Discard any review containing any emoji (matched via unicode block pattern).
- **Word Count Check:** Discard any review containing fewer than 8 words.
- **Strict English Check:** Identify and drop non-English reviews using `langdetect` + strict Hinglish vocabulary stopword matching.
- **PII Scrubbing:** Anonymize personal entities (`PERSON`, `EMAIL_ADDRESS`, `PHONE_NUMBER`, `LOCATION`, `URL`) using Presidio.
- **PII Whitelisting:** Protect domain-specific terms (e.g. `Groww`, `NIFTY`, `SIP`, `NAV`, `UPI`) from false-positive redaction.
- **Text Normalization:** Fix malformed unicode (via `ftfy`) and strip extra whitespace.
- Store output as `data/cleaned/reviews_clean.csv` and `data/cleaned/reviews_clean.json`.

---

### Pipeline Flow

```
fetch_reviews.py (incremental sync)
    → data/raw/reviews.csv / json (master raw)
        → cleaner.py (PII & strict formatting)
            → data/cleaned/reviews_clean.csv / json (master cleaned)
```

### Tasks

- [x] Implement `fetch_reviews.py` — incremental master reviews sync
- [x] Implement de-duplication using SHA-256 hash of review text
- [x] Implement strict emoji presence check
- [x] Implement word count filter (< 8 words)
- [x] Implement strict English language check (Indic + Hinglish filters)
- [x] Implement PII scrubbing using Presidio and keyword whitelisting
- [x] Save master output to data/raw/ and data/cleaned/ as CSV & JSON
- [x] Write `tests/test_cleaner.py` with unit tests for each cleaning filter

### Acceptance Criteria
- Raw master file updated with correct minimal schema
- Clean master file has zero duplicates, zero emojis, zero reviews < 8 words
- Strictly 100% English reviews remain (no Indic scripts or Hinglish)
- No PII detected in clean review texts post-scrubbing

---

## Phase 3 — Embedding, Clustering & Quote Extraction

### Goal
Convert the clean review corpus into dense vector embeddings, group them into themes, rank the top 3, and extract 3 verbatim, validated user quotes.

### Modules

#### `src/processing/embedder.py`

**Model:** `BAAI/bge-large-en-v1.5`  
**Dimensions:** 1024  
**Runtime:** Local via `sentence-transformers` (no external API)

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("BAAI/bge-large-en-v1.5")

def embed_reviews(texts: list[str]) -> np.ndarray:
    """Returns (N, 1024) embedding matrix."""
    return model.encode(texts, normalize_embeddings=True, show_progress_bar=True)
```

**Output:** Embedding matrix saved as `data/cleaned/embeddings_YYYY-WNN.npy`

---

#### `src/processing/clusterer.py`

**Algorithm:** k-means (primary)  
**Max clusters:** 5  
**Surfaces:** Top 3 clusters by size + silhouette score

```python
def cluster_reviews(embeddings, n_clusters=5) -> dict:
    """
    Returns cluster assignments, centroids, and cluster sizes.
    Auto-selects optimal k using silhouette score for k in [3, n_clusters].
    (k=2 is excluded because it splits strictly by sentiment, failing to yield 
     the required 3 distinct topic-based themes.)
    """
```

**Theme Labeling:** After clustering, send the top 3 clusters' top 5 reviews to Groq sequentially (with a 2-second delay between calls to avoid hitting the 12K TPM and 30 RPM limits) to generate a 2–4 word theme label (e.g., "App Performance", "Withdrawal Experience"). To conserve token usage (100K daily limit):
- Only label the top 3 clusters by size (since we only surface the top 3 themes).
- Truncate each review to a maximum of 150 characters before sending.

**Output:**
```json
{
  "themes": [
    { "id": 0, "label": "App Performance", "size": 87, "review_indices": [...] },
    { "id": 1, "label": "Withdrawal Experience", "size": 62, "review_indices": [...] },
    { "id": 2, "label": "Customer Support", "size": 48, "review_indices": [...] }
  ]
}
```

---

#### `src/processing/quote_extractor.py`

**Responsibilities:**
- For each of the top 3 themes, select the review closest to the cluster centroid
- Extract the most representative sentence from that review as the quote
- **Validate:**
  - Quote substring exists verbatim in the source `review_text`
  - Quote passes PII check (re-run Presidio scan on quote text)
  - Quote is between 20–200 characters (readable length)

```python
def extract_quotes(clean_reviews_df, themes, embeddings) -> list[dict]:
    """
    Returns list of 3 validated quote dicts:
    [{ "theme": str, "quote": str, "source_review_id": str }]
    """
```

---

### Tasks

- [x] Implement `embedder.py` — load `BAAI/bge-large-en-v1.5`, embed all reviews, save `.npy`
- [x] Implement `clusterer.py` — k-means with silhouette-based k selection
- [x] Implement Groq-based theme label generation for each cluster
- [x] Implement `quote_extractor.py` — centroid proximity + verbatim validation
- [x] Add PII re-check on extracted quotes
- [x] Write `tests/test_embedder.py`, `tests/test_clusterer.py`, `tests/test_quote_extractor.py`

### Acceptance Criteria
- Embeddings have shape `(N, 1024)` with normalized vectors
- Exactly 3 theme clusters returned with human-readable labels
- Exactly 3 quotes returned, each confirmed verbatim in the source review CSV
- No PII detected in any extracted quote

---

## Phase 4 — LLM Analysis via Groq

### Goal
Use Groq's ultra-fast inference API to generate the weekly pulse summary, action recommendations, and the Mutual Fund Exit Load fee explainer. All prompts are structured for deterministic, schema-compliant JSON output.

### Groq Client Setup & Rate Limit Strategy

For `llama-3.3-70b-versatile`, the API limits are:
- **RPM:** 30
- **RPD:** 1K
- **TPM:** 12K (very strict)
- **TPD:** 100K (very strict)

To respect these limits, the system implements:
- **Sequential Calls with Delay:** Introduce a 2-second sleep between API calls.
- **Strict Token Budgeting:** Truncate review inputs for theme labeling to 150 characters; keep system and user prompts minimal.
- **Model Fallback:** Fall back to `llama-3.1-8b-instant` (higher limits: 500K TPD, 14.4K RPD) if rate limits or daily quotas are exceeded.
- **Exponential Backoff:** Catch `groq.RateLimitError` and retry with backoff.

```python
from groq import Groq

client = Groq(api_key=os.environ["GROQ_API_KEY"])

PRIMARY_MODEL   = "llama-3.3-70b-versatile"
FALLBACK_MODEL  = "llama-3.1-8b-instant"
```

---

### Module: `src/analysis/pulse_generator.py`

**Inputs:** Top 3 themes (labels + sizes), 3 validated quotes, cluster metadata  
**Output:** Structured weekly pulse JSON

**System Prompt:**
```
You are a product analyst generating a weekly customer feedback summary for Groww.
Respond ONLY with valid JSON matching the schema provided.
Do NOT add any text outside the JSON block.
```

**User Prompt Template:**
```
Generate a weekly product pulse for Groww based on the following data:

Top Themes:
1. {theme_1} ({size_1} reviews)
2. {theme_2} ({size_2} reviews)
3. {theme_3} ({size_3} reviews)

Representative Quotes:
- "{quote_1}" (re: {theme_1})
- "{quote_2}" (re: {theme_2})
- "{quote_3}" (re: {theme_3})

Output JSON schema:
{
  "weekly_summary": "<string, ≤250 words>",
  "sentiment": { "positive": <int%>, "negative": <int%>, "neutral": <int%> },
  "action_ideas": ["<idea_1>", "<idea_2>", "<idea_3>"]
}
```

**Validation:** Parse returned JSON; if schema invalid, retry once with FALLBACK_MODEL.

---

### Module: `src/analysis/fee_explainer.py`

**Inputs:** Fee scenario label ("Mutual Fund Exit Load"), source URLs  
**Output:** Structured fee explainer JSON

**System Prompt:**
```
You are a compliance writer for Groww.
Generate a factual, neutral fee explanation. Use ONLY verified facts.
Respond ONLY with valid JSON. Do NOT add recommendations or comparisons.
```

**User Prompt Template:**
```
Generate a fee explainer for: Mutual Fund Exit Load

Rules:
- Maximum 6 bullet points
- Neutral tone, facts only
- Include source references
- Include a "last_checked" date field (today's date)

Output JSON schema:
{
  "scenario": "Mutual Fund Exit Load",
  "bullets": ["<bullet_1>", ..., "<bullet_6>"],
  "sources": ["<source_name_1>", "<source_name_2>"],
  "last_checked": "<Month YYYY>"
}
```

**Validation:** Confirm `bullets` length ≤ 6; retry if invalid JSON.

---

### Tasks

- [x] Implement `pulse_generator.py` with Groq API call + JSON schema validation
- [x] Implement `fee_explainer.py` with Groq API call + bullet count enforcement
- [x] Add model fallback logic (primary → fallback on API error or schema failure)
- [x] Add retry-with-feedback logic for Gate 1 and Gate 2 re-runs
- [x] Save outputs to `data/outputs/pulse_YYYY-WNN.json` and `data/outputs/fee_explainer_YYYY-WNN.json`
- [x] Write `tests/test_pulse_generator.py` and `tests/test_fee_explainer.py`

### Acceptance Criteria
- Weekly pulse JSON produced with `weekly_summary` ≤ 250 words and exactly 3 `action_ideas`
- Fee explainer JSON has ≤ 6 bullets, all factual in tone, with sources and `last_checked` populated
- Both outputs are valid, parseable JSON
- Fallback to `llama-3.1-8b-instant` confirmed when primary model fails or hits limits

---

## Phase 5 — MCP Delivery & Approval Gates

### Goal
Wire up all 4 approval gates and implement the MCP-based Google Doc append and Gmail draft actions. No direct Google API calls. All writes are gated behind explicit user approval. The project integrates with an external, separately deployed MCP server (hosted on Railway) that handles Google Docs and Gmail tools. The backend points to this external server using environment variables (`MCP_GDOC_SERVER_URL` and `MCP_GMAIL_SERVER_URL`).
- `append_to_google_doc(document_id: str, content: str, iso_week: str = None) -> str`: Appends or updates the weekly pulse in Google Docs. Supports idempotency by searching for week markers.
- `create_gmail_draft(recipient: str, subject: str, body: str) -> str`: Creates an email draft in Gmail with the summary and Google Doc link.
- **Simulation Mode**: If Google credentials are not set, writes content to local mock files (`data/outputs/gdoc_simulation.md` and `data/outputs/gmail_simulation.txt`) and returns simulated IDs.

### Module: `src/delivery/approval_gates.py`

Implements an interactive approval loop for each gate:

```python
def approval_gate(gate_number: int, label: str, payload: dict) -> bool:
    """
    Displays the payload to the user in a formatted preview.
    Prompts: [A]pprove / [R]eject / [F]eedback
    Returns True if approved, False if rejected.
    """
```

**Gate Behaviour Summary:**

| Gate | Presents | On Approve | On Reject |
|---|---|---|---|
| Gate 1 | Themes · Quotes · Pulse · Actions | Move to Gate 2 | Re-call `pulse_generator.py` |
| Gate 2 | Fee bullets · Sources · Last Checked | Move to Gate 3 | Re-call `fee_explainer.py` |
| Gate 3 | Full structured payload for Doc append | Call `gdoc_mcp.py` | Abort workflow |
| Gate 4 | Email subject + body preview | Call `gmail_mcp.py` | Stop; log partial completion |

---

### Module: `src/delivery/gdoc_mcp.py`

**MCP Action:** Append structured entry to Google Doc  
**Target Doc:** `Weekly Review Pulse — Groww` (ID from `.env`)

```python
def append_to_gdoc(payload: dict) -> str:
    """
    Sends MCP request to Google Docs MCP server.
    Returns: doc_section_id (str)

    Payload:
    {
      "date": "YYYY-MM-DD",
      "weekly_pulse": "...",
      "fee_scenario": "Mutual Fund Exit Load",
      "explanation_bullets": [...],
      "source_links": [...]
    }
    """
```

**Idempotency Handling:** If `iso_week` already exists in state store, sends an UPDATE request (not INSERT) to the MCP server, targeting the existing `doc_section_id`.

---

### Module: `src/delivery/gmail_mcp.py`

**MCP Action:** Create Gmail draft (never auto-sent)  
**Draft Subject:** `Weekly Pulse + Fee Explainer — Groww`

```python
def create_gmail_draft(pulse_summary: str, fee_summary: str, doc_link: str) -> str:
    """
    Sends MCP request to Gmail MCP server.
    Returns: email_draft_id (str)

    Draft body structure:
    - Weekly Pulse Summary (text)
    - Fee Explainer Summary (text)
    - Link to Google Doc section
    """
```

---

### Tasks

- [x] Connect to external decoupled MCP Server (e.g., `https://bhavyamcpserver.up.railway.app`)
- [x] Implement `approval_gates.py` with formatted terminal display for each gate
- [x] Implement Gate 1 approval loop with re-run trigger for LLM if rejected
- [x] Implement Gate 2 approval loop with re-run trigger for fee explainer if rejected
- [x] Implement `gdoc_mcp.py` — MCP call for Google Doc append
- [x] Implement idempotent update logic in `gdoc_mcp.py` (insert vs update)
- [x] Implement `gmail_mcp.py` — MCP call for Gmail draft creation
- [x] Test Gate 3 rejection path (no doc write should occur)
- [x] Test Gate 4 rejection path (doc written, but no email draft)

### Acceptance Criteria
- Gate 1 and Gate 2 correctly loop back to LLM on rejection
- Gate 3 writes to Google Doc only after user approval; returns valid `doc_section_id`
- Gate 4 creates Gmail draft only after Gate 3 succeeds; never sends email
- Idempotency: re-running updates the existing doc section, does not create a new one

---

## Phase 6 — State Management, Audit Logging & Final Wiring

### Goal
Implement the idempotency state store and audit logger, wire all modules together in the main pipeline orchestrator, and run an end-to-end integration test.

### Module: `src/state/state_store.py`

```python
STATE_FILE = "state/run_state.json"

def check_existing_run(product: str, iso_week: str) -> dict | None:
    """Returns existing state record if found, else None."""

def save_run_state(product: str, iso_week: str, doc_section_id: str, email_draft_id: str, status: str):
    """Upserts the state record for (product, iso_week)."""
```

**State Schema (`state/run_state.json`):**
```json
{
  "Groww": {
    "2026-W23": {
      "doc_section_id": "section_abc123",
      "email_draft_id": "draft_xyz789",
      "status": "completed",
      "last_updated": "2026-06-08T16:00:00Z"
    }
  }
}
```

---

### Module: `src/state/audit_logger.py`

```python
AUDIT_FILE = "logs/audit.jsonl"

def log_run(product, iso_week, generated_report, doc_section_id, email_draft_id):
    """Appends a complete audit entry to logs/audit.jsonl."""

def query_log(product: str, iso_week: str) -> dict | None:
    """Searches audit log for a specific (product, iso_week) entry."""
```

---

### Main Orchestrator: `src/pipeline.py`

```python
def run_pipeline():
    # 1. Compute ISO week
    # 2. Check idempotency state
    # 3. Fetch & clean reviews  (Phase 2)
    # 4. Embed, cluster, extract quotes  (Phase 3)
    # 5. Generate pulse via Groq  (Phase 4)
    # 6. Generate fee explainer via Groq  (Phase 4)
    # 7. Gate 1: Pulse approval
    # 8. Gate 2: Fee explainer approval
    # 9. Gate 3: Google Doc append via MCP
    # 10. Gate 4: Gmail draft creation via MCP
    # 11. Save state + write audit log

if __name__ == "__main__":
    run_pipeline()
```

---

### Tasks

- [ ] Implement `state_store.py` with upsert and lookup logic
- [ ] Implement `audit_logger.py` with append-only JSONL writer
- [ ] Implement `pipeline.py` — wire all phases in sequence
- [ ] Add ISO week computation at pipeline start
- [ ] Add idempotency check at pipeline start (branch to update mode if week exists)
- [ ] Run end-to-end integration test with real reviews
- [ ] Verify audit log entry is complete after each run
- [ ] Verify re-run of same week triggers update, not duplicate

### Acceptance Criteria
- Full pipeline runs end-to-end with no errors
- State file updated correctly after each run
- Audit log contains a complete, valid JSON entry for each run
- Re-running for same ISO week updates (not duplicates) the Google Doc and Gmail draft
- Running `python src/pipeline.py` completes all 4 gates successfully

---

## Phase 7 — Scheduler

### Goal
Automate the weekly pipeline run using a cron-based scheduler. The scheduler triggers `pipeline.py` every Monday at a configured time (default: 8:00 AM IST). A lightweight HTTP endpoint also allows manual on-demand triggering without editing code.

### Module: `src/scheduler/scheduler.py`

**Library:** `APScheduler` (Advanced Python Scheduler)  
**Trigger Type:** `CronTrigger` — runs once per week on a configurable day/hour

```python
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from src.pipeline import run_pipeline
import logging

logging.basicConfig(
    filename="logs/scheduler.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

scheduler = BlockingScheduler(timezone="Asia/Kolkata")

@scheduler.scheduled_job(
    CronTrigger(
        day_of_week=os.getenv("SCHEDULER_DAY_OF_WEEK", "mon"),
        hour=int(os.getenv("SCHEDULER_HOUR", 8)),
        minute=0
    )
)
def weekly_job():
    logging.info("Scheduler triggered: starting weekly pipeline run")
    try:
        run_pipeline()
        logging.info("Pipeline completed successfully")
    except Exception as e:
        logging.error(f"Pipeline failed: {e}")

if __name__ == "__main__":
    logging.info("Scheduler started. Next run: Monday 08:00 IST")
    scheduler.start()
```

---

### Module: `src/scheduler/trigger.py`

**Purpose:** Expose a lightweight Flask HTTP endpoint for manual pipeline triggering (useful for demos and ad-hoc runs).  
**Endpoint:** `POST /trigger`

```python
from flask import Flask, jsonify
from src.pipeline import run_pipeline
import threading

app = Flask(__name__)

@app.route("/trigger", methods=["POST"])
def trigger_pipeline():
    """Manually trigger the pipeline in a background thread."""
    thread = threading.Thread(target=run_pipeline)
    thread.start()
    return jsonify({"status": "triggered", "message": "Pipeline run started"}), 202

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(port=int(os.getenv("SCHEDULER_TRIGGER_PORT", 5050)))
```

**Usage:**
```bash
# Start the scheduler (blocking)
python src/scheduler/scheduler.py

# Start the manual trigger endpoint
python src/scheduler/trigger.py

# Manually trigger a run
curl -X POST http://localhost:5050/trigger
```

---

### Scheduler Behaviour

| Scenario | Behaviour |
|---|---|
| Weekly cron fires | Calls `run_pipeline()` → full pipeline including approval gates |
| Same ISO week already in state | Idempotency kicks in → update mode, no duplicate |
| Pipeline raises an exception | Logged to `logs/scheduler.log`; next scheduled run unaffected |
| Manual trigger via HTTP | Pipeline runs in background thread; immediate 202 response returned |
| Scheduler downtime / missed run | Next cron trigger runs normally; missed runs are NOT auto-retried |

---

### Scheduler Log Format (`logs/scheduler.log`)

```
2026-06-09 08:00:01 [INFO] Scheduler triggered: starting weekly pipeline run
2026-06-09 08:04:22 [INFO] Pipeline completed successfully
2026-06-16 08:00:01 [INFO] Scheduler triggered: starting weekly pipeline run
2026-06-16 08:01:05 [ERROR] Pipeline failed: Groq API timeout
```

---

### Tasks

- [ ] Implement `scheduler.py` with `APScheduler` cron job wired to `run_pipeline()`
- [ ] Make `SCHEDULER_DAY_OF_WEEK` and `SCHEDULER_HOUR` configurable via `.env`
- [ ] Implement `trigger.py` Flask app with `POST /trigger` and `GET /health` endpoints
- [ ] Add structured logging to `logs/scheduler.log` for every run (start, success, failure)
- [ ] Write `tests/test_scheduler.py` — mock `run_pipeline` and verify cron fires correctly
- [ ] Test manual trigger via `curl -X POST http://localhost:5050/trigger`
- [ ] Test that missed-run idempotency works (same week triggered twice → update mode)

### Acceptance Criteria
- Scheduler starts and logs "Scheduler started" message
- Cron fires on the configured day/hour (verify with a 1-minute test interval)
- `POST /trigger` returns `202` and pipeline starts in background thread
- All scheduler events (start, success, error) appear in `logs/scheduler.log`
- Double-triggering the same ISO week does not create duplicate Google Doc entries

---

## Phase 8 — Dashboard UI

### Goal
Build a Streamlit-based internal dashboard that allows Product, Support, and Leadership teams to visually explore the latest weekly pulse, fee explainer, and full run history — without touching the command line.

### Framework
**Streamlit** — chosen for rapid internal dashboard development with no frontend build step.  
**Charts:** Plotly for interactive visualizations.

---

### App Entry Point: `src/dashboard/app.py`

```python
import streamlit as st

st.set_page_config(
    page_title="Groww Review Pulse Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar navigation
st.sidebar.title("📊 Groww Pulse")
page = st.sidebar.radio(
    "Navigate",
    ["Weekly Pulse", "Fee Explainer", "Audit History", "Run Pipeline"]
)
```

---

### Page: `src/dashboard/pages/weekly_pulse.py`

**Purpose:** Display the latest (or selected) week's pulse report.  
**Data Source:** `data/outputs/pulse_YYYY-WNN.json`

**UI Sections:**

| Section | Component | Details |
|---|---|---|
| **Header** | Title + ISO Week badge | "Week 23, 2026" |
| **Top Themes** | Horizontal bar chart (Plotly) | Theme label vs. review count |
| **Sentiment** | Donut chart (Plotly) | Positive / Negative / Neutral % |
| **Real User Quotes** | 3 styled quote cards | Theme tag + verbatim quote text |
| **Weekly Summary** | Markdown text block | ≤250-word stakeholder narrative |
| **Action Ideas** | Numbered list with icons | 3 actionable recommendations |
| **Week Selector** | Sidebar dropdown | Browse past weeks from state store |

---

### Page: `src/dashboard/pages/fee_explainer.py`

**Purpose:** Display the Mutual Fund Exit Load fee explainer.  
**Data Source:** `data/outputs/fee_explainer_YYYY-WNN.json`

**UI Sections:**

| Section | Component | Details |
|---|---|---|
| **Header** | Title + "Last Checked" badge | "Mutual Fund Exit Load — June 2026" |
| **Bullets** | Styled bullet list | Max 6 neutral fact bullets |
| **Official Sources** | Clickable link list | Named sources with URLs |
| **Disclaimer** | Info callout box | "Facts only. Refer to latest scheme documents." |

---

### Page: `src/dashboard/pages/audit_history.py`

**Purpose:** Show a full table of all pipeline runs with their status and links.  
**Data Source:** `logs/audit.jsonl`

**UI Sections:**

| Section | Component | Details |
|---|---|---|
| **Run History Table** | Streamlit dataframe | ISO Week · Timestamp · Status · Doc ID · Draft ID |
| **Row Expander** | Expandable row | Click to see full pulse + fee explainer for that week |
| **Status Badges** | Colored tags | ✅ completed / ⚠️ partial / ❌ failed |
| **Search & Filter** | Text input + date range | Filter by week or status |

---

### Page: Run Pipeline (inline trigger)

**Purpose:** Allow authorized users to trigger a pipeline run directly from the dashboard.  
**Backend:** Calls `POST http://localhost:5050/trigger` (Phase 7 Flask endpoint)

```python
if st.button("▶ Run Pipeline Now"):
    response = requests.post("http://localhost:5050/trigger")
    if response.status_code == 202:
        st.success("Pipeline triggered! Check Audit History for updates.")
    else:
        st.error("Failed to trigger pipeline. Is the scheduler running?")
```

---

### Reusable Components

#### `src/dashboard/components/theme_chart.py`
```python
def render_theme_chart(themes: list[dict]):
    """Renders a Plotly horizontal bar chart of theme labels vs. review counts."""
```

#### `src/dashboard/components/quote_card.py`
```python
def render_quote_card(theme: str, quote: str):
    """Renders a styled Streamlit card with theme badge and verbatim quote."""
```

#### `src/dashboard/components/sentiment_gauge.py`
```python
def render_sentiment_donut(positive: int, negative: int, neutral: int):
    """Renders a Plotly donut chart for sentiment distribution."""
```

---

### Dashboard Data Flow

```
state/run_state.json          → Week selector dropdown
data/outputs/pulse_*.json     → Weekly Pulse page
data/outputs/fee_*.json       → Fee Explainer page
logs/audit.jsonl              → Audit History page
Flask /trigger endpoint       → Run Pipeline button
```

---

### Running the Dashboard

```bash
# Start the manual trigger backend (Phase 7)
python src/scheduler/trigger.py &

# Launch the Streamlit dashboard
streamlit run src/dashboard/app.py --server.port 8501
```

Dashboard accessible at: `http://localhost:8501`

---

### Tasks

- [ ] Implement `app.py` — Streamlit entry point with sidebar navigation
- [ ] Implement `weekly_pulse.py` — theme bar chart, sentiment donut, quote cards, summary, actions
- [ ] Implement `fee_explainer.py` — bullet list, sources, disclaimer callout
- [ ] Implement `audit_history.py` — run history table with expandable rows and status badges
- [ ] Implement `Run Pipeline` page — button that calls Phase 7 trigger endpoint
- [ ] Implement `theme_chart.py`, `quote_card.py`, `sentiment_gauge.py` components
- [ ] Add week selector to sidebar (populated from `state/run_state.json`)
- [ ] Handle empty state gracefully (no runs yet → friendly empty state message)
- [ ] Test dashboard with at least 2 weeks of audit data

### Acceptance Criteria
- Dashboard launches at `http://localhost:8501` with no errors
- Weekly Pulse page renders theme chart, sentiment donut, 3 quote cards, summary, and 3 action ideas
- Fee Explainer page renders all bullets, sources, and last-checked date
- Audit History table shows all past runs with correct status badges
- Run Pipeline button successfully calls the trigger endpoint and shows a success toast
- Week selector correctly loads data for any previously completed run

---

## Cross-Phase Checklist

### Security & Privacy
- [ ] `.env` is in `.gitignore`
- [ ] PII scrubbing runs before any data leaves the cleaning pipeline
- [ ] No raw PII appears in audit logs, state store, or LLM prompts
- [ ] Dashboard run trigger is restricted to localhost (no public exposure)

### Error Handling
- [ ] All external API calls (Groq, MCP) wrapped in try/except with meaningful error messages
- [ ] Groq model fallback (`llama-3.3-70b-versatile` → `llama-3.1-8b-instant`) and rate limit retry backoff implemented
- [ ] Pipeline aborts cleanly if review fetch returns < 50 reviews
- [ ] Scheduler logs all errors without crashing the scheduling loop
- [ ] Dashboard shows friendly empty states when no run data is available

### Testing
- [ ] Unit tests for all processing modules (cleaner, embedder, clusterer, quote extractor)
- [ ] Unit tests for LLM output schema validation
- [ ] Unit test for scheduler cron trigger logic
- [ ] Integration test for full pipeline with sample data
- [ ] Manual UI test: run dashboard with 2+ weeks of mock data

### Deliverables Checklist
- [ ] `data/raw/reviews_sample.csv` — sample of raw reviews
- [ ] `data/outputs/pulse_YYYY-WNN.json` — generated pulse
- [ ] `data/outputs/fee_explainer_YYYY-WNN.json` — generated fee explainer
- [ ] Screenshot: Google Doc append (Gate 3)
- [ ] Screenshot: Gmail draft (Gate 4)
- [ ] Screenshot: Dashboard — Weekly Pulse page
- [ ] Screenshot: Dashboard — Audit History page
- [ ] `logs/audit.jsonl` — audit trail
- [ ] `logs/scheduler.log` — scheduler run history
- [ ] `README.md` — setup, re-run, architecture, MCP gate instructions, dashboard usage

---

## Summary Timeline

```
Week 1
├── Day 1 (AM)  : Phase 1 — Scaffolding & Setup
├── Day 1 (PM)  : Phase 2 — Ingestion & Cleaning
├── Day 2       : Phase 3 — Embedding, Clustering & Quotes
├── Day 3       : Phase 4 — Groq LLM Analysis
├── Day 4       : Phase 5 — MCP Delivery & Approval Gates
└── Day 5       : Phase 6 — State, Audit & End-to-End Test

Week 2
├── Day 6       : Phase 7 — Scheduler (APScheduler + Flask trigger)
└── Day 7–8     : Phase 8 — Dashboard UI (Streamlit)
```
