from PyQt6.QtWidgets import QLabel, QVBoxLayout, QPushButton, QWidget
from PyQt6.QtCore import Qt, QTimer
from core.base_monitor import BaseMonitor
from assets.theme import TEXT_PRIMARY

class ClockMonitor(BaseMonitor):
    def __init__(self, parent=None, monitor_id="clock"):
        super().__init__(parent, monitor_id=monitor_id)
        
        # UI Layout
        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.time_label = QLabel("--:--:--")
        self.time_label.setObjectName("ValueLabel")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Adding a lock button consistent with InternetMonitor
        top_row = QVBoxLayout() 
        # We use a small layout to keep the clock centered but button accessible
        # Alternatively, we can just put the button at the top right
        self.lock_btn = QPushButton("🔓")
        self.lock_btn.setFixedSize(24, 24)
        self.lock_btn.setStyleSheet("background: transparent; color: #8A8A8A; font-size: 12px; border: none;")
        self.lock_btn.clicked.connect(self.toggle_lock)
        
        # To keep the clock centered, we place the lock button absolutely or in a corner
        self.lock_btn.setParent(self)
        self.lock_btn.move(250, 5)

        self.layout.addWidget(self.time_label)
        
        # Timer for clock updates
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)
        
        self.update_time()

    def update_time(self):
        from datetime import datetime
        now = datetime.now().strftime("%H:%M:%S")
        self.time_label.setText(now)
