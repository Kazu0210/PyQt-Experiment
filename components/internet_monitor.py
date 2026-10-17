from PyQt6.QtWidgets import QLabel, QHBoxLayout, QVBoxLayout, QPushButton, QWidget
from PyQt6.QtCore import Qt
from core.base_monitor import BaseMonitor
from components.sparkline import Sparkline

class InternetMonitor(BaseMonitor):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # UI Layout
        self.dot = QLabel()
        self.dot.setObjectName("StatusDot")
        self.dot.setFixedSize(10, 10)
        
        conn_label = QLabel("CONNECTION")
        
        top_row = QHBoxLayout()
        top_row.addWidget(self.dot)
        top_row.addWidget(conn_label)
        top_row.addStretch()
        
        self.lock_btn = QPushButton("🔓")
        self.lock_btn.setFixedSize(24, 24)
        self.lock_btn.setStyleSheet("background: transparent; color: #8A8A8A; font-size: 12px; border: none;")
        self.lock_btn.clicked.connect(self.toggle_lock)
        top_row.addWidget(self.lock_btn)
        
        self.layout.addLayout(top_row)
        
        self.metrics_row = QHBoxLayout()
        self.layout.addLayout(self.metrics_row)
        
        self.ping_val = None 
        self.down_val = None
        self.up_val = None
        
        self.spark = Sparkline()
        self.layout.addWidget(self.spark)

    def setup_metrics(self, ping_text, down_text, up_text):
        self.ping_val = self.create_metric(ping_text)
        self.down_val = self.create_metric(down_text)
        self.up_val = self.create_metric(up_text)

    def create_metric(self, text):
        block = QWidget()
        l = QVBoxLayout(block)
        l.setContentsMargins(0, 0, 0, 0)
        lbl = QLabel(text)
        val = QLabel("--")
        val.setObjectName("ValueLabel")
        l.addWidget(lbl)
        l.addWidget(val)
        self.metrics_row.addWidget(block, 1)
        return val
