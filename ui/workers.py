from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QObject, QRunnable, Signal


class WorkerSignals(QObject):
    result = Signal(object)
    error = Signal(str)
    finished = Signal()


class Worker(QRunnable):
    def __init__(self, function: Callable[[], object]) -> None:
        super().__init__()
        # Keep the Python/QObject signal bridge alive until queued GUI slots run.
        # Qt's default QRunnable auto-delete can invalidate it too early.
        self.setAutoDelete(False)
        self.function = function
        self.signals = WorkerSignals()

    def run(self) -> None:
        try:
            self.signals.result.emit(self.function())
        except Exception as exc:  # Worker errors must never crash the UI.
            self.signals.error.emit(str(exc))
        finally:
            self.signals.finished.emit()

