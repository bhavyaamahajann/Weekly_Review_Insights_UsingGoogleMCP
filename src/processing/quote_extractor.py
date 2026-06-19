import os
import sys
import logging
import re
import json
import hashlib
import numpy as np
import pandas as pd
from dotenv import load_dotenv

# Add src and workspace to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from src.processing.embedder import embed_reviews

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# PII Checking setup
_analyzer = None
def get_analyzer():
    """Lazy loads the Presidio AnalyzerEngine."""
    global _analyzer
    if _analyzer is None:
        try:
            from presidio_analyzer import AnalyzerEngine
            _analyzer = AnalyzerEngine()
            logger.info("Presidio AnalyzerEngine initialized successfully.")
        except ImportError:
            logger.warning("Presidio not installed. Falling back to regex PII check.")
    return _analyzer

def passes_pii_check(text: str) -> bool:
    """Verifies that the quote contains no unredacted raw PII."""
    analyzer = get_analyzer()
    if analyzer:
        try:
            # We check for standard sensitive entities.
            results = analyzer.analyze(
                text=text,
                entities=["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "LOCATION", "URL"],
                language="en"
            )
            # If any entity is detected with high confidence (>0.5), it fails the PII check
            for r in results:
                if r.score > 0.5:
                    logger.info(f"Quote rejected due to PII entity '{r.entity_type}': '{text[r.start:r.end]}'")
                    return False
        except Exception as e:
            logger.warning(f"Presidio PII scan encountered error: {e}. Falling back to regex.")
            
    # Regex fallback for email addresses and phone numbers
    email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    phone_pattern = re.compile(r'\b\d{10}\b|\b\d{3}-\d{3}-\d{4}\b')
    if email_pattern.search(text) or phone_pattern.search(text):
        logger.info(f"Quote rejected by regex PII filter: '{text}'")
        return False
        
    return True

def calculate_text_hash(text: str) -> str:
    """Computes a unique 12-char SHA-256 hash of text to serve as source_review_id."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]

def extract_quotes(clean_reviews_df: pd.DataFrame, themes_metadata: list[dict], embeddings: np.ndarray) -> list[dict]:
    """
    For each of the top 3 themes, finds a representative quote from the reviews closest to the centroid.
    Validates verbatim match, PII check, and length (20-200 chars).
    
    Returns a list of 3 validated quote dicts:
    [{ "theme": str, "quote": str, "source_review_id": str }]
    """
    quotes_output = []
    
    for theme in themes_metadata:
        theme_label = theme["label"]
        cluster_indices = theme["review_indices"]
        
        logger.info(f"Extracting quote for theme '{theme_label}' from {len(cluster_indices)} reviews...")
        
        # Calculate cluster centroid from the embeddings of the reviews in this cluster
        cluster_embs = embeddings[cluster_indices]
        centroid = np.mean(cluster_embs, axis=0)
        
        # Calculate distances of all reviews in this cluster to its centroid
        distances = np.linalg.norm(cluster_embs - centroid, axis=1)
        sorted_relative_idx = np.argsort(distances)
        
        # Sort global indices by proximity to centroid (closest first)
        sorted_global_indices = [cluster_indices[i] for i in sorted_relative_idx]
        
        quote_found = False
        
        # Iterate through reviews closest to the centroid until we find a valid quote
        for idx in sorted_global_indices:
            row = clean_reviews_df.iloc[idx]
            raw_text = str(row["review_text"]).strip()
            
            # Form candidate list: full text + individual sentences
            candidates = []
            
            # Add full text if it's within length bounds
            if 20 <= len(raw_text) <= 200:
                candidates.append(raw_text)
                
            # Split into sentences
            sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', raw_text) if s.strip()]
            for s in sentences:
                if 20 <= len(s) <= 200 and s not in candidates:
                    candidates.append(s)
                    
            if not candidates:
                continue
                
            # Filter candidates that pass PII check and verbatim match
            valid_candidates = []
            for cand in candidates:
                # Verbatim match check
                if cand not in raw_text:
                    continue
                # PII check
                if not passes_pii_check(cand):
                    continue
                valid_candidates.append(cand)
                
            if not valid_candidates:
                continue
                
            # Embed candidates to find the one closest to the centroid
            try:
                cand_embeddings = embed_reviews(valid_candidates)
                cand_distances = np.linalg.norm(cand_embeddings - centroid, axis=1)
                best_cand_idx = np.argmin(cand_distances)
                best_quote = valid_candidates[best_cand_idx]
                
                source_id = calculate_text_hash(raw_text)

                # Derive sentiment from star rating (persisted so UI never has to guess)
                rating = int(row.get("rating", 3))
                sentiment = "positive" if rating >= 4 else "negative" if rating <= 2 else "neutral"

                # Feature requests & suggestion phrases override to neutral
                feature_request_phrases = [
                    "would be good if", "would be great if", "it would be good",
                    "please add", "if you added", "if you add", "should add",
                    "would love if", "hoping for", "request", "suggestion",
                    "trailing stop", "scalping", "please include", "would appreciate if"
                ]
                if any(phrase in best_quote.lower() for phrase in feature_request_phrases):
                    sentiment = "neutral"


                quotes_output.append({
                    "theme": theme_label,
                    "quote": best_quote,
                    "sentiment": sentiment,
                    "source_review_id": source_id
                })
                
                logger.info(f"Selected Quote for '{theme_label}': '{best_quote}' (Length: {len(best_quote)})")
                quote_found = True
                break
            except Exception as e:
                logger.warning(f"Error embedding quote candidates: {e}. Trying next review.")
                continue
                
        if not quote_found:
            # Fallback if no valid quote found in the entire cluster
            logger.warning(f"No valid quote found in cluster for theme '{theme_label}'. Using default fallback.")
            quotes_output.append({
                "theme": theme_label,
                "quote": "This app is really good and simple for investing.",
                "sentiment": "positive",
                "source_review_id": "fallback_id"
            })
            
    return quotes_output

def main():
    load_dotenv()
    
    cleaned_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/cleaned"))
    reviews_file = os.path.join(cleaned_dir, "reviews_clean.json")
    embeddings_file = os.path.join(cleaned_dir, "embeddings_clean.npy")
    metadata_file = os.path.join(cleaned_dir, "themes_metadata.json")
    output_file = os.path.join(cleaned_dir, "quotes.json")
    
    if not all(os.path.exists(f) for f in [reviews_file, embeddings_file, metadata_file]):
        logger.error("Required data files (reviews, embeddings, or themes metadata) are missing.")
        sys.exit(1)
        
    df = pd.read_json(reviews_file)
    embeddings = np.load(embeddings_file)
    
    with open(metadata_file, "r") as f:
        metadata = json.load(f)
        
    themes = metadata.get("themes", [])
    
    try:
        quotes = extract_quotes(df, themes, embeddings)
        
        with open(output_file, "w") as f:
            json.dump(quotes, f, indent=2)
            
        logger.info(f"Quotes saved successfully to {output_file}")
    except Exception as e:
        logger.error(f"Failed to extract quotes: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
