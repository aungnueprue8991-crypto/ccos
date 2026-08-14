"""Teaching interaction — expert agent packages a skill/knowledge lesson."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ags.shared.types import new_id, now_ts


@dataclass
class TeachingSession:
    session_id: str = field(default_factory=new_id)
    teacher_id: str = ""
    student_id: str = ""
    topic: str = ""
    lesson: str = ""
    domain: str = "general"
    status: str = "proposed"  # proposed | active | completed | rejected
    created_at: float = field(default_factory=now_ts)
    outcome: str = ""


class TeachingProtocol:
    def start(self, teacher_id: str, student_id: str, topic: str, lesson: str, domain: str) -> TeachingSession:
        return TeachingSession(
            teacher_id=teacher_id, student_id=student_id,
            topic=topic, lesson=lesson, domain=domain, status="active",
        )

    def complete(self, session: TeachingSession, success: bool) -> TeachingSession:
        session.status = "completed"
        session.outcome = "learned" if success else "not_retained"
        return session
