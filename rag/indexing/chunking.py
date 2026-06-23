import uuid
from dataclasses import dataclass
from typing import Dict, List, Optional

from rag.indexing.text_extraction import DocumentElement

CHILD_TOKEN_TARGET_MAX = 500
SENTENCE_OVERLAP_TOKEN_MAX = 50
PARENT_TOKEN_TARGET_MAX = 1500
LIST_ITEMS_PER_CHUNK = 10


def estimate_tokens(text: str) -> int:
    """Rough heuristic: ~4 characters per token, no tokenizer dependency needed."""
    return max(1, len(text) // 4)


@dataclass
class Chunk:
    id: str
    is_parent: bool
    text: str
    halaman: int
    tipe_konten: str
    posisi_section: Optional[str]
    chunk_index: int
    token_count: int
    parent_chunk_id: Optional[str] = None
    embedding: Optional[List[float]] = None


def _split_paragraph(text: str) -> List[str]:
    if estimate_tokens(text) <= CHILD_TOKEN_TARGET_MAX:
        return [text]

    sentences = [s.strip() for s in text.replace("\n", " ").split(". ") if s.strip()]
    parts: List[str] = []
    current: List[str] = []
    current_tokens = 0

    for sentence in sentences:
        sentence_tokens = estimate_tokens(sentence)
        if current_tokens + sentence_tokens > CHILD_TOKEN_TARGET_MAX and current:
            parts.append(". ".join(current) + ".")
            overlap_sentence = current[-1]
            if estimate_tokens(overlap_sentence) <= SENTENCE_OVERLAP_TOKEN_MAX:
                current = [overlap_sentence]
                current_tokens = estimate_tokens(overlap_sentence)
            else:
                current = []
                current_tokens = 0
        current.append(sentence)
        current_tokens += sentence_tokens

    if current:
        parts.append(". ".join(current) + ".")
    return parts


def _split_list(text: str) -> List[str]:
    lines = [line for line in text.splitlines() if line.strip()]
    if len(lines) <= LIST_ITEMS_PER_CHUNK + 1:
        return [text]

    header, items = lines[0], lines[1:]
    parts = []
    for i in range(0, len(items), LIST_ITEMS_PER_CHUNK):
        group = items[i:i + LIST_ITEMS_PER_CHUNK]
        parts.append("\n".join([header] + group))
    return parts


def build_chunks(elements: List[DocumentElement]) -> List[Chunk]:
    """Hierarchical parent-child chunking per AI-05 section 7: each section header
    starts a new parent chunk; tables are always atomic; long lists/paragraphs split."""
    chunks: List[Chunk] = []
    parent_texts: Dict[str, List[str]] = {}
    current_section: Optional[str] = None
    parent_id: Optional[str] = None
    parent_token_count = 0
    chunk_index = 0

    def start_new_parent(halaman: int, section: Optional[str]) -> str:
        nonlocal chunk_index
        new_parent_id = str(uuid.uuid4())
        chunks.append(Chunk(
            id=new_parent_id,
            is_parent=True,
            text="",
            halaman=halaman,
            tipe_konten="header",
            posisi_section=section,
            chunk_index=chunk_index,
            token_count=0,
        ))
        chunk_index += 1
        parent_texts[new_parent_id] = []
        return new_parent_id

    for element in elements:
        if element.tipe_konten == "header":
            current_section = element.text
            parent_id = start_new_parent(element.halaman, current_section)
            parent_token_count = 0
            continue

        if parent_id is None:
            parent_id = start_new_parent(element.halaman, element.posisi_section or current_section)
            parent_token_count = 0

        if element.tipe_konten == "tabel":
            child_texts = [element.text]
        elif element.tipe_konten == "list":
            child_texts = _split_list(element.text)
        else:
            child_texts = _split_paragraph(element.text)

        for child_text in child_texts:
            token_count = estimate_tokens(child_text)

            if parent_token_count >= PARENT_TOKEN_TARGET_MAX:
                parent_id = start_new_parent(element.halaman, element.posisi_section or current_section)
                parent_token_count = 0

            chunks.append(Chunk(
                id=str(uuid.uuid4()),
                is_parent=False,
                text=child_text,
                halaman=element.halaman,
                tipe_konten=element.tipe_konten,
                posisi_section=element.posisi_section or current_section,
                chunk_index=chunk_index,
                token_count=token_count,
                parent_chunk_id=parent_id,
            ))
            chunk_index += 1
            parent_texts[parent_id].append(child_text)
            parent_token_count += token_count

    for chunk in chunks:
        if chunk.is_parent:
            chunk.text = "\n\n".join(parent_texts.get(chunk.id, []))
            chunk.token_count = estimate_tokens(chunk.text)

    return chunks
