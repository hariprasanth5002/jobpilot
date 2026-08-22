from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Union

from retrieval.retriever import RetrievalResponse


@dataclass
class StructuredContext:
    """
    Structured context segmented by origin source with preserved metadata.
    """
    question: str
    intent: str
    retrieval_strategy: List[str]
    resume: List[Dict[str, Any]] = field(default_factory=list)
    job_description: List[Dict[str, Any]] = field(default_factory=list)
    user_details: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def total_chunks(self) -> int:
        return len(self.resume) + len(self.job_description) + len(self.user_details)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "question": self.question,
            "intent": self.intent,
            "retrieval_strategy": self.retrieval_strategy,
            "total_chunks": self.total_chunks,
            "resume": self.resume,
            "job_description": self.job_description,
            "user_details": self.user_details,
        }


def build_context(
    question: str,
    retrieval_result: Union[RetrievalResponse, Dict[str, Any]],
) -> StructuredContext:
    """
    Transform raw retrieved chunks into a clearly structured context
    segregated by source (RESUME, JOB DESCRIPTION, USER DETAILS).
    """
    if isinstance(retrieval_result, RetrievalResponse):
        intent = retrieval_result.intent
        strategy = retrieval_result.retrieval_strategy
        results = retrieval_result.results
    elif isinstance(retrieval_result, dict):
        intent = retrieval_result.get("intent", "GENERAL_JOB_QUESTION")
        strategy = retrieval_result.get("retrieval_strategy", ["resume", "job_description", "user_details"])
        results = retrieval_result.get("results", [])
    else:
        intent = "GENERAL_JOB_QUESTION"
        strategy = ["resume", "job_description", "user_details"]
        results = []

    resume_chunks: List[Dict[str, Any]] = []
    jd_chunks: List[Dict[str, Any]] = []
    user_chunks: List[Dict[str, Any]] = []

    for r in results:
        chunk_entry = {
            "rank": r.get("rank", 0),
            "faiss_id": r.get("faiss_id", 0),
            "chunk_id": r.get("chunk_id", 0),
            "source": r.get("source", ""),
            "section": r.get("section", ""),
            "text": r.get("text", ""),
            "distance": r.get("distance", 0.0),
        }

        source = str(r.get("source", "")).lower()
        if source == "resume":
            resume_chunks.append(chunk_entry)
        elif source == "job_description":
            jd_chunks.append(chunk_entry)
        elif source == "user_details":
            user_chunks.append(chunk_entry)
        else:
            # Fallback based on metadata or default to user_details
            user_chunks.append(chunk_entry)

    return StructuredContext(
        question=question.strip() if question else "",
        intent=intent,
        retrieval_strategy=strategy,
        resume=resume_chunks,
        job_description=jd_chunks,
        user_details=user_chunks,
    )


def format_llm_prompt_context(context: StructuredContext) -> str:
    """
    Produce a clean, strictly organized context prompt string for the LLM.
    """
    sections: List[str] = [
        "SYSTEM CONTEXT",
        f"Target Intent: {context.intent}",
        f"USER QUESTION: {context.question}",
        "",
    ]

    # 1. Resume Information
    sections.append("RESUME INFORMATION:")
    if context.resume:
        for c in context.resume:
            sections.append(f"[Chunk ID: {c['chunk_id']} | Section: {c['section']}]")
            sections.append(c["text"])
            sections.append("")
    else:
        sections.append("(No resume information retrieved)")
        sections.append("")

    # 2. Job Description Information
    sections.append("JOB DESCRIPTION:")
    if context.job_description:
        for c in context.job_description:
            sections.append(f"[Chunk ID: {c['chunk_id']} | Section: {c['section']}]")
            sections.append(c["text"])
            sections.append("")
    else:
        sections.append("(No job description information retrieved)")
        sections.append("")

    # 3. User Details
    sections.append("USER DETAILS:")
    if context.user_details:
        for c in context.user_details:
            sections.append(f"[Chunk ID: {c['chunk_id']} | Section: {c['section']}]")
            sections.append(c["text"])
            sections.append("")
    else:
        sections.append("(No additional user details retrieved)")
        sections.append("")

    # 4. Strict Guardrail Rules for the LLM
    sections.append("IMPORTANT RULES:")
    sections.append("- Use ONLY the supplied context above to answer the user question.")
    sections.append("- Never invent or assume user experience, skills, projects, or credentials.")
    sections.append("- Clearly distinguish candidate facts from job requirements.")
    sections.append("- If specific information is missing or unverified, explicitly state that it is not found in the context.")

    return "\n".join(sections)
