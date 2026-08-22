"""
JobPilot API Test Suite
========================
Tests the FastAPI layer using TestClient (no live server needed).
All existing RAG infrastructure (FAISS index, chunks.json) must be present.

Run from backend/:
    venv\\Scripts\\python.exe test_api.py
"""

import io
import json
import os
import sys
from pathlib import Path

# Ensure imports resolve from backend/
BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app, raise_server_exceptions=False)

# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

SEPARATOR = "-" * 75
WIDE_SEP  = "=" * 75

passed = 0
failed = 0


def _header(title: str) -> None:
    print(f"\n{WIDE_SEP}")
    print(f"  {title}")
    print(WIDE_SEP)


def _result(label: str, ok: bool, detail: str = "") -> None:
    global passed, failed
    status_str = "PASS" if ok else "FAIL"
    print(f"  [{status_str}] {label}")
    if detail:
        print(f"         {detail}")
    if ok:
        passed += 1
    else:
        failed += 1


def _check(label: str, condition: bool, detail: str = "") -> bool:
    _result(label, condition, detail)
    return condition


# ---------------------------------------------------------------------------
# TEST 1 – SKILL_GAP intent
# ---------------------------------------------------------------------------
_header("TEST 1 | POST /api/chat | SKILL_GAP")
print("  Question: 'What skills am I missing for this job?'")

resp = client.post("/api/chat", json={"question": "What skills am I missing for this job?"})
print(f"  HTTP Status: {resp.status_code}")

if resp.status_code == 200:
    body = resp.json()
    print(f"  Intent:  {body.get('intent')}")
    print(f"  Sources: {len(body.get('sources', []))} chunks")
    print(f"  Guardrail blocked: {body.get('guardrail_blocked')}")
    print(f"  Answer snippet: {str(body.get('answer', ''))[:200]}")

    _check("HTTP 200 OK", resp.status_code == 200)
    _check("intent == SKILL_GAP", body.get("intent") == "SKILL_GAP",
           f"got: {body.get('intent')}")
    _check("answer non-empty", bool(body.get("answer", "").strip()),
           "answer is empty")
    _check("sources list returned", isinstance(body.get("sources"), list) and len(body["sources"]) > 0,
           f"sources: {body.get('sources')}")
    _check("guardrail_blocked == False", body.get("guardrail_blocked") is False,
           f"guardrail_blocked={body.get('guardrail_blocked')}")
else:
    print(f"  Response body: {resp.text[:400]}")
    _check("HTTP 200 OK", False, f"got HTTP {resp.status_code}")
    _check("intent == SKILL_GAP", False, "request failed")
    _check("answer non-empty", False, "request failed")
    _check("sources list returned", False, "request failed")
    _check("guardrail_blocked == False", False, "request failed")

# ---------------------------------------------------------------------------
# TEST 2 – PROJECT_GUIDANCE intent
# ---------------------------------------------------------------------------
_header("TEST 2 | POST /api/chat | PROJECT_GUIDANCE")
print("  Question: 'How should I explain my Agri Notifier project?'")

resp = client.post("/api/chat", json={"question": "How should I explain my Agri Notifier project?"})
print(f"  HTTP Status: {resp.status_code}")

if resp.status_code == 200:
    body = resp.json()
    print(f"  Intent:  {body.get('intent')}")
    print(f"  Sources: {len(body.get('sources', []))} chunks")
    sources_text = [s.get("source") for s in body.get("sources", [])]
    print(f"  Source types: {sources_text}")
    print(f"  Answer snippet: {str(body.get('answer', ''))[:200]}")

    _check("HTTP 200 OK", resp.status_code == 200)
    _check("intent == PROJECT_GUIDANCE", body.get("intent") == "PROJECT_GUIDANCE",
           f"got: {body.get('intent')}")
    _check("answer non-empty", bool(body.get("answer", "").strip()))
    _check("resume source in results", "resume" in sources_text,
           f"sources: {sources_text}")
else:
    print(f"  Response body: {resp.text[:400]}")
    _check("HTTP 200 OK", False, f"got HTTP {resp.status_code}")
    _check("intent == PROJECT_GUIDANCE", False, "request failed")
    _check("answer non-empty", False, "request failed")
    _check("resume source in results", False, "request failed")

# ---------------------------------------------------------------------------
# TEST 3 – JD_EXPLANATION intent
# ---------------------------------------------------------------------------
_header("TEST 3 | POST /api/chat | JD_EXPLANATION")
print("  Question: 'What does AWS experience mean in this job description?'")

resp = client.post("/api/chat", json={"question": "What does AWS experience mean in this job description?"})
print(f"  HTTP Status: {resp.status_code}")

if resp.status_code == 200:
    body = resp.json()
    print(f"  Intent:  {body.get('intent')}")
    print(f"  Sources: {len(body.get('sources', []))} chunks")
    sources_text = [s.get("source") for s in body.get("sources", [])]
    print(f"  Source types: {sources_text}")
    print(f"  Answer snippet: {str(body.get('answer', ''))[:200]}")

    _check("HTTP 200 OK", resp.status_code == 200)
    _check("intent == JD_EXPLANATION", body.get("intent") == "JD_EXPLANATION",
           f"got: {body.get('intent')}")
    _check("answer non-empty", bool(body.get("answer", "").strip()))
    _check("job_description source in results", "job_description" in sources_text,
           f"sources: {sources_text}")
else:
    print(f"  Response body: {resp.text[:400]}")
    _check("HTTP 200 OK", False, f"got HTTP {resp.status_code}")
    _check("intent == JD_EXPLANATION", False, "request failed")
    _check("answer non-empty", False, "request failed")
    _check("job_description source in results", False, "request failed")

# ---------------------------------------------------------------------------
# TEST 4 – Guardrail blocks insufficient context query
# ---------------------------------------------------------------------------
_header("TEST 4 | POST /api/chat | Guardrail Interception")
print("  Question: 'What is the secret database deployment passphrase?'")

resp = client.post("/api/chat", json={"question": "What is the secret database deployment passphrase?"})
print(f"  HTTP Status: {resp.status_code}")

if resp.status_code == 200:
    body = resp.json()
    print(f"  Intent:     {body.get('intent')}")
    print(f"  Guardrail:  {body.get('guardrail_blocked')}")
    print(f"  Sources:    {body.get('sources')}")
    print(f"  Answer:     {str(body.get('answer', ''))[:200]}")

    _check("HTTP 200 OK", resp.status_code == 200)
    _check("guardrail_blocked == True", body.get("guardrail_blocked") is True,
           f"guardrail_blocked={body.get('guardrail_blocked')}")
    _check("sources == []", body.get("sources") == [],
           f"sources: {body.get('sources')}")
    _check("safe fallback answer present", bool(body.get("answer", "").strip()),
           "answer is empty")
else:
    print(f"  Response body: {resp.text[:400]}")
    _check("HTTP 200 OK", False, f"got HTTP {resp.status_code}")
    _check("guardrail_blocked == True", False, "request failed")
    _check("sources == []", False, "request failed")
    _check("safe fallback answer present", False, "request failed")

# ---------------------------------------------------------------------------
# TEST 5 – Empty/invalid question
# ---------------------------------------------------------------------------
_header("TEST 5 | POST /api/chat | Empty Question Handling")

for label, payload in [
    ("empty string",         {"question": ""}),
    ("whitespace only",      {"question": "   "}),
    ("missing field",        {}),
]:
    print(f"\n  Sub-test: {label}")
    resp = client.post("/api/chat", json=payload)
    print(f"  HTTP Status: {resp.status_code}")
    print(f"  Body snippet: {resp.text[:200]}")
    _check(
        f"invalid input rejected ({label})",
        resp.status_code in (400, 422),
        f"got HTTP {resp.status_code}",
    )

# ---------------------------------------------------------------------------
# TEST 6 – Document upload (resume PDF)
# ---------------------------------------------------------------------------
_header("TEST 6 | POST /api/documents/resume | PDF Upload")

sample_pdf = BACKEND_DIR / "sample_resume.pdf"
if sample_pdf.exists():
    print(f"  Using sample PDF: {sample_pdf}")
    with open(sample_pdf, "rb") as f:
        pdf_bytes = f.read()

    resp = client.post(
        "/api/documents/resume",
        files={"file": ("sample_resume.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    print(f"  HTTP Status: {resp.status_code}")
    if resp.status_code == 200:
        body = resp.json()
        print(f"  New chunks:   {body.get('new_chunks')}")
        print(f"  Total chunks: {body.get('total_chunks')}")
        print(f"  Vectors indexed: {body.get('vectors_indexed')}")

        _check("HTTP 200 OK", resp.status_code == 200)
        _check("new_chunks > 0", (body.get("new_chunks") or 0) > 0,
               f"new_chunks={body.get('new_chunks')}")
        _check("vectors_indexed > 0", (body.get("vectors_indexed") or 0) > 0)
    else:
        print(f"  Error body: {resp.text[:400]}")
        _check("HTTP 200 OK", False, f"got HTTP {resp.status_code}")
        _check("new_chunks > 0", False, "request failed")
        _check("vectors_indexed > 0", False, "request failed")
else:
    print(f"  [SKIP] sample_resume.pdf not found at {sample_pdf} — skipping document upload test.")

# ---------------------------------------------------------------------------
# TEST 7 – Invalid file type rejection
# ---------------------------------------------------------------------------
_header("TEST 7 | POST /api/documents/resume | Invalid File Type Rejection")

fake_txt = b"This is not a PDF file."
resp = client.post(
    "/api/documents/resume",
    files={"file": ("resume.txt", io.BytesIO(fake_txt), "text/plain")},
)
print(f"  HTTP Status: {resp.status_code}")
print(f"  Body: {resp.text[:300]}")
_check("non-PDF rejected (400 or 415)", resp.status_code in (400, 415),
       f"got HTTP {resp.status_code}")

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
print(f"\n{WIDE_SEP}")
print("  API TEST SUMMARY")
print(WIDE_SEP)
print(f"  Total checks passed : {passed}")
print(f"  Total checks failed : {failed}")
print(f"  Overall result      : {'ALL PASSED' if failed == 0 else f'{failed} FAILED'}")
print(WIDE_SEP)

if failed > 0:
    sys.exit(1)
