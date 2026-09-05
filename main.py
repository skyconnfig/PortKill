from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys


def _relaunch_with_project_venv() -> None:
    """Make double-clicking main.py use the project's isolated Qt runtime."""
    if os.name != "nt" or getattr(sys, "frozen", False):
        return
    project_python = Path(__file__).resolve().parent / ".venv" / "Scripts" / "python.exe"
    try:
        current_python = Path(sys.executable).resolve()
    except OSError:
        current_python = Path(sys.executable)
    if not project_python.is_file() or current_python == project_python.resolve():
        return
    os.execv(
        str(project_python),
        [str(project_python), str(Path(__file__).resolve()), *sys.argv[1:]],
    )


try:
    from PySide6.QtWidgets import QApplication
except ImportError:
    _relaunch_with_project_venv()
    raise

from ui.main_window import MainWindow
from ui.styles import DARK_QSS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="PortKill Windows 端口占用释放工具")
    parser.add_argument("--port", type=str, default="", help="管理员重启后恢复的端口")
    parser.add_argument("--auto-query", action="store_true", help="启动后自动查询")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    app = QApplication(sys.argv)
    app.setApplicationName("PortKill")
    app.setApplicationDisplayName("PortKill")
    app.setStyleSheet(DARK_QSS)

    window = MainWindow(initial_port=args.port, auto_query=args.auto_query)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

