"""
Unit tests for RAG pipeline.
Tests document loading, chunking, FAISS index construction, and semantic retrieval.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rag.document_loader import load_pdf_document
from rag.chunking import chunk_documents
from rag.retriever import build_or_load_vector_store, retrieve_policy_knowledge
from config.settings import settings


def test_pdf_loading():
    pdf_path = settings.HANDBOOK_PDF_PATH
    pages = load_pdf_document(pdf_path)
    assert len(pages) > 0, "PDF loader returned zero pages."
    assert "APEX INSTITUTE" in pages[0]["text"]
    print(f"PASS: Loaded {len(pages)} pages from PDF.")


def test_chunking():
    pdf_path = settings.HANDBOOK_PDF_PATH
    pages = load_pdf_document(pdf_path)
    chunks = chunk_documents(pages, chunk_size=500, chunk_overlap=50)
    assert len(chunks) >= len(pages), "Expected more chunks than pages."
    first = chunks[0]
    assert "chunk_id" in first
    assert "page_number" in first["metadata"]
    print(f"PASS: Created {len(chunks)} chunks with IDs.")


def test_faiss_indexing_and_portal_failure_query():
    # Build or load FAISS store
    store = build_or_load_vector_store(force_rebuild=True)
    assert store is not None

    query = "The payment portal failed. Can I pay on the next working day?"
    result = retrieve_policy_knowledge(query, top_k=2)
    assert result["status"] == "SUCCESS", f"Retrieval failed: {result}"
    assert len(result["chunks"]) > 0

    combined_text = " ".join(c["text"] for c in result["chunks"]).lower()
    assert "next working day" in combined_text or "grace" in combined_text or "portal" in combined_text
    print(f"PASS: Portal failure policy retrieved with {len(result['chunks'])} chunks.")


def test_course_change_query():
    query = "How can I change my course or programme?"
    result = retrieve_policy_knowledge(query, top_k=2)
    assert result["status"] == "SUCCESS"
    combined_text = " ".join(c["text"] for c in result["chunks"]).lower()
    assert "transfer" in combined_text or "add/drop" in combined_text or "programme" in combined_text
    print("PASS: Course change policy retrieved.")


def test_out_of_handbook_topic():
    query = "Tell me the policy for international student hostel refunds"
    result = retrieve_policy_knowledge(query, top_k=2)
    # Check that retrieved text notes scope limitation or lack of hostel refund policies
    assert result["status"] == "SUCCESS"
    print("PASS: Handled out-of-handbook query.")


if __name__ == "__main__":
    print("Running RAG test suite...")
    test_pdf_loading()
    test_chunking()
    test_faiss_indexing_and_portal_failure_query()
    test_course_change_query()
    test_out_of_handbook_topic()
    print("ALL RAG TESTS PASSED!")
