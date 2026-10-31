"""
Embedding Generation for RAG Pipeline.
Provides local offline embeddings via Sentence Transformers or cloud embeddings via OpenAI.
"""

import logging
from typing import Optional
from langchain_core.embeddings import Embeddings
from config.settings import settings

logger = logging.getLogger("rag.embeddings")

_cached_embedding_model: Optional[Embeddings] = None


def get_embedding_function() -> Embeddings:
    """
    Returns configured embedding model instance (Sentence Transformers local or OpenAI).
    Caches instance in memory for fast performance.
    """
    global _cached_embedding_model
    if _cached_embedding_model is not None:
        return _cached_embedding_model

    provider = settings.EMBEDDING_PROVIDER.lower()
    logger.info(f"Initializing embedding provider: {provider} (model: {settings.EMBEDDING_MODEL})")

    if provider == "openai" and settings.has_openai_key:
        try:
            from langchain_openai import OpenAIEmbeddings
            _cached_embedding_model = OpenAIEmbeddings(
                model=settings.EMBEDDING_MODEL if "embedding" in settings.EMBEDDING_MODEL else "text-embedding-3-small",
                api_key=settings.LLM_API_KEY,
                base_url=settings.LLM_BASE_URL,
            )
            return _cached_embedding_model
        except Exception as e:
            logger.warning(f"Failed to initialize OpenAIEmbeddings ({e}), falling back to local SentenceTransformers.")

    # Default: Local offline SentenceTransformers
    try:
        from sentence_transformers import SentenceTransformer

        class DirectSentenceTransformerEmbeddings(Embeddings):
            def __init__(self, model_name: str):
                self.model = SentenceTransformer(model_name)

            def embed_documents(self, texts: list[str]) -> list[list[float]]:
                embs = self.model.encode(texts, normalize_embeddings=True)
                return embs.tolist()

            def embed_query(self, text: str) -> list[float]:
                emb = self.model.encode(text, normalize_embeddings=True)
                return emb.tolist()

        _cached_embedding_model = DirectSentenceTransformerEmbeddings(settings.EMBEDDING_MODEL)
        return _cached_embedding_model
    except Exception as e:
        logger.error(f"Failed to load SentenceTransformer: {e}", exc_info=True)
        raise
