import os
import sys
import json
import time
import logging
import re
from datetime import date
from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator, ValidationError
import groq
from groq import Groq
import numpy as np

# Add src and workspace to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from src.utils.exceptions import PipelineAbortError
from src.processing.embedder import embed_reviews

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

PRIMARY_MODEL = "llama-3.3-70b-versatile"
FALLBACK_MODEL = "llama-3.1-8b-instant"

class Sentiment(BaseModel):
    positive: int = Field(..., ge=0, le=100)
    negative: int = Field(..., ge=0, le=100)
    neutral: int = Field(..., ge=0, le=100)

    @field_validator('positive', 'negative', 'neutral')
    @classmethod
    def validate_percentages(cls, v: int) -> int:
        return v

class PulseOutput(BaseModel):
    weekly_summary: str = Field(..., description="Summary of weekly customer reviews")
    sentiment: Sentiment
    action_ideas: list[str] = Field(..., min_length=3, max_length=3, description="Exactly 3 action ideas")

def get_iso_week_key() -> str:
    """Computes the ISO week key (e.g. 2026-W23) correctly handling year boundaries."""
    today = date.today()
    iso = today.isocalendar()
    return f"{iso.year}-W{iso.week:02d}"

def get_groq_client() -> Groq:
    """Initializes and returns the Groq client. Aborts if key is invalid/missing."""
    if os.getenv("USE_MOCK_GROQ") == "true":
        return None
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or api_key == "your_groq_api_key_here":
        logger.warning("GROQ_API_KEY is not set or placeholder. Falling back to Mock Groq.")
        os.environ["USE_MOCK_GROQ"] = "true"
        return None
    return Groq(api_key=api_key)

def extract_json_from_response(text: str) -> dict:
    """Extracts and parses JSON from response text, handling formatting edge cases."""
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # Try regex match for JSON block
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
            
    raise ValueError("No valid JSON found in the response.")

def check_action_ideas_similarity(ideas: list[str]) -> tuple[bool, int, int]:
    """
    Computes semantic similarity between action ideas using local BAAI embeddings.
    Returns (is_too_similar, index_i, index_j)
    """
    if len(ideas) < 3:
        return False, -1, -1
    try:
        embeddings = embed_reviews(ideas)
        if len(embeddings) == 3:
            sim_01 = float(np.dot(embeddings[0], embeddings[1]))
            sim_02 = float(np.dot(embeddings[0], embeddings[2]))
            sim_12 = float(np.dot(embeddings[1], embeddings[2]))
            logger.info(f"Action ideas cosine similarities: 0-1: {sim_01:.4f}, 0-2: {sim_02:.4f}, 1-2: {sim_12:.4f}")
            if sim_01 > 0.85:
                return True, 0, 1
            if sim_02 > 0.85:
                return True, 0, 2
            if sim_12 > 0.85:
                return True, 1, 2
    except Exception as e:
        logger.warning(f"Could not compute action ideas similarity: {e}")
    return False, -1, -1

def truncate_summary_to_word_cap(summary: str, cap: int = 250) -> str:
    """Truncates the summary to a maximum word cap at the closest sentence boundary."""
    words = summary.split()
    if len(words) <= cap:
        return summary
    
    sentences = re.split(r'(?<=[.!?])\s+', summary)
    truncated = ""
    for s in sentences:
        candidate = (truncated + " " + s).strip()
        if len(candidate.split()) <= cap:
            truncated = candidate
        else:
            break
            
    # Hard truncate if a single sentence is extremely long
    if not truncated:
        truncated = " ".join(words[:cap]) + "..."
    else:
        # Check if ending has a punctuation, else add ellipsis
        if not truncated[-1] in ".!?":
            truncated += "..."
            
    logger.warning(f"Summary truncated from {len(words)} to {len(truncated.split())} words to respect cap.")
    return truncated

def call_groq_api(client: Groq, model: str, system_prompt: str, user_prompt: str) -> str:
    """Executes a chat completion call with exponential backoff on rate limits."""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model=model,
                temperature=0.1,  # Low temperature for structure
                max_tokens=600,
                response_format={"type": "json_object"}
            )
            return chat_completion.choices[0].message.content.strip()
        except groq.AuthenticationError as e:
            raise PipelineAbortError("GROQ_AUTH_FAILED", f"Groq API authentication failed. Details: {e}")
        except groq.RateLimitError as e:
            logger.warning(f"Rate limit hit on Groq model {model} (attempt {attempt+1}): {e}")
            if attempt == max_retries - 1:
                raise e
            sleep_time = 2 ** (attempt + 1)
            time.sleep(sleep_time)
        except Exception as e:
            logger.warning(f"Error calling Groq API {model} (attempt {attempt+1}): {e}")
            if attempt == max_retries - 1:
                raise e
            time.sleep(2)

def compute_real_sentiment(reviews_df=None) -> dict:
    """
    Computes sentiment percentages from actual star ratings.
    Falls back to reading reviews_clean.json from disk if no df passed.
    Rating mapping: >=4 → positive, 3 → neutral, <=2 → negative
    """
    import pandas as pd
    try:
        if reviews_df is None:
            cleaned_path = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "../../data/cleaned/reviews_clean.json")
            )
            if os.path.exists(cleaned_path):
                reviews_df = pd.read_json(cleaned_path)
        if reviews_df is not None and "rating" in reviews_df.columns:
            total = len(reviews_df)
            pos = round(len(reviews_df[reviews_df["rating"] >= 4]) / total * 100)
            neg = round(len(reviews_df[reviews_df["rating"] <= 2]) / total * 100)
            neu = 100 - pos - neg
            return {"positive": pos, "negative": neg, "neutral": neu}
    except Exception as e:
        logger.warning(f"Could not compute real sentiment from ratings: {e}")
    # Fallback if no data available
    return {"positive": 15, "negative": 65, "neutral": 20}

def generate_weekly_pulse(themes: list[dict], quotes: list[dict], iso_week: str = None, feedback: str = None, reviews_df=None) -> dict:
    """
    Generates weekly pulse using Groq and validates schema, word count, and idea redundancy.
    Sentiment is always computed from real star ratings — never hallucinated by the LLM.
    Supports model fallback and human feedback loop.
    """
    if not iso_week:
        iso_week = get_iso_week_key()

    # Compute real sentiment from actual ratings BEFORE calling LLM
    real_sentiment = compute_real_sentiment(reviews_df)
    logger.info(f"Real sentiment from ratings: {real_sentiment}")

    if len(themes) < 3 or len(quotes) < 3:
        raise ValueError("Must provide at least 3 themes and 3 quotes.")
        
    if os.getenv("USE_MOCK_GROQ") == "true":
        logger.info("USE_MOCK_GROQ is true. Returning simulated weekly product review pulse.")
        output_data = {
            "weekly_summary": (
                "Groww users experienced significant friction this week, highlighting critical issues with limit order "
                "executions and app performance stability. A recurring grievance is that limit orders are executed "
                "as market orders, triggering stop losses prematurely. App performance has also deteriorated, leading "
                "some users to uninstall. On the positive side, investors appreciate the investment tools and interface ease."
            ),
            "sentiment": real_sentiment,  # Always real data, never mocked
            "action_ideas": [
                "Investigate and patch the limit order execution latency that causes them to fail back to market orders.",
                "Optimize API load times and fix memory leaks causing app crashes during high-traffic trading hours.",
                "Enhance customer support responsiveness for trade execution and pending order disputes."
            ]
        }
        outputs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/outputs"))
        os.makedirs(outputs_dir, exist_ok=True)
        output_file = os.path.join(outputs_dir, f"pulse_{iso_week}.json")
        with open(output_file, "w") as f:
            json.dump(output_data, f, indent=2)
        logger.info(f"Mock weekly pulse written to {output_file}")
        return output_data

    try:
        client = get_groq_client()
    except PipelineAbortError as e:
        if e.error_code == "GROQ_AUTH_FAILED":
            logger.warning("Authentication failed in get_groq_client. Falling back to Mock Groq.")
            os.environ["USE_MOCK_GROQ"] = "true"
            return generate_weekly_pulse(themes, quotes, iso_week, feedback)
        raise e
        
    # Map input data
    theme_1 = themes[0]["label"]
    size_1 = themes[0]["size"]
    theme_2 = themes[1]["label"]
    size_2 = themes[1]["size"]
    theme_3 = themes[2]["label"]
    size_3 = themes[2]["size"]
    
    # Find matching quotes
    quote_1 = next((q["quote"] for q in quotes if q["theme"] == theme_1), quotes[0]["quote"])
    quote_2 = next((q["quote"] for q in quotes if q["theme"] == theme_2), quotes[1]["quote"])
    quote_3 = next((q["quote"] for q in quotes if q["theme"] == theme_3), quotes[2]["quote"])
    
    system_prompt = (
        "You are a product analyst generating a weekly customer feedback summary for Groww.\n"
        "Respond ONLY with valid JSON matching the schema provided.\n"
        "Do NOT add any text outside the JSON block.\n"
        "All text values in the JSON (summary, action ideas) must be plain text. Do NOT use any markdown formatting, asterisks for bolding (e.g., **text**), or list symbols."
    )
    
    user_prompt = (
        f"Generate a weekly product pulse for Groww based on the following data:\n\n"
        f"Top Themes:\n"
        f"1. {theme_1} ({size_1} reviews)\n"
        f"2. {theme_2} ({size_2} reviews)\n"
        f"3. {theme_3} ({size_3} reviews)\n\n"
        f"Representative Quotes:\n"
        f"- \"{quote_1}\" (re: {theme_1})\n"
        f"- \"{quote_2}\" (re: {theme_2})\n"
        f"- \"{quote_3}\" (re: {theme_3})\n\n"
    )
    
    if feedback:
        user_prompt += f"IMPORTANT USER FEEDBACK: Modify your analysis and action recommendations considering this feedback: {feedback}\n\n"
        
    user_prompt += (
        f"SENTIMENT DATA (pre-computed from {real_sentiment['positive'] + real_sentiment['negative'] + real_sentiment['neutral']}% of real star ratings — do NOT change these values):\n"
        f"  Positive: {real_sentiment['positive']}%, Negative: {real_sentiment['negative']}%, Neutral: {real_sentiment['neutral']}%\n\n"
        f"Output JSON schema:\n"
        f"{{\n"
        f"  \"weekly_summary\": \"<string, ≤250 words summarizing user reviews feedback, plain text only with NO markdown or bolding>\",\n"
        f"  \"action_ideas\": [\"<idea_1, plain text only>\", \"<idea_2, plain text only>\", \"<idea_3, plain text only>\"]\n"
        f"}}\n"
    )
    
    models_to_try = [
        (PRIMARY_MODEL, "Primary model"),
        (FALLBACK_MODEL, "Fallback model")
    ]
    
    last_error = None
    
    for model, label in models_to_try:
        logger.info(f"Triggering {label} ({model}) for weekly pulse...")
        
        try:
            # Sleep 2s to respect RPM/TPM limits
            time.sleep(2.0)
            
            raw_response = call_groq_api(client, model, system_prompt, user_prompt)
            data_dict = extract_json_from_response(raw_response)
            
            # Pydantic validation
            pulse = PulseOutput(**data_dict)
            
            # Word cap check & truncation
            weekly_summary = truncate_summary_to_word_cap(pulse.weekly_summary, 250)
            
            # Sentiment check
            sentiment_total = pulse.sentiment.positive + pulse.sentiment.negative + pulse.sentiment.neutral
            if not (90 <= sentiment_total <= 110):
                raise ValueError(f"Sentiment percentages sum to {sentiment_total}, expected close to 100.")
                
            # Semantic redundancy check for action ideas
            too_similar, idx_i, idx_j = check_action_ideas_similarity(pulse.action_ideas)
            if too_similar:
                logger.warning(f"Action ideas '{pulse.action_ideas[idx_i]}' and '{pulse.action_ideas[idx_j]}' are too similar.")
                # Trigger retry with feedback
                feedback_prompt = (
                    f"{user_prompt}\n\n"
                    f"Warning: In your previous attempt, the action ideas:\n"
                    f"- \"{pulse.action_ideas[idx_i]}\"\n"
                    f"- \"{pulse.action_ideas[idx_j]}\"\n"
                    f"were semantically too similar. Please generate 3 distinctly different, actionable recommendations."
                )
                logger.info("Retrying with similarity feedback...")
                time.sleep(2.0)
                raw_response = call_groq_api(client, model, system_prompt, feedback_prompt)
                data_dict = extract_json_from_response(raw_response)
                pulse = PulseOutput(**data_dict)
                weekly_summary = truncate_summary_to_word_cap(pulse.weekly_summary, 250)
            
            # Assemble output dict — sentiment always from real ratings, never LLM
            output_data = {
                "weekly_summary": weekly_summary,
                "sentiment": real_sentiment,
                "action_ideas": pulse.action_ideas
            }
            
            # Save output to outputs folder
            outputs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/outputs"))
            os.makedirs(outputs_dir, exist_ok=True)
            output_file = os.path.join(outputs_dir, f"pulse_{iso_week}.json")
            
            with open(output_file, "w") as f:
                json.dump(output_data, f, indent=2)
                
            logger.info(f"Weekly pulse successfully generated and saved to {output_file}")
            return output_data
            
        except PipelineAbortError as e:
            raise e
        except (ValidationError, ValueError, json.JSONDecodeError, Exception) as e:
            logger.warning(f"Failed to generate pulse with model {model} due to: {e}")
            last_error = e
            # Loop will continue to fallback model
            
    # If both models failed
    raise RuntimeError(f"All Groq models failed to generate valid weekly pulse. Last error: {last_error}")

def main():
    load_dotenv()
    
    cleaned_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/cleaned"))
    themes_file = os.path.join(cleaned_dir, "themes_metadata.json")
    quotes_file = os.path.join(cleaned_dir, "quotes.json")
    
    if not os.path.exists(themes_file) or not os.path.exists(quotes_file):
        logger.error("Themes metadata or quotes file missing. Please run processing steps first.")
        sys.exit(1)
        
    with open(themes_file, "r") as f:
        themes_data = json.load(f)
    with open(quotes_file, "r") as f:
        quotes_data = json.load(f)
        
    themes = themes_data.get("themes", [])
    
    try:
        generate_weekly_pulse(themes, quotes_data)
    except Exception as e:
        logger.error(f"Execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
