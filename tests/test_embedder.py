import unittest
import numpy as np
import os
import sys

# Add src and workspace to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.processing.embedder import embed_reviews

class TestEmbedder(unittest.TestCase):
    
    def test_embed_reviews_valid(self):
        texts = ["This is a test review for Groww app.", "Another sample text to embed."]
        embeddings = embed_reviews(texts)
        
        # Verify shape and dtype
        self.assertEqual(embeddings.shape, (2, 1024))
        self.assertEqual(embeddings.dtype, np.float32)
        
        # Verify normalization (L2 norm should be close to 1)
        for emb in embeddings:
            norm = np.linalg.norm(emb)
            self.assertAlmostEqual(norm, 1.0, places=5)
            
    def test_embed_reviews_empty(self):
        embeddings = embed_reviews([])
        self.assertEqual(embeddings.shape, (0, 1024))

if __name__ == "__main__":
    unittest.main()
