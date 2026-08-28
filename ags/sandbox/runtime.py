"""Safe execution sandbox — subprocess isolation, timeout, destroy after use."""

from __future__ import annotations

import subprocess
import tempfile
import textwrap
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

from ags.shared.types import new_id, now_ts


@dataclass
class SandboxResult:
    sandbox_id: str
    success: bool
    stdout: str = ""
    stderr: str = ""
    returncode: int = 0
    timed_out: bool = False
    duration_ms: float = 0.0
    meta: Dict[str, Any] = field(default_factory=dict)


class SafeSandbox:
    def __init__(self, timeout_s: float = 3.0, max_output: int = 8000):
        self.timeout_s = timeout_s
        self.max_output = max_output

    def run_python(self, code: str, env_vars: Optional[Dict[str, str]] = None) -> SandboxResult:
        sid = new_id()
        start = now_ts()
        code = textwrap.dedent(code)
        banned = (
            "import os",
            "import sys",
            "import subprocess",
            "__import__",
            "open(",
            "eval(",
            "exec(",
            "compile(",
            "os.system",
            "socket",
        )
        lowered = code.lower()
        for b in banned:
            if b in lowered:
                return SandboxResult(
                    sandbox_id=sid,
                    success=False,
                    stderr=f"Blocked pattern: {b}",
                    returncode=1,
                    meta={"blocked": b},
                )

        with tempfile.TemporaryDirectory(prefix="ags-sbx-") as tmp:
            script = Path(tmp) / "snippet.py"
            script.write_text(code, encoding="utf-8")
            try:
                proc = subprocess.run(
                    ["python3", str(script)],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_s,
                    cwd=tmp,
                    env=env_vars or {"PATH": "/usr/bin:/bin", "HOME": tmp},
                )
                out = (proc.stdout or "")[: self.max_output]
                err = (proc.stderr or "")[: self.max_output]
                return SandboxResult(
                    sandbox_id=sid,
                    success=proc.returncode == 0,
                    stdout=out,
                    stderr=err,
                    returncode=proc.returncode,
                    duration_ms=(now_ts() - start) * 1000,
                )
            except subprocess.TimeoutExpired:
                return SandboxResult(
                    sandbox_id=sid,
                    success=False,
                    timed_out=True,
                    returncode=-1,
                    stderr="timeout",
                    duration_ms=self.timeout_s * 1000,
                )
            except Exception as e:
                return SandboxResult(
                    sandbox_id=sid, success=False, stderr=str(e), returncode=1
                )

    def eval_expression(self, expr: str) -> SandboxResult:
        code = f"print(repr(({expr})))"
        return self.run_python(code)
