"""
Chat Route
-----------
POST /api/chat
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, field_validator

from api.pipeline import run_pipeline

router = APIRouter(prefix="/api", tags=["chat"])


class ChatRequest(BaseModel):
    question: str

    @field_validator("question")
    @classmethod
    def question_must_not_be_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("question must not be empty or blank.")
        return v.strip()


@router.post("/chat", status_code=status.HTTP_200_OK)
async def chat(request: ChatRequest):
    """
    Run the full RAG pipeline for a user question and return a structured answer.

    Flow: question → query_understanding → FAISS retrieval → context_builder
          → guardrails → Ollama LLM (or safe fallback) → response
    """
    try:
        result = run_pipeline(request.question)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Knowledge base not found. Please upload your resume and job "
                f"description before asking questions. Detail: {exc}"
            ),
        )
    except ConnectionError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Cannot reach Ollama. Ensure Ollama is running locally. Detail: {exc}",
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"LLM generation error: {exc}",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected pipeline error. Please try again. ({type(exc).__name__})",
        )

    return {
        "question": result["question"],
        "intent": result["intent"],
        "answer": result["answer"],
        "sources": result["sources"],
        "guardrail_blocked": result["guardrail_blocked"],
    }
