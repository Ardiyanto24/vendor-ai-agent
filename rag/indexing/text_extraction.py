import io
from dataclasses import dataclass
from typing import List, Optional

import httpx
import openpyxl
import pdfplumber


@dataclass
class DocumentElement:
    tipe_konten: str  # paragraf | tabel | list | header
    text: str
    halaman: int
    posisi_section: Optional[str] = None


def download_file(file_url: str) -> bytes:
    response = httpx.get(file_url, timeout=30.0)
    response.raise_for_status()
    return response.content


def _looks_like_header(block: str) -> bool:
    return len(block) < 80 and "\n" not in block and (block.isupper() or block.endswith(":"))


def _starts_with_number(line: str) -> bool:
    stripped = line.strip()
    return len(stripped) > 1 and stripped[0].isdigit() and stripped[1] in ".)"


def _looks_like_list(lines: List[str]) -> bool:
    if len(lines) < 2:
        return False
    bullet_lines = sum(
        1 for line in lines if line.strip().startswith(("-", "*", "•")) or _starts_with_number(line)
    )
    return bullet_lines >= len(lines) * 0.6


def extract_pdf_elements(file_bytes: bytes) -> List[DocumentElement]:
    elements: List[DocumentElement] = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page_index, page in enumerate(pdf.pages, start=1):
            for table in page.extract_tables():
                rows = [" | ".join(cell or "" for cell in row) for row in table]
                if rows:
                    elements.append(DocumentElement("tabel", "\n".join(rows), page_index))

            text = page.extract_text() or ""
            blocks = [block.strip() for block in text.split("\n\n") if block.strip()]
            for block in blocks:
                lines = block.splitlines()
                if _looks_like_header(block):
                    elements.append(DocumentElement("header", block, page_index))
                elif _looks_like_list(lines):
                    elements.append(DocumentElement("list", block, page_index))
                else:
                    elements.append(DocumentElement("paragraf", block, page_index))
    return elements


def extract_excel_elements(file_bytes: bytes) -> List[DocumentElement]:
    elements: List[DocumentElement] = []
    workbook = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
    for sheet_index, sheet in enumerate(workbook.worksheets, start=1):
        rows = []
        for row in sheet.iter_rows(values_only=True):
            if any(cell is not None for cell in row):
                rows.append(" | ".join("" if cell is None else str(cell) for cell in row))
        if rows:
            elements.append(DocumentElement("tabel", "\n".join(rows), sheet_index, posisi_section=sheet.title))
    return elements


def extract_elements(file_bytes: bytes, file_type: str) -> List[DocumentElement]:
    if file_type == "pdf":
        return extract_pdf_elements(file_bytes)
    if file_type == "excel":
        return extract_excel_elements(file_bytes)
    raise ValueError(f"Unsupported file_type: {file_type}")


def elements_to_text(elements: List[DocumentElement]) -> str:
    return "\n\n".join(element.text for element in elements)
