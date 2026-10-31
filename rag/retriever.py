"""
Vector Database Indexing and Retrieval Module.
Builds and queries FAISS vector store with source metadata and similarity scoring.
"""

import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from config.settings import settings
from rag.document_loader import load_pdf_document
from rag.chunking import chunk_documents
from rag.embeddings import get_embedding_function

logger = logging.getLogger("rag.retriever")

_cached_vector_store: Optional[FAISS] = None


def build_or_load_vector_store(force_rebuild: bool = False) -> FAISS:
    """
    Load persisted FAISS index from disk or build from PDF handbook if missing/requested.
    """
    global _cached_vector_store
    if _cached_vector_store is not None and not force_rebuild:
        return _cached_vector_store

    index_dir = settings.VECTOR_STORE_DIR / "faiss_index"
    embeddings = get_embedding_function()

    if index_dir.exists() and not force_rebuild:
        try:
            logger.info(f"Loading existing FAISS vector store from {index_dir}")
            _cached_vector_store = FAISS.load_local(
                str(index_dir),
                embeddings,
                allow_dangerous_deserialization=True,
            )
            return _cached_vector_store
        except Exception as e:
            logger.warning(f"Failed to load existing FAISS index ({e}), rebuilding index.")

    logger.info("Building new FAISS vector store from student handbook PDF...")
    pdf_path = settings.HANDBOOK_PDF_PATH
    if not pdf_path.exists():
        from data.create_handbook_pdf import generate_handbook_pdf
        generate_handbook_pdf()

    pages = load_pdf_document(pdf_path)
    chunks = chunk_documents(pages)

    docs = [
        Document(
            page_content=chunk["text"],
            metadata=chunk["metadata"],
        )
        for chunk in chunks
    ]

    vector_store = FAISS.from_documents(docs, embeddings)
    index_dir.parent.mkdir(parents=True, exist_ok=True)
    vector_store.save_local(str(index_dir))
    logger.info(f"FAISS index built with {len(docs)} documents and saved to {index_dir}.")

    _cached_vector_store = vector_store
    return _cached_vector_store


def retrieve_policy_knowledge(query: str, top_k: int = None, score_threshold: float = 1.4) -> Dict[str, Any]:
    """
    Retrieve relevant policy chunks using FAISS similarity search.
    Returns structured results with chunk IDs, page numbers, text snippets, and scores.
    In FAISS L2 distance, lower score indicates higher similarity (0 = identical).
    """
    start_time = time.time()
    k = top_k or settings.TOP_K_RETRIEVAL

    if not query or not query.strip():
        return {
            "status": "EMPTY",
            "query": query,
            "chunks": [],
            "formatted_context": "",
            "message": "Query string was empty.",
            "latency_ms": round((time.time() - start_time) * 1000, 2),
        }

    try:
        store = build_or_load_vector_store()
        # similarity_search_with_score returns list of (Document, score)
        results = store.similarity_search_with_score(query, k=k)

        chunks = []
        for doc, score in results:
            # For normalized embeddings with L2 distance, distance <= score_threshold is considered relevant
            chunks.append({
                "chunk_id": doc.metadata.get("chunk_id", "UNKNOWN"),
                "source": doc.metadata.get("source", "student_handbook.pdf"),
                "page_number": doc.metadata.get("page_number", 1),
                "text": doc.page_content,
                "distance_score": round(float(score), 4),
            })

        # Format context string for LLM injection
        if chunks:
            formatted_context = "\n\n---\n\n".join(
                f"[Source: {c['source']} | Page: {c['page_number']} | Chunk ID: {c['chunk_id']}]\n{c['text']}"
                for c in chunks
            )
            status = "SUCCESS"
            msg = f"Retrieved {len(chunks)} relevant policy chunks."
        else:
            formatted_context = ""
            status = "EMPTY"
            msg = "No relevant policy documents found matching the query."

        latency_ms = round((time.time() - start_time) * 1000, 2)
        logger.info(f"RAG retrieval completed for '{query[:30]}...' in {latency_ms}ms (found {len(chunks)} chunks).")

        return {
            "status": status,
            "query": query,
            "chunks": chunks,
            "formatted_context": formatted_context,
            "message": msg,
            "latency_ms": latency_ms,
        }
    except Exception as e:
        logger.error(f"Error during RAG retrieval for query '{query}': {e}", exc_info=True)
        return {
            "status": "ERROR",
            "query": query,
            "chunks": [],
            "formatted_context": "",
            "message": f"Vector retrieval error: {str(e)}",
            "latency_ms": round((time.time() - start_time) * 1000, 2),
        }
