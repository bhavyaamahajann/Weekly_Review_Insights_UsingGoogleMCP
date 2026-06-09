import json
import time
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

def main():
    print("Loading cleaned reviews...")
    with open("data/cleaned/reviews_clean.json", "r") as f:
        reviews = json.load(f)
    
    texts = [r["review_text"] for r in reviews]
    print(f"Total reviews: {len(texts)}")
    
    if not texts:
        print("No reviews found. Exiting.")
        return
        
    print("Loading SentenceTransformer model BAAI/bge-large-en-v1.5...")
    start_time = time.time()
    # Loading local model or downloading
    model = SentenceTransformer("BAAI/bge-large-en-v1.5")
    print(f"Model loaded in {time.time() - start_time:.2f} seconds.")
    
    print("Generating embeddings...")
    start_time = time.time()
    embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=True)
    print(f"Embeddings generated in {time.time() - start_time:.2f} seconds. Shape: {embeddings.shape}")
    
    # Evaluate k-means for k in [2, 3, 4, 5, 6]
    print("\nEvaluating K-Means Clustering:")
    best_k = 2
    best_score = -1
    best_labels = None
    
    for k in range(2, 7):
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(embeddings)
        score = silhouette_score(embeddings, labels)
        print(f"k = {k} | Silhouette Score: {score:.4f}")
        if score > best_score:
            best_score = score
            best_k = k
            best_labels = labels
            
    print(f"\nBest number of clusters: {best_k} (Silhouette Score: {best_score:.4f})")
    
    # Analyze the best clusters
    df = pd.DataFrame({
        "text": texts,
        "cluster": best_labels,
        "rating": [r["rating"] for r in reviews]
    })
    
    for cluster_id in range(best_k):
        cluster_df = df[df["cluster"] == cluster_id]
        print(f"\n--- Cluster {cluster_id} (Size: {len(cluster_df)}) ---")
        print("Average Rating:", f"{cluster_df['rating'].mean():.2f}")
        print("Sample Reviews:")
        samples = cluster_df.sample(min(5, len(cluster_df)), random_state=42)["text"].tolist()
        for i, sample in enumerate(samples, 1):
            print(f"  {i}. {sample}")

if __name__ == "__main__":
    main()
