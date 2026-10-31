"""
RAG Package initialization for Student Support Agent.
"""

from rag.document_loader import load_pdf_document, clean_text
from rag.chunking import chunk_documents
from rag.embeddings import get_embedding_function
from rag.retriever import build_or_load_vector_store, retrieve_policy_knowledge

__all__ = [
    "load_pdf_document",
    "clean_text",
    "chunk_documents",
    "get_embedding_function",
    "build_or_load_vector_store",
    "retrieve_policy_knowledge",
]
