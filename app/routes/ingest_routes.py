import httpx
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import Optional

from app.services.pdf_ingestion_service import ingest_pdf_content
from app.utils.logger import logger

router = APIRouter(prefix="/ingest", tags=["Document Ingestion"])


class UrlIngestRequest(BaseModel):
    url: str
    category: Optional[str] = "GIFT City Circular"
    filename: Optional[str] = "downloaded_guideline.pdf"


@router.post("/pdf-file")
async def ingest_pdf_file_endpoint(
    file: UploadFile = File(...),
    category: Optional[str] = Form("GIFT City Compliance PDF"),
):
    """
    Ingest a local PDF directly via Postman multipart/form-data.
    Upload file key: `file`
    Optional form field: `category`
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    try:
        content = await file.read()
        res = await ingest_pdf_content(
            filename=file.filename,
            pdf_bytes=content,
            category=category,
        )
        return {"success": True, "data": res}
    except Exception as e:
        logger.error(f"[Ingest PDF] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pdf-url")
async def ingest_pdf_url_endpoint(req: UrlIngestRequest):
    """
    Download a PDF from a public web URL and ingest into Qdrant.
    Postman JSON body:
    {
      "url": "https://example.com/gift_city_regulation.pdf",
      "category": "Tax Circular"
    }
    """
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            resp = await client.get(req.url)
            if resp.status_code != 200:
                raise HTTPException(status_code=400, detail=f"Failed to fetch PDF from URL. HTTP {resp.status_code}")
            pdf_bytes = resp.content

        filename = req.filename or req.url.split("/")[-1] or "remote_doc.pdf"
        res = await ingest_pdf_content(
            filename=filename,
            pdf_bytes=pdf_bytes,
            category=req.category or "GIFT City Regulatory PDF",
        )
        return {"success": True, "data": res}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Ingest URL] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
