import unittest
import numpy as np
import pandas as pd
import os
import sys

# Add src and workspace to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.processing.clusterer import (
    clean_label,
    extract_keyphrases_offline,
    cluster_reviews
)

class TestClusterer(unittest.TestCase):
    
    def test_clean_label(self):
        self.assertEqual(clean_label('"App Performance"'), "App Performance")
        self.assertEqual(clean_label('**Withdrawal Issues**'), "Withdrawal Issues")
        self.assertEqual(clean_label('this is a very long theme title name'), "This Is A Very")
        
    def test_extract_keyphrases_offline(self):
        texts = [
            "chart loading speed is very slow",
            "the stock chart lags so much",
            "fix the options chart bugs"
        ]
        label = extract_keyphrases_offline(texts)
        # Check that it extracted words of interest (e.g. chart, speed, loading, lags, options, bugs)
        self.assertTrue(any(word in label.lower() for word in ["chart", "speed", "lag", "bug", "option"]))
        
    def test_cluster_reviews_logic(self):
        # Create synthetic data of size 10
        np.random.seed(42)
        mock_embeddings = np.random.randn(10, 1024).astype(np.float32)
        # Normalize mock embeddings
        norms = np.linalg.norm(mock_embeddings, axis=1, keepdims=True)
        mock_embeddings = mock_embeddings / norms
        
        df = pd.DataFrame({
            "review_text": [
                "This app is very useful for stock trading.",
                "High charges on stock brokerage compared to others.",
                "KYC process took three days to complete.",
                "Unable to withdraw my money from wallet.",
                "Chart loading speed and lagging issue in options.",
                "Excellent user interface and clear details.",
                "Mutual fund investment is simple and fast here.",
                "Customer support has not responded for two days.",
                "Limit order failed to execute in option chain.",
                "Cannot buy minor mutual fund stocks on app."
            ],
            "rating": [5, 2, 3, 1, 2, 5, 5, 1, 2, 3],
            "thumbs_up_count": [1, 5, 2, 10, 3, 0, 1, 8, 4, 2],
            "app_version": ["1.0", "1.0", "1.1", "1.0", "1.1", "1.0", "1.0", "1.1", "1.0", "1.1"],
            "source": ["google_play"] * 10
        })
        
        # We run in offline/fallback mode (GROQ_API_KEY is not read or set to None internally if not present)
        result = cluster_reviews(mock_embeddings, df, max_clusters=4)
        
        # Verify result contains the keys
        self.assertIn("optimal_k", result)
        self.assertIn("silhouette_score", result)
        self.assertIn("themes", result)
        
        # Verify themes count is equal to optimal_k or top 5
        themes = result["themes"]
        self.assertEqual(len(themes), min(5, result["optimal_k"]))
        
        # Verify each theme schema
        for t in themes:
            self.assertIn("id", t)
            self.assertIn("label", t)
            self.assertIn("size", t)
            self.assertIn("review_indices", t)
            self.assertTrue(t["size"] > 0)
            self.assertEqual(len(t["review_indices"]), t["size"])

if __name__ == "__main__":
    unittest.main()
