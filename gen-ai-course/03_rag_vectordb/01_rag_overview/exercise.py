"""
RAG Overview - Hands-on Exercise

This exercise demonstrates the basic RAG workflow using ChromaDB
and real sentence-transformer embeddings.

Estimated Time: 30 minutes
"""

from typing import List, Tuple
from sentence_transformers import SentenceTransformer
import chromadb

# ============================================================================
# PART 1: Setup and Imports
# ============================================================================

# Sample documents for our knowledge base
SAMPLE_DOCUMENTS = [
    {
        "id": "doc1",
        "content": """
        Python is a high-level, interpreted programming language known for its
        readability and versatility. It supports multiple programming paradigms
        including procedural, object-oriented, and functional programming.
        Python is widely used in web development, data science, machine learning,
        and automation. The language emphasizes code readability with its use
        of significant whitespace.
        """,
    },
    {
        "id": "doc2",
        "content": """
        Large Language Models (LLMs) are artificial intelligence systems trained
        on vast amounts of text data. They can understand and generate human-like
        text. Examples include GPT-4, Claude, and Gemini. LLMs use transformer
        architectures and are capable of tasks like translation, summarization,
        question answering, and creative writing. They have revolutionized
        natural language processing applications.
        """,
    },
    {
        "id": "doc3",
        "content": """
        Retrieval-Augmented Generation (RAG) is a technique that combines
        information retrieval with text generation. RAG systems first retrieve
        relevant documents from a knowledge base, then use them to augment
        the prompt sent to an LLM. This helps reduce hallucinations and provides
        source attribution. RAG is essential for building accurate AI systems
        that can access up-to-date or domain-specific information.
        """,
    },
    {
        "id": "doc4",
        "content": """
        Vector databases are specialized database systems designed to store
        and query high-dimensional vector embeddings. They enable semantic
        similarity search, where documents can be found based on meaning
        rather than exact keyword matching. Popular vector databases include
        Pinecone, Weaviate, Chroma, and Milvus. They are fundamental to RAG
        systems for efficient document retrieval.
        """,
    },
    {
        "id": "doc5",
        "content": """
        Prompt engineering is the practice of designing and optimizing prompts
        for large language models. Effective prompts clearly specify the desired
        output format, provide relevant context, and use techniques like
        few-shot learning. Key concepts include role prompting, chain-of-thought
        reasoning, and temperature settings. Good prompt engineering can
        significantly improve LLM output quality without changing the model.
        """,
    },
]


# ============================================================================
# PART 2: Embedding with sentence-transformers
# ============================================================================


class SimpleEmbedding:
    """
    Free local embeddings using sentence-transformers.
    Model: all-MiniLM-L6-v2 (384-dim, fast, no API key needed)
    """

    def __init__(self):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.dimension = self.model.get_sentence_embedding_dimension()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents."""
        return self.model.encode(texts, normalize_embeddings=True).tolist()

    def embed_query(self, text: str) -> List[float]:
        """Embed a query."""
        return self.model.encode(text, normalize_embeddings=True).tolist()


# ============================================================================
# PART 3: ChromaDB Vector Store
# ============================================================================


class SimpleVectorStore:
    """
    ChromaDB-backed in-memory vector store.
    In production, swap EphemeralClient for PersistentClient.
    """

    def __init__(self):
        self.embeddings = SimpleEmbedding()
        self._client = chromadb.EphemeralClient()
        self._collection = self._client.create_collection(
            "rag_overview", metadata={"hnsw:space": "cosine"}
        )
        self._docs: List[dict] = []

    def add_documents(self, docs: List[dict]):
        """Add documents to the vector store."""
        texts = [doc["content"] for doc in docs]
        vectors = self.embeddings.embed_documents(texts)
        self._collection.add(
            ids=[doc["id"] for doc in docs],
            embeddings=vectors,
            metadatas=[{"idx": i} for i in range(len(docs))],
        )
        self._docs.extend(docs)
        print(f"Added {len(docs)} documents to the vector store")

    def similarity_search(self, query: str, k: int = 3) -> List[Tuple[dict, float]]:
        """Find k most similar documents to the query."""
        query_vector = self.embeddings.embed_query(query)
        n = min(k, self._collection.count())
        if n == 0:
            return []

        results = self._collection.query(query_embeddings=[query_vector], n_results=n)
        id_to_doc = {doc["id"]: doc for doc in self._docs}
        return [
            (id_to_doc[id_], 1 - dist)
            for id_, dist in zip(results["ids"][0], results["distances"][0])
        ]


# ============================================================================
# PART 4: Simple RAG Pipeline
# ============================================================================


class SimpleRAG:
    """
    A simple RAG pipeline demonstration.
    In production, use LangChain's RAG implementations.
    """

    def __init__(self, documents: List[dict]):
        self.vector_store = SimpleVectorStore()
        self.vector_store.add_documents(documents)

    def retrieve(self, query: str, k: int = 3) -> List[dict]:
        """Retrieve relevant documents for a query."""
        results = self.vector_store.similarity_search(query, k)
        return [doc for doc, score in results]

    def generate_context(self, query: str, retrieved_docs: List[dict]) -> str:
        """Generate augmented context from retrieved documents."""
        context_parts = [
            f"Document {i} (ID: {doc['id']}):\n{doc['content'].strip()}"
            for i, doc in enumerate(retrieved_docs, 1)
        ]
        return "\n\n".join(context_parts)

    def answer(self, query: str) -> dict:
        """Answer a query using RAG."""
        retrieved_docs = self.retrieve(query, k=2)
        context = self.generate_context(query, retrieved_docs)

        response = f"""
Based on the retrieved context, here is my answer to: "{query}"

[In a real RAG system, this would be generated by an LLM using the context below]

Retrieved Context:
{context}

Source Documents: {[doc['id'] for doc in retrieved_docs]}
"""
        return {"query": query, "response": response, "retrieved_docs": retrieved_docs}


# ============================================================================
# PART 5: Run the Exercise
# ============================================================================


def main():
    """Main function to demonstrate RAG workflow."""

    print("=" * 60)
    print("RAG Overview - Hands-on Exercise")
    print("=" * 60)

    print("\n[Step 1] Initializing RAG system with sample documents...")
    rag = SimpleRAG(SAMPLE_DOCUMENTS)

    test_queries = [
        "What is Python programming language?",
        "How do LLMs work?",
        "What is vector database?",
    ]

    print("\n[Step 2] Testing RAG with sample queries...\n")

    for query in test_queries:
        print("-" * 60)
        print(f"Query: {query}")
        print("-" * 60)
        result = rag.answer(query)
        print(result["response"])
        print()

    print("\n[Step 3] Exercise Complete!")
    print("\nTry modifying the test_queries or adding your own documents")
    print("to explore the RAG workflow further.")


if __name__ == "__main__":
    main()


# ============================================================================
# EXERCISE TASKS
# ============================================================================

"""
EXERCISE TASKS:
1. Add more documents to the SAMPLE_DOCUMENTS list related to AI/ML
2. Try a different model: SentenceTransformer('all-mpnet-base-v2') for higher accuracy
3. Add document metadata (source, date, author) and include in retrieval
4. Implement a simple reranking of retrieved documents
5. Swap EphemeralClient for PersistentClient to persist the index across runs

BONUS: Add an actual LLM call (e.g., via Ollama or Anthropic API) to generate answers
"""
