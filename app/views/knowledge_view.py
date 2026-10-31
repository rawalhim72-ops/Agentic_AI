"""
Knowledge Base & Policy Document View for Streamlit.
Provides inspection of the Student Policy Handbook, vector chunks,
and a semantic retrieval testing sandbox.
"""

import streamlit as st
import pandas as pd
from config.settings import settings
from rag.document_loader import load_pdf_document
from rag.chunking import chunk_documents
from rag.retriever import retrieve_policy_knowledge, build_or_load_vector_store


def render_knowledge_view():
    """Renders the Knowledge Base and Vector Store exploration interface."""
    st.markdown('<div class="enterprise-badge">● Semantic Policy Grounding</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div style="margin-bottom: 1.2rem;">
            <h1 style="font-size: 1.85rem; font-weight: 800; margin: 0; color: #F8FAFC; letter-spacing: -0.02em;">
                Student Policy Knowledge Base
            </h1>
            <p style="font-size: 0.88rem; color: #94A3B8; margin: 4px 0 0 0;">
                Document extraction, semantic chunking, and FAISS vector index grounded on the official Student Policy Handbook.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    pdf_path = settings.HANDBOOK_PDF_PATH
    pdf_exists = pdf_path.exists()

    # Top KPI cards
    k1, k2, k3 = st.columns(3)
    with k1:
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-label">Source Document</div>
                <div class="stat-value" style="font-size: 1.15rem; color: #60A5FA;">{pdf_path.name}</div>
                <div class="stat-subtitle">Synthetic Policy PDF</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with k2:
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-label">Index Architecture</div>
                <div class="stat-value" style="font-size: 1.25rem;">FAISS FlatL2</div>
                <div class="stat-subtitle">{settings.EMBEDDING_MODEL}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with k3:
        faiss_exists = (settings.VECTOR_STORE_DIR / "faiss_index").exists()
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-label">Index Status</div>
                <div class="stat-value" style="color: {'#10B981' if faiss_exists else '#F87171'}; font-size: 1.25rem;">
                    {'Active & Persistent' if faiss_exists else 'Not Built'}
                </div>
                <div class="stat-subtitle">Chunk size: {settings.CHUNK_SIZE} (overlap: {settings.CHUNK_OVERLAP})</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

    # Document Chunks Explorer
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.subheader("📚 Indexed Document Chunks")
    st.caption("Each chunk maintains unique provenance metadata including source file, page number, and sub-index.")

    try:
        pages = load_pdf_document(pdf_path)
        chunks = chunk_documents(pages)

        chunk_rows = []
        for c in chunks:
            chunk_rows.append({
                "Chunk ID": c["chunk_id"],
                "Page": c["metadata"].get("page_number"),
                "Char Count": c["metadata"].get("char_count"),
                "Text Preview": c["text"][:120] + "...",
                "Full Text": c["text"],
            })
        df_chunks = pd.DataFrame(chunk_rows)

        st.dataframe(
            df_chunks[["Chunk ID", "Page", "Char Count", "Text Preview"]],
            use_container_width=True,
            hide_index=True,
        )

        col_bld, _ = st.columns([1, 3])
        with col_bld:
            if st.button("🔄 Rebuild FAISS Vector Index"):
                with st.spinner("Re-generating embeddings and building FAISS index..."):
                    build_or_load_vector_store(force_rebuild=True)
                st.success("FAISS index rebuilt successfully.")
                st.rerun()

    except Exception as e:
        st.error(f"Error reading handbook: {e}")
    st.markdown("</div>", unsafe_allow_html=True)

    # Semantic Retrieval Sandbox
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.subheader("🧪 Semantic Similarity Search Sandbox")
    st.caption("Test vector similarity queries and observe retrieved chunks and distance scores in real time.")

    query_input = st.text_input(
        "Enter a policy inquiry:",
        value="Can I pay on the next working day if the payment portal fails?",
    )
    top_k = st.slider("Top-K Chunks to Retrieve", min_value=1, max_value=5, value=2)

    if st.button("🔍 Execute Vector Search"):
        with st.spinner("Searching FAISS vector database..."):
            res = retrieve_policy_knowledge(query_input, top_k=top_k)

        st.markdown(f"**Status:** `{res['status']}` • **Latency:** `{res['latency_ms']:.1f} ms`")

        if res["chunks"]:
            for i, chunk in enumerate(res["chunks"]):
                st.markdown(
                    f"""
                    <div class="trace-box" style="border-left: 3px solid #3B82F6; margin-bottom: 8px;">
                        <b>Rank #{i+1}</b> | <b>Chunk ID:</b> <code>{chunk['chunk_id']}</code> | <b>Page:</b> {chunk['page_number']} | <b>L2 Distance:</b> {chunk.get('distance_score', 0):.4f}<br/>
                        <div style="margin-top: 6px; color: #F1F5F9; font-size: 0.85rem;">{chunk['text']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.warning("No relevant policy chunks found.")
    st.markdown("</div>", unsafe_allow_html=True)
