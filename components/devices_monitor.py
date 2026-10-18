from PyQt6.QtWidgets import (
    QLabel,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QScrollArea,
    QWidget,
    QSizePolicy,
)
from PyQt6.QtCore import Qt
from core.base_monitor import BaseMonitor
from assets.theme import TEXT_SECONDARY, NEON_BLUE, GOOD, WARN

_KIND_META = {
    "bluetooth": ("BT", NEON_BLUE),
    "usb_receiver": ("USB RX", WARN),
    "usb": ("USB", GOOD),
}


class DevicesMonitor(BaseMonitor):
    def __init__(self, parent=None, monitor_id="devices"):
        super().__init__(parent, monitor_id=monitor_id)
        self.setFixedSize(300, 240)

        self.dot = QLabel()
        self.dot.setObjectName("StatusDot")
        self.dot.setFixedSize(10, 10)
        self.dot.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        title = QLabel("DEVICES")
        title.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        top_row = QHBoxLayout()
        top_row.addWidget(self.dot)
        top_row.addWidget(title)
        top_row.addStretch()

        self.lock_btn = QPushButton("🔓")
        self.lock_btn.setFixedSize(24, 24)
        self.lock_btn.setStyleSheet(
            "background: transparent; color: #8A8A8A; font-size: 12px; border: none;"
        )
        self.lock_btn.clicked.connect(self.toggle_lock)
        top_row.addWidget(self.lock_btn)
        self.layout.addLayout(top_row)

        count_block = QWidget()
        count_block.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        count_layout = QVBoxLayout(count_block)
        count_layout.setContentsMargins(0, 0, 0, 0)
        count_layout.setSpacing(2)
        count_layout.addWidget(QLabel("CONNECTED"))
        self.count_val = QLabel("0")
        self.count_val.setObjectName("ValueLabel")
        count_layout.addWidget(self.count_val)
        self.layout.addWidget(count_block)

        self.device_list = QVBoxLayout()
        self.device_list.setSpacing(4)
        self.device_list.setContentsMargins(0, 0, 0, 0)

        list_host = QWidget()
        list_host.setLayout(self.device_list)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setStyleSheet(
            "QScrollArea { background: transparent; border: none; }"
            "QScrollBar:vertical { width: 4px; background: transparent; }"
            f"QScrollBar::handle:vertical {{ background: {TEXT_SECONDARY}; border-radius: 2px; }}"
            "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }"
        )
        scroll.setWidget(list_host)
        self.layout.addWidget(scroll, 1)

        self._empty_label = QLabel("No devices")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.device_list.addWidget(self._empty_label)
        self.device_list.addStretch()

        self._device_rows = []

    def _make_row(self, name: str, kind: str) -> QWidget:
        label_text, color = _KIND_META.get(kind, ("USB", GOOD))

        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(8)

        name_label = QLabel(name)
        name_label.setObjectName("DeviceLabel")
        name_label.setWordWrap(False)
        name_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        name_label.setToolTip(name)

        kind_label = QLabel(label_text)
        kind_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        kind_label.setStyleSheet(
            f"color: {color}; font-family: 'Inter', 'Segoe UI', sans-serif;"
            f"font-size: 9px; letter-spacing: 1px; border: 1px solid {color};"
            f"border-radius: 3px; padding: 2px 5px; background: transparent;"
        )
        kind_label.setFixedHeight(18)

        row_layout.addWidget(name_label, 1)
        row_layout.addWidget(kind_label, 0)
        return row

    def update_devices(self, devices):
        devices = list(devices) if devices else []
        self.count_val.setText(str(len(devices)))

        state = "good" if devices else "bad"
        for w in (self.dot, self.count_val):
            w.setProperty("state", state)
            w.style().unpolish(w)
            w.style().polish(w)

        while self._device_rows:
            row = self._device_rows.pop()
            self.device_list.removeWidget(row)
            row.deleteLater()

        self._empty_label.setVisible(not devices)

        for device in devices:
            if isinstance(device, dict):
                name = str(device.get("name") or "").strip()
                kind = str(device.get("kind") or "usb").strip().lower()
            else:
                name = str(device).strip()
                kind = "bluetooth"
            if not name:
                continue
            row = self._make_row(name, kind)
            self.device_list.insertWidget(self.device_list.count() - 1, row)
            self._device_rows.append(row)
