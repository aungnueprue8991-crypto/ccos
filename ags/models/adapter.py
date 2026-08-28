"""AGS Model Adapter — pluggable LLM; identity persists across model swaps."""

from __future__ import annotations

import hashlib
import json
import logging
import random
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

log = logging.getLogger("ags.models")

try:
    import requests

    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class BaseModelAdapter(ABC):
    @abstractmethod
    def generate(
        self, prompt: str, system: str = "", max_tokens: int = 512, temperature: float = 0.7
    ) -> str:
        ...

    @abstractmethod
    def structured(
        self, prompt: str, system: str = "", schema_hint: str = ""
    ) -> Dict[str, Any]:
        ...

    def embed(self, text: str) -> List[float]:
        raise NotImplementedError("Embeddings not supported")

    @property
    def model_name(self) -> str:
        return "unknown"


class MockAdapter(BaseModelAdapter):
    @property
    def model_name(self) -> str:
        return "mock/test"

    def generate(
        self, prompt: str, system: str = "", max_tokens: int = 512, temperature: float = 0.7
    ) -> str:
        kw = prompt.lower()
        if "hypothesis" in kw:
            return (
                "I hypothesize that the observed pattern follows a mathematical "
                "relationship between the input variables, specifically quadratic."
            )
        if "experiment" in kw:
            return (
                "I will test by systematically varying one variable, recording outputs, "
                "and checking for the predicted pattern."
            )
        if "question" in kw:
            return "What rule governs the relationship between the observed values?"
        if "learn" in kw or "reflect" in kw:
            return "I have updated my understanding based on the experimental outcome."
        return "I am processing the observations and updating my internal model."

    def structured(self, prompt: str, system: str = "", schema_hint: str = "") -> Dict:
        kw = prompt.lower()
        if "hypothesis" in kw:
            return {
                "statement": "The sequence follows f(n)=n^2+c",
                "confidence": 0.55,
                "prediction": "next value follows the rule",
                "domain": "mathematics",
            }
        if "question" in kw or "gap" in kw:
            return {
                "question": "What mathematical relationship explains the outputs?",
                "urgency": 0.7,
                "domain": "pattern_analysis",
            }
        if "experiment" in kw:
            return {
                "title": "Test quadratic hypothesis",
                "method": "Vary n from 1 to 10, compare to n^2",
                "code": "results=[(n,n*n) for n in range(1,11)]",
                "expected": "Outputs match f(n)=n^2",
            }
        if "learn" in kw:
            return {"learned": "Pattern confirmed", "confidence_delta": 0.15, "skill": None}
        return {"result": "ok", "data": {}}

    def embed(self, text: str) -> List[float]:
        h = int(hashlib.sha256(text.encode()).hexdigest(), 16)
        random.seed(h)
        return [random.uniform(-1, 1) for _ in range(128)]


class ModelRouter:
    def __init__(self, primary: BaseModelAdapter, fallback: Optional[BaseModelAdapter] = None):
        self.primary = primary
        self.fallback = fallback or MockAdapter()
        self._failure_count = 0

    def generate(self, *args, **kwargs) -> str:
        try:
            result = self.primary.generate(*args, **kwargs)
            if result.startswith("[ERROR") or result.startswith("[OLLAMA"):
                raise RuntimeError(result)
            self._failure_count = 0
            return result
        except Exception as e:
            self._failure_count += 1
            log.warning("Primary failed (%d): %s", self._failure_count, e)
            return self.fallback.generate(*args, **kwargs)

    def structured(self, *args, **kwargs) -> Dict:
        try:
            result = self.primary.structured(*args, **kwargs)
            self._failure_count = 0
            return result
        except Exception as e:
            self._failure_count += 1
            return self.fallback.structured(*args, **kwargs)


def build_adapter_from_config(cfg: Dict) -> BaseModelAdapter:
    provider = cfg.get("provider", "mock").lower()
    if provider == "mock":
        return MockAdapter()
    return MockAdapter()
