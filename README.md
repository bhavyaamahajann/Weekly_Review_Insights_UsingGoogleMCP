# Groww AI Product Review Pulse & Support Explainer (Milestone 2)

An AI-powered automated feedback orchestration pipeline that analyzes Groww's public Play Store reviews, clusters them to identify key product issues, detects fee-related confusion, generates structured weekly internal updates and support explainer snippets, and publishes them to Google Docs and Gmail using **Model Context Protocol (MCP)** with strict human approval gates.

---

## 1. Milestone 2 Problem Statement & Goals

This system is built as a complete Product + Support workflow solution to address Milestone 2:
- **Product Sentiment & Trend Tracking:** Automate clustering of raw reviews into themes to find what is trending and what needs action.
- **Proactive Support Communication:** Detect recurring confusion around a specific fee or charge and generate a factual, reusable customer explanation snippet.
- **Human-in-the-Loop MCP Delivery:** Securely log outputs to internal resources (Google Docs) and prepare ready-to-use email drafts (Gmail) after explicit user sign-off.

---

## 2. Core System Architecture

```
                       [ Input: Play Store Reviews CSV ]
                                      │
                                      ▼
                        [ Step 1: Review Intelligence ]
                          ├── Clean & Scrub PII
                          ├── Local Vector Embeddings (BGE-Large)
                          ├── k-Means Theme Clustering (Max 5 Themes)
                          └── Exit Load Confusion Detection
                                      │
                                      ▼
                      [ Step 2 & 3: Structured LLM Gen ]
                          ├── Weekly Internal Pulse (≤ 250 words)
                          └── Support Fee Explainer (≤ 6 bullets)
                                      │
                                      ▼
                         [ Human-in-the-Loop Gating ]
                          ├── Gate 1: Approve Weekly Pulse
                          ├── Gate 2: Approve Fee Explainer
                          ├── Gate 3: Confirm GDoc Write Payload
                          └── Gate 4: Confirm Gmail Draft Template
                                      │
                                      ▼
                      [ Step 4: MCP Service Integration ]
                          ├── Google Doc MCP (Append Entry)
                          └── Gmail MCP (Create Email Draft)
                                      │
                                      ▼
                    [ Premium Vite/React Dashboard UI ]
```

---

## 3. Workflow Steps & Deliverables

### Step 1 — Review Intelligence Layer
- **Ingestion & Anonymization:** Scrubs PII (emails, phone numbers, names) from Play Store reviews and filters for English reviews.
- **Clustering:** Generates local vector embeddings using `BAAI/bge-large-en-v1.5` and clusters reviews using k-Means (constrained to a maximum of 5 themes).
- **Signal Detection:** Selects the top 3 themes, extracts representative quotes, and flags fee-related pain points.

### Step 2 — Weekly Product Pulse (Internal Output)
A structured update (≤250 words) containing:
1. **Summary of Top Themes:** Key user categories.
2. **User Quotes:** Real representative feedback.
3. **Key Observations:** Trends and system pain points.
4. **Strategic Action Ideas:** 3 prioritized action items for product teams.

### Step 3 — Fee Explainer (Derived from Insights)
A factual explanation snippet generated directly from user exit load complaints:
- **Length:** ≤6 clear bullet points.
- **Tone:** Neutral and compliance-compliant.
- **Sources:** 4-6 links to official mutual fund guidelines.
- **Metadata:** Dynamic `"Last checked: [Month Year]"` entry.

---

## 4. MCP Gating & Human Approval Points

> [!IMPORTANT]
> To simulate real-world governance, the orchestrator enforces **4 human-in-the-loop approval gates** before making any MCP tool calls:
> 1. **Gate 1 (Weekly Pulse Approval):** Preview generated themes, quotes, and pulse. Choose `[A]pprove`, `[R]eject`, or input feedback to regenerate.
> 2. **Gate 2 (Fee Explainer Approval):** Review support explanation bullets. Choose `[A]pprove`, `[R]eject`, or edit.
> 3. **Gate 3 (GDoc MCP Gate):** Preview Google Doc append payload. Confirm before sending write request.
> 4. **Gate 4 (Gmail MCP Gate):** View subject and body template. Confirm to create Gmail draft.

---

## 5. Identified Fee Scenario: Mutual Fund Exit Load

### The Reviews Pain Point
User reviews frequently indicate confusion regarding **Mutual Fund Exit Load** charges during redemption. Specifically:
- Disappointment when charged fee for redemptions done within 365 days.
- Inability to find AMC-specific exit load percentages easily.
- Deductions made directly from proceeds without clear prior notifications.

### Source Reference List (Official URLs)
1. **Groww Help Center:** https://groww.in/help
2. **Groww Exit Load Information Page:** https://groww.in/p/exit-load-in-mutual-funds
3. **SEBI Investor Education Resources:** https://www.sebi.gov.in/investor/investor-education.html
4. **AMFI India Mutual Fund Guidelines:** https://www.amfiindia.com/investor-corner
5. **Groww Mutual Fund Charges Details:** https://groww.in/mutual-funds/charges

---

## 6. How to Run

### Setup Environment
1. **Activate the virtual environment:**
   ```bash
   source venv/bin/activate
   ```
2. **Copy `.env.example` to `.env` and fill in API keys:**
   ```bash
   cp .env.example .env
   ```

### A. Run CLI Pipeline (Includes CLI Approval Gates)
To run the automated ingest, cleaning, clustering, LLM generation, and approval gates:
```bash
python src/pipeline.py
```

### B. Start the Premium Dashboard UI (Vite/React)
To launch the stakeholder visualization web app:
```bash
cd "Improve UI Design"
npm run dev
```
Open your browser and navigate to `http://localhost:5173`. You can explore weeks, look at theme trends, and view **Email snapshots** for generated drafts.

### C. Run Background Services
- **Scheduler Cron:** `python src/scheduler/scheduler.py`
- **Manual Trigger API:** `python src/scheduler/trigger.py`

### D. Run Unit Tests
To execute all 35 verify checks:
```bash
venv/bin/python -m unittest discover tests
```

---

## 7. Deliverables Mapping

| Deliverable | Location in Workspace | Description |
| :--- | :--- | :--- |
| **Reviews CSV Sample** | [reviews_sample.csv](file:///Users/apple/Desktop/Cursor/Weekly%20Reviews%20Insight%20report/data/raw/reviews.csv) | Ingested Google Play Store CSV dataset. |
| **Weekly Product Pulse** | [pulse_2026-W25.json](file:///Users/apple/Desktop/Cursor/Weekly%20Reviews%20Insight%20report/data/outputs/pulse_2026-W25.json) | Generated JSON report for Step 2. |
| **Google Doc Snippet** | [gdoc_simulation.md](file:///Users/apple/Desktop/Cursor/Weekly%20Reviews%20Insight%20report/data/outputs/gdoc_simulation.md) | Simulated mock append file documenting logged reports. |
| **Email Draft Output** | [gmail_simulation.txt](file:///Users/apple/Desktop/Cursor/Weekly%20Reviews%20Insight%20report/data/outputs/gmail_simulation.txt) | Generated Gmail MCP draft matching final formatting. |
| **Source List** | Sections 5 & 6 in `README.md` | Compliance sources for fee explanations. |

---

## 8. Skills Tested
* **✔ Insight extraction** from unstructured reviews.
* **✔ Theme clustering** and signal strength modeling.
* **✔ Reusable support snippets** conversion.
* **✔ Controlled summarization** under strict token caps.
* **✔ MCP tool calling** with strict approval gating.
