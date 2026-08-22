import re
from typing import Dict, List, Optional, Tuple

# Predefined patterns mapped to canonical section names
# Ordered intentionally (more specific patterns first, e.g. "Required Skills" before "Skills")
SECTION_PATTERNS: List[Tuple[str, re.Pattern]] = [
    # --- Job Description Sections ---
    (
        "About the Role",
        re.compile(
            r"^(about\s+(the\s+)?(role|job|position|company|us)|role\s+overview|position\s+summary|job\s+summary|job\s+overview|who\s+we\s+are)$",
            re.IGNORECASE,
        ),
    ),
    (
        "Responsibilities",
        re.compile(
            r"^(responsibilities|key\s+responsibilities|duties|job\s+responsibilities|core\s+responsibilities|what\s+you('ll|\s+will)\s+do|roles?\s*(&|and)\s*responsibilities)$",
            re.IGNORECASE,
        ),
    ),
    (
        "Required Skills",
        re.compile(
            r"^(required\s+skills|mandatory\s+skills|core\s+skills|essential\s+skills)$",
            re.IGNORECASE,
        ),
    ),
    (
        "Preferred Skills",
        re.compile(
            r"^(preferred\s+skills|nice\s+to\s+have(s)?|preferred\s+qualifications|desired\s+skills|bonus\s+points?|plus)$",
            re.IGNORECASE,
        ),
    ),
    (
        "Requirements",
        re.compile(
            r"^(requirements|job\s+requirements|minimum\s+requirements|must\s+haves?|what\s+(we('re|\s+are)\s+looking\s+for|you\s+need))$",
            re.IGNORECASE,
        ),
    ),
    (
        "Qualifications",
        re.compile(
            r"^(qualifications|basic\s+qualifications|minimum\s+qualifications|eligibility(\s+criteria)?)$",
            re.IGNORECASE,
        ),
    ),
    # --- Resume Sections ---
    (
        "Summary",
        re.compile(
            r"^(summary(\s*(/|&|and)?\s*profile)?|profile|professional\s+summary|executive\s+summary|personal\s+profile|career\s+summary|about\s+me|career\s+objective|objective)$",
            re.IGNORECASE,
        ),
    ),
    (
        "Skills",
        re.compile(
            r"^(skills(\s*(&|and)\s*technologies)?|technical\s+skills|core\s+competencies|key\s+skills|technologies|tools(\s*(&|and)\s*technologies)?|skill\s*set)$",
            re.IGNORECASE,
        ),
    ),
    (
        "Experience",
        re.compile(
            r"^(experience|work\s+experience|professional\s+experience|employment\s+history|work\s+history|career\s+history)$",
            re.IGNORECASE,
        ),
    ),
    (
        "Education",
        re.compile(
            r"^(education(al)?(\s+(background|qualifications|details))?|academic(\s+(background|qualifications|record))?|academics|degrees?)$",
            re.IGNORECASE,
        ),
    ),
    (
        "Projects",
        re.compile(
            r"^(projects|key\s+projects|personal\s+projects|academic\s+projects|technical\s+projects)$",
            re.IGNORECASE,
        ),
    ),
    (
        "Certifications",
        re.compile(
            r"^(certifications?|certificates?|licenses?(\s*(&|and)\s*certifications?)?|professional\s+certifications|courses?(\s*(&|and)\s*certifications?))$",
            re.IGNORECASE,
        ),
    ),
    (
        "Achievements",
        re.compile(
            r"^(achievements?|honors?(\s*(&|and)\s*awards?)?|awards?(\s*(&|and)\s*achievements?)?|key\s+accomplishments|accomplishments)$",
            re.IGNORECASE,
        ),
    ),
]


def _match_section_header(line: str) -> Optional[str]:
    """
    Check if a line matches a known section header deterministically.
    """
    clean_line = line.strip()

    # Reject lines that are too long to be a section header
    if not clean_line or len(clean_line) > 60:
        return None

    # Strip markdown headers, numbering, bullets, colons, dashes, and formatting symbols
    normalized = re.sub(r"^([#*_\-–—•\d\.\)\s]+)", "", clean_line)
    normalized = re.sub(r"[:*_\s]+$", "", normalized).strip()

    if not normalized or len(normalized) > 50:
        return None

    # Check against compiled patterns
    for section_name, pattern in SECTION_PATTERNS:
        if pattern.match(normalized):
            return section_name

    return None


def detect_sections(text: str) -> Dict[str, str]:
    """
    Segment cleaned document text into structured sections.

    - Detects standard resume and job description section headers.
    - Preserves unclassified initial text under 'General' (e.g. contact info/header).
    - If no sections are detected, preserves the entire text under 'General'.
    - Returns a mapping of {section_title: section_content}.
    """
    if not text or not text.strip():
        return {}

    lines = text.split("\n")
    sections: Dict[str, List[str]] = {}
    current_section = "General"
    sections[current_section] = []

    for line in lines:
        detected_header = _match_section_header(line)

        if detected_header:
            current_section = detected_header
            if current_section not in sections:
                sections[current_section] = []
        else:
            sections[current_section].append(line)

    # Clean and format output dictionary, discarding empty sections
    result: Dict[str, str] = {}
    for section_name, section_lines in sections.items():
        content = "\n".join(section_lines).strip()
        if content:
            result[section_name] = content

    # If all text was stripped or somehow empty, preserve full text
    if not result and text.strip():
        result["General"] = text.strip()

    return result
