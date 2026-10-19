from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from assets.theme import BORDER, NEON_BLUE, SURFACE, TEXT_PRIMARY, TEXT_SECONDARY, BAD
from core.lock_auth import get_password_hash, verify_password


class LockScreen(QWidget):
    unlocked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("LockScreen")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._password_hash = get_password_hash()

        self.setStyleSheet(f"""
            QWidget#LockScreen {{
                background: transparent;
                border: none;
            }}
            QWidget#LockCard {{
                background-color: {SURFACE};
                border: 1px solid {NEON_BLUE};
                border-radius: 8px;
            }}
            QLabel#LockTitle {{
                color: {NEON_BLUE};
                font-family: 'Inter', 'Segoe UI', sans-serif;
                font-size: 18px;
                letter-spacing: 6px;
                border: none;
                background: transparent;
            }}
            QLabel#LockHint {{
                color: {TEXT_SECONDARY};
                font-family: 'Inter', 'Segoe UI', sans-serif;
                font-size: 10px;
                letter-spacing: 2px;
                border: none;
                background: transparent;
            }}
            QLabel#LockError {{
                color: {BAD};
                font-family: 'Inter', 'Segoe UI', sans-serif;
                font-size: 10px;
                letter-spacing: 1px;
                border: none;
                background: transparent;
            }}
            QLineEdit#LockPassword {{
                background: #0A0A0A;
                color: {TEXT_PRIMARY};
                border: 1px solid {BORDER};
                border-radius: 4px;
                padding: 8px 12px;
                font-family: 'IBM Plex Mono', 'Consolas', monospace;
                font-size: 14px;
            }}
            QLineEdit#LockPassword:focus {{
                border: 1px solid {NEON_BLUE};
            }}
            QPushButton#UnlockButton {{
                background: transparent;
                color: {NEON_BLUE};
                border: 1px solid {NEON_BLUE};
                border-radius: 4px;
                padding: 8px 16px;
                font-family: 'Inter', 'Segoe UI', sans-serif;
                font-size: 11px;
                letter-spacing: 2px;
            }}
            QPushButton#UnlockButton:hover {{
                background: rgba(0, 242, 255, 40);
            }}
            QPushButton#CloseButton {{
                background: transparent;
                color: {TEXT_SECONDARY};
                border: none;
                font-size: 16px;
                padding: 0;
            }}
            QPushButton#CloseButton:hover {{
                color: {TEXT_PRIMARY};
            }}
        """)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addStretch()

        row = QHBoxLayout()
        row.addStretch()

        self._card = QWidget()
        self._card.setObjectName("LockCard")
        self._card.setFixedWidth(320)
        card_layout = QVBoxLayout(self._card)
        card_layout.setContentsMargins(28, 16, 28, 28)
        card_layout.setSpacing(12)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        close_btn = QPushButton("×")
        close_btn.setObjectName("CloseButton")
        close_btn.setFixedSize(24, 24)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.hide_prompt)
        header.addStretch()
        header.addWidget(close_btn)

        title = QLabel("LOCKED")
        title.setObjectName("LockTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        hint = QLabel("ENTER PASSWORD")
        hint.setObjectName("LockHint")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.password = QLineEdit()
        self.password.setObjectName("LockPassword")
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.setPlaceholderText("Password")
        self.password.returnPressed.connect(self.try_unlock)
        self.password.textChanged.connect(self._clear_error)

        self.error = QLabel("")
        self.error.setObjectName("LockError")
        self.error.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error.setFixedHeight(16)

        unlock_btn = QPushButton("UNLOCK")
        unlock_btn.setObjectName("UnlockButton")
        unlock_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        unlock_btn.clicked.connect(self.try_unlock)

        card_layout.addLayout(header)
        card_layout.addWidget(title)
        card_layout.addWidget(hint)
        card_layout.addWidget(self.password)
        card_layout.addWidget(self.error)
        card_layout.addWidget(unlock_btn)

        row.addWidget(self._card)
        row.addStretch()
        outer.addLayout(row)
        outer.addStretch()
        self.hide_prompt()

    def is_prompt_visible(self):
        return not self._card.isHidden()

    def show_prompt(self):
        self.reset()
        self._card.show()
        self.focus_password()

    def hide_prompt(self):
        self.reset()
        self._card.hide()

    def reset(self):
        self.password.clear()
        self.error.clear()

    def focus_password(self):
        self.password.setFocus(Qt.FocusReason.OtherFocusReason)

    def _clear_error(self, text):
        if text and self.error.text():
            self.error.clear()

    def try_unlock(self):
        if verify_password(self.password.text(), self._password_hash):
            self.reset()
            self.unlocked.emit()
            return
        self.password.clear()
        self.error.setText("INCORRECT PASSWORD")
        self.focus_password()
