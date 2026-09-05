from __future__ import annotations

import os
from dataclasses import dataclass

from PySide6.QtCore import QThreadPool, QTimer, Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from core.port_finder import find_process_by_port
from core.privilege import is_admin, relaunch_as_admin
from core.process_manager import ProcessKillResult, force_kill_process, terminate_process
from models.port_process import PortProcess
from ui.confirm_dialog import ConfirmDialog
from ui.icons import lucide_icon
from ui.result_card import ResultCard
from ui.workers import Worker
from utils.constants import MAX_HISTORY


@dataclass(frozen=True)
class OperationOutcome:
    result: ProcessKillResult
    remaining: list[PortProcess]


class MainWindow(QMainWindow):
    toast_changed = Signal(str)

    def __init__(self, initial_port: str = "", auto_query: bool = False) -> None:
        super().__init__()
        self.setWindowTitle("PortKill")
        self.setMinimumSize(620, 560)
        self.resize(700, 680)
        self.pool = QThreadPool(self)
        self.pool.setMaxThreadCount(2)
        self._active_workers: set[Worker] = set()
        self.current_port: int | None = None
        self.current_results: list[PortProcess] = []
        self.history: list[int] = []
        self.result_cards: list[ResultCard] = []
        self._query_token = 0

        self._build_ui()
        self._install_shortcuts()
        if initial_port:
            self.port_input.setText(initial_port)
        if auto_query and initial_port:
            QTimer.singleShot(250, self.query_port)
        else:
            self.port_input.setFocus()

    def _build_ui(self) -> None:
        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        topbar = QFrame()
        topbar.setObjectName("topbar")
        topbar.setFixedHeight(58)
        top_layout = QHBoxLayout(topbar)
        top_layout.setContentsMargins(20, 8, 16, 8)
        top_layout.setSpacing(10)
        brand_icon = QLabel()
        brand_icon.setPixmap(lucide_icon("shield-check", 25, "#58A6FF").pixmap(25, 25))
        top_layout.addWidget(brand_icon)
        brand_text = QVBoxLayout()
        brand_text.setSpacing(0)
        title = QLabel("PortKill")
        title.setObjectName("appTitle")
        subtitle = QLabel("Windows 端口占用释放工具")
        subtitle.setObjectName("appSubtitle")
        brand_text.addWidget(title)
        brand_text.addWidget(subtitle)
        top_layout.addLayout(brand_text)
        top_layout.addStretch()
        admin_badge = QLabel("管理员模式" if is_admin() else "普通权限")
        admin_badge.setObjectName("badge" if is_admin() else "serviceBadge")
        top_layout.addWidget(admin_badge)
        self.pin_button = QToolButton()
        self.pin_button.setObjectName("iconButton")
        self.pin_button.setIcon(lucide_icon("pin", 17, "#8B949E"))
        self.pin_button.setToolTip("窗口置顶")
        self.pin_button.clicked.connect(self.toggle_always_on_top)
        top_layout.addWidget(self.pin_button)
        root_layout.addWidget(topbar)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(24, 24, 24, 22)
        content_layout.setSpacing(16)

        input_card = QFrame()
        input_card.setObjectName("inputCard")
        input_layout = QVBoxLayout(input_card)
        input_layout.setContentsMargins(18, 16, 18, 16)
        input_layout.setSpacing(10)
        eyebrow = QLabel("端口查询")
        eyebrow.setObjectName("eyebrow")
        input_layout.addWidget(eyebrow)
        prompt = QLabel("请输入被占用的端口号")
        prompt.setStyleSheet("font-size: 18px; font-weight: 700;")
        input_layout.addWidget(prompt)
        input_row = QHBoxLayout()
        input_row.setSpacing(10)
        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText("例如 8080")
        self.port_input.setMaxLength(5)
        self.port_input.setClearButtonEnabled(True)
        self.port_input.setToolTip("输入 1 到 65535 的端口号")
        self.port_input.textChanged.connect(self._invalidate_query)
        input_row.addWidget(self.port_input, 1)
        self.query_button = QPushButton("查询端口")
        self.query_button.setObjectName("primaryButton")
        self.query_button.setIcon(lucide_icon("search", 16, "#FFFFFF"))
        self.query_button.setMinimumWidth(120)
        self.query_button.clicked.connect(self.query_port)
        input_row.addWidget(self.query_button)
        input_layout.addLayout(input_row)
        helper = QLabel("Enter 查询  ·  Ctrl+L 聚焦输入框  ·  F5 重新查询  ·  Esc 清空结果")
        helper.setObjectName("helper")
        input_layout.addWidget(helper)
        content_layout.addWidget(input_card)

        result_heading = QHBoxLayout()
        section_title = QLabel("端口状态")
        section_title.setObjectName("sectionTitle")
        result_heading.addWidget(section_title)
        result_heading.addStretch()
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setFixedWidth(90)
        self.progress.setFixedHeight(4)
        self.progress.hide()
        result_heading.addWidget(self.progress)
        self.result_summary = QLabel("等待查询")
        self.result_summary.setObjectName("helper")
        result_heading.addWidget(self.result_summary)
        content_layout.addLayout(result_heading)

        self.results_container = QWidget()
        self.results_layout = QVBoxLayout(self.results_container)
        self.results_layout.setContentsMargins(0, 0, 0, 0)
        self.results_layout.setSpacing(10)
        self._show_empty_state()
        content_layout.addWidget(self.results_container)

        history_card = QFrame()
        history_card.setObjectName("historyCard")
        history_layout = QHBoxLayout(history_card)
        history_layout.setContentsMargins(14, 10, 14, 10)
        history_layout.setSpacing(8)
        history_icon = QLabel()
        history_icon.setPixmap(lucide_icon("history", 15, "#8B949E").pixmap(15, 15))
        history_layout.addWidget(history_icon)
        history_label = QLabel("最近使用")
        history_label.setObjectName("metaLabel")
        history_layout.addWidget(history_label)
        self.history_layout = history_layout
        history_layout.addStretch()
        content_layout.addWidget(history_card)
        content_layout.addStretch()
        scroll.setWidget(content)
        root_layout.addWidget(scroll, 1)

        self.toast = QFrame(root)
        self.toast.setObjectName("toast")
        toast_layout = QHBoxLayout(self.toast)
        toast_layout.setContentsMargins(12, 8, 12, 8)
        toast_layout.setSpacing(7)
        toast_icon = QLabel()
        toast_icon.setPixmap(lucide_icon("check-circle-2", 16, "#3FB950").pixmap(16, 16))
        toast_layout.addWidget(toast_icon)
        self.toast_text = QLabel()
        self.toast_text.setObjectName("toastText")
        toast_layout.addWidget(self.toast_text)
        self.toast.adjustSize()
        self.toast.hide()
        self.toast_timer = QTimer(self)
        self.toast_timer.setSingleShot(True)
        self.toast_timer.timeout.connect(self.toast.hide)

        self.setCentralWidget(root)

    def _install_shortcuts(self) -> None:
        QShortcut(QKeySequence("Ctrl+L"), self, activated=self.focus_port_input)
        QShortcut(QKeySequence("F5"), self, activated=self.query_port)
        QShortcut(QKeySequence("Escape"), self, activated=self.clear_current_result)

    def _show_empty_state(self) -> None:
        self._clear_results_layout()
        card = QFrame()
        card.setObjectName("emptyCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 28, 20, 28)
        layout.setSpacing(8)
        icon = QLabel()
        icon.setPixmap(lucide_icon("activity", 28, "#58A6FF").pixmap(28, 28))
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon)
        title = QLabel("输入端口后，开始查询")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 15px; font-weight: 700;")
        layout.addWidget(title)
        hint = QLabel("PortKill 会扫描真实 Windows 网络连接，并显示占用它的进程")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setObjectName("helper")
        layout.addWidget(hint)
        self.results_layout.addWidget(card)

    def _clear_results_layout(self) -> None:
        while self.results_layout.count():
            item = self.results_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.result_cards.clear()

    def _show_free_state(self, port: int, message: str | None = None) -> None:
        self._clear_results_layout()
        card = QFrame()
        card.setObjectName("emptyCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 20, 18, 20)
        layout.setSpacing(7)
        status = QLabel(message or f"✓ 端口 {port} 当前未被占用")
        status.setObjectName("statusLabel")
        status.setProperty("status", "free")
        status.style().unpolish(status)
        status.style().polish(status)
        layout.addWidget(status)
        detail = QLabel("现在可以启动你的开发服务了。")
        detail.setObjectName("helper")
        layout.addWidget(detail)
        self.results_layout.addWidget(card)

    def _show_error_state(self, message: str) -> None:
        self._clear_results_layout()
        card = QFrame()
        card.setObjectName("emptyCard")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(18, 18, 18, 18)
        icon = QLabel()
        icon.setPixmap(lucide_icon("circle-alert", 22, "#F85149").pixmap(22, 22))
        layout.addWidget(icon)
        label = QLabel(message)
        label.setObjectName("statusLabel")
        label.setProperty("status", "error")
        label.setWordWrap(True)
        layout.addWidget(label, 1)
        self.results_layout.addWidget(card)

    def _show_results(self, results: list[PortProcess]) -> None:
        self._clear_results_layout()
        for item in results:
            card = ResultCard(item)
            card.copy_pid.connect(self.copy_pid)
            card.copy_path.connect(self.copy_path)
            card.open_directory.connect(self.open_directory)
            card.terminate.connect(self.confirm_terminate)
            card.force_terminate.connect(self.confirm_force_terminate)
            self.result_cards.append(card)
            self.results_layout.addWidget(card)

    def _set_busy(self, busy: bool, text: str = "") -> None:
        self.query_button.setEnabled(not busy)
        self.progress.setVisible(busy)
        if text:
            self.result_summary.setText(text)
        self.port_input.setEnabled(not busy)

    def _invalidate_query(self) -> None:
        # Editing the field makes any previous query stale.
        self._query_token += 1

    def _set_query_busy(self, text: str) -> None:
        # Searching is non-destructive: keep the input and query button usable
        # so users can clear 1000 and immediately search another port.
        self.progress.show()
        self.result_summary.setText(text)
        self.port_input.setEnabled(True)
        self.query_button.setEnabled(True)

    def _query_worker_finished(self, token: int) -> None:
        if token == self._query_token:
            self.progress.hide()
            self.query_button.setEnabled(True)

    def _start_worker(self, worker: Worker) -> None:
        self._active_workers.add(worker)
        worker.signals.finished.connect(lambda worker=worker: self._release_worker(worker))
        self.pool.start(worker)

    def _release_worker(self, worker: Worker) -> None:
        self._active_workers.discard(worker)
        worker.signals.deleteLater()

    def query_port(self) -> None:
        text = self.port_input.text().strip()
        if not text.isdigit():
            self.result_summary.setText("输入有误")
            self._show_error_state("请输入正确的端口号")
            return
        port = int(text)
        if not 1 <= port <= 65535:
            self.result_summary.setText("输入有误")
            self._show_error_state("端口号范围必须为 1～65535")
            return

        self.current_port = port
        self._query_token += 1
        token = self._query_token
        self._remember_port(port)
        self._set_query_busy(f"正在查询端口 {port}...")
        worker = Worker(lambda: find_process_by_port(port))
        worker.signals.result.connect(lambda result: self._query_finished(token, port, result))
        worker.signals.error.connect(lambda message: self._query_failed(token, message))
        worker.signals.finished.connect(lambda: self._query_worker_finished(token))
        self._start_worker(worker)

    def _query_finished(self, token: int, port: int, result: object) -> None:
        if token != self._query_token:
            return
        results = list(result)
        self.current_results = results
        if not results:
            self.result_summary.setText("端口可用")
            self._show_free_state(port)
            return
        self.result_summary.setText(f"发现 {len(results)} 个相关进程")
        self._show_results(results)

    def _query_failed(self, token: int, message: str) -> None:
        if token != self._query_token:
            return
        self.result_summary.setText("查询失败")
        self._show_error_state(f"查询端口失败：{message}")

    def confirm_terminate(self, item: object) -> None:
        if not isinstance(item, PortProcess) or self.current_port is None:
            return
        dialog = ConfirmDialog(item.process_name, item.pid, self.current_port)
        if dialog.exec() != dialog.DialogCode.Accepted:
            return
        port = self.current_port
        self._set_busy(True, "正在结束进程...")
        worker = Worker(lambda: self._terminate_and_verify(item.pid, port, force=False))
        worker.signals.result.connect(lambda outcome: self._operation_finished(port, outcome))
        worker.signals.error.connect(lambda message: self._query_failed(self._query_token, message))
        worker.signals.finished.connect(lambda: self._set_busy(False))
        self._start_worker(worker)

    def confirm_force_terminate(self, item: object) -> None:
        if not isinstance(item, PortProcess) or self.current_port is None:
            return
        dialog = ConfirmDialog(item.process_name, item.pid, self.current_port, force=True)
        if dialog.exec() != dialog.DialogCode.Accepted:
            return
        port = self.current_port
        self._set_busy(True, "正在强制释放端口...")
        worker = Worker(lambda: self._terminate_and_verify(item.pid, port, force=True))
        worker.signals.result.connect(lambda outcome: self._operation_finished(port, outcome))
        worker.signals.error.connect(lambda message: self._query_failed(self._query_token, message))
        worker.signals.finished.connect(lambda: self._set_busy(False))
        self._start_worker(worker)

    @staticmethod
    def _terminate_and_verify(pid: int, port: int, *, force: bool) -> OperationOutcome:
        result = force_kill_process(pid) if force else terminate_process(pid)
        remaining = find_process_by_port(port) if result.status in {"success", "not_found"} else []
        return OperationOutcome(result, remaining)

    def _operation_finished(self, port: int, outcome: object) -> None:
        if not isinstance(outcome, OperationOutcome):
            self._show_error_state("操作失败：返回结果无效")
            return
        result = outcome.result
        if result.status == "success" and not outcome.remaining:
            self.current_results = []
            self.result_summary.setText("端口已成功释放")
            self._show_free_state(port, f"✓ 端口 {port} 已成功释放")
            self.show_toast(f"端口 {port} 已释放")
        elif result.status == "success" and outcome.remaining:
            self.current_results = outcome.remaining
            self.result_summary.setText("端口仍被占用")
            self._show_results(outcome.remaining)
            self._show_warning(f"进程已结束，但端口仍处于占用状态。当前发现 {len(outcome.remaining)} 个进程。")
        elif result.status == "timeout":
            self._ask_force_kill(result, port)
        elif result.status == "access_denied":
            self._ask_admin_restart(port)
        elif result.status == "protected":
            self._show_warning(result.message)
        else:
            self._show_error_state(result.message or "操作失败")

    def _ask_force_kill(self, result: ProcessKillResult, port: int) -> None:
        dialog = ConfirmDialog(result.process_name, result.pid, port, force=True, retry_prompt=True)
        if dialog.exec() != dialog.DialogCode.Accepted:
            self._show_warning("进程未退出，未执行强制结束。")
            return
        self._set_busy(True, "正在强制结束进程...")
        worker = Worker(lambda: self._terminate_and_verify(result.pid, port, force=True))
        worker.signals.result.connect(lambda outcome: self._operation_finished(port, outcome))
        worker.signals.error.connect(self._query_failed)
        worker.signals.finished.connect(lambda: self._set_busy(False))
        self._start_worker(worker)

    def _ask_admin_restart(self, port: int) -> None:
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Warning)
        box.setWindowTitle("需要管理员权限")
        box.setText("当前权限不足，无法结束该进程。")
        box.setInformativeText(f"是否以管理员身份重新启动 PortKill，并保留端口 {port}？")
        restart = box.addButton("以管理员身份重新启动", QMessageBox.ButtonRole.AcceptRole)
        box.addButton("取消", QMessageBox.ButtonRole.RejectRole)
        box.exec()
        if box.clickedButton() is restart:
            if relaunch_as_admin(port):
                self.close()
            else:
                self._show_error_state("管理员重启未启动，操作已取消。")

    def _show_warning(self, message: str) -> None:
        self._clear_results_layout()
        card = QFrame()
        card.setObjectName("emptyCard")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(18, 18, 18, 18)
        icon = QLabel()
        icon.setPixmap(lucide_icon("triangle-alert", 22, "#D29922").pixmap(22, 22))
        layout.addWidget(icon)
        label = QLabel(message)
        label.setObjectName("statusLabel")
        label.setProperty("status", "busy")
        label.setWordWrap(True)
        layout.addWidget(label, 1)
        self.results_layout.addWidget(card)

    def clear_current_result(self) -> None:
        self._query_token += 1
        self.current_results = []
        self.result_summary.setText("等待查询")
        self._show_empty_state()

    def focus_port_input(self) -> None:
        self.port_input.setFocus()
        self.port_input.selectAll()

    def copy_pid(self, pid: int) -> None:
        QApplication.clipboard().setText(str(pid))
        self.show_toast("PID 已复制")

    def copy_path(self, path: str) -> None:
        QApplication.clipboard().setText(path)
        self.show_toast("程序路径已复制")

    def open_directory(self, directory: str) -> None:
        if not directory or not os.path.isdir(directory):
            self.show_toast("程序目录不可用")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(directory))

    def _remember_port(self, port: int) -> None:
        if port in self.history:
            self.history.remove(port)
        self.history.insert(0, port)
        del self.history[MAX_HISTORY:]
        self._render_history()

    def _render_history(self) -> None:
        while self.history_layout.count() > 3:
            item = self.history_layout.takeAt(2)
            if item.widget():
                item.widget().deleteLater()
        for port in self.history:
            chip = QPushButton(str(port))
            chip.setObjectName("historyChip")
            chip.clicked.connect(lambda _checked=False, value=port: self._query_history(value))
            self.history_layout.insertWidget(self.history_layout.count() - 1, chip)

    def _query_history(self, port: int) -> None:
        self.port_input.setText(str(port))
        self.query_port()

    def toggle_always_on_top(self) -> None:
        enabled = not bool(self.windowFlags() & Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, enabled)
        self.show()
        self.show_toast("窗口已置顶" if enabled else "已取消窗口置顶")

    def show_toast(self, message: str) -> None:
        self.toast_text.setText(message)
        self.toast.adjustSize()
        self.toast.move(self.width() - self.toast.width() - 24, self.height() - self.toast.height() - 24)
        self.toast.show()
        self.toast.raise_()
        self.toast_timer.start(2200)

    def resizeEvent(self, event) -> None:  # noqa: N802 - Qt API name
        super().resizeEvent(event)
        if self.toast.isVisible():
            self.toast.move(self.width() - self.toast.width() - 24, self.height() - self.toast.height() - 24)

