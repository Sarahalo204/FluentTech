from __future__ import annotations

from pathlib import Path

from rag.retriever import retrieve


TEST_QUERIES = [
    "What can a B2 level speaker do in a workplace?",
    "Common grammar mistakes Arabic speakers make with articles",
    "How to answer tell me about yourself in a tech interview",
    "Professional email template for requesting a deadline extension",
    "What does cloud computing vocabulary include?",
    "Grammar rule for using present perfect vs simple past",
]


def run_tests() -> None:
    project_root = Path(__file__).resolve().parents[1]
    persist_dir = project_root / "chroma_db"

    print("=" * 80)
    print("FluentTech RAG Retrieval Test Suite")
    print("=" * 80)

    all_passed = True
    for query_index, query in enumerate(TEST_QUERIES, start=1):
        print(f"\n[Query {query_index}/6]")
        print(f"Query: {query}")
        print("-" * 80)

        results = retrieve(query, top_k=3, persist_dir=str(persist_dir))

        if not results:
            print("❌ No results returned.")
            all_passed = False
            continue

        for result_index, result in enumerate(results, start=1):
            score = result["similarity_score"]
            content_preview = result["content"][:100].replace("\n", " ")
            print(f"  {result_index}. [{score:.4f}] {content_preview}...")
            print(f"     Source: {result['source_file']} | Category: {result['file_category']}")

        max_score = max(r["similarity_score"] for r in results)
        if max_score > 0.65:
            print(f"✅ PASS (max score: {max_score:.4f})")
        else:
            print(f"❌ FAIL (max score: {max_score:.4f} <= 0.65)")
            all_passed = False

    print("\n" + "=" * 80)
    if all_passed:
        print("🎉 All 6 queries returned results with score > 0.65")
    else:
        print("⚠ Some queries did not meet the 0.65 score threshold")
    print("=" * 80)


if __name__ == "__main__":
    run_tests()
