from __future__ import annotations

import os
import subprocess
import sys


def is_admin() -> bool:
    if os.name != "nt":
        return False
    try:
        import ctypes

        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except (AttributeError, OSError):
        return False


def relaunch_as_admin(port: int) -> bool:
    if os.name != "nt":
        return False
    import ctypes

    if getattr(sys, "frozen", False):
        executable = sys.executable
        args = ["--port", str(port), "--auto-query"]
    else:
        executable = sys.executable
        args = [os.path.abspath(sys.argv[0]), "--port", str(port), "--auto-query"]
    params = subprocess.list2cmdline(args)
    result = ctypes.windll.shell32.ShellExecuteW(None, "runas", executable, params, None, 1)
    return result > 32

