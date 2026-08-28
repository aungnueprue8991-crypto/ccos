"""Multimodal binding — unify text/audio/vision/tool signals into percepts.

Lab-scale: text is primary; other modalities attach as structured side-channels
without requiring heavy ML stacks.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

from ags.shared.types import new_id, now_ts


@dataclass
class RawModality:
    modality: str  # text|audio|vision|tool|web|file|environment
    content: Any
    confidence: float = 1.0
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BoundPercept:
    percept_id: str = field(default_factory=new_id)
    text: str = ""
    modalities: List[str] = field(default_factory=list)
    features: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    timestamp: float = field(default_factory=now_ts)
    source: str = "binding"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class BindingEngine:
    def bind(self, signals: List[RawModality]) -> BoundPercept:
        if not signals:
            return BoundPercept(text="", confidence=0.0)
        texts: List[str] = []
        modalities: List[str] = []
        features: Dict[str, Any] = {}
        confs: List[float] = []
        for s in signals:
            modalities.append(s.modality)
            confs.append(float(s.confidence))
            if s.modality == "text":
                texts.append(str(s.content))
            elif s.modality == "audio":
                features["audio"] = s.content if isinstance(s.content, dict) else {"raw": str(s.content)[:200]}
                if isinstance(s.content, dict) and "transcript" in s.content:
                    texts.append(str(s.content["transcript"]))
                else:
                    texts.append(f"[audio:{str(s.content)[:80]}]")
            elif s.modality == "vision":
                features["vision"] = s.content if isinstance(s.content, dict) else {"desc": str(s.content)[:200]}
                if isinstance(s.content, dict) and "caption" in s.content:
                    texts.append(str(s.content["caption"]))
                else:
                    texts.append(f"[vision:{str(s.content)[:80]}]")
            elif s.modality == "tool":
                features.setdefault("tools", []).append(s.content)
                texts.append(f"[tool:{str(s.content)[:100]}]")
            else:
                features[s.modality] = s.content
                texts.append(f"[{s.modality}:{str(s.content)[:80]}]")
        conf = sum(confs) / len(confs) if confs else 0.0
        return BoundPercept(
            text=" ".join(texts).strip(),
            modalities=list(dict.fromkeys(modalities)),
            features=features,
            confidence=conf,
        )
