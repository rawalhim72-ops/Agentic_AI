"""
Text Chunking Module for RAG Pipeline.
Splits extracted document pages into semantic chunks with unique IDs and metadata tracking.
"""

import logging
from typing import List, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter
from config.settings import settings

logger = logging.getLogger("rag.chunking")


def chunk_documents(
    pages: List[Dict[str, Any]],
    chunk_size: int = None,
    chunk_overlap: int = None,
) -> List[Dict[str, Any]]:
    """
    Split pages into chunks with unique IDs and comprehensive source metadata.
    """
    c_size = chunk_size or settings.CHUNK_SIZE
    c_overlap = chunk_overlap or settings.CHUNK_OVERLAP

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=c_size,
        chunk_overlap=c_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len,
    )

    chunks = []
    chunk_counter = 0

    for page in pages:
        page_text = page["text"]
        page_meta = page["metadata"]
        page_num = page_meta.get("page_number", 1)
        source_name = page_meta.get("source", "document.pdf")

        split_texts = splitter.split_text(page_text)
        for sub_idx, chunk_text in enumerate(split_texts):
            chunk_id = f"CHUNK-{source_name[:8].upper()}-P{page_num}-{sub_idx:02d}"
            chunks.append({
                "chunk_id": chunk_id,
                "text": chunk_text.strip(),
                "metadata": {
                    **page_meta,
                    "chunk_id": chunk_id,
                    "chunk_index": chunk_counter,
                    "sub_index": sub_idx,
                    "char_count": len(chunk_text.strip()),
                }
            })
            chunk_counter += 1

    logger.info(f"Generated {len(chunks)} chunks from {len(pages)} pages (size={c_size}, overlap={c_overlap}).")
    return chunks
