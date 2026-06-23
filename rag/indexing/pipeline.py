import logging
from typing import List, Optional

from clients.supabase_client import get_supabase_client
from rag.indexing.chunking import build_chunks
from rag.indexing.embedding import embed_batch
from rag.indexing.text_extraction import DocumentElement

logger = logging.getLogger(__name__)


def run_indexing_pipeline(
    elements: List[DocumentElement],
    evaluasi_id: str,
    vendor_id: str,
    dokumen_upload_id: str,
) -> dict:
    """Pipeline B: hierarchical chunking + embedding + bulk insert into dokumen_chunk."""
    supabase = get_supabase_client()

    if not elements:
        _update_dokumen_upload(supabase, dokumen_upload_id, "skipped_no_text", 0)
        return {"status": "skipped_no_text", "chunk_count": 0}

    try:
        chunks = build_chunks(elements)
        parent_chunks = [c for c in chunks if c.is_parent]
        child_chunks = [c for c in chunks if not c.is_parent]

        if not child_chunks:
            _update_dokumen_upload(supabase, dokumen_upload_id, "skipped_no_text", 0)
            return {"status": "skipped_no_text", "chunk_count": 0}

        embeddings = embed_batch([c.text for c in child_chunks])
        for chunk, embedding in zip(child_chunks, embeddings):
            chunk.embedding = embedding

        rows = [_chunk_to_row(c, evaluasi_id, vendor_id, dokumen_upload_id) for c in parent_chunks + child_chunks]

        if supabase is not None:
            supabase.table("dokumen_chunk").insert(rows).execute()

        _update_dokumen_upload(supabase, dokumen_upload_id, "done", len(child_chunks))
        return {"status": "done", "chunk_count": len(child_chunks)}

    except Exception as exc:
        logger.error("Pipeline B (RAG indexing) gagal untuk dokumen_upload_id=%s: %s", dokumen_upload_id, exc)
        _update_dokumen_upload(supabase, dokumen_upload_id, "failed", None)
        return {"status": "failed", "chunk_count": None}


def _chunk_to_row(chunk, evaluasi_id: str, vendor_id: str, dokumen_upload_id: str) -> dict:
    return {
        "id": chunk.id,
        "evaluasi_id": evaluasi_id,
        "vendor_id": vendor_id,
        "dokumen_upload_id": dokumen_upload_id,
        "is_parent": chunk.is_parent,
        "parent_chunk_id": chunk.parent_chunk_id,
        "teks_chunk": chunk.text,
        "embedding": chunk.embedding,
        "halaman": chunk.halaman,
        "tipe_konten": chunk.tipe_konten,
        "posisi_section": chunk.posisi_section,
        "chunk_index": chunk.chunk_index,
        "token_count": chunk.token_count,
    }


def _update_dokumen_upload(supabase, dokumen_upload_id: str, indexing_rag_status: str, chunk_count: Optional[int]) -> None:
    if supabase is None:
        return
    supabase.table("dokumen_upload").update({
        "indexing_rag_status": indexing_rag_status,
        "chunk_count": chunk_count,
    }).eq("id", dokumen_upload_id).execute()
