# Edge Cases & Failure Scenarios
## Groww — Weekly Product Review Pulse & Fee Explainer

---

## Overview

This document catalogs every known and anticipated edge case across all 8 phases of the system pipeline. Each edge case is classified by:

- **Layer** — which architectural layer it belongs to
- **Severity** — `Critical` / `High` / `Medium` / `Low`
- **Type** — `Data`, `Infrastructure`, `LLM`, `MCP`, `Scheduler`, `UI`, `Security`
- **Detection Point** — where in the pipeline the issue surfaces
- **Mitigation** — the recommended handling strategy

---

## Edge Case Index

| # | Category | Edge Case | Severity |
|---|---|---|---|
| EC-01 | Ingestion | Google Play Store returns 0 reviews | Critical |
| EC-02 | Ingestion | Fetched reviews are all outside the time window | Critical |
| EC-03 | Ingestion | Review count below minimum threshold (< 50) | High |
| EC-04 | Ingestion | Review count at upper limit (> 300) | Medium |
| EC-05 | Ingestion | Play Store scraper rate-limited or blocked | High |
| EC-06 | Ingestion | All reviews are in a non-English language | High |
| EC-07 | Ingestion | Reviews contain only 1-star or only 5-star ratings | Medium |
| EC-08 | Ingestion | Network timeout during review fetch | High |
| EC-09 | Cleaning | All reviews removed after de-duplication | Critical |
| EC-10 | Cleaning | PII scrubber removes entire review text | High |
| EC-11 | Cleaning | Over-aggressive PII scrubbing removes meaningful content | Medium |
| EC-12 | Cleaning | Review text is only emojis or special characters | Low |
| EC-13 | Cleaning | Malformed encoding in review text (e.g., garbled UTF-8) | Medium |
| EC-14 | Cleaning | Review text is extremely long (> 2000 characters) | Low |
| EC-15 | Embedding | BAAI model fails to load locally | Critical |
| EC-16 | Embedding | GPU/CPU OOM during embedding generation | High |
| EC-17 | Embedding | Embedding produces NaN or zero vectors | High |
| EC-18 | Embedding | Embedding model version mismatch on re-run | Medium |
| EC-19 | Clustering | All reviews cluster into a single group | High |
| EC-20 | Clustering | Optimal k = 1 (silhouette score never improves) | High |
| EC-21 | Clustering | Cluster sizes are all equal — tie in ranking | Medium |
| EC-22 | Clustering | Theme label generation returns identical labels | Medium |
| EC-23 | Clustering | Theme label is too generic (e.g., "Other", "App") | Medium |
| EC-24 | Quote Extraction | No verbatim match found in source reviews | Critical |
| EC-25 | Quote Extraction | Best quote candidate contains PII after scrubbing | High |
| EC-26 | Quote Extraction | Quote is too short (< 20 chars) or too long (> 200 chars) | Medium |
| EC-27 | Quote Extraction | All top quotes are from the same review | Medium |
| EC-28 | Quote Extraction | Quote contains offensive or harmful language | High |
| EC-29 | LLM (Groq) | Groq API key is invalid or expired | Critical |
| EC-30 | LLM (Groq) | Groq API returns non-JSON output | High |
| EC-31 | LLM (Groq) | JSON schema mismatch in LLM response | High |
| EC-32 | LLM (Groq) | Weekly summary exceeds 250-word limit | Medium |
| EC-33 | LLM (Groq) | Action ideas are duplicates or too similar | Medium |
| EC-34 | LLM (Groq) | LLM generates fabricated/hallucinated quotes | Critical |
| EC-35 | LLM (Groq) | Fee explainer has more than 6 bullets | Medium |
| EC-36 | LLM (Groq) | Fee explainer contains a recommendation or opinion | High |
| EC-37 | LLM (Groq) | Primary model (llama3-70b) rate-limited | High |
| EC-38 | LLM (Groq) | Both primary and fallback models unavailable | Critical |
| EC-39 | LLM (Groq) | Response truncated due to context length | High |
| EC-40 | Approval Gates | User rejects Gate 1 repeatedly (infinite loop) | High |
| EC-41 | Approval Gates | User approves Gate 1 but rejects Gate 2 | Medium |
| EC-42 | Approval Gates | User abandons pipeline mid-gate (Ctrl+C) | High |
| EC-43 | Approval Gates | Gate 3 MCP call fails after user approval | Critical |
| EC-44 | Approval Gates | Gate 4 MCP call fails after Gate 3 succeeds | High |
| EC-45 | MCP / Google Doc | Doc ID in .env is incorrect or deleted | Critical |
| EC-46 | MCP / Google Doc | MCP server is down or unreachable | Critical |
| EC-47 | MCP / Google Doc | Doc section append creates a duplicate heading | High |
| EC-48 | MCP / Google Doc | Doc hits character/size limit | Medium |
| EC-49 | MCP / Gmail | Gmail draft creation fails silently | High |
| EC-50 | MCP / Gmail | Draft accidentally sent by user manually | Low |
| EC-51 | State & Idempotency | State file is corrupted or malformed JSON | Critical |
| EC-52 | State & Idempotency | Two pipeline instances run simultaneously for same week | Critical |
| EC-53 | State & Idempotency | ISO week computation crosses year boundary | Medium |
| EC-54 | State & Idempotency | State file is missing on first run | Low |
| EC-55 | Audit Logging | Audit log file is not writable (permission error) | High |
| EC-56 | Audit Logging | Audit log grows very large over many weeks | Low |
| EC-57 | Audit Logging | Run completes but audit log entry is missing | Medium |
| EC-58 | Scheduler | Scheduler fires during pipeline approval gate wait | High |
| EC-59 | Scheduler | Scheduled run fires with no internet/API access | High |
| EC-60 | Scheduler | Cron expression misconfigured (fires every minute) | High |
| EC-61 | Scheduler | Server restarts mid-pipeline run | High |
| EC-62 | Scheduler | Manual trigger fires while scheduled run is active | High |
| EC-63 | Dashboard | Dashboard loaded with no pipeline runs yet | Medium |
| EC-64 | Dashboard | Dashboard loaded while pipeline is currently running | Medium |
| EC-65 | Dashboard | Pulse JSON file is corrupted or partially written | High |
| EC-66 | Dashboard | Audit log has entries with missing fields | Medium |
| EC-67 | Dashboard | Week selector shows a week with only partial data | Medium |
| EC-68 | Dashboard | Run Pipeline button pressed multiple times rapidly | Medium |
| EC-69 | Security | .env file accidentally committed to Git | Critical |
| EC-70 | Security | PII appears in audit log due to scrubber miss | High |
| EC-71 | Security | Groq API key exposed in logs or error messages | High |
| EC-72 | Security | Dashboard trigger endpoint exposed on public network | Critical |

---

## Layer 1 — Ingestion Edge Cases

### EC-01 | Google Play Store Returns 0 Reviews
**Severity:** Critical | **Type:** Data | **Detection:** `fetch_reviews.py`

**Scenario:** The scraper successfully connects to the Play Store but receives zero reviews for Groww within the configured review window.

**Causes:**
- App ID changed or app was temporarily unlisted
- Regional restriction on public review visibility
- Scraper is parsing an incorrect page structure

**Mitigation:**
```python
if len(reviews) == 0:
    raise PipelineAbortError(
        "FETCH_ZERO_REVIEWS",
        "No reviews returned from Play Store. "
        "Verify APP_ID='com.nextbillion.groww' and review window settings."
    )
```
- Log the error with timestamp, APP_ID, and review window used
- Abort pipeline immediately — do NOT write partial state
- Alert user with actionable error message

---

### EC-02 | All Fetched Reviews Are Outside the Time Window
**Severity:** Critical | **Type:** Data | **Detection:** `fetch_reviews.py` (date filter step)

**Scenario:** The scraper returns reviews, but after applying the `REVIEW_WINDOW_WEEKS` date filter, zero reviews remain within the target window.

**Mitigation:**
- Log how many reviews were fetched vs. how many passed the date filter
- Surface a clear error: `"All N reviews fetched fall outside the 8–12 week window"`
- Suggest widening `REVIEW_WINDOW_WEEKS` in config
- Abort pipeline

---

### EC-03 | Review Count Below Minimum Threshold (< 50)
**Severity:** High | **Type:** Data | **Detection:** `fetch_reviews.py` post-filter

**Scenario:** After date filtering, fewer than 50 reviews remain — insufficient for meaningful clustering.

**Mitigation:**
```python
MIN_REVIEWS_THRESHOLD = 50
if len(filtered_reviews) < MIN_REVIEWS_THRESHOLD:
    raise PipelineAbortError(
        "INSUFFICIENT_REVIEWS",
        f"Only {len(filtered_reviews)} reviews passed filters. "
        f"Minimum required: {MIN_REVIEWS_THRESHOLD}. "
        "Consider widening REVIEW_WINDOW_WEEKS."
    )
```
- Make threshold configurable via `.env` (`MIN_REVIEWS_THRESHOLD`)
- Do not proceed to embedding — clustering on < 50 reviews produces unreliable themes

---

### EC-04 | Review Count Exceeds Upper Limit (> 300)
**Severity:** Medium | **Type:** Data | **Detection:** `fetch_reviews.py`

**Scenario:** More than 300 reviews are returned, exceeding the target volume and potentially causing OOM during embedding.

**Mitigation:**
- Truncate to 300 reviews by selecting a stratified sample (proportional across rating buckets: 1-star, 2-star, 3-star, 4-star, 5-star)
- Log the total fetched count vs. sampled count
- Do NOT randomly truncate — preserve rating distribution to avoid sentiment bias

---

### EC-05 | Play Store Scraper Rate-Limited or Blocked
**Severity:** High | **Type:** Infrastructure | **Detection:** `fetch_reviews.py`

**Scenario:** The `google-play-scraper` library receives a `429 Too Many Requests` or connection refused error from Google's servers.

**Mitigation:**
- Implement exponential backoff: retry 3 times with delays of 10s, 30s, 60s
- If all retries fail, abort pipeline and log the HTTP status code
- Consider adding `SCRAPER_DELAY_SECONDS` to `.env` to throttle between page fetches
- In the scheduler context, reschedule for 2 hours later if rate-limited

---

### EC-06 | All Reviews Are in a Non-English Language
**Severity:** High | **Type:** Data | **Detection:** `cleaner.py` (post-normalization)

**Scenario:** The fetched reviews are predominantly in Hindi, Gujarati, or other regional languages, making English embeddings and LLM prompts unreliable.

**Mitigation:**
- Add a `langdetect` language filter step in `cleaner.py`
- Only keep reviews where `detect(text) == 'en'` (configurable)
- If < 50 English reviews remain after filtering, surface: `"Insufficient English reviews for analysis. Consider adding multilingual support."`
- Log the language distribution of dropped reviews

---

### EC-07 | Reviews Contain Only Extreme Ratings (All 1-star or All 5-star)
**Severity:** Medium | **Type:** Data | **Detection:** Post-fetch analysis

**Scenario:** The review dataset for the week contains only 1-star or only 5-star reviews, leading to heavily skewed sentiment output.

**Mitigation:**
- Log the rating distribution in the ingestion step
- In the Groq pulse generation prompt, include the rating distribution as context
- Flag the weekly summary with a `"Note: Ratings distribution is skewed"` warning in the output JSON
- Do NOT abort — skewed data is valid signal

---

### EC-08 | Network Timeout During Review Fetch
**Severity:** High | **Type:** Infrastructure | **Detection:** `fetch_reviews.py`

**Scenario:** The HTTP request to Google Play Store times out (e.g., `requests.exceptions.Timeout`).

**Mitigation:**
- Set explicit timeout: `FETCH_TIMEOUT_SECONDS = 30`
- Retry 3 times with exponential backoff
- On final failure, abort pipeline with error: `"Review fetch timed out after 3 attempts"`
- Log the timeout duration and attempt count

---

## Layer 2 — Cleaning Edge Cases

### EC-09 | All Reviews Removed After De-duplication
**Severity:** Critical | **Type:** Data | **Detection:** `cleaner.py`

**Scenario:** Every review in the dataset is a duplicate of another, leaving 0 unique reviews after de-duplication (e.g., a bot-flooding scenario on the Play Store).

**Mitigation:**
```python
if len(deduped_df) == 0:
    raise PipelineAbortError(
        "ALL_DUPLICATES",
        "All fetched reviews were duplicates. "
        "The dataset may have been bot-flooded. Manual review recommended."
    )
```
- Log the original count vs. post-dedup count
- Abort pipeline and flag for human review

---

### EC-10 | PII Scrubber Removes Entire Review Text
**Severity:** High | **Type:** Data | **Detection:** `cleaner.py` (post-PII step)

**Scenario:** The Presidio analyzer incorrectly classifies the entire review as PII (e.g., a review that is just a phone number or an email address), resulting in an empty string after anonymization.

**Mitigation:**
```python
if len(scrubbed_text.strip()) == 0:
    # Drop the review entirely — do not pass empty strings downstream
    dropped_count += 1
    continue
```
- Log each dropped review (without the PII content) and the reason
- If > 30% of reviews are dropped this way, raise a `DataQualityWarning` and surface it to the user before proceeding

---

### EC-11 | Over-Aggressive PII Scrubbing Removes Meaningful Content
**Severity:** Medium | **Type:** Data | **Detection:** Manual review / output inspection

**Scenario:** Presidio incorrectly flags product-specific terms like "Groww", "NIFTY", or "SIP" as PII entities (false positives), redacting them and distorting the review meaning.

**Mitigation:**
- Maintain a `PII_WHITELIST` in config: `["Groww", "NIFTY", "SIP", "NAV", "UPI", "NSE", "BSE"]`
- Apply whitelist to skip recognition for whitelisted terms before anonymization
- Log a count of false-positive redactions detected via whitelist

---

### EC-12 | Review Text Is Only Emojis or Special Characters
**Severity:** Low | **Type:** Data | **Detection:** `cleaner.py` (normalization step)

**Scenario:** A review contains only emojis (`"🔥🔥🔥"`) or punctuation with no meaningful text content.

**Mitigation:**
- Add a post-normalization check: after stripping emojis and special characters, if `len(alphanumeric_chars) < 10`, drop the review
- Log dropped emoji-only reviews separately

---

### EC-13 | Malformed Encoding in Review Text
**Severity:** Medium | **Type:** Data | **Detection:** `cleaner.py` (normalization step)

**Scenario:** Review text contains garbled UTF-8 characters (e.g., `"â€™"` instead of `"'"`), causing downstream embedding distortion.

**Mitigation:**
- Apply `text.encode('utf-8', errors='replace').decode('utf-8')` during normalization
- Use `ftfy` library to fix broken unicode: `ftfy.fix_text(review_text)`
- Add `ftfy>=6.1.0` to `requirements.txt`

---

### EC-14 | Extremely Long Review Text (> 2000 Characters)
**Severity:** Low | **Type:** Data | **Detection:** `embedder.py`

**Scenario:** A single review is extremely long (e.g., a multi-paragraph essay), which may exceed the embedding model's token limit and be truncated.

**Mitigation:**
- `BAAI/bge-large-en-v1.5` has a 512-token limit; texts longer than this are automatically truncated by `sentence-transformers`
- Log a warning for reviews > 2000 characters: `"Review {id} truncated during embedding (>512 tokens)"`
- Optionally: during quote extraction, skip reviews > 2000 characters as they're harder to present cleanly

---

## Layer 2 — Embedding & Clustering Edge Cases

### EC-15 | BAAI Model Fails to Load Locally
**Severity:** Critical | **Type:** Infrastructure | **Detection:** `embedder.py` at startup

**Scenario:** `SentenceTransformer('BAAI/bge-large-en-v1.5')` raises an error — e.g., model cache is corrupted, disk is full, or HuggingFace Hub is unreachable on first download.

**Mitigation:**
```python
try:
    model = SentenceTransformer("BAAI/bge-large-en-v1.5")
except Exception as e:
    raise PipelineAbortError(
        "MODEL_LOAD_FAILED",
        f"Failed to load BAAI/bge-large-en-v1.5: {e}. "
        "Check disk space, internet connection (first run), and ~/.cache/huggingface."
    )
```
- On first run: ensure the model is downloaded before running the pipeline (add a `setup.py` prefetch step)
- On subsequent runs: model loads from local cache — internet not required

---

### EC-16 | OOM (Out-of-Memory) During Embedding Generation
**Severity:** High | **Type:** Infrastructure | **Detection:** `embedder.py`

**Scenario:** Embedding 300 reviews on a machine with limited RAM/VRAM causes an `OutOfMemoryError`.

**Mitigation:**
- Process reviews in batches: default `EMBED_BATCH_SIZE = 32` (configurable via `.env`)
- Catch `torch.cuda.OutOfMemoryError` and `MemoryError`
- On OOM, halve the batch size and retry up to 3 times
- As a last resort, fall back to CPU inference: `model = SentenceTransformer(..., device='cpu')`

---

### EC-17 | Embedding Produces NaN or Zero Vectors
**Severity:** High | **Type:** Data | **Detection:** `embedder.py` post-encoding

**Scenario:** One or more embeddings are all-zeros or contain NaN values, which corrupts clustering distance calculations.

**Mitigation:**
```python
nan_mask = np.isnan(embeddings).any(axis=1)
zero_mask = (embeddings == 0).all(axis=1)
bad_indices = np.where(nan_mask | zero_mask)[0]

if len(bad_indices) > 0:
    # Drop affected reviews and log
    embeddings = np.delete(embeddings, bad_indices, axis=0)
    reviews_df = reviews_df.drop(index=bad_indices).reset_index(drop=True)
    log.warning(f"Dropped {len(bad_indices)} reviews with invalid embeddings")
```

---

### EC-18 | Embedding Model Version Mismatch on Re-run
**Severity:** Medium | **Type:** Infrastructure | **Detection:** `embedder.py` on re-run

**Scenario:** The cached `.npy` embeddings for a week were generated with a different version of `BAAI/bge-large-en-v1.5` than the currently installed version, leading to inconsistent vector spaces.

**Mitigation:**
- Store the model version/commit hash alongside the embeddings file in a metadata sidecar: `embeddings_YYYY-WNN.meta.json`
- On re-run, compare stored model hash with current; if mismatch, re-embed from scratch
- Log the version used for each embedding run

---

### EC-19 | All Reviews Cluster Into a Single Group
**Severity:** High | **Type:** Data | **Detection:** `clusterer.py`

**Scenario:** k-means with k=2 through k=5 all produce poor silhouette scores, with nearly all reviews assigned to one dominant cluster.

**Mitigation:**
- If best silhouette score < `MIN_SILHOUETTE_THRESHOLD = 0.15`, fall back to a pre-defined topic taxonomy
- Pre-defined fallback themes: `["App Performance", "Transaction Issues", "Account & KYC", "Customer Support", "Investment Features"]`
- Log the silhouette scores for all tested k values
- Mark the generated report with a `"themes_source": "fallback_taxonomy"` flag

---

### EC-20 | Optimal k = 1 (Silhouette Score Never Improves Beyond Single Cluster)
**Severity:** High | **Type:** Data | **Detection:** `clusterer.py`

**Scenario:** The review corpus is so homogeneous (e.g., all reviews discuss the same crash bug this week) that all k values produce worse silhouette scores than k=1.

**Mitigation:**
- Force k=3 (minimum required themes) even if silhouette doesn't improve
- In the weekly summary, note: `"Reviews this week are highly concentrated around a single issue"`
- All 3 quotes should come from that dominant cluster (label variations as sub-themes)

---

### EC-21 | Cluster Sizes Are All Equal — Tie in Ranking
**Severity:** Medium | **Type:** Data | **Detection:** `clusterer.py` (theme ranking step)

**Scenario:** Two or more clusters have identical review counts, making the "top 3 by volume" ranking ambiguous.

**Mitigation:**
- Use a secondary ranking signal: cluster **cohesion** (average intra-cluster cosine similarity)
- Ties in volume → rank by cohesion score (higher cohesion = more representative theme)
- Log the tie and the tiebreaker used

---

### EC-22 | Theme Label Generation Returns Identical Labels for Different Clusters
**Severity:** Medium | **Type:** LLM | **Detection:** `clusterer.py` (Groq theme labeling)

**Scenario:** Groq generates the same theme label (e.g., "App Issues") for two distinct clusters.

**Mitigation:**
- After Groq generates labels, check for exact duplicates across all themes
- If duplicate found, re-prompt Groq with: `"These two clusters must have different labels. Cluster A reviews: [...]. Cluster B reviews: [...]"`
- Retry up to 2 times; if still duplicate, append a differentiator: `"App Issues (Performance)"` vs `"App Issues (Login)"`

---

### EC-23 | Theme Label Is Too Generic
**Severity:** Medium | **Type:** LLM | **Detection:** `clusterer.py`

**Scenario:** Groq generates an overly generic theme label like `"Other"`, `"App"`, or `"Issues"` that provides no actionable insight.

**Mitigation:**
- Maintain a `GENERIC_LABEL_BLOCKLIST = ["Other", "App", "Issues", "Problem", "Feedback", "Review"]`
- If generated label is in the blocklist, re-prompt with: `"Be more specific. The label must describe the specific customer pain point, not a generic category."`
- Retry once; if still generic, use the most frequent bigram from that cluster as the label

---

## Layer 2 — Quote Extraction Edge Cases

### EC-24 | No Verbatim Match Found in Source Reviews
**Severity:** Critical | **Type:** Data | **Detection:** `quote_extractor.py` (validation step)

**Scenario:** The quote extracted by the extractor cannot be found verbatim in the source `review_text` column — this should never happen by design, but could occur if the cleaning step modified the text post-selection.

**Mitigation:**
```python
assert extracted_quote in source_review_text, (
    f"QUOTE_VERBATIM_VIOLATION: Quote not found in source review {review_id}. "
    "This indicates a cleaning/extraction ordering bug."
)
```
- If assertion fails, skip this candidate and try the next closest review in the cluster
- Log the violation with both the quote and the source text for debugging
- Under no circumstances allow a non-verbatim quote to pass to the LLM or output

---

### EC-25 | Best Quote Candidate Contains PII After Scrubbing
**Severity:** High | **Type:** Security | **Detection:** `quote_extractor.py`

**Scenario:** The verbatim quote contains PII that was not caught in the cleaning step (e.g., a first name embedded naturally in a sentence: `"I, Rahul, have been using Groww for 2 years..."`).

**Mitigation:**
- Re-run Presidio scan specifically on each extracted quote before accepting it
- If PII detected: skip this candidate, try the next closest review in the cluster
- If no PII-free quote can be found within a cluster after 5 attempts, skip that cluster's quote
- If fewer than 3 quotes can be found overall, abort with a `DATA_QUALITY` warning

---

### EC-26 | Quote Is Too Short or Too Long
**Severity:** Medium | **Type:** Data | **Detection:** `quote_extractor.py`

**Scenario:** The best candidate quote is either `< 20` characters (not meaningful) or `> 200` characters (too long for a stakeholder digest).

**Mitigation:**
- For too-short quotes: move to the next sentence in the same review
- For too-long quotes: truncate to the first `200` characters at a sentence boundary; append `"..."`
- Log quote length violations and how they were resolved

---

### EC-27 | All Top Quotes Come From the Same Review
**Severity:** Medium | **Type:** Data | **Detection:** `quote_extractor.py`

**Scenario:** The three cluster centroids all happen to be closest to a single very long review, producing 3 quotes from the same source.

**Mitigation:**
- After extracting each quote, track `source_review_id`
- If a `source_review_id` is reused, move to the next closest review in that cluster until a unique source is found
- Enforce: all 3 final quotes must come from different `source_review_id` values

---

### EC-28 | Quote Contains Offensive or Harmful Language
**Severity:** High | **Type:** Security | **Detection:** `quote_extractor.py`

**Scenario:** A verbatim user quote contains profanity, hate speech, or personally offensive content that is inappropriate for a stakeholder report.

**Mitigation:**
- Add a content moderation check using a lightweight profanity filter (e.g., `better-profanity` library)
- If flagged: skip the candidate, try the next review in the cluster
- Log the flagged content type (not the content itself)
- If no clean quote found in a cluster after 5 attempts, use a generic placeholder: `"[Quote withheld — content moderation]"`

---

## Layer 3 — LLM (Groq) Edge Cases

### EC-29 | Groq API Key Is Invalid or Expired
**Severity:** Critical | **Type:** Infrastructure | **Detection:** `pulse_generator.py` or `fee_explainer.py` on first API call

**Scenario:** The `GROQ_API_KEY` in `.env` is incorrect, expired, or has been revoked.

**Mitigation:**
```python
try:
    response = client.chat.completions.create(...)
except groq.AuthenticationError as e:
    raise PipelineAbortError(
        "GROQ_AUTH_FAILED",
        "Groq API authentication failed. "
        "Check GROQ_API_KEY in .env. "
        f"Details: {e}"
    )
```
- Abort immediately — do not attempt fallback (fallback uses same key)
- Provide direct link to Groq Console in error message: `https://console.groq.com/keys`

---

### EC-30 | Groq API Returns Non-JSON Output
**Severity:** High | **Type:** LLM | **Detection:** `pulse_generator.py`, `fee_explainer.py`

**Scenario:** Despite the system prompt instructing JSON-only output, Groq returns a response with preamble text like `"Sure! Here is the JSON: {...}"`.

**Mitigation:**
```python
import re

def extract_json_from_response(text: str) -> dict:
    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Extract JSON block from markdown code fence or surrounding text
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        return json.loads(match.group())
    raise LLMOutputError("No valid JSON found in Groq response")
```
- If JSON extraction still fails after regex: retry with FALLBACK_MODEL with a stronger prompt: `"RESPOND WITH ONLY RAW JSON. NO PREAMBLE. NO EXPLANATION."`

---

### EC-31 | JSON Schema Mismatch in LLM Response
**Severity:** High | **Type:** LLM | **Detection:** `pulse_generator.py`, `fee_explainer.py`

**Scenario:** Groq returns valid JSON, but it is missing required fields (e.g., `action_ideas` is absent, or `sentiment` has wrong keys).

**Mitigation:**
- Use `pydantic` for strict schema validation of all LLM outputs
- Define `PulseOutput` and `FeeExplainerOutput` Pydantic models
- On `ValidationError`: retry once with the same model, appending: `"Your previous response was missing required fields: {missing_fields}. Try again."`
- On second failure: retry with FALLBACK_MODEL

---

### EC-32 | Weekly Summary Exceeds 250-Word Limit
**Severity:** Medium | **Type:** LLM | **Detection:** `pulse_generator.py` validation

**Scenario:** Despite the prompt specifying ≤250 words, Groq generates a summary that is longer.

**Mitigation:**
```python
word_count = len(summary.split())
if word_count > 250:
    # Truncate at sentence boundary closest to 250 words
    sentences = summary.split('. ')
    truncated = ""
    for s in sentences:
        if len((truncated + s).split()) <= 250:
            truncated += s + ". "
        else:
            break
    summary = truncated.strip()
    log.warning(f"Summary truncated from {word_count} to {len(summary.split())} words")
```

---

### EC-33 | Action Ideas Are Duplicates or Too Similar
**Severity:** Medium | **Type:** LLM | **Detection:** `pulse_generator.py`

**Scenario:** Groq generates 3 action ideas that are semantically near-identical (e.g., "Fix the app crashes", "Resolve app crashes during peak hours", "Prevent app from crashing").

**Mitigation:**
- After receiving ideas, compute pairwise cosine similarity between their embeddings (reuse the BAAI model)
- If any pair has similarity > 0.85, re-prompt: `"Action ideas {i} and {j} are too similar. Please provide 3 distinctly different, actionable recommendations."`
- Retry once per offense

---

### EC-34 | LLM Generates Fabricated/Hallucinated Quotes
**Severity:** Critical | **Type:** LLM | **Detection:** `quote_extractor.py` (verbatim check)

**Scenario:** Despite explicit instructions to use only provided quotes, an LLM-integrated step outputs a quote that does not exist verbatim in the source review corpus.

**Mitigation:**
- The quote extraction step is **not LLM-driven** — quotes are extracted algorithmically (centroid proximity) and validated via exact string matching before any LLM sees them
- Quotes are passed to Groq as pre-validated strings; Groq is NOT asked to generate or paraphrase quotes
- This architectural decision is the primary safeguard against EC-34

---

### EC-35 | Fee Explainer Has More Than 6 Bullets
**Severity:** Medium | **Type:** LLM | **Detection:** `fee_explainer.py`

**Scenario:** Groq returns 7 or 8 bullets despite the prompt specifying a maximum of 6.

**Mitigation:**
```python
if len(bullets) > 6:
    bullets = bullets[:6]  # Hard truncate to first 6 bullets
    log.warning(f"Fee explainer truncated from {original_count} to 6 bullets")
```
- Always enforce the hard cap programmatically, regardless of LLM output

---

### EC-36 | Fee Explainer Contains a Recommendation or Opinion
**Severity:** High | **Type:** LLM | **Detection:** `fee_explainer.py`

**Scenario:** Despite the neutral-tone instruction, Groq includes opinion phrases like `"You should..."`, `"It is advisable to..."`, or `"We recommend..."` in the fee explainer bullets.

**Mitigation:**
- Maintain an `OPINION_PHRASE_BLOCKLIST = ["you should", "we recommend", "it is advisable", "consider", "it's better to", "you may want to"]`
- After receiving bullets, scan each bullet for blocklisted phrases (case-insensitive)
- If found: re-prompt with: `"Bullet {i} contains an opinion phrase. Rewrite it as a pure factual statement without any recommendations."`
- Retry only the offending bullet, not the full explainer

---

### EC-37 | Primary Model Rate-Limited
**Severity:** High | **Type:** Infrastructure | **Detection:** `pulse_generator.py`, `fee_explainer.py`

**Scenario:** Groq's `llama3-70b-8192` model returns a `429 RateLimitError` due to token/request quota exhaustion.

**Mitigation:**
```python
except groq.RateLimitError:
    log.warning("Primary model rate-limited. Switching to fallback: mixtral-8x7b-32768")
    return call_groq(model=FALLBACK_MODEL, ...)
```
- Switch immediately to `mixtral-8x7b-32768`
- Log the rate limit event with timestamp
- If fallback is also rate-limited, wait 60 seconds and retry once

---

### EC-38 | Both Primary and Fallback Models Unavailable
**Severity:** Critical | **Type:** Infrastructure | **Detection:** `pulse_generator.py`, `fee_explainer.py`

**Scenario:** Both `llama3-70b-8192` and `mixtral-8x7b-32768` are unavailable (Groq outage or account suspended).

**Mitigation:**
- After both models fail: abort pipeline with error `"GROQ_ALL_MODELS_UNAVAILABLE"`
- Store the cleaned + embedded + clustered data to disk (do not re-run expensive embedding)
- Allow the user to re-run only the LLM phase once Groq is restored, using cached embeddings/clusters
- Check Groq status at: `https://groqstatus.com`

---

### EC-39 | LLM Response Truncated Due to Context Length
**Severity:** High | **Type:** LLM | **Detection:** `pulse_generator.py`

**Scenario:** The input prompt (themes + quotes + cluster metadata) is too long, causing Groq to truncate the output (response ends mid-sentence or mid-JSON).

**Mitigation:**
- Monitor `finish_reason` in the Groq response:
  ```python
  if response.choices[0].finish_reason == "length":
      raise LLMOutputError("Response truncated — context too long. Reducing prompt size.")
  ```
- If truncated: reduce prompt by removing cluster metadata (keep only theme labels + quotes)
- `llama3-70b-8192` has an 8192-token context — enforce a 2000-token limit on all input prompts

---

## Layer 4 — MCP Delivery & Approval Gate Edge Cases

### EC-40 | User Rejects Gate 1 Repeatedly (Infinite Loop Risk)
**Severity:** High | **Type:** UX | **Detection:** `approval_gates.py`

**Scenario:** The user keeps rejecting Gate 1 (Weekly Pulse), causing endless LLM re-generation cycles.

**Mitigation:**
```python
MAX_GATE_RETRIES = 3

for attempt in range(MAX_GATE_RETRIES):
    pulse = pulse_generator.generate(...)
    approved = approval_gate(1, "Weekly Pulse", pulse)
    if approved:
        break
    if attempt == MAX_GATE_RETRIES - 1:
        raise PipelineAbortError(
            "GATE1_MAX_RETRIES",
            f"Gate 1 rejected {MAX_GATE_RETRIES} times. "
            "Pipeline aborted. Re-run with adjusted configuration."
        )
```
- After max retries: abort cleanly, log all generated variants for post-run inspection

---

### EC-41 | User Approves Gate 1 but Rejects Gate 2
**Severity:** Medium | **Type:** UX | **Detection:** `approval_gates.py`

**Scenario:** The Weekly Pulse (Gate 1) is approved, but the Fee Explainer (Gate 2) is rejected multiple times.

**Mitigation:**
- Gate 1 approval is cached — do NOT re-run pulse generation on Gate 2 rejection
- Apply the same `MAX_GATE_RETRIES = 3` cap to Gate 2
- If Gate 2 aborts: save the approved pulse to `data/outputs/` as a partial result
- Log partial completion status in the audit log: `"status": "partial_gate2_rejected"`

---

### EC-42 | User Abandons Pipeline Mid-Gate (Ctrl+C / Process Kill)
**Severity:** High | **Type:** Infrastructure | **Detection:** Signal handler in `pipeline.py`

**Scenario:** The user presses Ctrl+C or the process is killed while waiting at an approval gate prompt.

**Mitigation:**
```python
import signal

def handle_sigint(sig, frame):
    log.warning("Pipeline interrupted by user (SIGINT). Saving partial state.")
    state_store.save_run_state(..., status="interrupted")
    audit_logger.log_run(..., status="interrupted")
    sys.exit(0)

signal.signal(signal.SIGINT, handle_sigint)
```
- Save all completed work to disk before exiting
- Set run `status = "interrupted"` in state store
- On next run: detect interrupted state and offer to resume from the last completed gate

---

### EC-43 | Gate 3 MCP Call Fails After User Approval
**Severity:** Critical | **Type:** Infrastructure | **Detection:** `gdoc_mcp.py`

**Scenario:** The user approves Gate 3, but the MCP action to append to Google Doc fails (MCP server down, network error, auth failure).

**Mitigation:**
- Wrap MCP call in try/except; retry 3 times with 10s backoff
- If all retries fail: save the payload to `data/outputs/pending_gdoc_YYYY-WNN.json`
- Set run status to `"gdoc_failed"` in state and audit log
- Provide user with manual recovery instructions: paste the pending payload manually
- Do NOT proceed to Gate 4 if Gate 3 fails

---

### EC-44 | Gate 4 MCP Call Fails After Gate 3 Succeeds
**Severity:** High | **Type:** Infrastructure | **Detection:** `gmail_mcp.py`

**Scenario:** Google Doc is successfully appended (Gate 3), but the Gmail draft creation (Gate 4) fails.

**Mitigation:**
- Retry Gmail MCP call 3 times with backoff
- If all fail: save the email payload to `data/outputs/pending_gmail_YYYY-WNN.json`
- Set run status to `"gmail_failed"` in state store
- Log `doc_section_id` (Gate 3 succeeded) in audit — partial completion is recorded
- Do NOT re-run the full pipeline — only the Gmail draft step needs to be retried

---

## MCP / Google Doc Edge Cases

### EC-45 | Google Doc ID in .env Is Incorrect or Doc Was Deleted
**Severity:** Critical | **Type:** Configuration | **Detection:** `gdoc_mcp.py`

**Scenario:** The `GDOC_DOCUMENT_ID` in `.env` points to a non-existent or inaccessible document.

**Mitigation:**
- On startup, add a `preflight_check()` function that verifies the Doc ID is accessible via MCP before running the pipeline
- If preflight fails: abort with clear error: `"Google Doc ID '{id}' not found or not accessible. Update GDOC_DOCUMENT_ID in .env."`

---

### EC-46 | MCP Server Is Down or Unreachable
**Severity:** Critical | **Type:** Infrastructure | **Detection:** `gdoc_mcp.py`, `gmail_mcp.py`

**Scenario:** The MCP server at `MCP_GDOC_SERVER_URL` or `MCP_GMAIL_SERVER_URL` is offline.

**Mitigation:**
- Add MCP connectivity check to `preflight_check()` before each gate
- If server unreachable: surface error immediately before asking for user approval (no point approving if MCP is down)
- Store pending payloads to disk for manual recovery

---

### EC-47 | Doc Append Creates a Duplicate Heading
**Severity:** High | **Type:** Data | **Detection:** `gdoc_mcp.py` (idempotency check)

**Scenario:** The idempotency check fails (e.g., `state_store.py` is queried but returns stale data), causing a second append for the same ISO week, creating a duplicate section in the Google Doc.

**Mitigation:**
- Before appending, query the existing Doc content via MCP and scan for a section heading matching the current ISO week
- If heading found: switch to UPDATE mode automatically, regardless of state store status
- Log: `"Duplicate heading detected. Switching to update mode."`

---

### EC-48 | Google Doc Hits Size Limit
**Severity:** Medium | **Type:** Data | **Detection:** `gdoc_mcp.py`

**Scenario:** The Google Doc has accumulated many weekly entries and is approaching Google's document size limit (~1.02 million characters).

**Mitigation:**
- Before each append, check the current document character count via MCP
- If current size > 800,000 characters: warn the user and suggest archiving older sections
- If size > 950,000 characters: abort the append and create a new archive document instead

---

## MCP / Gmail Edge Cases

### EC-49 | Gmail Draft Creation Fails Silently
**Severity:** High | **Type:** Infrastructure | **Detection:** `gmail_mcp.py`

**Scenario:** The MCP call to create a Gmail draft returns a 200 status but no `email_draft_id` in the response body (silent failure).

**Mitigation:**
```python
response = mcp_gmail.create_draft(payload)
if not response.get("draft_id"):
    raise MCPError("GMAIL_SILENT_FAIL", "Draft creation returned no draft_id")
```
- Always validate that `draft_id` is non-null and non-empty in the response

---

### EC-50 | Draft Accidentally Sent by User Manually
**Severity:** Low | **Type:** Operational | **Detection:** N/A (post-pipeline user action)

**Scenario:** A stakeholder finds the Gmail draft and manually sends it before the weekly review cycle is complete.

**Mitigation:**
- Add a clear subject line prefix: `"[DRAFT - DO NOT SEND] Weekly Pulse + Fee Explainer — Groww"`
- Add a disclaimer banner at the top of the draft body: `"⚠️ This is an automatically generated draft. Please review before sending."`
- Document the draft review process in the README

---

## State & Idempotency Edge Cases

### EC-51 | State File Is Corrupted or Malformed JSON
**Severity:** Critical | **Type:** Infrastructure | **Detection:** `state_store.py`

**Scenario:** `state/run_state.json` contains malformed JSON (e.g., due to a crash mid-write).

**Mitigation:**
```python
try:
    with open(STATE_FILE) as f:
        state = json.load(f)
except json.JSONDecodeError:
    log.error("State file corrupted. Backing up and initializing fresh state.")
    shutil.copy(STATE_FILE, f"{STATE_FILE}.bak.{int(time.time())}")
    state = {}
```
- Always write state atomically using a temp file + rename pattern:
  ```python
  with open(STATE_FILE + ".tmp", "w") as f:
      json.dump(state, f)
  os.replace(STATE_FILE + ".tmp", STATE_FILE)
  ```

---

### EC-52 | Two Pipeline Instances Run Simultaneously for Same Week
**Severity:** Critical | **Type:** Infrastructure | **Detection:** `state_store.py`

**Scenario:** A manual trigger fires while the scheduled run is already in progress, or two scheduled runs overlap due to a configuration error.

**Mitigation:**
- Implement a file-based lock: `state/pipeline.lock`
- On pipeline start: attempt to acquire the lock (fail immediately if locked)
- On pipeline end/interrupt: always release the lock (even via `finally` block)
```python
LOCK_FILE = "state/pipeline.lock"

if os.path.exists(LOCK_FILE):
    raise PipelineAbortError("PIPELINE_ALREADY_RUNNING", 
        "Another pipeline instance is running. Check state/pipeline.lock")

with open(LOCK_FILE, "w") as f:
    f.write(str(os.getpid()))

try:
    run_pipeline()
finally:
    os.remove(LOCK_FILE)
```

---

### EC-53 | ISO Week Computation Crosses Year Boundary
**Severity:** Medium | **Type:** Data | **Detection:** `state_store.py`

**Scenario:** The pipeline runs in the last week of December or first week of January, where ISO week numbering wraps (e.g., Jan 1 can be ISO Week 52 of the previous year).

**Mitigation:**
```python
from datetime import date

def get_iso_week_key() -> str:
    today = date.today()
    iso = today.isocalendar()
    return f"{iso.year}-W{iso.week:02d}"  # e.g., "2026-W01", "2025-W52"
```
- Use `date.isocalendar().year` (not `date.year`) to correctly handle year-boundary weeks
- Write a unit test specifically covering Dec 28 – Jan 4 date ranges

---

### EC-54 | State File Is Missing on First Run
**Severity:** Low | **Type:** Infrastructure | **Detection:** `state_store.py`

**Scenario:** The `state/run_state.json` file does not exist on the very first pipeline run.

**Mitigation:**
```python
def load_state() -> dict:
    if not os.path.exists(STATE_FILE):
        return {}  # Fresh state — not an error
    with open(STATE_FILE) as f:
        return json.load(f)
```
- Initialize an empty state dict; this is expected behavior on first run

---

## Audit Logging Edge Cases

### EC-55 | Audit Log File Is Not Writable
**Severity:** High | **Type:** Infrastructure | **Detection:** `audit_logger.py`

**Scenario:** `logs/audit.jsonl` cannot be written due to file permissions or a full disk.

**Mitigation:**
- Wrap all log writes in try/except
- If write fails: attempt to write to a fallback location (`/tmp/groww_audit_fallback.jsonl`)
- Surface a non-blocking warning to the user; do NOT abort the pipeline over a logging failure
- Log the disk/permission error to stderr

---

### EC-56 | Audit Log Grows Very Large Over Many Weeks
**Severity:** Low | **Type:** Operational | **Detection:** `audit_logger.py`

**Scenario:** After 52+ weeks of weekly runs, `logs/audit.jsonl` becomes very large and slow to query.

**Mitigation:**
- Implement log rotation: archive entries older than `LOG_RETENTION_WEEKS = 52` to `logs/archive/audit_YYYY.jsonl`
- Add `query_log()` function that supports filtering by year to avoid full-file scans
- Dashboard Audit History page paginates results (max 20 rows per page)

---

### EC-57 | Run Completes But Audit Log Entry Is Missing
**Severity:** Medium | **Type:** Data | **Detection:** `audit_logger.py`

**Scenario:** The pipeline completes successfully but the final audit log write fails silently.

**Mitigation:**
- Always write the audit log entry as the very last step in `pipeline.py`
- Wrap in try/except; if write fails, write a minimal "completed but unlogged" entry to stderr
- The state store always has the run recorded — audit log is secondary

---

## Phase 7 — Scheduler Edge Cases

### EC-58 | Scheduler Fires During an Active Pipeline Approval Gate Wait
**Severity:** High | **Type:** Infrastructure | **Detection:** `scheduler.py`

**Scenario:** The scheduler fires its cron job for the next week while the previous week's pipeline is still waiting at an approval gate (e.g., user went on vacation).

**Mitigation:**
- The file-based lock (`state/pipeline.lock`) from EC-52 prevents the new cron job from starting
- Scheduler logs: `"Pipeline already running. Skipping this week's scheduled trigger."`
- The missed scheduled run is NOT automatically retried — user must trigger manually

---

### EC-59 | Scheduled Run Fires With No Internet or API Access
**Severity:** High | **Type:** Infrastructure | **Detection:** `scheduler.py` → `pipeline.py`

**Scenario:** The server loses internet connectivity exactly when the Monday 8:00 AM cron fires.

**Mitigation:**
- Add a connectivity preflight check at the start of `run_pipeline()`:
  ```python
  def check_connectivity():
      try:
          requests.get("https://api.groq.com", timeout=5)
      except requests.exceptions.ConnectionError:
          raise PipelineAbortError("NO_INTERNET", "No internet access. Aborting scheduled run.")
  ```
- Log the connectivity failure with timestamp
- Scheduler loop continues unaffected; next week's run is unimpaired

---

### EC-60 | Cron Expression Misconfigured (Fires Every Minute)
**Severity:** High | **Type:** Configuration | **Detection:** `scheduler.py` startup

**Scenario:** A typo in `SCHEDULER_DAY_OF_WEEK` or `SCHEDULER_HOUR` causes the scheduler to fire far more frequently than intended (e.g., every minute).

**Mitigation:**
- On scheduler startup, print the next 3 scheduled run times clearly:
  ```
  Scheduler started.
  Next runs:
    1. 2026-06-09 08:00:00 IST (Monday)
    2. 2026-06-16 08:00:00 IST (Monday)
    3. 2026-06-23 08:00:00 IST (Monday)
  ```
- The file-based lock (EC-52) also limits rapid-fire concurrent runs
- Validate cron parameters against an allowlist on startup

---

### EC-61 | Server Restarts Mid-Pipeline Run
**Severity:** High | **Type:** Infrastructure | **Detection:** `state_store.py` on next startup

**Scenario:** The server or process crashes mid-pipeline (e.g., OOM kill) while a run is in progress.

**Mitigation:**
- On `pipeline.py` startup: check if `state/pipeline.lock` exists with a PID that is no longer running
  ```python
  if os.path.exists(LOCK_FILE):
      stored_pid = int(open(LOCK_FILE).read())
      if not psutil.pid_exists(stored_pid):
          log.warning(f"Stale lock detected (PID {stored_pid} not running). Clearing lock.")
          os.remove(LOCK_FILE)
  ```
- Mark the interrupted run as `"status": "crashed"` in the state store
- Offer the user the option to resume from the last completed step

---

### EC-62 | Manual Trigger Fires While Scheduled Run Is Active
**Severity:** High | **Type:** Infrastructure | **Detection:** `trigger.py` → lock check

**Scenario:** A user hits `POST /trigger` while the Monday cron is still running.

**Mitigation:**
- `trigger.py` checks for `state/pipeline.lock` before spawning a thread
- If locked: return `409 Conflict` with body: `{"error": "Pipeline already running. Try again later."}`

---

## Phase 8 — Dashboard UI Edge Cases

### EC-63 | Dashboard Loaded With No Pipeline Runs Yet
**Severity:** Medium | **Type:** UI | **Detection:** `app.py`, all pages

**Scenario:** A user opens the dashboard before any pipeline run has completed.

**Mitigation:**
- Each page checks if its data source exists before rendering
- If no data: render a friendly empty state:
  ```
  📊 No data yet.
  Run the pipeline first: click "Run Pipeline" in the sidebar
  or trigger via: curl -X POST http://localhost:5050/trigger
  ```
- Never raise an unhandled exception on missing data files

---

### EC-64 | Dashboard Loaded While Pipeline Is Currently Running
**Severity:** Medium | **Type:** UI | **Detection:** `app.py`

**Scenario:** A user views the dashboard while a pipeline run is in progress, showing stale data from last week.

**Mitigation:**
- Check for the existence of `state/pipeline.lock` on every page load
- If lock exists: display a banner: `"⚙️ Pipeline is currently running. Data shown is from the last completed run."`
- Auto-refresh the page every 30 seconds while the lock is active

---

### EC-65 | Pulse JSON File Is Corrupted or Partially Written
**Severity:** High | **Type:** Data | **Detection:** Dashboard `weekly_pulse.py`

**Scenario:** The `data/outputs/pulse_YYYY-WNN.json` file was partially written during a crash and contains invalid JSON.

**Mitigation:**
```python
try:
    with open(pulse_file) as f:
        data = json.load(f)
except json.JSONDecodeError:
    st.error(
        f"⚠️ Pulse data for {week} is corrupted. "
        "Re-run the pipeline to regenerate."
    )
    st.stop()
```
- Never crash the dashboard on bad JSON — always surface a user-friendly error

---

### EC-66 | Audit Log Has Entries With Missing Fields
**Severity:** Medium | **Type:** Data | **Detection:** Dashboard `audit_history.py`

**Scenario:** Some audit log entries from older runs are missing newer fields (e.g., `email_draft_id` was added in a later version), causing `KeyError` when the dashboard renders the table.

**Mitigation:**
- Always use `.get(field, default)` when reading audit log fields in the dashboard
- Display `"—"` for missing fields rather than crashing
- Add a migration utility that backfills missing fields in older audit entries

---

### EC-67 | Week Selector Shows a Week With Only Partial Data
**Severity:** Medium | **Type:** UI | **Detection:** Dashboard week selector

**Scenario:** A week where the pipeline was interrupted (e.g., Gate 3 failed) appears in the week selector, but only has pulse data — no fee explainer or Doc section.

**Mitigation:**
- Load the run status from `state/run_state.json` alongside the week selector
- Tag incomplete weeks with a status badge: `"⚠️ Partial"`
- When a partial week is selected: render what's available and display a clear callout: `"Fee Explainer not available for this week (pipeline did not complete)."`

---

### EC-68 | Run Pipeline Button Pressed Multiple Times Rapidly
**Severity:** Medium | **Type:** UI | **Detection:** Dashboard Run Pipeline page

**Scenario:** A user double-clicks or rapidly clicks the "▶ Run Pipeline Now" button, sending multiple `POST /trigger` requests.

**Mitigation:**
- Disable the button immediately after first click using Streamlit session state:
  ```python
  if st.session_state.get("trigger_sent"):
      st.button("▶ Run Pipeline Now", disabled=True)
  else:
      if st.button("▶ Run Pipeline Now"):
          st.session_state["trigger_sent"] = True
          requests.post(...)
  ```
- The file-based lock on the Flask side (EC-62) also rejects duplicate concurrent triggers

---

## Security Edge Cases

### EC-69 | `.env` File Accidentally Committed to Git
**Severity:** Critical | **Type:** Security | **Detection:** Pre-commit hook / CI check

**Scenario:** The `.env` file containing `GROQ_API_KEY` is accidentally committed to a Git repository.

**Mitigation:**
- Add `.env` to `.gitignore` immediately (Phase 1 task)
- Set up a pre-commit hook using `detect-secrets` or `git-secrets`:
  ```bash
  pip install detect-secrets
  detect-secrets scan > .secrets.baseline
  ```
- Add to `.gitignore`:
  ```
  .env
  *.env
  .env.*
  !.env.example
  ```
- If committed: immediately rotate the Groq API key; treat the old key as compromised

---

### EC-70 | PII Appears in Audit Log Due to Scrubber Miss
**Severity:** High | **Type:** Security | **Detection:** Audit log review

**Scenario:** The Presidio PII scrubber misses a PII entity in a review, and that un-scrubbed text ends up in the audit log (via quotes or the weekly summary).

**Mitigation:**
- Run a final Presidio scan on the entire generated report payload before writing to the audit log
- If PII detected in the payload: redact it before logging
- Log a `"pii_post_scrub_detected": true` flag in the audit entry for human review
- The quotes passed to the LLM must always be from the PII-scrubbed corpus, not the raw corpus

---

### EC-71 | Groq API Key Exposed in Logs or Error Messages
**Severity:** High | **Type:** Security | **Detection:** Log review

**Scenario:** An exception handler accidentally logs the full Groq API key (e.g., in the exception message of an HTTP error response that includes request headers).

**Mitigation:**
- Use a `SecretFilter` log filter that scrubs the `GROQ_API_KEY` value from all log messages before writing
  ```python
  class SecretFilter(logging.Filter):
      def filter(self, record):
          record.msg = record.msg.replace(os.getenv("GROQ_API_KEY", ""), "***REDACTED***")
          return True
  ```
- Never log the full Groq client object or HTTP request headers

---

### EC-72 | Dashboard Trigger Endpoint Exposed on Public Network
**Severity:** Critical | **Type:** Security | **Detection:** Network configuration review

**Scenario:** The Flask trigger server (`trigger.py`) is accidentally bound to `0.0.0.0` instead of `127.0.0.1`, making the `POST /trigger` endpoint publicly accessible on the internet.

**Mitigation:**
- Always bind Flask to localhost explicitly:
  ```python
  app.run(host="127.0.0.1", port=int(os.getenv("SCHEDULER_TRIGGER_PORT", 5050)))
  ```
- Add a startup warning if host is not `127.0.0.1`
- Add a simple API token check for the trigger endpoint:
  ```python
  @app.route("/trigger", methods=["POST"])
  def trigger_pipeline():
      token = request.headers.get("X-Trigger-Token")
      if token != os.getenv("TRIGGER_SECRET_TOKEN"):
          return jsonify({"error": "Unauthorized"}), 401
  ```

---

## Summary Matrix

| Severity | Count | Key Phases Affected |
|---|---|---|
| **Critical** | 16 | Ingestion, Embedding, LLM, MCP, State, Scheduler, Security |
| **High** | 32 | All phases |
| **Medium** | 18 | Cleaning, Clustering, LLM, Approval Gates, Dashboard |
| **Low** | 6 | Cleaning, Audit Logging, Gmail, Operational |
| **Total** | **72** | All 8 phases |

---

## Recommended Testing Priorities

### Must Test Before Any Deployment
1. EC-01, EC-03 — Review volume edge cases (mock scraper to return 0 / <50 reviews)
2. EC-24 — Verbatim quote validation (inject a quote not in source corpus; expect assertion error)
3. EC-34 — Confirm LLM hallucinated quotes are architecturally impossible (unit test quote extractor isolation)
4. EC-51, EC-52 — State store corruption and concurrent run prevention
5. EC-69 — `.gitignore` contains `.env` (verify with `git check-ignore -v .env`)
6. EC-72 — Flask bound to `127.0.0.1` only (verify with `netstat`)

### Should Test Before Production
7. EC-30, EC-31 — LLM JSON extraction and schema validation
8. EC-37, EC-38 — Groq rate limit and full outage fallback
9. EC-42 — SIGINT handler saves state on Ctrl+C
10. EC-43, EC-44 — MCP failure after user approval
11. EC-62 — Concurrent trigger lock behavior
12. EC-63, EC-65 — Dashboard empty states and corrupted JSON handling
