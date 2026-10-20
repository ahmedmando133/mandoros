"""
MANDOROS Desktop Application Runner (Windows / macOS / Linux).
Runs MANDOROS locally on 127.0.0.1 with zero server dependencies and zero load on Render.
Launches a dedicated native desktop window (via pywebview if available, or Chrome/Edge --app mode).
"""

from __future__ import annotations

import os
import sys
import time
import socket
import threading
import subprocess
import webbrowser
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))
os.chdir(ROOT_DIR)

from infra_stability import start_background_janitor


def find_free_port(default_port: int = 7860) -> int:
    """Finds a free local TCP port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if s.connect_ex(("127.0.0.1", default_port)) != 0:
            return default_port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def launch_native_window(url: str, title: str = "MANDOROS • Clinical Evidence & Meta-Analysis"):
    """
    Attempts to launch in a standalone native desktop window:
    1. Try pywebview for embedded OS WebKit/WebView2 window
    2. Try Chrome / Edge in standalone '--app' mode
    3. Fallback to system default browser
    """
    try:
        import webview
        print(f"[Desktop App] Launching via PyWebView window: {url}")
        webview.create_window(title, url, width=1440, height=920, resizable=True)
        webview.start()
        return
    except ImportError:
        pass

    # Windows Chrome / Edge --app mode
    if sys.platform == "win32":
        candidates = [
            Path(os.environ.get("PROGRAMFILES(X86)", "C:/Program Files (x86)")) / "Google/Chrome/Application/chrome.exe",
            Path(os.environ.get("PROGRAMFILES", "C:/Program Files")) / "Google/Chrome/Application/chrome.exe",
            Path(os.environ.get("LOCALAPPDATA", "")) / "Google/Chrome/Application/chrome.exe",
            Path(os.environ.get("PROGRAMFILES(X86)", "C:/Program Files (x86)")) / "Microsoft/Edge/Application/msedge.exe",
            Path(os.environ.get("PROGRAMFILES", "C:/Program Files")) / "Microsoft/Edge/Application/msedge.exe",
        ]
        for c in candidates:
            if c.exists():
                print(f"[Desktop App] Launching standalone app window via {c.name}: {url}")
                try:
                    subprocess.Popen([str(c), f"--app={url}", f"--app-window-size=1440,920"])
                    return
                except Exception:
                    pass

    # macOS Chrome / Safari app mode
    elif sys.platform == "darwin":
        chrome_mac = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
        if chrome_mac.exists():
            print(f"[Desktop App] Launching Chrome macOS app mode: {url}")
            try:
                subprocess.Popen([str(chrome_mac), f"--app={url}"])
                return
            except Exception:
                pass

    print(f"[Desktop App] Opening in default web browser: {url}")
    webbrowser.open(url)


def main():
    print("=" * 70)
    print("🚀 MANDOROS Local Desktop Edition Starting...")
    print("=" * 70)

    # 1. Start local disk & memory janitor
    start_background_janitor(interval_seconds=300)

    # 2. Allocate free local port
    port = find_free_port(7860)
    local_url = f"http://127.0.0.1:{port}"
    os.environ["PORT"] = str(port)

    # 3. Build Gradio app
    from app import build_app
    demo = build_app()
    demo.queue(default_concurrency_limit=4, max_size=60)

    # 4. Launch Gradio in a background thread
    fav = "assets/favicon.ico" if os.path.exists("assets/favicon.ico") else None

    def _run_server():
        demo.launch(
            server_name="127.0.0.1",
            server_port=port,
            favicon_path=fav,
            prevent_thread_lock=True,
            show_error=True
        )

    server_thread = threading.Thread(target=_run_server, daemon=True)
    server_thread.start()

    # Wait for server to boot
    time.sleep(2.0)
    print(f"✅ MANDOROS Local Server Online at {local_url}")

    # 5. Open native desktop window
    launch_native_window(local_url)

    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[Desktop App] Closing MANDOROS. Goodbye!")


if __name__ == "__main__":
    main()
