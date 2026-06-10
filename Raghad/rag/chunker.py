from __future__ import annotations

from typing import List

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

def chunk_documents(docs: List[Document]) -> List[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n## ", "\n### ", "\n", " "],
    )
    all_chunks: List[Document] = []

    for doc_index, doc in enumerate(docs):
        chunks = splitter.split_text(doc.page_content)
        for chunk_index, chunk_text in enumerate(chunks):
            metadata = dict(doc.metadata)
            metadata["chunk_index"] = chunk_index
            metadata["parent_document_index"] = doc_index
            all_chunks.append(Document(page_content=chunk_text, metadata=metadata))

    chunk_sizes = [len(doc.page_content) for doc in all_chunks]
    total_chunks = len(all_chunks)
    avg_chunk = sum(chunk_sizes) / total_chunks if total_chunks else 0
    min_chunk = min(chunk_sizes) if chunk_sizes else 0
    max_chunk = max(chunk_sizes) if chunk_sizes else 0

    print(f"Total chunks: {total_chunks}")
    print(f"Average chunk size: {avg_chunk:.1f}")
    print(f"Min chunk size: {min_chunk}")
    print(f"Max chunk size: {max_chunk}")

    return all_chunks


if __name__ == "__main__":
    from rag.loader import load_documents

    docs = load_documents("knowledge_base")
    chunk_documents(docs)
