from __future__ import annotations

from dataclasses import dataclass

import psutil

from core.process_protection import is_protected, protection_message


@dataclass(frozen=True)
class ProcessKillResult:
    status: str
    pid: int
    process_name: str
    message: str


def _get_process(pid: int) -> tuple[psutil.Process | None, ProcessKillResult | None]:
    try:
        process = psutil.Process(pid)
        name = process.name()
        if is_protected(pid, name):
            return None, ProcessKillResult("protected", pid, name, protection_message())
        return process, None
    except psutil.NoSuchProcess:
        return None, ProcessKillResult("not_found", pid, "未知进程", "进程已经不存在。")
    except psutil.AccessDenied:
        return None, ProcessKillResult("access_denied", pid, "未知进程", "当前权限不足，无法结束该进程。")
    except (psutil.ZombieProcess, PermissionError, OSError) as exc:
        return None, ProcessKillResult("failed", pid, "未知进程", f"无法读取进程：{exc}")


def terminate_process(pid: int, timeout: float = 1.5) -> ProcessKillResult:
    process, early_result = _get_process(pid)
    if early_result:
        return early_result
    assert process is not None
    name = process.name()
    try:
        process.terminate()
        process.wait(timeout=timeout)
        return ProcessKillResult("success", pid, name, "进程已结束。")
    except psutil.TimeoutExpired:
        return ProcessKillResult("timeout", pid, name, "进程没有正常退出。")
    except psutil.NoSuchProcess:
        return ProcessKillResult("success", pid, name, "进程已结束。")
    except psutil.AccessDenied:
        return ProcessKillResult("access_denied", pid, name, "当前权限不足，无法结束该进程。")
    except (psutil.ZombieProcess, PermissionError, OSError) as exc:
        return ProcessKillResult("failed", pid, name, f"结束进程失败：{exc}")


def force_kill_process(pid: int, timeout: float = 1.5) -> ProcessKillResult:
    process, early_result = _get_process(pid)
    if early_result:
        return early_result
    assert process is not None
    name = process.name()
    try:
        process.kill()
        process.wait(timeout=timeout)
        return ProcessKillResult("success", pid, name, "进程已强制结束。")
    except psutil.TimeoutExpired:
        return ProcessKillResult("timeout", pid, name, "强制结束后进程仍未退出。")
    except psutil.NoSuchProcess:
        return ProcessKillResult("success", pid, name, "进程已结束。")
    except psutil.AccessDenied:
        return ProcessKillResult("access_denied", pid, name, "当前权限不足，无法强制结束该进程。")
    except (psutil.ZombieProcess, PermissionError, OSError) as exc:
        return ProcessKillResult("failed", pid, name, f"强制结束进程失败：{exc}")

