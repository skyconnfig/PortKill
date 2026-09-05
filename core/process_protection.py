from __future__ import annotations

PROTECTED_PIDS = {0, 4}
PROTECTED_NAMES = {
    "system",
    "registry",
    "smss.exe",
    "csrss.exe",
    "wininit.exe",
    "services.exe",
    "lsass.exe",
    "winlogon.exe",
}


def is_protected(pid: int, process_name: str | None = None) -> bool:
    return pid in PROTECTED_PIDS or (process_name or "").casefold() in PROTECTED_NAMES


def protection_message() -> str:
    return "这是 Windows 关键系统进程。\n为了防止系统崩溃，PortKill 不允许结束该进程。"


