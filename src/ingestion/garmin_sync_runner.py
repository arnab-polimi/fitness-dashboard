"""Safely invoke a local GarminDB refresh script from the dashboard."""
from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import Any, Dict


# This is the existing sync stage from the user's Garmin study project.  It
# downloads/imports/analyzes GarminDB data, but does not generate or email a
# report (unlike master_run.bat).
DEFAULT_GARMIN_SYNC_SCRIPT = r"E:\stravaanalysis\Garmin codes\daily_garmin_sync.bat"


class GarminSyncRunner:
    """Runs the local GarminDB refresh batch file and returns a safe summary."""

    _SENSITIVE_LINE = re.compile(r"password|passwd|token|secret|authorization", re.IGNORECASE)

    @classmethod
    def is_available(cls, script_path: str = DEFAULT_GARMIN_SYNC_SCRIPT) -> bool:
        """Return whether the configured batch file exists."""
        return bool(script_path) and Path(script_path).is_file()

    @classmethod
    def run(cls, script_path: str, timeout_seconds: int = 900) -> Dict[str, Any]:
        """Execute a local .bat sync script without invoking the email/report stage."""
        script = Path(script_path).expanduser()
        if not script.is_file():
            raise FileNotFoundError(f"Garmin sync script not found: {script}")
        if script.suffix.lower() not in {".bat", ".cmd"}:
            raise ValueError("Garmin sync script must be a .bat or .cmd file.")

        try:
            completed = subprocess.run(
                ["cmd.exe", "/d", "/c", str(script)],
                cwd=str(script.parent),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            output = cls._safe_tail((exc.stdout or "") + "\n" + (exc.stderr or ""))
            return {
                "status": "timed_out",
                "exit_code": None,
                "summary": output or f"Timed out after {timeout_seconds // 60} minutes.",
            }

        output = cls._safe_tail((completed.stdout or "") + "\n" + (completed.stderr or ""))
        return {
            "status": "success" if completed.returncode == 0 else "failed",
            "exit_code": completed.returncode,
            "summary": output or "Sync script finished without console output.",
        }

    @classmethod
    def _safe_tail(cls, output: str, max_lines: int = 12) -> str:
        """Keep a short troubleshooting tail while avoiding credential-bearing lines."""
        safe_lines = [
            line for line in output.splitlines()
            if line.strip() and not cls._SENSITIVE_LINE.search(line)
        ]
        return "\n".join(safe_lines[-max_lines:])
