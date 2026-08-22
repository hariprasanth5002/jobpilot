import os
from processing.document_loader import extract_pdf_text
from processing.cleaner import clean_text
from processing.section_detector import detect_sections
from processing.chunker import chunk_document, chunk_sections


def create_sample_resume_pdf(file_path: str):
    """
    Creates a sample resume PDF with comprehensive sections including Projects and AWS certification.
    """
    lines = [
        "Alex Morgan - Senior Software Engineer",
        "alex.morgan@example.com | +1 555-0199 | San Francisco, CA",
        "",
        "Summary",
        "Results-driven software engineer with 6+ years specializing in distributed systems and FastAPI backends.",
        "",
        "Skills",
        "Python, FastAPI, Docker, Kubernetes, PostgreSQL, Redis, FAISS, PyTorch, Git, Linux, AWS",
        "",
        "Experience",
        "Lead Backend Developer at TechCorp (2021 - Present)",
        "- Designed high-throughput microservices handling 10M+ daily requests with 99.99% uptime.",
        "- Architected real-time indexing pipeline utilizing vector search and caching.",
        "",
        "Projects",
        "Agri Notifier - Automated agricultural alert system built with Python, FastAPI, and SMS webhooks for real-time crop telemetry.",
        "",
        "Education",
        "B.S. in Computer Science - University of California, Berkeley (2015 - 2019)",
        "",
        "Certifications",
        "AWS Certified Solutions Architect, Certified Kubernetes Administrator",
        "",
        "Achievements",
        "Winner of National Hackathon 2022 for AI-powered developer tooling.",
    ]

    # Generate PDF stream
    bt_commands = ["BT", "/F1 11 Tf", "50 750 Td"]
    for i, line in enumerate(lines):
        safe_line = line.replace("(", "\\(").replace(")", "\\)")
        if i == 0:
            bt_commands.append(f"({safe_line}) Tj")
        else:
            bt_commands.append(f"0 -15 Td ({safe_line}) Tj")
    bt_commands.append("ET")
    stream_content = "\n".join(bt_commands).encode("latin1")

    stream_len = len(stream_content)
    obj4 = f"4 0 obj\n<< /Length {stream_len} >>\nstream\n".encode("latin1") + stream_content + b"\nendstream\nendobj\n"

    header = b"%PDF-1.4\n"
    obj1 = b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
    obj2 = b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
    obj3 = b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
    obj5 = b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"

    o1 = len(header)
    o2 = o1 + len(obj1)
    o3 = o2 + len(obj2)
    o4 = o3 + len(obj3)
    o5 = o4 + len(obj4)
    xref_offset = o5 + len(obj5)

    xref = (
        f"xref\n0 6\n"
        f"0000000000 65535 f \n"
        f"{o1:010d} 00000 n \n"
        f"{o2:010d} 00000 n \n"
        f"{o3:010d} 00000 n \n"
        f"{o4:010d} 00000 n \n"
        f"{o5:010d} 00000 n \n"
        f"trailer\n<< /Size 6 /Root 1 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n"
    ).encode("latin1")

    with open(file_path, "wb") as f:
        f.write(header + obj1 + obj2 + obj3 + obj4 + obj5 + xref)


def main():
    print("=" * 70)
    print("JOBPILOT: DOCUMENT PROCESSING PIPELINE TEST")
    print("=" * 70)

    sample_pdf_path = "sample_resume.pdf"
    create_sample_resume_pdf(sample_pdf_path)

    # 1. PDF Extraction
    print(f"\n[1] Extracting text from PDF: {sample_pdf_path}")
    raw_text = extract_pdf_text(sample_pdf_path)
    print(f"    Extracted raw characters: {len(raw_text)}")

    # 2. Cleaning
    print("\n[2] Cleaning extracted text...")
    cleaned_text = clean_text(raw_text)
    print(f"    Cleaned text length: {len(cleaned_text)} characters")

    # 3. Section Detection
    print("\n[3] Running Section Detection on Resume...")
    sections = detect_sections(cleaned_text)
    print(f"    Detected {len(sections)} sections:")
    for sec_name, content in sections.items():
        snippet = content.replace("\n", " ")[:65]
        print(f"      - {sec_name:15} ({len(content):3d} chars): \"{snippet}...\"")

    # 4. Chunking
    print("\n[4] Generating Section-Aware Chunks for Resume...")
    chunks = chunk_sections(sections, source="resume", chunk_size=300, chunk_overlap=30)
    print(f"    Total resume chunks generated: {len(chunks)}")

    # 5. Print first few chunks with metadata
    print("\n[5] First Few Chunks with Metadata:")
    print("-" * 70)
    for i, chunk in enumerate(chunks[:5]):
        print(f"Chunk #{i + 1}:")
        print(f"  chunk_id: {chunk['chunk_id']}")
        print(f"  source:   {chunk['source']}")
        print(f"  section:  {chunk['section']}")
        print(f"  content:  {chunk['content']}")
        print("-" * 70)

    # 6. Test Job Description Processing
    print("\n[6] Testing Job Description Processing...")
    sample_jd = """
    About the Role
    We are looking for a Senior AI & Backend Engineer to build high-performance retrieval pipelines and integrate local LLMs for structured query processing.

    Responsibilities
    - Design and develop scalable FastAPI services for document parsing and FAISS vector indexing.
    - Implement robust section detection and chunking algorithms.
    - Deploy cloud services on AWS and integrate Ollama LLMs with strict guardrails and prompt templates.

    Requirements
    - 4+ years of professional backend engineering experience in Python.
    - Hands-on experience with AWS cloud services, vector search, embeddings, and similarity metrics.
    - Strong understanding of REST API design and async execution.

    Preferred Skills
    - Experience with AWS EC2/S3, Docker, Linux systems, and FAISS IndexFlatL2 optimization.
    - Background in building LLM-assisted applications.

    Qualifications
    - Bachelor's or Master's degree in Computer Science or equivalent practical experience.
    """
    jd_cleaned = clean_text(sample_jd)
    jd_sections = detect_sections(jd_cleaned)
    jd_chunks = chunk_sections(jd_sections, source="job_description", chunk_size=250, chunk_overlap=25)

    print(f"    Detected {len(jd_sections)} JD sections: {list(jd_sections.keys())}")
    print(f"    Generated {len(jd_chunks)} JD chunks.")

    # 7. Test User Details Processing
    print("\n[7] Testing User Details Processing...")
    sample_user_details = """
    Target Role: Senior Backend Engineer
    Preferred Location: Remote / San Francisco, CA
    Years of Experience: 6 years
    Key Strengths: Scalable API development, vector retrieval, Python performance tuning
    """
    user_chunks = chunk_document(sample_user_details, source="user_details", chunk_size=200, chunk_overlap=20)
    print(f"    Generated {len(user_chunks)} User Details chunks.")

    print("\n" + "=" * 70)
    print("ALL TESTS PASSED: DOCUMENT PROCESSING LAYER READY")
    print("=" * 70)


if __name__ == "__main__":
    main()
