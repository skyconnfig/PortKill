from __future__ import annotations

import os

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from core.process_protection import is_protected
from models.port_process import PortProcess
from ui.icons import lucide_icon


class ResultCard(QFrame):
    copy_pid = Signal(int)
    copy_path = Signal(str)
    open_directory = Signal(str)
    terminate = Signal(object)
    force_terminate = Signal(object)

    def __init__(self, item: PortProcess, parent: QFrame | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("resultCard")
        self.item = item
        protected = is_protected(item.pid, item.process_name)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        header = QHBoxLayout()
        process_icon = QLabel()
        process_icon.setPixmap(lucide_icon("terminal", 20, "#58A6FF").pixmap(20, 20))
        header.addWidget(process_icon)
        name = QLabel(item.process_name)
        name.setObjectName("processName")
        header.addWidget(name)
        if item.category:
            category = QLabel(item.category)
            category.setObjectName("badge")
            header.addWidget(category)
        if item.service_name:
            service = QLabel(f"服务 · {item.service_name}")
            service.setObjectName("serviceBadge")
            header.addWidget(service)
        header.addStretch()
        status = QLabel(item.status)
        status.setObjectName("metaLabel")
        header.addWidget(status)
        layout.addLayout(header)

        grid = QGridLayout()
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(6)
        self._add_field(grid, 0, 0, "协议", item.protocol)
        self._add_field(grid, 0, 1, "端口", str(item.port))
        self._add_field(grid, 1, 0, "PID", str(item.pid))
        self._add_field(grid, 1, 1, "状态", item.status)
        layout.addLayout(grid)

        path = item.executable_path or "暂无权限读取程序路径"
        path_label = QLabel(path)
        path_label.setObjectName("pathLabel")
        path_label.setWordWrap(True)
        path_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(path_label)

        actions = QHBoxLayout()
        actions.setSpacing(6)
        pid_button = self._small_button("复制 PID", "copy")
        pid_button.clicked.connect(lambda: self.copy_pid.emit(item.pid))
        actions.addWidget(pid_button)
        if item.executable_path:
            path_button = self._small_button("复制路径", "clipboard")
            path_button.clicked.connect(lambda: self.copy_path.emit(item.executable_path or ""))
            actions.addWidget(path_button)
            directory = os.path.dirname(item.executable_path)
            open_button = self._small_button("打开目录", "folder-open")
            open_button.clicked.connect(lambda: self.open_directory.emit(directory))
            actions.addWidget(open_button)
        actions.addStretch()
        kill_button = QPushButton("结束进程并释放端口")
        kill_button.setIcon(lucide_icon("zap", 15, "#FF7B72"))
        kill_button.setObjectName("dangerButton")
        kill_button.setEnabled(not protected)
        kill_button.clicked.connect(lambda: self.terminate.emit(item))
        actions.addWidget(kill_button)
        force_button = QPushButton("强制释放端口")
        force_button.setIcon(lucide_icon("triangle-alert", 15, "#FF7B72"))
        force_button.setObjectName("forceButton")
        force_button.setEnabled(not protected)
        force_button.setToolTip("立即终止该进程并重新验证端口")
        force_button.clicked.connect(lambda: self.force_terminate.emit(item))
        actions.addWidget(force_button)
        layout.addLayout(actions)

        if protected:
            protected_label = QLabel("这是 Windows 关键系统进程，PortKill 已保护该进程")
            protected_label.setObjectName("protectedBadge")
            layout.addWidget(protected_label)

    @staticmethod
    def _add_field(grid: QGridLayout, row: int, column: int, title: str, value: str) -> None:
        cell = QVBoxLayout()
        cell.setSpacing(1)
        title_label = QLabel(title)
        title_label.setObjectName("metaLabel")
        value_label = QLabel(value)
        value_label.setObjectName("valueLabel")
        cell.addWidget(title_label)
        cell.addWidget(value_label)
        grid.addLayout(cell, row, column)

    @staticmethod
    def _small_button(text: str, icon: str) -> QPushButton:
        button = QPushButton(text)
        button.setIcon(lucide_icon(icon, 14, "#8B949E"))
        return button

