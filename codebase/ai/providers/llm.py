from __future__ import annotations

import os
import requests
from pathlib import Path
from typing import Any, Protocol

class LLMResponse:
    def __init__(self, text: str, usage: dict[str, Any] | None = None):
        self.text = text
        self.usage = usage

class LLMProvider(Protocol):
    def generate(self, prompt: str) -> str | LLMResponse:
        ...

# ==========================================
# Dynamic SDK Imports & Checks
# ==========================================

try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False


# ==========================================
# 1. OpenRouter Provider (REST API)
# ==========================================
class OpenRouterLLMProvider:
    def __init__(self, api_key: str, model: str = "google/gemini-2.5-flash"):
        self.api_key = api_key
        self.model = model

    def generate(self, prompt: str) -> str | LLMResponse:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0
        }
        res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=30)
        res.raise_for_status()
        data = res.json()
        text = data["choices"][0]["message"]["content"]
        usage = data.get("usage")
        return LLMResponse(text=text, usage=usage)


# ==========================================
# 2. OpenAI Provider (SDK or REST Fallback)
# ==========================================
class OpenAILLMProvider:
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model = model
        if HAS_OPENAI:
            self.client = openai.OpenAI(api_key=api_key)
        else:
            self.client = None

    def generate(self, prompt: str) -> str | LLMResponse:
        if self.client:
            res = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0
            )
            text = res.choices[0].message.content
            usage = {
                "prompt_tokens": res.usage.prompt_tokens,
                "completion_tokens": res.usage.completion_tokens,
                "total_tokens": res.usage.total_tokens
            } if res.usage else None
            return LLMResponse(text=text, usage=usage)
        else:
            # Fallback to direct HTTP Request
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.0
            }
            res = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=30)
            res.raise_for_status()
            data = res.json()
            text = data["choices"][0]["message"]["content"]
            usage = data.get("usage")
            return LLMResponse(text=text, usage=usage)


# ==========================================
# 3. Anthropic Provider (SDK or REST Fallback)
# ==========================================
class AnthropicLLMProvider:
    def __init__(self, api_key: str, model: str = "claude-3-5-haiku-20241022"):
        self.api_key = api_key
        self.model = model
        if HAS_ANTHROPIC:
            self.client = anthropic.Anthropic(api_key=api_key)
        else:
            self.client = None

    def generate(self, prompt: str) -> str | LLMResponse:
        if self.client:
            res = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0
            )
            text = res.content[0].text
            usage = {
                "prompt_tokens": res.usage.input_tokens,
                "completion_tokens": res.usage.output_tokens,
                "total_tokens": res.usage.input_tokens + res.usage.output_tokens
            } if res.usage else None
            return LLMResponse(text=text, usage=usage)
        else:
            # Fallback to direct HTTP Request
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json"
            }
            payload = {
                "model": self.model,
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.0
            }
            res = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload, timeout=30)
            res.raise_for_status()
            data = res.json()
            text = data["content"][0]["text"]
            usage = data.get("usage")
            return LLMResponse(text=text, usage=usage)


# ==========================================
# 4. Gemini Provider (SDK or REST Fallback)
# ==========================================
class GeminiLLMProvider:
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        self.api_key = api_key
        self.model = model
        if HAS_GEMINI:
            genai.configure(api_key=api_key)
            self.client = genai.GenerativeModel(model)
        else:
            self.client = None

    def generate(self, prompt: str) -> str | LLMResponse:
        if self.client:
            res = self.client.generate_content(
                prompt,
                generation_config={"temperature": 0.0}
            )
            text = res.text
            return LLMResponse(text=text)
        else:
            # Fallback to direct HTTP Request
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
            headers = {
                "Content-Type": "application/json"
            }
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.0
                }
            }
            res = requests.post(url, headers=headers, json=payload, timeout=30)
            res.raise_for_status()
            data = res.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            
            usage_metadata = data.get("usageMetadata", {})
            usage = {
                "prompt_tokens": usage_metadata.get("promptTokenCount"),
                "completion_tokens": usage_metadata.get("candidatesTokenCount"),
                "total_tokens": usage_metadata.get("totalTokenCount")
            } if usage_metadata else None
            return LLMResponse(text=text, usage=usage)


# ==========================================
# Helper to Load `.env` File Manually
# ==========================================
def load_env():
    # Candidates for .env locations
    env_candidates = [
        Path(".env"),
        Path(__file__).resolve().parents[1] / ".env",
        Path(__file__).resolve().parents[2] / ".env",
    ]
    for env_path in env_candidates:
        if env_path.exists():
            try:
                for line in env_path.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip("'\"")
                        if k and v:
                            os.environ[k] = v
                break
            except Exception:
                pass


# ==========================================
# Provider Resolver
# ==========================================
def get_llm_provider() -> tuple[LLMProvider | None, str]:
    load_env()
    
    # Priority order: OpenRouter -> OpenAI -> Anthropic -> Gemini
    if os.environ.get("OPENROUTER_API_KEY"):
        return OpenRouterLLMProvider(os.environ["OPENROUTER_API_KEY"]), "OpenRouter"
        
    if os.environ.get("OPENAI_API_KEY"):
        return OpenAILLMProvider(os.environ["OPENAI_API_KEY"]), "OpenAI"
        
    if os.environ.get("ANTHROPIC_API_KEY"):
        return AnthropicLLMProvider(os.environ["ANTHROPIC_API_KEY"]), "Anthropic"
        
    if os.environ.get("GEMINI_API_KEY"):
        return GeminiLLMProvider(os.environ["GEMINI_API_KEY"]), "Gemini"
        
    return None, "Mock"
