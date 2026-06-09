# Context Document: Groww Weekly Product Review Pulse & Fee Explainer

---

## 1. Project Overview

**Project Name:** Weekly Product Review Pulse & Fee Explainer  
**Product:** Groww (Investment & Mutual Fund Platform)  
**Type:** AI-Powered Automated Reporting Workflow  
**Delivery Mechanism:** MCP (Model Context Protocol) servers with human approval gates

This project automates the end-to-end process of collecting, analyzing, and distributing customer feedback insights for Groww. Instead of manually sifting through hundreds of app reviews, the system uses LLMs to extract patterns, themes, and quotes — then routes the final output through an approval-gated workflow to update a Google Doc and draft a stakeholder email.

---

## 2. Problem Being Solved

### Business Pain Point
Groww's Product, Support, and Leadership teams rely on app store reviews to track customer sentiment and spot recurring product issues. This process today is:
- **Manual and time-consuming** — reviews must be read individually
- **Inconsistent** — no standardized format for weekly review digests
- **Delayed** — insights often lag behind the review data by days or weeks
- **Siloed** — different teams may interpret the same reviews differently

### Solution
Automate the extraction of structured insights from Google Play Store reviews using LLMs, and deliver a formatted weekly pulse to stakeholders via Google Workspace — all gated through human approval to maintain accuracy and accountability.

---

## 3. Stakeholders & Beneficiaries

| Team | How They Benefit |
|---|---|
| **Product Team** | Prioritize roadmap initiatives based on real customer pain points |
| **Support Team** | Identify recurring complaints and prepare proactive responses |
| **Leadership** | Monitor customer sentiment and overall platform health at a glance |

---

## 4. Scope & Constraints

### In Scope
- **Product:** Groww only
- **Review Source:** Google Play Store (public reviews)
- **Review Window:** Rolling 8–12 weeks
- **Volume:** 150–300 reviews per cycle
- **Outputs:** Weekly Product Pulse + Mutual Fund Exit Load Fee Explainer

### Out of Scope
- Apple App Store reviews (not included in this iteration)
- Direct calls to Google Docs API or Gmail API (avoided by design; MCP used instead)
- Automatic email sending (drafts created only, never auto-sent)
- Any fee scenarios other than Mutual Fund Exit Load in this version

---

## 5. Data Sources

### Primary Data
| Source | Type | Details |
|---|---|---|
| Google Play Store | Public App Reviews | Text, Rating (1–5 stars), Date |

### Reference Sources (for Fee Explainer)
| # | Source |
|---|---|
| 1 | Groww Help Center |
| 2 | Groww Exit Load Information Page |
| 3 | SEBI Investor Education Resources |
| 4 | Mutual Fund Scheme Information Document (SID) |
| 5 | Groww Mutual Fund Documentation |
| 6 | Relevant AMC Scheme Documents |

---

## 6. Workflow Details

### Part A — Weekly Product Pulse

The pulse pipeline runs in 6 sequential steps:

#### Step 1: Review Ingestion
- Fetch public reviews from Google Play Store
- Store: review text, star rating, review date
- Target volume: 150–300 reviews from the last 8–12 weeks

#### Step 2: Data Cleaning
- **De-duplication:** Remove identical or near-identical review texts
- **Empty Review Removal:** Discard blank or whitespace-only entries
- **PII Scrubbing:** Strip personally identifiable information (names, emails, phone numbers) from review text
- **Text Normalization:** Standardize encoding, punctuation, and casing for consistent downstream processing

#### Step 3: Theme Discovery (Clustering + LLM)
- Convert cleaned reviews into dense vector **embeddings** using [`BAAI/bge-large-en-v1.5`](https://huggingface.co/BAAI/bge-large-en-v1.5) (1024-dim, runs locally via `sentence-transformers`)
- Apply **clustering algorithms** (k-means / DBSCAN) to group semantically similar reviews
- Generate up to **5 theme clusters**; surface the **top 3** by volume and business importance
- Expected primary themes:
  1. **App Performance** — crashes, slow load times, UI bugs
  2. **Withdrawal Experience** — delays, failures, unclear timelines
  3. **Customer Support** — responsiveness, resolution quality, communication

#### Step 4: Quote Extraction
- Extract exactly **3 verbatim user quotes** — one per major theme
- **Validation rules:**
  - Quote must exist word-for-word in the source review
  - No LLM-generated or paraphrased quotes allowed
  - All quotes must be PII-free post-scrubbing

#### Step 5: Weekly Summary Generation (LLM)
- **LLM:** [Groq](https://groq.com) via GroqCloud API (`llama3-70b-8192` primary, `mixtral-8x7b-32768` fallback)
- Generate a **≤250-word stakeholder narrative** covering:
  - Top findings and trend analysis
  - Overall customer sentiment (positive, negative, neutral breakdown)
  - Key signals for the product and support teams

#### Step 6: Action Recommendations (LLM)
- **LLM:** Groq (same model as Step 5)
- Generate exactly **3 actionable improvement ideas**, e.g.:
  - Improve withdrawal transparency with real-time status updates
  - Reduce app crashes during peak trading hours
  - Improve support ticket tracking and response time visibility

---

### Part B — Fee Explainer

#### Fee Scenario
**Mutual Fund Exit Load**

#### Purpose
Provide a neutral, factual, standardized explanation of exit load fees for use in customer support responses and internal knowledge-sharing across Groww teams.

#### Output Requirements
- Exactly **6 bullet points** maximum
- **Neutral tone** — no recommendations or opinions
- **Facts only** — no product comparisons
- Must include **source references**
- Must include a **"Last Checked" verification date**

#### Sample Output
```
Mutual Fund Exit Load

• Exit load is a fee charged when units are redeemed before a scheme-defined holding period.
• Exit load conditions vary by mutual fund scheme.
• The fee is generally expressed as a percentage of redemption value.
• Exit load, when applicable, is deducted at the time of redemption.
• Details are specified in the Scheme Information Document (SID).
• Investors should refer to the latest scheme documents for current exit load rules.

Last Checked: June 2026

Official Sources:
1. Groww Help Center
2. Groww Exit Load Information Page
```

---

## 7. MCP-Based Approval Workflow

All output delivery is exclusively handled by **MCP (Model Context Protocol) servers**. This enforces a human-in-the-loop model where no action is taken without explicit user approval.

### Approval Gate 1 — Weekly Pulse Review
**Trigger:** After LLM generates themes, quotes, summary, and action ideas  
**User Reviews:** Themes · Quotes · Weekly note · Action ideas  
**Action on Approval:** Proceed to Fee Explainer generation

### Approval Gate 2 — Fee Explainer Review
**Trigger:** After LLM generates fee explanation bullets and source links  
**User Reviews:** Explanation bullets · Source links  
**Action on Approval:** Proceed to Google Doc append

### Approval Gate 3 — Google Doc Append
**Trigger:** After both Gate 1 and Gate 2 are approved  
**MCP Action:** Append to Google Doc titled *"Weekly Review Pulse — Groww"*  
**Payload Schema:**
```json
{
  "date": "YYYY-MM-DD",
  "weekly_pulse": "...",
  "fee_scenario": "Mutual Fund Exit Load",
  "explanation_bullets": [],
  "source_links": []
}
```
**Action on Approval:** Doc section created/updated; proceed to email draft

### Approval Gate 4 — Gmail Draft Creation
**Trigger:** After Google Doc is successfully appended  
**MCP Action:** Create Gmail draft (never auto-sent)  
**Draft Subject:** `Weekly Pulse + Fee Explainer — Groww`  
**Draft Body Contains:**
- Weekly Pulse Summary
- Fee Explainer Summary
- Direct link to the Google Doc section  

**Action on Approval:** Draft saved to Gmail; workflow complete

---

## 8. Idempotency Design

To prevent duplicate reports being created for the same review period, the system tracks state using four keys per run:

| Key | Purpose |
|---|---|
| `Product Name` | Scopes the run to a specific product (Groww) |
| `ISO Week` | Identifies the calendar week of the run |
| `Document Section ID` | References the specific Google Doc section created |
| `Email Draft ID` | References the Gmail draft created |

**Behavior on re-run:** If an `ISO Week` entry already exists for the product, the system **updates** the existing document section and email draft rather than creating new ones.

---

## 9. Auditability

Every pipeline execution is logged with the following metadata to ensure full traceability:

| Field | Description |
|---|---|
| `Timestamp` | Exact datetime the run was executed |
| `Product` | Product name (Groww) |
| `ISO Week` | Calendar week identifier |
| `Generated Report` | Full text of the weekly pulse and fee explainer |
| `Doc Section ID` | Google Doc section appended |
| `Email Draft ID` | Gmail draft created |

**Key audit question the log answers:**  
> *"What was sent, when, and for which week?"*

---

## 10. Deliverables

| # | Deliverable | Format |
|---|---|---|
| 1 | Working Prototype + Demo Video | Code + Video (≤3 min) |
| 2 | Weekly Product Pulse Report | PDF / MD / Google Doc |
| 3 | Google Doc Append Proof | Screenshot |
| 4 | Gmail Draft Proof | Screenshot |
| 5 | Sample Reviews Dataset | CSV |
| 6 | Source URL List | Text / MD |
| 7 | README | Markdown |

### README Must Cover
- Setup instructions (environment, dependencies, API keys)
- Re-run instructions with idempotency behavior explained
- MCP approval gate locations and how to interact with them
- Fee scenario(s) covered and how to add new ones
- Data sources and how reviews are collected
- Architecture overview with diagram

---

## 11. Key Design Decisions

| Decision | Rationale |
|---|---|
| **MCP over direct API calls** | Enforces human approval gates; avoids credential management complexity |
| **No auto-sending emails** | Preserves human oversight over all external communications |
| **Verbatim quote validation** | Prevents hallucinated or fabricated user quotes in reports |
| **Max 5 themes, surface top 3** | Balances coverage with readability for stakeholder digests |
| **Idempotency via ISO Week** | Prevents duplicate reports and enables safe re-runs |
| **PII scrubbing before LLM input** | Protects user privacy and complies with data handling best practices |
| **Groq as LLM provider** | Ultra-fast inference speed; ideal for real-time report generation |
| **BAAI/bge-large-en-v1.5 for embeddings** | High-quality 1024-dim embeddings; runs fully locally via `sentence-transformers` with no external API cost |
