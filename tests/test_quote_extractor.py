import unittest
import numpy as np
import pandas as pd
import os
import sys

# Add src and workspace to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.processing.quote_extractor import (
    passes_pii_check,
    calculate_text_hash,
    extract_quotes
)

class TestQuoteExtractor(unittest.TestCase):
    
    def test_calculate_text_hash(self):
        text = "This is a test review of Groww app."
        h1 = calculate_text_hash(text)
        self.assertEqual(len(h1), 12)
        # Verify deterministic hash
        self.assertEqual(h1, calculate_text_hash(text))
        
    def test_passes_pii_check(self):
        # Clean text should pass
        self.assertTrue(passes_pii_check("I love this app for investing in mutual funds."))
        # Redacted PII tags should pass (since the text is already scrubbed)
        self.assertTrue(passes_pii_check("My name is <PERSON> and my email is <EMAIL_ADDRESS>."))
        # Text with raw PII (like a clear email or phone) should fail
        self.assertFalse(passes_pii_check("my email is john.doe@gmail.com and phone is 9988776655"))
        
    def test_extract_quotes(self):
        # Setup synthetic inputs
        np.random.seed(42)
        mock_embeddings = np.random.randn(6, 1024).astype(np.float32)
        # Normalize
        norms = np.linalg.norm(mock_embeddings, axis=1, keepdims=True)
        mock_embeddings = mock_embeddings / norms
        
        df = pd.DataFrame({
            "review_text": [
                "this app is very useful for stock trading and easy to handle",
                "charges are very high on options brokerage please reduce it",
                "kyc approval is taking too much time on my account help me",
                "unable to withdraw cash from wallet showing technical error",
                "chart loading speed is slow and options charts are lagging",
                "excellent and simple interface for mutual funds investing"
            ]
        })
        
        # 3 mock themes
        themes_metadata = [
            {"label": "App Features", "review_indices": [0, 5]},
            {"label": "Brokerage Charges", "review_indices": [1]},
            {"label": "Technical Errors", "review_indices": [2, 3, 4]}
        ]
        
        quotes = extract_quotes(df, themes_metadata, mock_embeddings)
        
        # Verify output list
        self.assertEqual(len(quotes), 3)
        
        # Verify fields and conditions
        for q in quotes:
            self.assertIn("theme", q)
            self.assertIn("quote", q)
            self.assertIn("source_review_id", q)
            
            theme = q["theme"]
            quote = q["quote"]
            source_id = q["source_review_id"]
            
            # Verify length constraints (20 - 200)
            self.assertTrue(20 <= len(quote) <= 200)
            
            # Verify verbatim match in the source reviews
            verbatim_found = any(quote in r_text for r_text in df["review_text"])
            self.assertTrue(verbatim_found)
            
            # Verify source review id exists in df text hashes
            source_hashes = [calculate_text_hash(t) for t in df["review_text"]]
            self.assertIn(source_id, source_hashes)

if __name__ == "__main__":
    unittest.main()
