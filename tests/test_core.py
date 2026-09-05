from __future__ import annotations

import socket

from core.port_finder import find_process_by_port
from core.process_protection import is_protected


def test_find_process_by_port_finds_real_listener() -> None:
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(("127.0.0.1", 0))
    listener.listen(1)
    try:
        port = listener.getsockname()[1]
        results = find_process_by_port(port)
        assert any(item.pid > 0 and item.port == port for item in results)
        assert any(item.status == "LISTEN" for item in results)
    finally:
        listener.close()


def test_system_process_protection() -> None:
    assert is_protected(4, "System")
    assert is_protected(1234, "services.exe")
    assert not is_protected(1234, "example.exe")

