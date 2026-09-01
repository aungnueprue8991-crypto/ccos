"""Optional real LLM client — uses env from nexus setup / llm_config."""
from __future__ import annotations
import json, os, urllib.error, urllib.request
from typing import Any, Dict, List
from .llm_config import get_llm_config

class LLMClient:
    def __init__(self) -> None:
        self.cfg = get_llm_config()

    @property
    def available(self) -> bool:
        if self.cfg.get("provider") in (None, "none"):
            return False
        if self.cfg.get("provider") == "ollama":
            return True
        return bool(self.cfg.get("api_key_set"))

    def chat(self, messages: List[Dict[str, str]], temperature: float = 0.2) -> Dict[str, Any]:
        if not self.available:
            return {"ok": False, "error": "no_llm_configured", "content": None, "provider": self.cfg.get("provider")}
        base = self.cfg.get("base_url") or "https://api.openai.com/v1"
        model = self.cfg.get("model") or "gpt-4o-mini"
        url = base.rstrip("/") + "/chat/completions"
        body = {"model": model, "messages": messages, "temperature": temperature}
        headers = {"Content-Type": "application/json"}
        key = (
            os.environ.get("OPENAI_API_KEY")
            or os.environ.get("OPENROUTER_API_KEY")
            or os.environ.get("NEXUS_API_KEY")
            or os.environ.get("ANTHROPIC_API_KEY")
        )
        if key and self.cfg.get("provider") != "ollama":
            headers["Authorization"] = f"Bearer {key}"
        if self.cfg.get("provider") == "anthropic" and "api.anthropic.com" in (base or ""):
            return {"ok": False, "error": "use_openai_compatible_proxy_or_openrouter_for_anthropic", "content": None}
        req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            content = data["choices"][0]["message"]["content"]
            return {"ok": True, "content": content, "raw": data, "provider": self.cfg.get("provider")}
        except urllib.error.HTTPError as e:
            err = e.read().decode("utf-8", errors="replace")[:500]
            return {"ok": False, "error": f"http_{e.code}", "detail": err, "content": None}
        except Exception as e:
            return {"ok": False, "error": type(e).__name__, "detail": str(e), "content": None}

    def reason(self, prompt: str, system: str = "You are a careful scientific assistant.") -> Dict[str, Any]:
        return self.chat([{"role": "system", "content": system}, {"role": "user", "content": prompt}])
