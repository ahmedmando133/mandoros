import time
import uuid
from pathlib import Path
from typing import Optional
from infra_stability.storage_memory_janitor import SESSION_ROOT


def create_isolated_session(prefix: str = "run") -> Path:
    """
    Generates a unique isolated workspace folder for a user run:
    e.g. /tmp/mandoros_runtime_sessions/run_1697723901234_a1b2c3/
    Ensures 50+ concurrent users never overwrite each other's workbooks or HTML dashboards.
    """
    SESSION_ROOT.mkdir(parents=True, exist_ok=True)
    run_id = f"{prefix}_{int(time.time() * 1000)}_{uuid.uuid4().hex[:6]}"
    run_dir = SESSION_ROOT / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def get_session_file_path(run_dir: Path, filename: str) -> Path:
    """Returns an absolute Path inside the designated session directory."""
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir / filename
