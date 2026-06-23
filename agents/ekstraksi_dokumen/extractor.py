import json
import os
import time
from pathlib import Path
from typing import Optional

PROMPT_DIR = Path(__file__).resolve().parent.parent.parent / "prompts" / "ekstraksi_dokumen"
MAX_RETRIES = 2
BACKOFF_BASE_SECONDS = 5
CONFIDENCE_THRESHOLD = 0.7
FIELD_KEYS = [
    "nama_perusahaan", "harga_penawaran", "kontak",
    "spesifikasi_ditawarkan", "masa_garansi", "payment_terms",
]


def _load_prompt(filename: str) -> str:
    return (PROMPT_DIR / filename).read_text(encoding="utf-8")


def _fill_template(template: str, values: dict) -> str:
    for key, value in values.items():
        template = template.replace(f"{{{{{key}}}}}", str(value))
    return template


def _get_client():
    from openai import OpenAI

    return OpenAI(
        base_url=os.environ["OPENROUTER_BASE_URL"],
        api_key=os.environ["OPENROUTER_API_KEY"],
    )


def _parse_json_strict(content: str) -> dict:
    cleaned = content.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[len("json"):]
    return json.loads(cleaned.strip())


def _validate_schema(data: dict) -> None:
    for key in FIELD_KEYS:
        if key not in data or "nilai" not in data[key] or "confidence" not in data[key]:
            raise ValueError(f"Field '{key}' tidak sesuai schema yang diharapkan")
    if "confidence_overall" not in data:
        raise ValueError("Field 'confidence_overall' tidak ditemukan")


def _flag_low_confidence(data: dict) -> dict:
    low_confidence_fields = []
    for key in FIELD_KEYS:
        confidence = data[key].get("confidence", 0.0)
        perlu_verifikasi = confidence < CONFIDENCE_THRESHOLD
        data[key]["perlu_verifikasi"] = perlu_verifikasi
        if perlu_verifikasi:
            low_confidence_fields.append(key)
    data["fields_perlu_verifikasi"] = low_confidence_fields
    return data


def extract_fields(document_text: str, nama_vendor_hint: Optional[str]) -> dict:
    """Pipeline A: call LLM with prompts/ekstraksi_dokumen, retry 2x with exponential backoff."""
    system_prompt = _load_prompt("system.md")
    user_template = _load_prompt("user_template.md")
    user_content = _fill_template(user_template, {
        "document_text": document_text,
        "nama_vendor_hint": nama_vendor_hint or "Tidak ada",
    })

    client = _get_client()
    last_error = None

    for attempt in range(MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model="deepseek/deepseek-v4-flash",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                max_tokens=2000,
                timeout=60.0,
            )
            data = _parse_json_strict(response.choices[0].message.content)
            _validate_schema(data)
            return _flag_low_confidence(data)
        except Exception as exc:
            last_error = exc
            if attempt < MAX_RETRIES:
                time.sleep(BACKOFF_BASE_SECONDS * (2 ** attempt))

    raise RuntimeError(f"Ekstraksi field gagal setelah {MAX_RETRIES} retry") from last_error
