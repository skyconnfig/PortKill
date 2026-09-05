from __future__ import annotations

import socket
from collections.abc import Iterable

import psutil

from models.port_process import PortProcess

PROCESS_CATEGORIES = {
    "node.exe": "Node.js",
    "python.exe": "Python",
    "java.exe": "Java",
    "javaw.exe": "Java",
    "dotnet.exe": ".NET",
    "php.exe": "PHP",
    "mysqld.exe": "MySQL",
    "postgres.exe": "PostgreSQL",
    "redis-server.exe": "Redis",
    "nginx.exe": "Nginx",
}


def _local_port(connection: psutil._common.sconn) -> int | None:
    try:
        return int(connection.laddr.port) if connection.laddr else None
    except (AttributeError, TypeError, ValueError):
        return None


def _protocol(connection: psutil._common.sconn) -> str:
    if connection.type == socket.SOCK_DGRAM:
        return "UDP"
    return "TCP"


def _service_names_by_pid() -> dict[int, str]:
    services: dict[int, str] = {}
    try:
        # pywin32 is the primary Windows service lookup path.
        import win32service

        manager = win32service.OpenSCManager(
            None,
            None,
            win32service.SC_MANAGER_ENUMERATE_SERVICE,
        )
        try:
            entries = win32service.EnumServicesStatusEx(
                manager,
                win32service.SC_ENUM_PROCESS_INFO,
                win32service.SERVICE_WIN32,
                win32service.SERVICE_STATE_ALL,
            )
            for service_name, display_name, status_info in entries:
                if isinstance(status_info, tuple) and len(status_info) >= 8:
                    pid = int(status_info[7] or 0)
                    if pid:
                        services.setdefault(pid, display_name or service_name)
        finally:
            win32service.CloseServiceHandle(manager)
    except Exception:
        pass

    if services or not hasattr(psutil, "win_service_iter"):
        return services
    # Fallback for restricted environments where SCM enumeration is denied.
    try:
        for service in psutil.win_service_iter():
            try:
                pid = service.pid()
                if pid:
                    services.setdefault(pid, service.name())
            except (psutil.Error, OSError):
                continue
    except (psutil.Error, OSError):
        pass
    return services


def _process_info(pid: int, service_names: dict[int, str]) -> PortProcess | None:
    try:
        process = psutil.Process(pid)
        name = process.name() or f"PID {pid}"
        executable_path: str | None
        try:
            executable_path = process.exe()
        except (psutil.Error, OSError, PermissionError):
            executable_path = None
        return PortProcess(
            port=0,
            protocol="",
            status="",
            pid=pid,
            process_name=name,
            executable_path=executable_path,
            category=PROCESS_CATEGORIES.get(name.casefold()),
            service_name=service_names.get(pid),
        )
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, OSError):
        return None


def _sort_key(item: PortProcess) -> tuple[int, int, str]:
    return (0 if item.status == "LISTEN" else 1, item.pid, item.process_name.casefold())


def find_process_by_port(port: int) -> list[PortProcess]:
    """Scan real Windows inet connections and return one row per matching PID."""
    connections = psutil.net_connections(kind="inet")
    matched: dict[int, tuple[str, str]] = {}
    for connection in connections:
        if _local_port(connection) != port or connection.pid is None:
            continue
        status = (connection.status or "UNKNOWN").upper()
        protocol = _protocol(connection)
        previous = matched.get(connection.pid)
        # Prefer LISTEN and TCP when a process owns several records.
        if previous is None or (
            status == "LISTEN" and previous[0] != "LISTEN"
        ) or (status == previous[0] and protocol == "TCP" and previous[1] != "TCP"):
            matched[connection.pid] = (status, protocol)

    service_names = _service_names_by_pid()
    results: list[PortProcess] = []
    for pid, (status, protocol) in matched.items():
        item = _process_info(pid, service_names)
        if item is None:
            continue
        results.append(
            PortProcess(
                port=port,
                protocol=protocol,
                status=status,
                pid=item.pid,
                process_name=item.process_name,
                executable_path=item.executable_path,
                category=item.category,
                service_name=item.service_name,
            )
        )
    return sorted(results, key=_sort_key)

