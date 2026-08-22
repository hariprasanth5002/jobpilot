"""
Document Upload Routes
-----------------------
POST /api/documents/resume
POST /api/documents/job-description
"""

import shutil
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from api.pipeline import UPLOAD_DIR, ingest_document

router = APIRouter(prefix="/api/documents", tags=["documents"])

# Allowed MIME types for PDF uploads
_ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/x-pdf",
    "application/octet-stream",  # some clients send this for PDFs
}


def _save_upload(upload_file: UploadFile, filename: str) -> Path:
    """Persist the uploaded file to the uploads directory and return its path."""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    dest = UPLOAD_DIR / filename
    with dest.open("wb") as out_file:
        shutil.copyfileobj(upload_file.file, out_file)
    return dest


def _validate_pdf(upload_file: UploadFile) -> None:
    """Raise HTTPException if the upload does not look like a PDF."""
    # Check filename extension
    if upload_file.filename and not upload_file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are accepted. Please upload a .pdf file.",
        )
    # Check content-type header (allow missing / octet-stream as fallback)
    content_type = (upload_file.content_type or "").split(";")[0].strip().lower()
    if content_type and content_type not in _ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported media type '{content_type}'. Expected application/pdf.",
        )


@router.post("/resume", status_code=status.HTTP_200_OK)
async def upload_resume(file: UploadFile = File(...)):
    """
    Upload a resume PDF.

    Runs: PDF → extract → clean → chunk → embed → FAISS (merged with existing KB).
    """
    _validate_pdf(file)

    saved_path = _save_upload(file, "resume.pdf")

    try:
        result = ingest_document(str(saved_path), source="resume")
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error during PDF processing: {exc}",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error processing resume: {exc}",
        )

    return {
        "message": "Resume uploaded and indexed successfully.",
        **result,
    }


@router.post("/job-description", status_code=status.HTTP_200_OK)
async def upload_job_description(file: UploadFile = File(...)):
    """
    Upload a job description PDF.

    Runs: PDF → extract → clean → chunk → embed → FAISS (merged with existing KB).
    """
    _validate_pdf(file)

    saved_path = _save_upload(file, "job_description.pdf")

    try:
        result = ingest_document(str(saved_path), source="job_description")
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error during PDF processing: {exc}",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error processing job description: {exc}",
        )

    return {
        "message": "Job description uploaded and indexed successfully.",
        **result,
    }
