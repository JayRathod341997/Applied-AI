"""
Vector Databases - Hands-on Exercise

This exercise demonstrates working with vector databases using ChromaDB
and real sentence-transformer embeddings.

Estimated Time: 45 minutes
"""

from typing import List, Dict, Any, Tuple, Optional
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel
import chromadb


# ============================================================================
# PART 1: HuggingFace Embedding (free, local, no API key needed)
# ============================================================================


class HuggingFaceEmbedding:
    """Free local embeddings using HuggingFace transformers (mean pooling)."""

    def __init__(self, model_name: str = "google-bert/bert-base-uncased"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        self.model.eval()
        self.dimension = self.model.config.hidden_size

    def _mean_pool(self, model_output, attention_mask) -> torch.Tensor:
        token_embeddings = model_output.last_hidden_state
        mask = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        return torch.sum(token_embeddings * mask, 1) / torch.clamp(mask.sum(1), min=1e-9)

    def embed(self, text: str) -> List[float]:
        """Generate normalized embedding for a single text."""
        return self.embed_batch([text])[0]

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate normalized embeddings for multiple texts."""
        encoded = self.tokenizer(texts, padding=True, truncation=True, return_tensors="pt")
        with torch.no_grad():
            output = self.model(**encoded)
        pooled = self._mean_pool(output, encoded["attention_mask"])
        normalized = F.normalize(pooled, p=2, dim=1)
        return normalized.tolist()


# ============================================================================
# PART 2: ChromaDB Vector Store
# ============================================================================


class ChromaVectorStore:
    """
    In-memory vector store backed by ChromaDB.
    Mirrors the interface of a production vector database.
    """

    def __init__(self, collection_name: str = "exercise"):
        self.client = chromadb.EphemeralClient()
        self.collection = self.client.create_collection(
            collection_name, metadata={"hnsw:space": "cosine"}
        )

    def add(self, id: str, vector: List[float], metadata: Dict[str, Any] = None):
        """Add a vector to the store."""
        self.collection.add(
            ids=[id],
            embeddings=[vector],
            metadatas=[metadata or {}],
        )

    def search(
        self,
        query_vector: List[float],
        k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[str, float, Dict]]:
        """
        Search for k most similar vectors.

        Returns:
            List of (id, similarity_score, metadata) tuples
        """
        n = min(k, self.collection.count())
        if n == 0:
            return []

        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=n,
            where=filter_metadata,
        )
        # cosine space: distance = 1 - cosine_sim → similarity = 1 - distance
        return [
            (id_, 1 - dist, meta)
            for id_, dist, meta in zip(
                results["ids"][0],
                results["distances"][0],
                results["metadatas"][0],
            )
        ]

    def delete(self, id: str):
        """Delete a vector by ID."""
        self.collection.delete(ids=[id])

    def count(self) -> int:
        """Return the number of vectors in the store."""
        return self.collection.count()


# ============================================================================
# PART 3: Real Database Integration Examples
# ============================================================================


def example_pinecone_usage():
    """
    Example of using Pinecone vector database.
    Note: Requires 'pip install pinecone-client'
    """
    # This is pseudocode
    """
    from pinecone import Pinecone

    pc = Pinecone(api_key="your-api-key")
    index = pc.Index("my-index")

    index.upsert(
        vectors=[
            {"id": "vec1", "values": [0.1, 0.2, ...], "metadata": {"text": "doc1"}},
        ]
    )

    results = index.query(vector=[0.1, 0.2, ...], top_k=5, include_metadata=True)
    return results
    """
    pass


# ============================================================================
# PART 4: Demo
# ============================================================================


def main():
    """Demonstrate the ChromaDB vector store with real embeddings."""

    print("=" * 60)
    print("Vector Databases - Hands-on Exercise")
    print("=" * 60)

    documents = [
        {
            "id": "doc1",
            "text": "Python is a high-level programming language",
            "metadata": {"source": "tutorial", "topic": "programming"},
        },
        {
            "id": "doc2",
            "text": "Machine learning is a subset of artificial intelligence",
            "metadata": {"source": "tutorial", "topic": "AI"},
        },
        {
            "id": "doc3",
            "text": "Deep learning uses neural networks with multiple layers",
            "metadata": {"source": "article", "topic": "AI"},
        },
        {
            "id": "doc4",
            "text": "JavaScript is used for web development",
            "metadata": {"source": "tutorial", "topic": "programming"},
        },
        {
            "id": "doc5",
            "text": "Natural language processing deals with text data",
            "metadata": {"source": "article", "topic": "NLP"},
        },
    ]

    embed_fn = HuggingFaceEmbedding()
    vector_store = ChromaVectorStore()

    print("\n[Step 1] Adding documents to ChromaDB...")
    for doc in documents:
        vector = embed_fn.embed(doc["text"])
        vector_store.add(doc["id"], vector, doc["metadata"])

    print(f"Added {vector_store.count()} documents")

    print("\n[Step 2] Testing similarity search...")
    queries = [
        "What is Python programming?",
        "Tell me about artificial intelligence",
    ]

    for query in queries:
        print(f"\nQuery: {query}")
        print("-" * 40)
        query_vector = embed_fn.embed(query)
        results = vector_store.search(query_vector, k=3)
        for id_, score, metadata in results:
            print(f"  {id_} (score: {score:.3f}) - {metadata}")

    print("\n[Step 3] Testing metadata filtering...")
    query_vector = embed_fn.embed("Tell me about programming")
    results = vector_store.search(
        query_vector, k=3, filter_metadata={"topic": "programming"}
    )

    print("Filtered by topic=programming:")
    for id_, score, metadata in results:
        print(f"  {id_} (score: {score:.3f})")

    print("\n[Step 4] Exercise complete!")
    print("Try modifying the documents or adding more queries")


if __name__ == "__main__":
    main()


# ============================================================================
# EXERCISE TASKS
# ============================================================================

"""
EXERCISE TASKS:
1. Try a different sentence-transformer model (e.g., 'all-mpnet-base-v2')
2. Add support for batch adding of vectors using embed_batch()
3. Add persistence: swap EphemeralClient for chromadb.PersistentClient(path="./chroma_db")
4. Implement a simple reranking step after retrieval
5. Add support for updating existing vectors

BONUS: Integrate with Pinecone using the pseudocode above
"""
