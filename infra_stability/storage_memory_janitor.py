import gc
import shutil
import tempfile
import threading
import time
from pathlib import Path
from typing import Dict, Any

SESSION_ROOT = Path(tempfile.gettempdir()) / "mandoros_runtime_sessions"
SESSION_ROOT.mkdir(parents=True, exist_ok=True)

_janitor_started = False
_janitor_lock = threading.Lock()


def cleanup_expired_sessions(max_age_seconds: int = 1800, max_folder_mb: int = 200) -> Dict[str, Any]:
    """
    Keeps Render disk and 512MB RAM clean: deletes temp session folders older than 30 mins
    or trims oldest sessions if total temp disk exceeds 200 MB, then forces garbage collection.
    """
    now = time.time()
    deleted_count = 0
    reclaimed_bytes = 0
    try:
        items = []
        total_bytes = 0
        if SESSION_ROOT.exists():
            for p in SESSION_ROOT.iterdir():
                try:
                    mtime = p.stat().st_mtime
                    size = sum(f.stat().st_size for f in p.rglob("*") if f.is_file()) if p.is_dir() else p.stat().st_size
                    if now - mtime > max_age_seconds:
                        shutil.rmtree(p, ignore_errors=True) if p.is_dir() else p.unlink(missing_ok=True)
                        deleted_count += 1
                        reclaimed_bytes += size
                    else:
                        items.append((mtime, size, p))
                        total_bytes += size
                except Exception:
                    continue

            items.sort(key=lambda x: x[0])
            while total_bytes > max_folder_mb * 1024 * 1024 and items:
                _, sz, oldest_path = items.pop(0)
                shutil.rmtree(oldest_path, ignore_errors=True) if oldest_path.is_dir() else oldest_path.unlink(missing_ok=True)
                total_bytes -= sz
                deleted_count += 1
                reclaimed_bytes += sz
    finally:
        try:
            import matplotlib.pyplot as plt
            plt.close("all")
        except Exception:
            pass
        gc.collect()

    return {
        "deleted_sessions": deleted_count,
        "reclaimed_bytes": reclaimed_bytes,
        "remaining_active_sessions": len(items) if 'items' in locals() else 0,
        "current_disk_bytes": total_bytes if 'total_bytes' in locals() else 0,
    }


def get_storage_stats() -> Dict[str, Any]:
    """Returns current active sessions count and disk utilization."""
    if not SESSION_ROOT.exists():
        return {"session_count": 0, "disk_mb": 0.0}
    try:
        sessions = [p for p in SESSION_ROOT.iterdir() if p.is_dir()]
        total_bytes = sum(f.stat().st_size for f in SESSION_ROOT.rglob("*") if f.is_file())
        return {
            "session_count": len(sessions),
            "disk_mb": round(total_bytes / (1024 * 1024), 2),
        }
    except Exception:
        return {"session_count": 0, "disk_mb": 0.0}


def start_background_janitor(interval_seconds: int = 300):
    """Starts the storage and memory janitor background daemon thread once."""
    global _janitor_started
    with _janitor_lock:
        if _janitor_started:
            return
        _janitor_started = True

        def _loop():
            while True:
                try:
                    cleanup_expired_sessions()
                except Exception:
                    pass
                time.sleep(interval_seconds)

        t = threading.Thread(
            target=_loop,
            daemon=True,
            name="MandorosStorageJanitor"
        )
        t.start()
