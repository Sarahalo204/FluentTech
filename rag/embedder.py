"""Embedding utilities for the FluentTech RAG pipeline.

Adapted to use HuggingFace BAAI/bge-small-en-v1.5 embeddings (free, no API key).
"""

from __future__ import annotations

from pathlib import Path
from typing import List

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma


# ─── Embedding Model ───────────────────────────────────────────────────────
# BAAI/bge-small-en-v1.5: best-in-class retrieval model for its size
# - Trained specifically for semantic search / retrieval tasks
# - Outperforms all-MiniLM-L6-v2 on MTEB retrieval benchmarks
# - 384-dim embeddings, ~33M params, runs fast on CPU
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"


def get_embeddings() -> HuggingFaceEmbeddings:
    """Create and return the HuggingFace embeddings instance."""
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
    )


def _estimate_token_count(docs: List[Document]) -> int:
    return sum(max(len(doc.page_content) // 4, 1) for doc in docs)


def _get_collection_count(vectordb: Chroma, fallback: int = 0) -> int:
    try:
        return vectordb._collection.count()
    except Exception:
        try:
            return len(vectordb._collection.get(include=["ids"])["ids"])
        except Exception:
            return fallback


def build_vector_store(chunks: List[Document], persist_dir: str = "./chroma_db") -> Chroma:
    persist_path = Path(persist_dir)
    embeddings = get_embeddings()

    if persist_path.exists() and any(persist_path.iterdir()):
        print(f"Found existing Chroma DB at {persist_dir}; loading existing store.")
        vectordb = Chroma(
            persist_directory=persist_dir,
            collection_name="fluenttech_kb",
            embedding_function=embeddings,
        )
    else:
        print(f"No existing Chroma DB found at {persist_dir}; creating a new vector store.")
        vectordb = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=persist_dir,
            collection_name="fluenttech_kb",
        )

    total_docs = _get_collection_count(vectordb, fallback=len(chunks))
    print(f"Total documents in collection: {total_docs}")
    sample_metadata = [doc.metadata for doc in chunks[:3]]
    print("Sample metadata for first 3 docs:")
    for index, metadata in enumerate(sample_metadata, start=1):
        print(f"  {index}. {metadata}")
    print(f"Estimated token count: {_estimate_token_count(chunks)}")

    return vectordb


if __name__ == "__main__":
    from rag.chunker import chunk_documents
    from rag.loader import load_documents

    project_root = Path(__file__).resolve().parents[1]
    knowledge_base_dir = project_root / "knowledge_base"
    persist_dir = project_root / "chroma_db"

    docs = load_documents(str(knowledge_base_dir))
    chunks = chunk_documents(docs)
    store = build_vector_store(chunks, persist_dir=str(persist_dir))
    print(f"RAG vector store ready. Collection document count: {_get_collection_count(store, fallback=len(chunks))}")
