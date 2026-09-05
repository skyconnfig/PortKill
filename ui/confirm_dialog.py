from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QVBoxLayout


class ConfirmDialog(QDialog):
    def __init__(
        self,
        process_name: str,
        pid: int,
        port: int,
        *,
        force: bool = False,
        retry_prompt: bool = False,
    ) -> None:
        super().__init__()
        self.setWindowTitle("确认强制结束" if force else "确认结束进程")
        self.setMinimumWidth(390)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 20)
        layout.setSpacing(12)

        if retry_prompt:
            title_text = "进程没有正常退出。"
            detail_text = f"端口 {port} 仍被占用，是否强制结束？"
        elif force:
            title_text = f"确定要强制结束 {process_name} 吗？"
            detail_text = f"强制结束会立即终止该进程，端口 {port} 将被释放。"
        else:
            title_text = f"确定要结束 {process_name} 吗？"
            detail_text = f"结束该进程后端口 {port} 将被释放。"
        title = QLabel(title_text)
        title.setStyleSheet("font-size: 16px; font-weight: 700;")
        layout.addWidget(title)

        message = QLabel(f"PID：{pid}\n\n{detail_text}")
        message.setWordWrap(True)
        message.setStyleSheet("color: #8B949E; line-height: 1.4;")
        layout.addWidget(message)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
        action = buttons.addButton(
            "强制结束" if force else "确认结束", QDialogButtonBox.ButtonRole.AcceptRole
        )
        if force:
            action.setObjectName("dangerButton")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons, alignment=Qt.AlignmentFlag.AlignRight)

