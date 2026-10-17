import sys
import socket
import time
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QFrame)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QPoint, QTimer
from PyQt6.QtGui import QPainter, QPen, QColor
import theme_monitor as theme

class Sparkline(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.samples = []
        self.current_color = theme.TEXT_SECONDARY
        self.setMinimumHeight(30)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def add_sample(self, value, state):
        self.samples.append(value)
        if len(self.samples) > 60:
            self.samples.pop(0)
        
        color_map = {"good": theme.GOOD, "warn": theme.WARN, "bad": theme.BAD}
        self.current_color = color_map.get(state, theme.TEXT_SECONDARY)
        self.update()

    def paintEvent(self, event):
        if len(self.samples) < 2:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        pen = QPen(QColor(self.current_color))
        pen.setWidthF(1.5)
        painter.setPen(pen)
        
        w = self.width()
        h = self.height()
        
        max_val = max(self.samples) if max(self.samples) > 0 else 1
        min_val = min(self.samples)
        rng = max_val - min_val if max_val != min_val else 1
        
        n = len(self.samples) - 1
        points = []
        for i, val in enumerate(self.samples):
            x = (i / n) * (w - 1)
            y = h - 1 - ((val - min_val) / rng * (h - 2))
            points.append(QPoint(int(x), int(y)))
            
        for i in range(len(points) - 1):
            painter.drawLine(points[i], points[i+1])

class NetworkWorker(QThread):
    status_updated = pyqtSignal(bool, float, str)

    def run(self):
        while True:
            online, ping = self.check_internet()
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.status_updated.emit(online, ping, timestamp)
            self.msleep(1000)

    def check_internet(self):
        start_time = time.time()
        for host, port in theme.TARGET_HOSTS if hasattr(theme, 'TARGET_HOSTS') else [("8.8.8.8", 53)]:
            try:
                socket.setdefaulttimeout(2)
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((host, port))
                    ping = (time.time() - start_time) * 1000
                    return True, ping
            except:
                continue
        return False, 999.0

class InstrumentPanel(QWidget):
    def __init__(self):
        super().__init__()
        theme.load_fonts()
        self.initUI()
        
        self.worker = NetworkWorker()
        self.worker.status_updated.connect(self.update_metrics)
        self.worker.start()
        
        self._drag_pos = QPoint()

    def initUI(self):
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(240, 168)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.root = QFrame()
        self.root.setObjectName("root")
        # Make the internal monitor panel background transparent to blend with main window
        self.root.setStyleSheet("background: transparent; border: none;")
        outer.addWidget(self.root)

        layout = QVBoxLayout(self.root)
        layout.setContentsMargins(16, 12, 12, 14)
        layout.setSpacing(10)

        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(8)

        self.dot = QLabel()
        self.dot.setObjectName("StatusDot")
        self.dot.setFixedSize(10, 10)

        conn_label = QLabel("CONNECTION")

        top_row.addWidget(self.dot, 0, Qt.AlignmentFlag.AlignVCenter)
        top_row.addWidget(conn_label, 0, Qt.AlignmentFlag.AlignVCenter)
        top_row.addStretch()

        self.close_btn = QPushButton("×")
        self.close_btn.setObjectName("CloseBtn")
        self.close_btn.setFixedSize(20, 20)
        self.close_btn.clicked.connect(self.close)
        top_row.addWidget(self.close_btn, 0, Qt.AlignmentFlag.AlignTop)

        layout.addLayout(top_row)

        metrics_row = QHBoxLayout()
        metrics_row.setContentsMargins(0, 0, 0, 0)
        metrics_row.setSpacing(12)

        self.ping_val = self.create_metric_block("PING", metrics_row)
        self.down_val = self.create_metric_block("DOWN", metrics_row)
        self.up_val = self.create_metric_block("UP", metrics_row)

        layout.addLayout(metrics_row)

        self.spark = Sparkline()
        self.spark.setMinimumHeight(36)
        layout.addWidget(self.spark)

        self.setStyleSheet(theme.build_stylesheet())

    def create_metric_block(self, label_text, layout):
        block = QWidget()
        l = QVBoxLayout(block)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(2)

        lbl = QLabel(label_text)
        val = QLabel("--")
        val.setObjectName("ValueLabel")

        l.addWidget(lbl)
        l.addWidget(val)
        layout.addWidget(block, 1)
        return val

    def update_metrics(self, online, ping, timestamp):
        if not online:
            state = "bad"
        elif ping < theme.PING_GOOD:
            state = "good"
        elif ping < theme.PING_WARN:
            state = "warn"
        else:
            state = "bad"

        for widget in [self.dot, self.ping_val]:
            widget.setProperty("state", state)
            self.style().unpolish(widget)
            self.style().polish(widget)

        self.ping_val.setText(f"{int(ping)}ms")
        self.down_val.setText("12.4")
        self.up_val.setText("2.1")
        
        self.spark.add_sample(ping, state)
        
        if hasattr(self, 'last_state') and self.last_state != state:
            self.pulse_dot()
        self.last_state = state

    def pulse_dot(self):
        self.dot.setFixedSize(14, 14)
        QTimer.singleShot(200, lambda: self.dot.setFixedSize(10, 10))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

if __name__ == "__main__":
    theme.TARGET_HOSTS = [("8.8.8.8", 53), ("1.1.1.1", 53)]
    app = QApplication(sys.argv)
    window = InstrumentPanel()
    window.show()
    sys.exit(app.exec())
