import unittest
import os
import sys

# Add src and workspace to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.processing.cleaner import (
    calculate_sha256,
    clean_review_text,
    is_english,
    preprocess_pii_whitelist,
    postprocess_pii_whitelist,
    scrub_pii,
    EMOJI_PATTERN,
    PII_WHITELIST
)

try:
    from presidio_analyzer import AnalyzerEngine
    from presidio_anonymizer import AnonymizerEngine
    presidio_installed = True
except ImportError:
    presidio_installed = False

class TestCleaner(unittest.TestCase):
    
    def test_calculate_sha256(self):
        text = "This is a test review of Groww."
        expected_hash = "7e8d301315fef208d5fe2eab72a738e08378a53b5e4066fb58b7fe77c3da0546"
        self.assertEqual(calculate_sha256(text), expected_hash)
        
    def test_clean_review_text(self):
        # Unicode fixing, whitespace trimming, casing
        raw_text = "   This is  â€™  a review   "
        expected = "this is ' a review"
        self.assertEqual(clean_review_text(raw_text), expected)
        
    def test_is_english(self):
        self.assertTrue(is_english("Excellent app for mutual funds."))
        self.assertTrue(is_english("very good app for investing"))
        # Non-English / Indic scripts
        self.assertFalse(is_english("यह ऐप बहुत अच्छा है"))  # Hindi
        self.assertFalse(is_english("નમસ્તે આ એક સારું એપ છે"))  # Gujarati
        # Hinglish / Mixed languages
        self.assertFalse(is_english("jb koi bda movement ane profit le skte he tb inke indicator kam krna bnd kr dete he"))
        self.assertFalse(is_english("ग्राहक लूटो ट्रेडिंग प्लेटफॉर्म pls avoid this platform if you want to save your money"))
        
    def test_emoji_pattern(self):
        # EMOJI_PATTERN should detect emojis
        self.assertTrue(bool(EMOJI_PATTERN.search("Groww app is great 🚀🔥")))
        self.assertTrue(bool(EMOJI_PATTERN.search("🔥🔥🔥")))
        # EMOJI_PATTERN should NOT match normal text
        self.assertFalse(bool(EMOJI_PATTERN.search("Groww app is great")))
        
    def test_word_count_filter(self):
        # Reviews with less than 8 words should be identified
        text_long = "this is a review with eight words in it"
        text_short = "too short review"
        self.assertTrue(len(text_long.split()) >= 8)
        self.assertFalse(len(text_short.split()) >= 8)
        
    def test_preprocess_pii_whitelist(self):
        text = "i am investing in groww app and looking at nifty index"
        whitelist = ["groww", "nifty"]
        processed_text, placeholders = preprocess_pii_whitelist(text, whitelist)
        
        self.assertIn("__WL_0__", processed_text)
        self.assertIn("__WL_1__", processed_text)
        self.assertEqual(placeholders["__WL_0__"], "groww")
        self.assertEqual(placeholders["__WL_1__"], "nifty")
        
        restored_text = postprocess_pii_whitelist(processed_text, placeholders)
        self.assertEqual(restored_text, text)
        
    @unittest.skipUnless(presidio_installed, "Presidio Analyzer/Anonymizer not installed")
    def test_scrub_pii(self):
        analyzer = AnalyzerEngine()
        anonymizer = AnonymizerEngine()
        
        # Test Person redaction
        text = "my name is john doe and i like this app"
        scrubbed = scrub_pii(text, analyzer, anonymizer, PII_WHITELIST)
        self.assertNotIn("john doe", scrubbed)
        self.assertIn("<PERSON>", scrubbed)
        
        # Test Email redaction
        text = "contact me at help@groww.in for details"
        scrubbed = scrub_pii(text, analyzer, anonymizer, PII_WHITELIST)
        self.assertNotIn("help@groww.in", scrubbed)
        self.assertIn("<EMAIL_ADDRESS>", scrubbed)
        
        # Test Whitelist preservation
        text = "groww is the best platform for mutual funds"
        scrubbed = scrub_pii(text, analyzer, anonymizer, PII_WHITELIST)
        self.assertIn("groww", scrubbed)
        
if __name__ == "__main__":
    unittest.main()
