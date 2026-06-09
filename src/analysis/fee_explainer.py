import os
import sys
import json
import time
import logging
import re
from datetime import date
from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError
import groq
from groq import Groq

# Add src and workspace to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from src.utils.exceptions import PipelineAbortError

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

PRIMARY_MODEL = "llama-3.3-70b-versatile"
FALLBACK_MODEL = "llama-3.1-8b-instant"

OPINION_PHRASE_BLOCKLIST = ["you should", "we recommend", "it is advisable", "consider", "it's better to", "you may want to"]

class FeeExplainerOutput(BaseModel):
    scenario: str = Field(..., description="The fee scenario name")
    bullets: list[str] = Field(..., description="Factual, neutral explanation bullets")
    sources: list[str] = Field(..., description="List of verification sources")
    last_checked: str = Field(..., description="Date of check, e.g. June 2026")

def get_iso_week_key() -> str:
    """Computes the ISO week key (e.g. 2026-W23) correctly handling year boundaries."""
    today = date.today()
    iso = today.isocalendar()
    return f"{iso.year}-W{iso.week:02d}"

def get_groq_client() -> Groq:
    """Initializes and returns the Groq client. Aborts if key is invalid/missing."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or api_key == "your_groq_api_key_here":
        raise PipelineAbortError(
            "GROQ_AUTH_FAILED",
            "Groq API authentication failed. GROQ_API_KEY is not set or placeholder in .env."
        )
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

def check_opinionated_language(bullets: list[str]) -> tuple[bool, int, str]:
    """Checks if any bullet contains opinionated blocklisted phrases."""
    for idx, bullet in enumerate(bullets):
        bullet_lower = bullet.lower()
        for phrase in OPINION_PHRASE_BLOCKLIST:
            if phrase in bullet_lower:
                return True, idx, phrase
    return False, -1, ""

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
                temperature=0.0,  # 0.0 temperature for maximum consistency and compliance facts
                max_tokens=500,
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

def generate_fee_explainer(scenario: str = "Mutual Fund Exit Load", sources: list[str] = None, iso_week: str = None) -> dict:
    """
    Generates compliance-compliant fee explainer using Groq.
    Validates output schema, bullet caps, and neutral tone.
    """
    if not iso_week:
        iso_week = get_iso_week_key()
        
    if not sources:
        sources = [
            "Groww Help Center",
            "Groww Exit Load Information Page",
            "SEBI Investor Education Resources"
        ]
        
    client = get_groq_client()
    
    today_str = date.today().strftime("%B %Y")
    
    system_prompt = (
        "You are a compliance writer for Groww.\n"
        "Generate a factual, neutral fee explanation. Use ONLY verified facts.\n"
        "Respond ONLY with valid JSON. Do NOT add recommendations, opinions, or comparisons."
    )
    
    user_prompt = (
        f"Generate a fee explainer for: {scenario}\n\n"
        f"Rules:\n"
        f"- Maximum 6 bullet points\n"
        f"- Neutral tone, facts only\n"
        f"- Do NOT use opinion phrases or recommendations (e.g. \"you should\", \"we recommend\", \"it is advisable\")\n"
        f"- Include source references: {', '.join(sources)}\n"
        f"- Include a \"last_checked\" date field: \"{today_str}\"\n\n"
        f"Output JSON schema:\n"
        f"{{\n"
        f"  \"scenario\": \"{scenario}\",\n"
        f"  \"bullets\": [\"<bullet_1>\", \"<bullet_2>\", \"<bullet_3>\", \"<bullet_4>\", \"<bullet_5>\", \"<bullet_6>\"],\n"
        f"  \"sources\": {json.dumps(sources)},\n"
        f"  \"last_checked\": \"{today_str}\"\n"
        f"}}\n"
    )
    
    models_to_try = [
        (PRIMARY_MODEL, "Primary model"),
        (FALLBACK_MODEL, "Fallback model")
    ]
    
    last_error = None
    
    for model, label in models_to_try:
        logger.info(f"Triggering {label} ({model}) for fee explainer...")
        
        try:
            # Sleep 2s to respect RPM/TPM limits
            time.sleep(2.0)
            
            raw_response = call_groq_api(client, model, system_prompt, user_prompt)
            data_dict = extract_json_from_response(raw_response)
            
            # Pydantic validation
            explainer = FeeExplainerOutput(**data_dict)
            
            # Verify and cap bullets
            bullets = explainer.bullets
            if len(bullets) > 6:
                logger.warning(f"Fee explainer returned {len(bullets)} bullets. Programmatically capping to 6.")
                bullets = bullets[:6]
                
            # Scan for opinionated phrases
            has_opinion, idx, phrase = check_opinionated_language(bullets)
            if has_opinion:
                logger.warning(f"Bullet index {idx} contains opinionated phrase '{phrase}'. Retrying with feedback.")
                feedback_prompt = (
                    f"{user_prompt}\n\n"
                    f"Warning: In your previous attempt, the bullet point:\n"
                    f"\"{bullets[idx]}\"\n"
                    f"contained the prohibited opinion phrase '{phrase}'. Please rewrite the explanations ensuring "
                    f"complete neutrality and zero recommendation language."
                )
                time.sleep(2.0)
                raw_response = call_groq_api(client, model, system_prompt, feedback_prompt)
                data_dict = extract_json_from_response(raw_response)
                explainer = FeeExplainerOutput(**data_dict)
                bullets = explainer.bullets
                if len(bullets) > 6:
                    bullets = bullets[:6]
                # Re-check opinions
                still_opinion, _, _ = check_opinionated_language(bullets)
                if still_opinion:
                    raise ValueError("Failed opinion check twice.")
                    
            # Assemble output dict
            output_data = {
                "scenario": explainer.scenario,
                "bullets": bullets,
                "sources": explainer.sources,
                "last_checked": explainer.last_checked
            }
            
            # Save output to outputs folder
            outputs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/outputs"))
            os.makedirs(outputs_dir, exist_ok=True)
            output_file = os.path.join(outputs_dir, f"fee_explainer_{iso_week}.json")
            
            with open(output_file, "w") as f:
                json.dump(output_data, f, indent=2)
                
            logger.info(f"Fee explainer successfully generated and saved to {output_file}")
            return output_data
            
        except PipelineAbortError as e:
            raise e
        except (ValidationError, ValueError, json.JSONDecodeError, Exception) as e:
            logger.warning(f"Failed to generate fee explainer with model {model} due to: {e}")
            last_error = e
            # Loop will continue to fallback model
            
    # If both models failed
    raise RuntimeError(f"All Groq models failed to generate valid fee explainer. Last error: {last_error}")

def main():
    load_dotenv()
    
    # Defaults
    scenario = "Mutual Fund Exit Load"
    sources = [
        "Groww Help Center",
        "Groww Exit Load Information Page",
        "SEBI Investor Education Resources"
    ]
    
    try:
        generate_fee_explainer(scenario, sources)
    except Exception as e:
        logger.error(f"Execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
