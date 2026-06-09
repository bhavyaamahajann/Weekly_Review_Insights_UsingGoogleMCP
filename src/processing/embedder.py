import os
import sys
import logging
import json
import numpy as np
from sentence_transformers import SentenceTransformer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Lazy load model to avoid loading overhead when importing the module if not needed
_model = None

def get_model() -> SentenceTransformer:
    """Lazy loads and returns the sentence transformer model."""
    global _model
    if _model is None:
        model_name = "BAAI/bge-large-en-v1.5"
        logger.info(f"Loading SentenceTransformer model '{model_name}'...")
        _model = SentenceTransformer(model_name)
        logger.info("SentenceTransformer model loaded successfully.")
    return _model

def embed_reviews(texts: list[str]) -> np.ndarray:
    """
    Generates normalized dense embeddings (1024-dim) for a list of review texts.
    Returns: (N, 1024) float32 numpy array.
    """
    if not texts:
        return np.empty((0, 1024), dtype=np.float32)
        
    model = get_model()
    # BGE model recommends using normalize_embeddings=True for cosine similarity compatibility
    embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=True)
    return np.array(embeddings, dtype=np.float32)

def main():
    cleaned_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/cleaned"))
    input_file = os.path.join(cleaned_dir, "reviews_clean.json")
    output_file = os.path.join(cleaned_dir, "embeddings_clean.npy")
    
    if not os.path.exists(input_file):
        logger.error(f"Cleaned reviews file not found at: {input_file}")
        sys.exit(1)
        
    logger.info(f"Loading cleaned reviews from {input_file}...")
    with open(input_file, "r") as f:
        reviews = json.load(f)
        
    texts = [r["review_text"] for r in reviews]
    logger.info(f"Loaded {len(texts)} cleaned reviews. Generating embeddings...")
    
    try:
        embeddings = embed_reviews(texts)
        np.save(output_file, embeddings)
        logger.info(f"Embeddings saved successfully to {output_file}. Shape: {embeddings.shape}")
    except Exception as e:
        logger.error(f"Failed to generate/save embeddings: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
