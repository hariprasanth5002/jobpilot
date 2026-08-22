import json
import os
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

from generation.guardrails import GuardrailResult
from generation.prompts import (
    build_generation_prompt,
    get_system_prompt,
)

DEFAULT_OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
DEFAULT_PREFERRED_MODELS = [
    "gemma3:1b",
    "qwen2.5-coder:7b",
    "mistral:latest",
    "llama3:latest",
    "qwen3-coder:30b",
]


class OllamaClient:
    """
    Direct HTTP client for local Ollama instance without external dependencies.
    """

    def __init__(
        self,
        host: str = DEFAULT_OLLAMA_HOST,
        model: Optional[str] = None,
        timeout: int = 120,
    ) -> None:
        self.host = host.rstrip("/")
        self.timeout = timeout
        self.model = model or os.environ.get("OLLAMA_MODEL") or self._discover_default_model()

    def get_available_models(self) -> List[str]:
        """
        Query Ollama for list of installed models.
        """
        url = f"{self.host}/api/tags"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "JobPilot/1.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return [m.get("name") for m in data.get("models", []) if m.get("name")]
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Ollama at {self.host}: {e}")

    def _discover_default_model(self) -> str:
        """
        Autodetect installed model preferring standard coding/chat models.
        """
        try:
            available = self.get_available_models()
            for pref in DEFAULT_PREFERRED_MODELS:
                if pref in available:
                    return pref
            if available:
                # Return first available model that is not purely an embedding model
                for m in available:
                    if "embed" not in m.lower():
                        return m
                return available[0]
        except Exception:
            pass
        return "llama3:latest"

    def check_health(self) -> Dict[str, Any]:
        """
        Verify Ollama connectivity and active model availability.
        """
        models = self.get_available_models()
        return {
            "status": "online",
            "host": self.host,
            "configured_model": self.model,
            "available_models": models,
            "model_ready": self.model in models,
        }

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
    ) -> str:
        """
        Send generation request to Ollama /api/generate endpoint.
        """
        url = f"{self.host}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system_prompt or get_system_prompt(),
            "stream": False,
            "options": {
                "temperature": temperature,
                "top_p": 0.9,
            },
        }

        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data_bytes,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "JobPilot/1.0",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result.get("response", "").strip()
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Ollama API HTTP {e.code} Error: {err_body}")
        except urllib.error.URLError as e:
            raise ConnectionError(f"Failed to reach Ollama at {self.host}: {e.reason}")


def generate_answer(
    question: str,
    intent: str,
    validated_guardrail_result: GuardrailResult,
    model_name: Optional[str] = None,
    client: Optional[OllamaClient] = None,
) -> Dict[str, Any]:
    """
    Generate structured, guardrailed answer for the user query.
    If guardrails mark context as disallowed/insufficient, Ollama is NOT called.
    """
    # Guardrail Check
    if not validated_guardrail_result.allowed:
        # -------------------------------------------------------------------
        # DEBUG: GUARDRAIL BLOCKED LOGGING
        # -------------------------------------------------------------------
        print()
        print("============================================================")
        print("LLM GENERATION — BLOCKED BY GUARDRAIL")
        print("============================================================")
        print(f"Warnings : {validated_guardrail_result.warnings}")
        print(f"Ollama Call: SKIPPED — insufficient/irrelevant context.")
        print("============================================================")
        print()
        return {
            "allowed": False,
            "intent": intent,
            "question": question,
            "answer": "I do not have sufficient information in the provided resume, job description, or candidate context to answer this question accurately.",
            "warnings": validated_guardrail_result.warnings,
            "model": None,
            "called_llm": False,
        }

    # Initialize client
    ollama_client = client or OllamaClient(model=model_name)

    # Build Prompt
    system_prompt = get_system_prompt()
    user_prompt = build_generation_prompt(
        question=question,
        intent=intent,
        prompt_context=validated_guardrail_result.prompt_context,
    )

    # -------------------------------------------------------------------
    # DEBUG: LLM GENERATION LOGGING
    # -------------------------------------------------------------------
    print()
    print("============================================================")
    print("LLM GENERATION")
    print("============================================================")
    print(f"Model       : {ollama_client.model}")
    print(f"Temperature : 0.1")
    print()
    print("FINAL PROMPT SENT TO OLLAMA")
    print("------------------------------------------------------------")
    print(user_prompt.encode('ascii', errors='replace').decode('ascii'))
    print("------------------------------------------------------------")
    print()
    print("Calling Ollama...")
    print("============================================================")
    print()

    # Call Ollama
    try:
        answer = ollama_client.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.1,
        )
    except Exception as ollama_err:
        print()
        print("============================================================")
        print("OLLAMA ERROR")
        print("============================================================")
        print(str(ollama_err))
        print("============================================================")
        print()
        raise

    # -------------------------------------------------------------------
    # DEBUG: OLLAMA RESPONSE LOGGING
    # -------------------------------------------------------------------
    print()
    print("============================================================")
    print("OLLAMA RESPONSE")
    print("============================================================")
    print(f"Model      : {ollama_client.model}")
    print(f"Generation : SUCCESS")
    print()
    print(answer.encode('ascii', errors='replace').decode('ascii'))
    print()
    print("============================================================")
    print()

    return {
        "allowed": True,
        "intent": intent,
        "question": question,
        "answer": answer,
        "warnings": validated_guardrail_result.warnings,
        "model": ollama_client.model,
        "called_llm": True,
    }
