import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

import main
from main import app
from agents.ekstraksi_dokumen import extractor
from rag.indexing.chunking import build_chunks
from rag.indexing.text_extraction import DocumentElement
from routers.v1 import agent as agent_router

client = TestClient(app)


def _auth_headers():
    main.SERVICE_TOKEN = "test-token"
    return {"X-Service-Token": "test-token"}


def test_ekstrak_dokumen_returns_202_immediately():
    headers = _auth_headers()
    payload = {
        "dokumen_upload_id": "11111111-1111-1111-1111-111111111111",
        "evaluasi_id": "22222222-2222-2222-2222-222222222222",
        "vendor_id": "33333333-3333-3333-3333-333333333333",
        "file_url": "https://example.com/file.pdf",
        "file_type": "pdf",
    }
    with patch.object(agent_router.BackgroundTasks, "add_task"):
        response = client.post("/v1/agent/ekstrak-dokumen", json=payload, headers=headers)
    assert response.status_code == 202
    assert response.json()["status"] == "accepted"


def _make_chat_response(content: str):
    message = MagicMock()
    message.content = content
    choice = MagicMock()
    choice.message = message
    response = MagicMock()
    response.choices = [choice]
    return response


def test_extractor_flags_low_confidence_fields():
    valid_json = json.dumps({
        "nama_perusahaan": {"nilai": "PT Maju", "confidence": 0.9},
        "harga_penawaran": {"nilai": 1000000, "confidence": 0.5, "mata_uang": "IDR"},
        "kontak": {"nilai": "08123", "confidence": 0.8},
        "spesifikasi_ditawarkan": {"nilai": ["A", "B"], "confidence": 0.6},
        "masa_garansi": {"nilai": "1 tahun", "confidence": 0.9},
        "payment_terms": {"nilai": "30 hari", "confidence": 0.95},
        "catatan_ekstraksi": "ok",
        "confidence_overall": 0.78,
    })
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _make_chat_response(valid_json)

    with patch.object(extractor, "_get_client", return_value=mock_client):
        result = extractor.extract_fields("isi dokumen", "PT Maju")

    assert result["harga_penawaran"]["perlu_verifikasi"] is True
    assert result["nama_perusahaan"]["perlu_verifikasi"] is False
    assert "harga_penawaran" in result["fields_perlu_verifikasi"]
    assert "spesifikasi_ditawarkan" in result["fields_perlu_verifikasi"]


def test_extractor_retries_then_raises_on_persistent_failure():
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _make_chat_response("bukan json")

    with patch.object(extractor, "_get_client", return_value=mock_client), \
         patch.object(extractor.time, "sleep", return_value=None):
        with pytest.raises(RuntimeError):
            extractor.extract_fields("isi dokumen", None)

    assert mock_client.chat.completions.create.call_count == 3


def test_chunking_keeps_table_atomic():
    elements = [
        DocumentElement("header", "SPESIFIKASI", 1),
        DocumentElement("tabel", "Item | Harga\nA | 100\nB | 200", 1),
    ]
    chunks = build_chunks(elements)
    table_chunks = [c for c in chunks if c.tipe_konten == "tabel"]
    assert len(table_chunks) == 1
    assert "Item | Harga" in table_chunks[0].text


def test_chunking_splits_long_list_per_10_items():
    items = "\n".join(f"- item {i}" for i in range(15))
    elements = [
        DocumentElement("header", "DAFTAR", 1),
        DocumentElement("list", "Daftar Barang\n" + items, 1),
    ]
    chunks = build_chunks(elements)
    list_chunks = [c for c in chunks if c.tipe_konten == "list"]
    assert len(list_chunks) == 2


def test_chunking_child_chunks_reference_parent():
    elements = [
        DocumentElement("header", "GARANSI", 1),
        DocumentElement("paragraf", "Garansi diberikan selama satu tahun penuh.", 1),
    ]
    chunks = build_chunks(elements)
    parents = [c for c in chunks if c.is_parent]
    children = [c for c in chunks if not c.is_parent]
    assert len(parents) == 1
    assert all(c.parent_chunk_id == parents[0].id for c in children)
