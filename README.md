# Groww Weekly Product Review Pulse & Fee Explainer

An AI-powered automated feedback orchestration pipeline that ingests Groww's public Google Play Store reviews, cleans and anonymizes them (PII scrubbing), clusters them using local vector embeddings, summarizes the top themes and verbatim quotes using Groq Cloud LLMs, generates a factual fee explainer, and delivers the finalized summaries to Google Docs and Gmail using **Model Context Protocol (MCP)** servers with human approval gating.

---

## 1. Project Architecture Overview

```
Play Store Reviews
        │
        ▼ (Sync Ingest & Dedup)
data/raw/reviews.csv
        │
        ▼ (PII Clean & Language Filters)
data/cleaned/reviews_clean.csv
        │
        ▼ (Local bge-large-en-v1.5 Embeddings)
Vector Embeddings (.npy)
        │
        ▼ (k-Means Silhouette Clustering)
Theme Clusters & Quotes
        │
        ▼ (Groq LLM Llama-3.3-70b-versatile)
Structured pulse & exit load explainers
        │
        ▼ (Human Approval Gates 1 & 2)
Approved Summaries
        │
        ▼ (Gate 3 - Google Doc Append tool)
MCP Google Workspace Server
        │
        ▼ (Gate 4 - Gmail Draft creation tool)
MCP Gmail Draft (Simulation fallback)
        │
        ▼
Streamlit Premium Dashboard / Audit log trail
```

---

## 2. Setup Instructions

### Prerequisites
- Python 3.11+
- Virtualenv package

### Step-by-Step Installation

1. **Clone the repository and navigate to the directory:**
   ```bash
   cd "Weekly Reviews Insight report"
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install python dependencies:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Verify environment and model downloads:**
   Verify that local embeddings (`BAAI/bge-large-en-v1.5`) and dependencies are ready:
   ```bash
   python tests/verify_env.py
   ```

---

## 3. Configuration & Environment Variables (`.env`)

Create a `.env` file in the root directory. You can copy the contents of `.env.example`:

```ini
GROQ_API_KEY=gsk_your_groq_cloud_api_key_here
MCP_GDOC_SERVER_URL=https://bhavyamcpserver.up.railway.app
MCP_GMAIL_SERVER_URL=https://bhavyamcpserver.up.railway.app
GDOC_DOCUMENT_ID=126paEr1-SJpFx7P2RWkzq6rPRUHfYjgqvhcXrNK21M0
GMAIL_RECIPIENT=mahajan.bhavya36@gmail.com
API_SECRET_KEY=Bhavya298172917230
REQUIRE_TERMINAL_APPROVAL=true

# Scheduler (Phase 7)
SCHEDULER_DAY_OF_WEEK=mon          # Day to run weekly pipeline (mon-sun)
SCHEDULER_HOUR=8                   # Hour to run (24h, IST)
SCHEDULER_TRIGGER_PORT=5050        # Port for manual HTTP trigger

# Dashboard (Phase 8)
DASHBOARD_PORT=8501                # Streamlit default port

# Scraper Configurations
MAX_REVIEWS_THRESHOLD=5000
REVIEW_WINDOW_WEEKS=10
MIN_REVIEWS_THRESHOLD=50
```

---

## 4. How to Run

### A. Run the End-to-End Orchestrator Pipeline (CLI)
To run the full flow (Ingest -> Clean -> Embed/Cluster -> LLM Gen -> Approval Loop -> MCP write):
```bash
python src/pipeline.py
```

### B. Start the Premium Dashboard UI (Streamlit)
To launch the stakeholder dashboard visualizer:
```bash
streamlit run src/dashboard/app.py --server.port 8501
```
Open your browser and navigate to `http://localhost:8501`.

### C. Run the Scheduler & Trigger Services
To start the weekly background cron scheduler:
```bash
python src/scheduler/scheduler.py
```
To run the trigger API backend for on-demand execution:
```bash
python src/scheduler/trigger.py
```

### D. Execute the Full Test Suite
To verify imports, logic, and simulations:
```bash
python -m unittest discover tests
```

---

## 5. MCP Approval Gates & How They Work

The system implements a strict human-in-the-loop validation design before committing any external changes:

- **Gate 1 (Weekly Pulse Review):** Displays the generated themes, quotes, and weekly pulse summaries in the terminal console. The user must input `[A]pprove`, `[R]eject`, or input feedback to regenerate analysis.
- **Gate 2 (Fee Explainer Review):** Displays compliance-verified bullet points and official reference links. The user can approve, reject, or provide feedback.
- **Gate 3 (Google Doc Append):** Presents the payload and asks for final confirmation before sending the write request to the external MCP server (appends to document ID).
- **Gate 4 (Gmail Draft Creation):** Shows the subject and body template of the email. Upon approval, it makes the Gmail MCP call to write the draft (never auto-sends).

*Note: In automated environments (e.g. GitHub Actions), set `REQUIRE_TERMINAL_APPROVAL=false` to bypass blocking inputs (headless mode).*

---

## 6. Fee Scenario & Review Signal Detection

### Identified Pain Point
From public user reviews, users frequently express confusion regarding **Mutual Fund Exit Load** charges during redemptions. Common issues include:
- Confusion about holding periods (e.g., exit load charged when redeeming within 1 year).
- Redeeming mutual funds and seeing unexpected charge deductions without knowing the exact rules.
- Difficulty finding specific charges for separate Asset Management Companies (AMCs) schemes.

### Action Taken
The pipeline automatically targets this recurring pain point, generating a factual, compliant 6-bullet explainer that support representatives can reuse to resolve ticket queues.

### Official Source References Listed
1. **Groww Help Center:** https://groww.in/help
2. **Groww Exit Load Mutual Fund Blog:** https://groww.in/blog/exit-load-in-mutual-funds
3. **Groww Mutual Fund House:** https://www.growwmf.in/
4. **SEBI Mutual Fund Regulations:** https://www.sebi.gov.in/
5. **Groww Mutual Fund Charges page:** https://groww.in/mutual-funds/charges
