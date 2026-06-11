"""Retriever utilities for the FluentTech RAG pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import List

from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

def retrieve(
    query: str, top_k: int = 5, filter_category: str = None, persist_dir: str = "./chroma_db"
) -> List[dict]:
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vectordb = Chroma(
        persist_directory=persist_dir,
        collection_name="fluenttech_kb",
        embedding_function=embeddings,
    )

    where_filter = None
    if filter_category:
        where_filter = {"file_category": {"$eq": filter_category}}

    results = vectordb.similarity_search_with_score(query, k=top_k, filter=where_filter)

    if not results or all(score < 0.5 for _, score in results):
        print(f"⚠ Warning: All retrieved documents have similarity score < 0.5 for query: '{query}'")
        return []

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

