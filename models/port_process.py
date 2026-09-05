from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PortProcess:
    port: int
    protocol: str
    status: str
    pid: int
    process_name: str
    executable_path: str | None
    category: str | None = None
    service_name: str | None = None


