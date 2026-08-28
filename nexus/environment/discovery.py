"""Environment Discovery Engine — inspect runtime world at boot and periodically."""

from __future__ import annotations

import os
import platform
import shutil
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class EnvironmentModel:
    os_name: str = ""
    os_version: str = ""
    platform: str = ""
    python_version: str = ""
    cpu_count: int = 0
    hostname: str = ""
    cwd: str = ""
    home: str = ""
    path_entries: List[str] = field(default_factory=list)
    available_commands: List[str] = field(default_factory=list)
    env_vars_sample: Dict[str, str] = field(default_factory=dict)
    disk_free_gb: Optional[float] = None
    packages_hint: List[str] = field(default_factory=list)
    permissions: Dict[str, bool] = field(default_factory=dict)
    unknowns: List[str] = field(default_factory=list)
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def can_do(self, action: str) -> bool:
        return self.permissions.get(action, False)


class EnvironmentDiscovery:
    PROBE_COMMANDS = (
        "python", "python3", "pip", "git", "curl", "wget",
        "node", "npm", "docker", "ffmpeg", "gcc", "make",
    )

    def discover(self, root: Optional[str] = None) -> EnvironmentModel:
        model = EnvironmentModel(
            os_name=platform.system(),
            os_version=platform.version()[:120],
            platform=platform.platform()[:120],
            python_version=sys.version.split()[0],
            cpu_count=os.cpu_count() or 0,
            hostname=platform.node(),
            cwd=str(Path(root or Path.cwd()).resolve()),
            home=str(Path.home()),
        )
        path = os.environ.get("PATH", "")
        model.path_entries = path.split(os.pathsep)[:40]
        for cmd in self.PROBE_COMMANDS:
            if shutil.which(cmd):
                model.available_commands.append(cmd)
        safe_keys = ("PATH", "HOME", "USER", "LANG", "SHELL", "VIRTUAL_ENV", "PYTHONPATH")
        for k in safe_keys:
            if k in os.environ:
                model.env_vars_sample[k] = os.environ[k][:200]
        try:
            usage = shutil.disk_usage(model.cwd)
            model.disk_free_gb = round(usage.free / (1024**3), 2)
        except Exception:
            model.unknowns.append("disk_usage")
        model.permissions = {
            "read_cwd": os.access(model.cwd, os.R_OK),
            "write_cwd": os.access(model.cwd, os.W_OK),
            "network": True,
            "execute_python": True,
            "git": "git" in model.available_commands,
        }
        for pkg in ("numpy", "pytest", "pydantic", "fastapi", "torch", "sklearn"):
            try:
                __import__(pkg)
                model.packages_hint.append(pkg)
            except Exception:
                pass
        if not model.available_commands:
            model.unknowns.append("no_probed_commands")
        return model
