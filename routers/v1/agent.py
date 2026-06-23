import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Literal, Optional

from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from agents.ekstraksi_dokumen.extractor import extract_fields
from clients.supabase_client import get_supabase_client
from rag.indexing.pipeline import run_indexing_pipeline
from rag.indexing.text_extraction import download_file, elements_to_text, extract_elements

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1/agent", tags=["agent"])


class EkstrakDokumenRequest(BaseModel):
    dokumen_upload_id: str
    evaluasi_id: str
    vendor_id: str
    file_url: str
    file_type: Literal["pdf", "excel"]
    nama_vendor_hint: Optional[str] = None


@router.post("/ekstrak-dokumen", status_code=202)
async def ekstrak_dokumen(payload: EkstrakDokumenRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(_process_dokumen, payload)
    return JSONResponse(
        status_code=202,
        content={"status": "accepted", "dokumen_upload_id": payload.dokumen_upload_id},
    )


def _process_dokumen(payload: EkstrakDokumenRequest) -> None:
    supabase = get_supabase_client()
    _update_status_ekstraksi(supabase, payload.dokumen_upload_id, "processing")

    try:
        file_bytes = download_file(payload.file_url)
        elements = extract_elements(file_bytes, payload.file_type)
        document_text = elements_to_text(elements)
    except Exception as exc:
        logger.error("Gagal mengunduh/mengekstrak teks dokumen_upload_id=%s: %s", payload.dokumen_upload_id, exc)
        _update_status_ekstraksi(supabase, payload.dokumen_upload_id, "failed")
        return

    with ThreadPoolExecutor(max_workers=2) as executor:
        future_a = executor.submit(_run_pipeline_a, document_text, payload, supabase)
        future_b = executor.submit(
            run_indexing_pipeline, elements, payload.evaluasi_id, payload.vendor_id, payload.dokumen_upload_id
        )
        pipeline_a_ok = future_a.result()
        pipeline_b_result = future_b.result()

    if not pipeline_a_ok:
        final_status = "failed"
    elif pipeline_b_result["status"] in ("done", "skipped_no_text"):
        final_status = "done"
    else:
        final_status = "done_partial"

    _update_status_ekstraksi(supabase, payload.dokumen_upload_id, final_status)


def _run_pipeline_a(document_text: str, payload: EkstrakDokumenRequest, supabase) -> bool:
    try:
        result = extract_fields(document_text, payload.nama_vendor_hint)
        if supabase is not None:
            supabase.table("dokumen_upload").update({
                "hasil_ekstraksi": result,
                "confidence_score": result.get("confidence_overall"),
            }).eq("id", payload.dokumen_upload_id).execute()
        return True
    except Exception as exc:
        logger.error("Pipeline A (ekstraksi field) gagal untuk dokumen_upload_id=%s: %s", payload.dokumen_upload_id, exc)
        return False


def _update_status_ekstraksi(supabase, dokumen_upload_id: str, status: str) -> None:
    if supabase is None:
        return
    supabase.table("dokumen_upload").update({"status_ekstraksi": status}).eq("id", dokumen_upload_id).execute()
