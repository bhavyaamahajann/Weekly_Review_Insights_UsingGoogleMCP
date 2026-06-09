import json
import re

# Load the Hinglish words list from cleaner.py (or a similar list)
HINGLISH_WORDS = {
    "hai", "he", "ho", "ka", "ki", "ke", "ko", "se", "bhi", "bnd", "band", "kam", 
    "kaam", "rha", "raha", "tha", "thi", "toh", "na", "ne", "krna", "karna", "kr", 
    "kar", "karne", "bda", "bada", "achha", "acha", "badiya", "badhiya", "sbse", 
    "sabse", "aur", "ya", "ek", "do", "par", "pe", "ab", "kuch", "hoga", "hoge", 
    "hota", "hote", "bhai", "sath", "saath", "le", "skte", "sakte", "dete", "deta", 
    "diya", "diyo", "liye", "bni", "bani", "wale", "wala", "wali", "bd", "baad", 
    "gaya", "gaye", "gyi", "gayi", "koi", "kuchh", "nhi", "nahi", "meraa", "mera", 
    "meri", "mere", "apna", "apne", "apni", "h", "par"
}

INDIC_PATTERN = re.compile(r'[\u0900-\u0dff]')

def inspect_cleaned():
    with open("data/cleaned/reviews_clean.json", "r") as f:
        reviews = json.load(f)
        
    print(f"Total reviews in reviews_clean.json: {len(reviews)}")
    
    suspicious = []
    for idx, r in enumerate(reviews):
        text = r["review_text"]
        words = set(re.sub(r"[^\w\s]", "", text).lower().split())
        
        # Check if it has any Indic character
        if INDIC_PATTERN.search(text):
            suspicious.append((idx, "Indic Script", text))
            continue
            
        # Check number of Hinglish words
        matching_words = words & HINGLISH_WORDS
        if len(matching_words) > 0:
            # Let's log ones with matching words to see if they are Hinglish
            suspicious.append((idx, f"Hinglish words ({list(matching_words)})", text))
            
    print(f"\nFound {len(suspicious)} reviews containing at least one Hinglish-like word.")
    print("Top 30 suspicious reviews:")
    for idx, reason, text in suspicious[:30]:
        print(f"[{idx}] Reason: {reason} | Text: {text}")

if __name__ == "__main__":
    inspect_cleaned()
