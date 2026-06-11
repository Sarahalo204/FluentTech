"""Embedding utilities for the FluentTech RAG pipeline."""

from __future__ import annotations

import os
from pathlib import Path
from typing import List

from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from langchain_chroma import Chroma

def _check_openai_key() -> None:
    if not os.environ.get("OPENAI_API_KEY"):
        raise EnvironmentError(
            "Missing OPENAI_API_KEY. Please add your key to a .env file or export it in your shell before running this script."
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
    _check_openai_key()

    persist_path = Path(persist_dir)
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

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
