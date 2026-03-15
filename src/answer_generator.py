"""AnswerGenerator: calls the LLM API to produce a grounded natural language answer."""
from __future__ import annotations

import os
import time

from src.models import Prompt

_MAX_RETRIES = 3
_BACKOFF_BASE = 1.0  # seconds


def _mock_answer(query: str, verse_context: str) -> str:
    return (
        "The Bhagavad Gita has something really practical to say about this. "
        "The core idea is simple: do what you need to do with full sincerity, "
        "but don't tie your peace of mind to whether things turn out the way you hoped. "
        "Your job is to show up and give your best — the results are not entirely in your hands.\n\n"
        "BG 2.47 — This verse is directly relevant to your question. "
        "Krishna is telling Arjuna (and through him, all of us) that we have the right to act, "
        "but we shouldn't obsess over the outcome. "
        "In the context of what you're asking, this means: take the action that feels right and responsible, "
        "without letting fear of failure or desire for a specific result paralyze you.\n\n"
        "BG 6.5 — This one goes a step further. It says you are your own best friend or your own worst enemy, "
        "depending on how you treat yourself. "
        "Applied to your situation, it's a reminder that the way you think about this matters. "
        "Approach it with self-respect and clarity, not self-doubt or anxiety.\n\n"
        "[Note: This is a mock response. Set LLM_MODEL=gemini-1.5-flash in .env for real AI answers.]"
    )


class AnswerGenerator:
    def __init__(
        self,
        model: str = "gpt-4o",
        api_key: str | None = None,
        base_url: str | None = None,
        max_retries: int = _MAX_RETRIES,
    ) -> None:
        self._model = model
        self._max_retries = max_retries
        self._mock = model == "mock"
        self._is_gemini = model.startswith("gemini")
        self._is_groq = model.startswith("groq/")

        if self._mock:
            return

        if self._is_gemini:
            from google import genai
            key = api_key or os.environ.get("GEMINI_API_KEY")
            if not key:
                raise EnvironmentError("GEMINI_API_KEY environment variable is not set.")
            self._gemini_client = genai.Client(api_key=key)
            self._gemini_model_name = model
        elif self._is_groq:
            from openai import OpenAI
            key = api_key or os.environ.get("GROQ_API_KEY")
            if not key:
                raise EnvironmentError("GROQ_API_KEY environment variable is not set.")
            self._client = OpenAI(api_key=key, base_url="https://api.groq.com/openai/v1")
            self._model = model[len("groq/"):]  # strip prefix for API call
        else:
            from openai import OpenAI
            key = api_key or os.environ.get("OPENAI_API_KEY")
            if not key:
                raise EnvironmentError("OPENAI_API_KEY environment variable is not set.")
            self._client = OpenAI(api_key=key, base_url=base_url)

    def generate(self, prompt: Prompt) -> str:
        if self._mock:
            return _mock_answer(prompt.userQuery, prompt.verseContext)

        if self._is_gemini:
            return self._generate_gemini(prompt)
        return self._generate_openai(prompt)
    def _generate_gemini(self, prompt: Prompt) -> str:
        full_prompt = (
            f"{prompt.systemInstruction}\n\n"
            f"CONTEXT (Bhagavad Gita Verses):\n{prompt.verseContext}\n\n"
            f"USER QUESTION: {prompt.userQuery}"
        )
        last_exc: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                from google import genai
                response = self._gemini_client.models.generate_content(
                    model=self._gemini_model_name,
                    contents=full_prompt,
                    config={"temperature": 0.85},
                )
                answer = response.text.strip()
                if not answer:
                    raise ValueError("Gemini returned an empty response")
                return answer
            except Exception as exc:
                last_exc = exc
                if attempt < self._max_retries - 1:
                    time.sleep(_BACKOFF_BASE * (2 ** attempt))
        raise RuntimeError(
            f"Answer generation failed after {self._max_retries} attempts: {last_exc}"
        ) from last_exc

    def _generate_openai(self, prompt: Prompt) -> str:
        from openai import APIStatusError, APITimeoutError, APIConnectionError
        last_exc: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                response = self._client.chat.completions.create(
                    model=self._model,
                    messages=[
                        {"role": "system", "content": prompt.systemInstruction},
                        {
                            "role": "user",
                            "content": (
                                f"CONTEXT (Bhagavad Gita Verses):\n{prompt.verseContext}\n\n"
                                f"USER QUESTION: {prompt.userQuery}"
                            ),
                        },
                    ],
                    temperature=0.85,
                )
                answer = response.choices[0].message.content or ""
                if not answer.strip():
                    raise ValueError("LLM returned an empty response")
                return answer
            except (APIStatusError, APITimeoutError, APIConnectionError) as exc:
                last_exc = exc
                if attempt < self._max_retries - 1:
                    time.sleep(_BACKOFF_BASE * (2 ** attempt))
            except Exception as exc:
                raise RuntimeError(f"Answer generation failed: {exc}") from exc
        raise RuntimeError(
            f"Answer generation failed after {self._max_retries} attempts: {last_exc}"
        ) from last_exc

    def is_reachable(self) -> bool:
        if self._mock:
            return True
        try:
            if self._is_gemini:
                return self._gemini_client is not None
            self._client.models.list()
            return True
        except Exception:
            return False
