import re
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Dict, List


class Intent(str, Enum):
    SKILL_GAP = "SKILL_GAP"
    JD_EXPLANATION = "JD_EXPLANATION"
    PREPARATION = "PREPARATION"
    INTERVIEW_PREPARATION = "INTERVIEW_PREPARATION"
    PROJECT_GUIDANCE = "PROJECT_GUIDANCE"
    RESUME_JD_MATCH = "RESUME_JD_MATCH"
    GENERAL_JOB_QUESTION = "GENERAL_JOB_QUESTION"


INTENT_RETRIEVAL_STRATEGIES: Dict[Intent, List[str]] = {
    Intent.SKILL_GAP: ["job_description", "resume"],
    Intent.JD_EXPLANATION: ["job_description"],
    Intent.PREPARATION: ["job_description", "resume", "user_details"],
    Intent.INTERVIEW_PREPARATION: ["job_description", "resume"],
    Intent.PROJECT_GUIDANCE: ["resume", "job_description"],
    Intent.RESUME_JD_MATCH: ["resume", "job_description"],
    Intent.GENERAL_JOB_QUESTION: ["resume", "job_description", "user_details"],
}


@dataclass
class QueryUnderstandingResult:
    """
    Result containing identified query intent and prioritization strategy.
    """
    intent: str
    retrieval_strategy: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# Deterministic pattern rules evaluated in priority order
INTENT_RULES = [
    # 1. Project Guidance (projects, portfolio, specific project discussions)
    (
        Intent.PROJECT_GUIDANCE,
        re.compile(
            r"\b(projects?|portfolio|highlight\b.*\bproject|explain\b.*\bproject|showcase\b.*\bproject|agri\s+notifier)\b",
            re.IGNORECASE,
        ),
    ),
    # 2. Resume-JD Match (matching, score, compatibility, fit, comparison)
    (
        Intent.RESUME_JD_MATCH,
        re.compile(
            r"\b(match(ing)?|fit\s+for(\s+this)?|fit\s+the|compare|comparison|compatibility|aligned\s+with|chances\s+of\s+getting|suitability)\b",
            re.IGNORECASE,
        ),
    ),
    # 3. Skill Gap (missing skills, skill requirements, gaps, lacking qualifications, skills to improve)
    (
        Intent.SKILL_GAP,
        re.compile(
            r"\b(missing(\s+skills?)?|skills?\s+(am\s+i\s+missing|do\s+i\s+lack|gap|gaps|do\s+i\s+need\s+to\s+improve)|lack(ing)?|skills?\s+required|do\s+i\s+have\s+the\s+skills|what\s+skills?\b.*\b(need|missing|lack|improve)|improve\b.*\bskills?)\b",
            re.IGNORECASE,
        ),
    ),
    # 4. JD Explanation (explaining requirements, responsibilities, terminology, or meaning in JD)
    (
        Intent.JD_EXPLANATION,
        re.compile(
            r"\b(what\s+does\b.*\bmean|mean\s+in\s+this|explain\b.*\b(job\s+description|jd|responsibilit|requirement|role|duty|section)|what\s+is\s+meant\s+by|clarify\b.*\b(requirement|responsibility))\b",
            re.IGNORECASE,
        ),
    ),
    # 5. Interview Preparation (interview questions, mock prep, questions recruiters/interviewers ask)
    (
        Intent.INTERVIEW_PREPARATION,
        re.compile(
            r"\b(interview(\s+questions?)?|questions?\s+(they\s+can|they\s+might|to\s+ask|can\s+they\s+ask)|mock\s+interview|behavioral\s+questions?|technical\s+questions?)\b",
            re.IGNORECASE,
        ),
    ),
    # 6. Preparation (how to prepare, study roadmap, what to learn, getting ready)
    (
        Intent.PREPARATION,
        re.compile(
            r"\b(prepare|preparation|study|learn|get\s+ready|how\s+should\s+i\s+prepare|roadmap|what\s+to\s+study|what\s+should\s+i\s+study)\b",
            re.IGNORECASE,
        ),
    ),
]


def understand_query(question: str) -> QueryUnderstandingResult:
    """
    Deterministically classify user query into an Intent and determine the appropriate
    retrieval source prioritization strategy without calling an LLM.

    Args:
        question: User query string.

    Returns:
        QueryUnderstandingResult with intent and prioritized retrieval_strategy.
    """
    if not question or not question.strip():
        fallback_intent = Intent.GENERAL_JOB_QUESTION
        return QueryUnderstandingResult(
            intent=fallback_intent.value,
            retrieval_strategy=INTENT_RETRIEVAL_STRATEGIES[fallback_intent],
        )

    clean_question = question.strip()

    # Rule evaluation in priority order
    for intent, pattern in INTENT_RULES:
        if pattern.search(clean_question):
            return QueryUnderstandingResult(
                intent=intent.value,
                retrieval_strategy=INTENT_RETRIEVAL_STRATEGIES[intent],
            )

    # Default fallback
    default_intent = Intent.GENERAL_JOB_QUESTION
    return QueryUnderstandingResult(
        intent=default_intent.value,
        retrieval_strategy=INTENT_RETRIEVAL_STRATEGIES[default_intent],
    )
