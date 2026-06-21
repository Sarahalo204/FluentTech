"""Retriever utilities for the FluentTech RAG pipeline using Supabase pgvector.

Adapted to use HuggingFace BAAI/bge-small-en-v1.5 embeddings.
"""

from __future__ import annotations

import os
from typing import List

from langchain_community.vectorstores import SupabaseVectorStore
from supabase.client import Client, create_client
from dotenv import load_dotenv

from rag.embedder import get_embeddings

load_dotenv()


def get_supabase_client() -> Client:
    """Initialize and return the Supabase client."""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables.")
        
    return create_client(supabase_url, supabase_key)


def retrieve(
    query: str, top_k: int = 5, filter_category: str = None
) -> List[dict]:
    embeddings = get_embeddings()
    supabase = get_supabase_client()
    
    vector_store = SupabaseVectorStore(
        client=supabase,
        embedding=embeddings,
        table_name="documents",
        query_name="match_documents"
    )

    where_filter = None
    if filter_category:
        where_filter = {"file_category": filter_category}

    results = vector_store.similarity_search_with_relevance_scores(
        query, k=top_k, filter=where_filter
    )

    if not results or all(score < 0.5 for _, score in results):
        print(f"⚠ Warning: All retrieved documents have similarity score < 0.5 for query: '{query}'")
        # Still return results as Supabase matching can sometimes have different scale depending on distance metric, 
        # but the warning is good for debugging.

    output = []
    for doc, score in results:
        output.append(
            {
                "content": doc.page_content,
                "source_file": doc.metadata.get("source_file", "unknown"),
                "file_category": doc.metadata.get("file_category", "unknown"),
                "similarity_score": score,
                "chunk_index": doc.metadata.get("chunk_index", -1),
            }
        )

    return output
