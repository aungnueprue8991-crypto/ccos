"""CCOS configuration — pydantic-settings production config."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class CCOSConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="CCOS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    workspace: Path = Field(default=Path("."))
    log_level: str = "INFO"
    max_concurrent_tasks: int = 8
    default_cpu_quota: float = 100.0
    default_memory_mb: float = 2048.0
    event_db: str = "observatory/ledger/events.db"
    enable_scheduler: bool = True
    enable_observatory_mirror_jsonl: bool = True
    constitution_version: str = "1.0.0"

    @property
    def storage_dir(self) -> Path:
        p = self.workspace / "storage"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def ledger_path(self) -> Path:
        p = self.workspace / self.event_db
        p.parent.mkdir(parents=True, exist_ok=True)
        return p


_config: Optional[CCOSConfig] = None


def get_config(workspace: Optional[Path | str] = None) -> CCOSConfig:
    global _config
    if _config is None or workspace is not None:
        kwargs = {}
        if workspace is not None:
            kwargs["workspace"] = Path(workspace)
        _config = CCOSConfig(**kwargs)
    return _config
