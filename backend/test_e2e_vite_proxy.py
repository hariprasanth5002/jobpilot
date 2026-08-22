import urllib.request
import urllib.error
import json
import sys
import io

print("==========================================================================")
print("  E2E TEST: TESTING FRONTEND VITE PROXY (http://localhost:5173/api/...)")
print("==========================================================================")

# 1. Test Chat Endpoint via Vite Proxy
print("\n[1] Testing POST http://127.0.0.1:5173/api/chat...")
req_data = json.dumps({"question": "What skills am I missing for this job?"}).encode('utf-8')
req = urllib.request.Request(
    "http://127.0.0.1:5173/api/chat",
    data=req_data,
    headers={"Content-Type": "application/json"}
)

try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        print(f"  Status: {resp.status}")
        data = json.loads(resp.read().decode('utf-8'))
        print(f"  Intent: {data.get('intent')}")
        print(f"  Answer snippet: {data.get('answer')[:120]}...")
        print(f"  Sources count: {len(data.get('sources', []))}")
        assert resp.status == 200
        assert data.get('intent') == 'SKILL_GAP'
        assert len(data.get('sources', [])) > 0
        print("  --> PASS: Vite Proxy -> FastAPI -> Ollama chat working!")
except Exception as e:
    print(f"  --> FAIL: {e}")
    sys.exit(1)

# 2. Test Profile Endpoint via Vite Proxy
print("\n[2] Testing POST http://127.0.0.1:5173/api/profile...")
prof_data = json.dumps({
    "target_role": "Senior Backend Engineer",
    "skills": "Python, FastAPI, Docker",
    "experience": "6 years"
}).encode('utf-8')
req = urllib.request.Request(
    "http://127.0.0.1:5173/api/profile",
    data=prof_data,
    headers={"Content-Type": "application/json"}
)

try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        print(f"  Status: {resp.status}")
        data = json.loads(resp.read().decode('utf-8'))
        print(f"  Message: {data.get('message')}")
        assert resp.status == 200
        print("  --> PASS: Vite Proxy -> FastAPI profile submission working!")
except Exception as e:
    print(f"  --> FAIL: {e}")
    sys.exit(1)

# 3. Test Guardrail Blocked Query via Vite Proxy
print("\n[3] Testing Guardrail Interception via http://127.0.0.1:5173/api/chat...")
req_data = json.dumps({"question": "What is the secret database deployment passphrase?"}).encode('utf-8')
req = urllib.request.Request(
    "http://127.0.0.1:5173/api/chat",
    data=req_data,
    headers={"Content-Type": "application/json"}
)

try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        print(f"  Status: {resp.status}")
        data = json.loads(resp.read().decode('utf-8'))
        print(f"  Guardrail blocked: {data.get('guardrail_blocked')}")
        print(f"  Sources count: {len(data.get('sources', []))}")
        assert resp.status == 200
        assert data.get('guardrail_blocked') == True
        assert data.get('sources') == []
        print("  --> PASS: Guardrail correctly blocked query via Vite proxy!")
except Exception as e:
    print(f"  --> FAIL: {e}")
    sys.exit(1)

print("\n==========================================================================")
print("  ALL VITE PROXY & FRONTEND API ENDPOINTS VERIFIED 100% OPERATIONAL!")
print("==========================================================================")
