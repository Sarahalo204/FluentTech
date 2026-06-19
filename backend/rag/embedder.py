"""Embedding utilities for the FluentTech RAG pipeline using Supabase pgvector.

Adapted to use HuggingFace BAAI/bge-small-en-v1.5 embeddings (free, no API key).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain_community.vectorstores import SupabaseVectorStore
from supabase.client import Client, create_client
from dotenv import load_dotenv

load_dotenv()

# ─── Embedding Model ───────────────────────────────────────────────────────
# BAAI/bge-small-en-v1.5: 384-dim embeddings, ~33M params, runs fast on CPU
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"


def get_embeddings() -> HuggingFaceEmbeddings:
    """Create and return the HuggingFace embeddings instance."""
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
    )


def get_supabase_client() -> Client:
    """Initialize and return the Supabase client."""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables.")
        
    return create_client(supabase_url, supabase_key)


def build_vector_store(chunks: List[Document]) -> SupabaseVectorStore:
    """
    Builds the vector store by pushing document chunks to Supabase pgvector.
    
    Note: SupabaseVectorStore.from_documents appends documents.
    If you want a fresh ingestion, you should clear the 'documents' table first.
    """
    embeddings = get_embeddings()
    supabase = get_supabase_client()
    
    print(f"Connecting to Supabase at {os.getenv('SUPABASE_URL')} to store {len(chunks)} chunks...")
    
    # Optional: Clear existing documents to avoid duplicates on re-ingestion.
    # Note: This deletes all records in the documents table.
    try:
        print("Clearing existing documents from Supabase to prevent duplicates...")
        supabase.table("documents").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
    except Exception as e:
        print(f"Warning: Could not clear existing documents. They might duplicate. Error: {e}")

    # Push to Supabase pgvector
    vector_store = SupabaseVectorStore.from_documents(
        chunks,
        embeddings,
        client=supabase,
        table_name="documents",
        query_name="match_documents",
        chunk_size=500  # Batch size
    )
    
    print(f"Successfully uploaded {len(chunks)} chunks to Supabase 'documents' table.")
    return vector_store


if __name__ == "__main__":
    from rag.chunker import chunk_documents
    from rag.loader import load_documents

    project_root = Path(__file__).resolve().parents[1]
    knowledge_base_dir = project_root / "knowledge_base"

    docs = load_documents(str(knowledge_base_dir))
    chunks = chunk_documents(docs)
    store = build_vector_store(chunks)
    print("RAG vector store ingestion complete!")
