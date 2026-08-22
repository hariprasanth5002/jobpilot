"""
Profile Route
--------------
POST /api/profile
"""

from fastapi import APIRouter, HTTPException, status

from api.pipeline import ingest_user_details
from models.user import UserDetails

router = APIRouter(prefix="/api", tags=["profile"])


@router.post("/profile", status_code=status.HTTP_200_OK)
async def submit_profile(user: UserDetails):
    """
    Accept structured user details and index them into the knowledge base.

    The details are converted to a structured text chunk (source='user_details')
    and merged into the FAISS index alongside the resume and job description.
    """
    try:
        result = ingest_user_details(user.model_dump())
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error processing user profile: {exc}",
        )

    return {
        "message": "User profile indexed successfully.",
        **result,
    }
