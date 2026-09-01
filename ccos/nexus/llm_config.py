"""Load LLM provider settings from NEXUS_HOME/.env and environment."""
from __future__ import annotations
import os
from pathlib import Path
from typing import Any, Dict

def _home() -> Path:
    return Path(os.environ.get("NEXUS_HOME", Path.home() / ".nexus"))

def load_env_file() -> Dict[str, str]:
    path = _home() / ".env"
    out: Dict[str, str] = {}
    if not path.exists():
        return out
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        out[k.strip()] = v.strip().strip('"').strip("'")
        if out[k.strip()] and k.strip() not in os.environ:
            os.environ[k.strip()] = out[k.strip()]
    return out

def get_llm_config() -> Dict[str, Any]:
    load_env_file()
    provider = "none"
    cfg_path = _home() / "config.yaml"
    if cfg_path.exists():
        for line in cfg_path.read_text().splitlines():
            if line.startswith("model_provider:"):
                provider = line.split(":", 1)[1].strip()
    api_key = (
        os.environ.get("OPENAI_API_KEY")
        or os.environ.get("ANTHROPIC_API_KEY")
        or os.environ.get("OPENROUTER_API_KEY")
        or os.environ.get("NEXUS_API_KEY")
    )
    return {
        "provider": provider,
        "api_key_set": bool(api_key),
        "api_key_preview": (api_key[:7] + "\u2026" + api_key[-4:]) if api_key and len(api_key) > 12 else ("set" if api_key else None),
        "base_url": os.environ.get("NEXUS_API_BASE_URL"),
        "model": os.environ.get("NEXUS_MODEL", "default"),
        "database_url_set": bool(os.environ.get("DATABASE_URL")),
        "temporal_host": os.environ.get("TEMPORAL_HOST"),
        "workflow_backend": os.environ.get("WORKFLOW_BACKEND", "sqlite"),
    }
