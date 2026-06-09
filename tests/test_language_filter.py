import json
import re
import pandas as pd
from langdetect import detect

# Clean list of Hinglish words (soft triggers):
# Words that might be Hinglish but can occasionally appear in English or are short.
HINGLISH_WORDS_STRICT = {
    "ho", "ka", "ki", "ke", "ko", "se", "bhi", "bnd", "band", "kam", 
    "kaam", "tha", "thi", "toh", "na", "ya", "ek", "ab", "le", "lo",
    "par", "he", "do", "me", "to", "hi", "mere"
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
    "nikal", "nikala", "nikle", "dalne", "achha", "acha", "accha"
}

INDIC_PATTERN = re.compile(r'[\u0900-\u0dff]')

def is_english_improved(text: str) -> bool:
    # 1. Indic script check (Devanagari, Tamil, etc.)
    if INDIC_PATTERN.search(text):
        return False
        
    # Strip punctuation and numbers
    clean_text = re.sub(r"[^\w\s]", "", text).strip()
    if not clean_text:
        return False
        
    words = set(clean_text.lower().split())
    
    # 2. Strong Hinglish check: if it contains even ONE strong Hinglish word, discard
    if len(words & STRONG_HINGLISH_WORDS) >= 1:
        return False
        
    # 3. Soft Hinglish check: if it contains >= 2 soft Hinglish words, discard
    # Note: we exclude common English words from checking here unless they are matched as Hinglish
    soft_matches = words & HINGLISH_WORDS_STRICT
    # We want to filter out 'do', 'me', 'he', 'to' as they are extremely common in English.
    # So we don't count them unless accompanied by other soft matches.
    # To be safe, let's just count matches excluding the English words, or require >= 2 matches of actual Hinglish words.
    actual_soft_matches = soft_matches - {"do", "me", "he", "to", "par"}
    if len(actual_soft_matches) >= 2 or (len(actual_soft_matches) >= 1 and len(soft_matches & {"do", "me", "he", "to", "par"}) >= 1):
        return False
        
    # 4. Standard langdetect
    try:
        if detect(clean_text) == "en":
            return True
    except Exception:
        pass
        
    # Fallback for short texts
    common_english_words = {
        "app", "good", "great", "nice", "best", "very", "excellent", "money", 
        "funds", "mutual", "stock", "stocks", "investment", "investing", "invest", 
        "fee", "fees", "charge", "charges", "payment", "transaction", "kyc", "bank",
        "account", "user", "ui", "interface", "support", "customer", "service",
        "the", "and", "for", "with", "this", "that", "easy", "simple", "fast"
    }
    is_ascii = all(ord(c) < 128 for c in clean_text)
    if is_ascii and (len(words & common_english_words) >= 2 or (len(words) <= 3 and len(words & common_english_words) >= 1)):
        return True
        
    return False


def test_on_raw():
    df = pd.read_json("data/raw/reviews.json")
    print(f"Total raw reviews: {len(df)}")
    
    dropped_by_improved = []
    kept_by_improved = []
    
    for idx, row in df.iterrows():
        text = str(row["review_text"])
        # Simple cleanup as in cleaner.py
        norm_text = re.sub(r"\s+", " ", text).strip().lower()
        if not norm_text:
            continue
            
        # Ignore emojis and word count check for this experiment to isolate language detection
        # Just run the language detector
        if is_english_improved(norm_text):
            kept_by_improved.append(norm_text)
        else:
            dropped_by_improved.append(norm_text)
            
    print(f"Improved filter: Kept {len(kept_by_improved)}, Dropped {len(dropped_by_improved)}")
    
    # Let's see some dropped reviews
    print("\nSample dropped reviews:")
    for text in dropped_by_improved[:20]:
        print("-", text)
        
    # Let's see if there are any obvious Hinglish reviews left in the kept set
    print("\nSuspicious reviews still KEPT:")
    suspicious_kept = []
    for text in kept_by_improved:
        words = set(text.split())
        # Let's check if there are any remaining Hinglish words
        all_hinglish = HINGLISH_WORDS_STRICT | {"he", "do", "ne", "par"}
        match = words & all_hinglish
        if len(match) > 0:
            suspicious_kept.append((list(match), text))
            
    for m, text in suspicious_kept[:20]:
        print(f"Matched {m} in: {text}")

if __name__ == "__main__":
    test_on_raw()
