from PyQt6.QtWidgets import QLabel, QVBoxLayout, QPushButton, QWidget
from PyQt6.QtCore import Qt, QTimer
from core.base_monitor import BaseMonitor
from assets.theme import TEXT_PRIMARY

class ClockMonitor(BaseMonitor):
    def __init__(self, parent=None, monitor_id="clock"):
        super().__init__(parent, monitor_id=monitor_id)
        
        self.use_24hr = True
        
        # UI Layout
        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.time_label = QLabel("--:--:--")
        self.time_label.setObjectName("ValueLabel")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Lock button
        self.lock_btn = QPushButton("🔓")
        self.lock_btn.setFixedSize(24, 24)
        self.lock_btn.setStyleSheet("background: transparent; color: #8A8A8A; font-size: 12px; border: none;")
        self.lock_btn.clicked.connect(self.toggle_lock)
        self.lock_btn.setParent(self)
        self.lock_btn.move(250, 5)

        # Format Toggle Button
        self.format_btn = QPushButton("24H")
        self.format_btn.setFixedSize(40, 20)
        self.format_btn.setStyleSheet("background: transparent; color: #8A8A8A; font-size: 9px; border: 1px solid #444; border-radius: 4px;")
        self.format_btn.clicked.connect(self.toggle_format)
        self.format_btn.setParent(self)
        self.format_btn.move(200, 5)

        self.layout.addWidget(self.time_label)
        
        # Timer for clock updates
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)
        
        self.update_time()

    def toggle_format(self):
        self.use_24hr = not self.use_24hr
        self.format_btn.setText("24H" if self.use_24hr else "12H")
        self.update_time()
        self.save_all_positions()

    def to_config(self):
        data = super().to_config()
        data["use_24hr"] = self.use_24hr
        return data

    def apply_config(self, data):
        super().apply_config(data)
        if "use_24hr" in data:
            self.use_24hr = bool(data["use_24hr"])
            self.format_btn.setText("24H" if self.use_24hr else "12H")
            self.update_time()

    def update_time(self):
        from datetime import datetime
        now = datetime.now()
        if self.use_24hr:
            time_str = now.strftime("%H:%M:%S")
        else:
            time_str = now.strftime("%I:%M:%S %p")
        self.time_label.setText(time_str)
