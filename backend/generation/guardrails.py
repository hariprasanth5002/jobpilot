from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from generation.context_builder import StructuredContext, format_llm_prompt_context


@dataclass
class GuardrailResult:
    """
    Validation outcome of context guardrail analysis.
    """
    allowed: bool
    warnings: List[str] = field(default_factory=list)
    context: Optional[StructuredContext] = None
    prompt_context: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "allowed": self.allowed,
            "warnings": self.warnings,
            "context": self.context.to_dict() if self.context else None,
            "prompt_context": self.prompt_context,
        }


class ContextGuardrail:
    """
    Validates and structures retrieval context before handing off to LLM generation.
    Enforces factual containment, source integrity, and missing information detection.
    """

    @staticmethod
    def validate(context: StructuredContext) -> GuardrailResult:
        warnings: List[str] = []

        # Rule 7 & Rule 1: Check for empty or insufficient context
        if not context.question or not context.question.strip():
            return GuardrailResult(
                allowed=False,
                warnings=["Empty or invalid question provided."],
                context=context,
                prompt_context="",
            )

        if context.total_chunks == 0:
            return GuardrailResult(
                allowed=False,
                warnings=["Insufficient information in the retrieved context."],
                context=context,
                prompt_context="",
            )

        # Rule 3, 5, 6: Verify source segregation integrity
        for chunk in context.resume:
            if chunk.get("source") != "resume":
                warnings.append(
                    f"Integrity warning: Chunk {chunk.get('chunk_id')} in resume context has source '{chunk.get('source')}'."
                )

        for chunk in context.job_description:
            if chunk.get("source") != "job_description":
                warnings.append(
                    f"Integrity warning: Chunk {chunk.get('chunk_id')} in JD context has source '{chunk.get('source')}'."
                )

        for chunk in context.user_details:
            if chunk.get("source") != "user_details":
                warnings.append(
                    f"Integrity warning: Chunk {chunk.get('chunk_id')} in user_details context has source '{chunk.get('source')}'."
                )

        # Generate formatted LLM prompt context
        prompt_context = format_llm_prompt_context(context)

        return GuardrailResult(
            allowed=True,
            warnings=warnings,
            context=context,
            prompt_context=prompt_context,
        )


def validate_context(context: StructuredContext) -> GuardrailResult:
    """
    Convenience function to run guardrail validation on structured context.
    """
    return ContextGuardrail.validate(context)
