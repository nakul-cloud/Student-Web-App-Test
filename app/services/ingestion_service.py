import json
from pathlib import Path
from typing import List, Dict, Any
from qdrant_client.models import PointStruct, TextIndexParams, TokenizerType
from app.providers.qdrant_provider import get_qdrant_client
from app.config.settings import settings
from app.utils.logger import logger


def load_seed_faqs() -> List[Dict[str, Any]]:
    """Loads curated GIFT City compliance FAQs from app/data/compliance_faqs.json."""
    data_path = Path(__file__).resolve().parent.parent / "data" / "compliance_faqs.json"
    if not data_path.exists():
        logger.warning(f"[Qdrant Seeding] FAQ data file not found at {data_path}")
        return []
    with open(data_path, "r", encoding="utf-8") as f:
        return json.load(f)


async def seed_qdrant_faqs() -> int:
    """Initializes vectorless Qdrant collection and upserts all curated compliance FAQs."""
    client = get_qdrant_client()
    collection_name = settings.qdrant_collection
    faqs = load_seed_faqs()

    if not faqs:
        logger.warning("[Qdrant Seeding] No FAQs loaded to seed.")
        return 0

    logger.info(f"[Qdrant Seeding] Checking collection: {collection_name}")
    collections_res = await client.get_collections()
    existing_collections = [c.name for c in collections_res.collections]

    if collection_name not in existing_collections:
        logger.info(f"[Qdrant Seeding] Creating vectorless collection '{collection_name}' (zero vector dimension)")
        await client.create_collection(
            collection_name=collection_name,
            vectors_config={},  # Vectorless: no dense vector storage
        )

        # Create full-text payload indexes on question, keywords, and answer
        for field_name in ("question", "keywords", "answer"):
            await client.create_payload_index(
                collection_name=collection_name,
                field_name=field_name,
                field_schema=TextIndexParams(
                    type="text",
                    tokenizer=TokenizerType.WORD,
                    min_token_len=2,
                    max_token_len=20,
                    lowercase=True,
                ),
            )
        logger.info("[Qdrant Seeding] Created full-text payload indices on 'question', 'keywords', and 'answer'")

    # Upsert points with payload only (id + metadata, vectors={})
    points = [
        PointStruct(
            id=faq["id"],
            vector={},  # Explicitly zero vectors
            payload={
                "id": faq["id"],
                "category": faq["category"],
                "question": faq["question"],
                "answer": faq["answer"],
                "source": faq["source"],
                "keywords": " ".join(faq["keywords"]) if isinstance(faq["keywords"], list) else str(faq["keywords"]),
            }
        )
        for faq in faqs
    ]

    await client.upsert(
        collection_name=collection_name,
        points=points,
    )
    logger.info(f"[Qdrant Seeding] Successfully ingested {len(points)} vectorless compliance FAQs into Qdrant.")
    return len(points)
