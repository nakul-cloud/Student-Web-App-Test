import io
import re
import uuid
from typing import List, Dict, Any
from pypdf import PdfReader
from qdrant_client.models import PointStruct

from app.providers.qdrant_provider import get_qdrant_client
from app.config.settings import settings
from app.utils.logger import logger


def extract_pages_from_pdf(pdf_bytes: bytes) -> List[Dict[str, Any]]:
    """Extracts text page-by-page to preserve section integrity."""
    reader = PdfReader(io.BytesIO(pdf_bytes))
    pages_data = []
    for idx, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        text = text.strip()
        if len(text) > 80:  # Skip blank/image-only pages
            pages_data.append({
                "page_num": idx + 1,
                "text": text,
            })
    return pages_data


def chunk_page_text(text: str, max_chars: int = 700) -> List[str]:
    """Chunks long text into logical paragraphs."""
    paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 30]
    chunks = []
    curr = ""
    for p in paragraphs:
        if len(curr) + len(p) <= max_chars:
            curr += " " + p if curr else p
        else:
            if curr:
                chunks.append(curr)
            curr = p
    if curr:
        chunks.append(curr)
    return chunks if chunks else [text[:max_chars]]


async def ingest_pdf_content(
    filename: str,
    pdf_bytes: bytes,
    category: str = "GIFT City IFSC Regulatory Guide"
) -> Dict[str, Any]:
    pages = extract_pages_from_pdf(pdf_bytes)
    if not pages:
        raise ValueError(f"Could not extract readable text from {filename}")

    client = get_qdrant_client()
    points = []
    
    # Use deterministic or unique integer ID range
    seed_offset = abs(hash(filename)) % 1000000

    point_counter = 0
    for page in pages:
        p_num = page["page_num"]
        chunks = chunk_page_text(page["text"])
        for c_idx, chunk in enumerate(chunks):
            point_counter += 1
            pid = seed_offset + point_counter
            words = [w for w in re.split(r"\W+", chunk.lower()) if len(w) > 3]

            # Formulate a representative compliance topic/question from first sentence
            first_line = chunk.split("\n")[0][:100]

            points.append(
                PointStruct(
                    id=pid,
                    vector={},  # Zero vector vectorless Qdrant point
                    payload={
                        "id": pid,
                        "category": category,
                        "question": f"{first_line} ({filename} p.{p_num})",
                        "answer": chunk,
                        "source": f"{filename} (Page {p_num})",
                        "keywords": " ".join(words[:40]),
                    }
                )
            )

    # Batch upsert in groups of 100
    batch_size = 100
    for i in range(0, len(points), batch_size):
        await client.upsert(
            collection_name=settings.qdrant_collection,
            points=points[i:i + batch_size],
        )

    logger.info(f"[PDF Ingest] Successfully indexed {len(points)} chunks from {filename} across {len(pages)} pages.")
    return {
        "filename": filename,
        "pages_processed": len(pages),
        "chunks_indexed": len(points),
        "status": "success",
    }
