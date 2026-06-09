import os
import sys
import hashlib
import logging
import re
import pandas as pd
from dotenv import load_dotenv
from langdetect import detect, DetectorFactory
import ftfy

# Set seed for langdetect reproducibility
DetectorFactory.seed = 0

# Add src to python path to import exceptions
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from src.utils.exceptions import PipelineAbortError

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# PII Scrubbing imports
try:
    from presidio_analyzer import AnalyzerEngine
    from presidio_anonymizer import AnonymizerEngine
    presidio_available = True
except ImportError:
    presidio_available = False
    logger.warning("Presidio Analyzer/Anonymizer not found. PII scrubbing will be bypassed.")

# Whitelist of terms to protect from PII scrubbing false-positives (EC-11)
PII_WHITELIST = ["Groww", "NIFTY", "SIP", "NAV", "UPI", "NSE", "BSE", "mutual fund", "stocks"]

# Emoji pattern for matching unicode ranges of emojis (EC-12 / User constraint)
EMOJI_PATTERN = re.compile(r'[\U00010000-\U0010FFFF\u2600-\u27BF]')

def calculate_sha256(text: str) -> str:
    """Calculates SHA-256 hash of text for de-duplication."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def clean_review_text(text: str) -> str:
    """Performs text normalization (whitespace, unicode fixing, lowercasing)."""
    if not isinstance(text, str):
        return ""
    # Fix malformed unicode (EC-13)
    text = ftfy.fix_text(text)
    # Strip extra whitespace and convert to lowercase
    text = re.sub(r"\s+", " ", text).strip().lower()
    return text

# Indic characters regex pattern (covers all main Indian scripts like Devanagari, Tamil, etc.)
INDIC_PATTERN = re.compile(r'[\u0900-\u0dff]')

# Clean list of Hinglish words (soft triggers):
# Words that might be Hinglish but can occasionally appear in English or are short.
HINGLISH_WORDS_STRICT = {
    "ho", "na", "ya", "lo", "par", "he", "do", "me", "to", "hi", "mere", "band"
}

# Words that are 100% Hinglish/Hindi in Latin script and should trigger immediate discard.
# None of these are valid, common English words.
STRONG_HINGLISH_WORDS = {
    "hai", "hain", "rha", "raha", "rhi", "rahi", "rhe", "rahe", "karna", "krna", 
    "karne", "kro", "karo", "badiya", "badhiya", "sbse", "sabse", "kuchh", "kuch",
    "hoga", "hoge", "hogi", "hota", "hote", "hoti", "sath", "saath", "skte", "sakte", 
    "dete", "deta", "deti", "diya", "diyo", "bni", "bani", "wale", "wala", "wali", 
    "baad", "gaya", "gaye", "gyi", "gayi", "nhi", "nahi", "meraa", "meri", "apna", 
    "apne", "apni", "ekdm", "ekdum", "mst", "bhut", "bohot", "bahut", "jyada", 
    "zyada", "ismein", "karen", "luto", "looto", "kiya", "liya", "rakha", "ruko", 
    "samajh", "samaj", "paisa", "paise", "rupaya", "rupaye", "theak", "theek", 
    "thik", "thika", "faltu", "isse", "bhejna", "bheja", "dalna", "dala", "bakwas", 
    "bkwas", "ghatiya", "bekar", "chor", "chori", "yaar", "hume", "humara", "hamara", 
    "hamari", "logo", "hotaa", "hega", "hogaa", "karke", "krke", "chalega", "chalegaa", 
    "nikal", "nikala", "nikle", "dalne", "achha", "acha", "accha",
    "bhi", "ki", "ka", "ke", "ko", "se", "toh", "kam", "kaam", "tha", "thi", "ek", 
    "ab", "le", "liye", "bnd", "kya", "kyu", "kyun", "kab", "kaha", "kaise", "kon", "kaun"
}

def is_english(text: str) -> bool:
    """Checks if the review text is in English (with strict checks for Indic and Hinglish)."""
    # 1. Indic script check (Hindi, Tamil, etc.)
    if INDIC_PATTERN.search(text):
        return False
        
    # Strip emojis and punctuation for language detection
    clean_text = re.sub(r"[^\w\s]", "", text).strip()
    if not clean_text:
        return False
        
    words = set(clean_text.lower().split())
    
    # 2. Strong Hinglish check: if it contains even ONE strong Hinglish word, discard
    if len(words & STRONG_HINGLISH_WORDS) >= 1:
        return False
        
    # 3. Soft Hinglish check: if it contains >= 2 soft Hinglish words, discard
    soft_matches = words & HINGLISH_WORDS_STRICT
    # We want to filter out 'do', 'me', 'he', 'to' as they are extremely common in English.
    # So we don't count them unless accompanied by other soft matches.
    # To be safe, let's just count matches excluding the English words, or require >= 2 matches of actual Hinglish words.
    actual_soft_matches = soft_matches - {"do", "me", "he", "to", "par"}
    if len(actual_soft_matches) >= 2 or (len(actual_soft_matches) >= 1 and len(soft_matches & {"do", "me", "he", "to", "par"}) >= 1):
        return False
        
    try:
        if detect(clean_text) == "en":
            return True
    except Exception:
        pass

    # Fallback/Lenient check for short texts:
    # If it contains common English stopwords/words, mark as English
    common_english_words = {
        "app", "good", "great", "nice", "best", "very", "excellent", "money", 
        "funds", "mutual", "stock", "stocks", "investment", "investing", "invest", 
        "fee", "fees", "charge", "charges", "payment", "transaction", "kyc", "bank",
        "account", "user", "ui", "interface", "support", "customer", "service",
        "the", "and", "for", "with", "this", "that", "easy", "simple", "fast"
    }
    # If at least 2 words are in the common English set, and it is ASCII, keep it!
    is_ascii = all(ord(c) < 128 for c in clean_text)
    if is_ascii and (len(words & common_english_words) >= 2 or (len(words) <= 3 and len(words & common_english_words) >= 1)):
        return True
        
    return False

def preprocess_pii_whitelist(text: str, whitelist: list) -> tuple[str, dict[str, str]]:
    """
    Replaces whitelist terms with placeholders to prevent Presidio from redacting them (EC-11).
    Returns (preprocessed_text, placeholders_map).
    """
    placeholders = {}
    temp_text = text
    for i, term in enumerate(whitelist):
        # Case-insensitive whole word replacement
        pattern = re.compile(rf"\b{re.escape(term)}\b", re.IGNORECASE)
        matches = pattern.findall(temp_text)
        if matches:
            placeholder = f"__WL_{i}__"
            placeholders[placeholder] = matches[0]
            temp_text = pattern.sub(placeholder, temp_text)
    return temp_text, placeholders

def postprocess_pii_whitelist(text: str, placeholders: dict[str, str]) -> str:
    """Restores whitelisted terms from placeholders back to their original state."""
    temp_text = text
    for placeholder, original_term in placeholders.items():
        temp_text = temp_text.replace(placeholder, original_term)
    return temp_text

def scrub_pii(text: str, analyzer, anonymizer, whitelist: list) -> str:
    """Scrubs PII from review text using Presidio (EC-10 & EC-11)."""
    if not presidio_available or not text:
        return text

    # Pre-process: protect whitelisted words
    temp_text, placeholders = preprocess_pii_whitelist(text, whitelist)

    # Analyze
    results = analyzer.analyze(
        text=temp_text,
        entities=["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "LOCATION", "URL"],
        language="en"
    )

    # Anonymize
    anonymized_result = anonymizer.anonymize(
        text=temp_text,
        analyzer_results=results
    )
    scrubbed_text = anonymized_result.text

    # Post-process: restore whitelisted words
    final_text = postprocess_pii_whitelist(scrubbed_text, placeholders)
    return final_text

def clean_corpus(input_file: str, output_csv: str, output_json: str, min_english_threshold: int = 50):
    """Loads raw reviews, cleans and sanitizes them, and writes the clean corpus."""
    logger.info(f"Loading raw reviews from {input_file}...")
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Raw review file not found: {input_file}")
        
    df = pd.read_csv(input_file)
    initial_count = len(df)
    logger.info(f"Loaded {initial_count} raw reviews.")

    # 1. Deduplication (SHA-256)
    logger.info("Step 1: Performing de-duplication...")
    df["text_hash"] = df["review_text"].astype(str).apply(calculate_sha256)
    deduped_df = df.drop_duplicates(subset=["text_hash"])
    dedup_dropped = initial_count - len(deduped_df)
    logger.info(f"De-duplication complete. Dropped {dedup_dropped} duplicates. Remaining: {len(deduped_df)}")

    # EC-09: All reviews removed after de-duplication
    if len(deduped_df) == 0:
        raise PipelineAbortError(
            "ALL_DUPLICATES",
            "All reviews in the dataset were duplicates. Pipeline aborted."
        )

    # Initialize Presidio
    analyzer = AnalyzerEngine() if presidio_available else None
    anonymizer = AnonymizerEngine() if presidio_available else None

    cleaned_records = []
    language_dropped = 0
    emoji_dropped = 0
    short_dropped = 0
    pii_dropped = 0
    long_review_warnings = 0

    # Process each review
    for idx, row in deduped_df.iterrows():
        raw_text = str(row["review_text"])

        # Check EC-14: Extremely long reviews
        if len(raw_text) > 2000:
            logger.warning(f"Review index {idx} is extremely long ({len(raw_text)} chars). Will be truncated in embedding.")
            long_review_warnings += 1

        # Text normalization
        norm_text = clean_review_text(raw_text)

        # Skip empty text
        if not norm_text:
            continue

        # 1. Emoji check: remove any review containing emojis (User constraint)
        if EMOJI_PATTERN.search(raw_text):
            emoji_dropped += 1
            continue

        # 2. Length check: remove all reviews with less than 8 words (User constraint)
        if len(norm_text.split()) < 8:
            short_dropped += 1
            continue

        # 3. Language filtering (EC-06)
        if not is_english(norm_text):
            language_dropped += 1
            continue

        # PII scrubbing (EC-10, EC-11)
        scrubbed_text = scrub_pii(norm_text, analyzer, anonymizer, PII_WHITELIST)

        # EC-10 Check: PII scrubber removes entire review text
        if not scrubbed_text.strip():
            logger.info(f"Review index {idx} dropped: entirely redacted by PII scrubber.")
            pii_dropped += 1
            continue

        # Keep the record
        cleaned_records.append({
            "review_text": scrubbed_text,
            "rating": row["rating"],
            "thumbs_up_count": row["thumbs_up_count"],
            "app_version": row["app_version"],
            "source": row["source"]
        })

    # Convert to DataFrame
    cleaned_df = pd.DataFrame(cleaned_records)
    final_count = len(cleaned_df)
    
    logger.info("=== Cleaning Pipeline Summary ===")
    logger.info(f"Initial raw count:              {initial_count}")
    logger.info(f"Duplicates dropped:              {dedup_dropped}")
    logger.info(f"Emoji reviews dropped:           {emoji_dropped}")
    logger.info(f"Short (< 8 words) dropped:       {short_dropped}")
    logger.info(f"Non-English reviews dropped:     {language_dropped}")
    logger.info(f"PII entirely redacted dropped:   {pii_dropped}")
    logger.info(f"Long review truncation warnings: {long_review_warnings}")
    logger.info(f"Final clean count:               {final_count}")

    # EC-10 Warning: If > 30% of reviews are dropped due to PII scrubbing
    if pii_dropped > 0.3 * len(deduped_df):
        logger.warning(f"HIGH REDACTION RATE: {pii_dropped} ({pii_dropped/len(deduped_df):.1%}) reviews were completely redacted by the PII scrubber.")

    # EC-06 Check: Insufficient English reviews (< 50)
    if final_count < min_english_threshold:
        raise PipelineAbortError(
            "INSUFFICIENT_REVIEWS",
            f"Only {final_count} clean English reviews remain, which is below the threshold of {min_english_threshold}. "
            "Pipeline aborted."
        )

    # Save outputs
    cleaned_df.to_csv(output_csv, index=False)
    cleaned_df.to_json(output_json, orient="records", indent=2)
    logger.info(f"Clean corpus saved. CSV: {output_csv}, JSON: {output_json}")
    return cleaned_df

def main():
    load_dotenv()
    
    raw_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/raw"))
    cleaned_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/cleaned"))
    os.makedirs(cleaned_dir, exist_ok=True)
    
    input_file = os.path.join(raw_dir, "reviews.csv")
    output_csv = os.path.join(cleaned_dir, "reviews_clean.csv")
    output_json = os.path.join(cleaned_dir, "reviews_clean.json")
    
    min_english_threshold = int(os.getenv("MIN_REVIEWS_THRESHOLD", 50))
    
    try:
        clean_corpus(input_file, output_csv, output_json, min_english_threshold)
    except PipelineAbortError as e:
        logger.error(f"Pipeline Aborted: {e.message}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected execution error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
