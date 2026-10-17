import sys
import socket
import time
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QFrame)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QPoint, QTimer
from PyQt6.QtGui import QPainter, QPen, QColor, QFontDatabase

# --- THEME CONFIGURATION ---
BG = "#0A0A0A"
SURFACE = "#141414"
BORDER = "#262626"
TEXT_PRIMARY = "#FAFAFA"
TEXT_SECONDARY = "#8A8A8A"
GOOD = "#22C55E"
WARN = "#F59E0B"
BAD = "#EF4444"
NEON_BLUE = "#00f2ff"

PING_GOOD = 80
PING_WARN = 200
TARGET_HOSTS = [("8.8.8.8", 53), ("1.1.1.1", 53)]

def load_fonts():
    fonts = {
        "Inter": "H:\\InternetMonitor\\assets\\fonts\\Inter-Regular.ttf",
        "IBM Plex Mono": "H:\\InternetMonitor\\assets\\fonts\\IBMPlexMono-Regular.ttf"
    }
    for family, path in fonts.items():
        try:
            QFontDatabase.addApplicationFont(path)
        except:
            pass

def get_monitor_stylesheet():
    return f"""
        QWidget {{
            border: none;
            background: transparent;
        }}
        QLabel {{
            color: {TEXT_SECONDARY};
            font-family: 'Inter', 'Segoe UI', sans-serif;
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
            border: none;
        }}
        QLabel#ValueLabel {{
            color: {TEXT_PRIMARY};
            font-family: 'IBM Plex Mono', 'Consolas', monospace;
            font-size: 20px;
            font-weight: 600;
            text-transform: none;
            letter-spacing: 0;
            border: none;
        }}
        QLabel#StatusDot {{
            background-color: {TEXT_SECONDARY};
            border-radius: 5px;
            min-width: 10px;
            max-width: 10px;
            min-height: 10px;
            max-height: 10px;
            border: none;
        }}
        QLabel#StatusDot[state="good"] {{ background-color: {GOOD}; }}
        QLabel#StatusDot[state="warn"] {{ background-color: {WARN}; }}
        QLabel#StatusDot[state="bad"] {{ background-color: {BAD}; }}
        QLabel#ValueLabel[state="good"] {{ color: {GOOD}; }}
        QLabel#ValueLabel[state="warn"] {{ color: {WARN}; }}
        QLabel#ValueLabel[state="bad"] {{ color: {BAD}; }}
    """

# --- COMPONENTS ---

class DraggableMonitor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(280, 180)
        self.setStyleSheet(get_monitor_stylesheet())
        self.is_locked = False
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        
        # UI Elements will be accessed by the main window
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
        
        metrics_row = QHBoxLayout()
        # These will be created and assigned by the main window's helper
        self.ping_val = None 
        self.down_val = None
        self.up_val = None
        self.layout.addLayout(metrics_row)
        self.metrics_row = metrics_row
        
        self.spark = Sparkline()
        self.layout.addWidget(self.spark)
        
        self._drag_pos = QPoint()

    def toggle_lock(self):
        self.is_locked = not self.is_locked
        self.lock_btn.setText("🔒" if self.is_locked else "🔓")
        self.lock_btn.setStyleSheet(f"background: transparent; color: {'#FAFAFA' if self.is_locked else '#8A8A8A'}; font-size: 12px; border: none;")

    def mousePressEvent(self, event):
        if self.is_locked:
            return
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self.is_locked:
            return
        if event.buttons() == Qt.MouseButton.LeftButton:
            new_pos = event.globalPosition().toPoint() - self._drag_pos
            
            # Constrain X axis
            if new_pos.x() < 0:
                new_pos.setX(0)
            elif new_pos.x() > self.parent().width() - self.width():
                new_pos.setX(self.parent().width() - self.width())
                
            # Constrain Y axis
            if new_pos.y() < 0:
                new_pos.setY(0)
            elif new_pos.y() > self.parent().height() - self.height():
                new_pos.setY(self.parent().height() - self.height())
                
            self.move(new_pos)

class Sparkline(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.samples = []
        self.current_color = TEXT_SECONDARY
        self.setMinimumHeight(30)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def add_sample(self, value, state):
        self.samples.append(value)
        if len(self.samples) > 60:
            self.samples.pop(0)
        color_map = {"good": GOOD, "warn": WARN, "bad": BAD}
        self.current_color = color_map.get(state, TEXT_SECONDARY)
        self.update()

    def paintEvent(self, event):
        if len(self.samples) < 2: return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor(self.current_color))
        pen.setWidthF(1.5)
        painter.setPen(pen)
        w, h = self.width(), self.height()
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
            self.status_updated.emit(online, ping, datetime.now().strftime("%H:%M:%S"))
            self.msleep(1000)
    def check_internet(self):
        start_time = time.time()
        for host, port in TARGET_HOSTS:
            try:
                socket.setdefaulttimeout(2)
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((host, port))
                    return True, (time.time() - start_time) * 1000
            except: continue
        return False, 999.0

# --- MAIN WINDOW ---

class IntegratedExperiment(QMainWindow):
    def __init__(self):
        super().__init__()
        load_fonts()
        self.setWindowTitle("Pulse Integrated Experiment")
        
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)

        self.shell = QWidget()
        self.setCentralWidget(self.shell)
        self.shell.setStyleSheet(f"background-color: rgba(0, 0, 0, 180); border: 2px solid {NEON_BLUE};")
        
        self.main_layout = QVBoxLayout(self.shell)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.monitor_container = DraggableMonitor()
        self.monitor_container.setParent(self.shell)
        
        # Create the metric blocks manually since they are inside the DraggableMonitor
        self.monitor_container.ping_val = self.create_monitor_metric("PING", self.monitor_container.metrics_row)
        self.monitor_container.down_val = self.create_monitor_metric("DOWN", self.monitor_container.metrics_row)
        self.monitor_container.up_val = self.create_monitor_metric("UP", self.monitor_container.metrics_row)

        # Position it initially in the center
        self.monitor_container.move(
            (self.shell.width() - self.monitor_container.width()) // 2,
            (self.shell.height() - self.monitor_container.height()) // 2
        )

        self.worker = NetworkWorker()
        self.worker.status_updated.connect(self.update_metrics)
        self.worker.start()

    def create_monitor_metric(self, text, layout):
        block = QWidget()
        l = QVBoxLayout(block)
        l.setContentsMargins(0, 0, 0, 0)
        lbl = QLabel(text)
        val = QLabel("--")
        val.setObjectName("ValueLabel")
        l.addWidget(lbl)
        l.addWidget(val)
        layout.addWidget(block, 1)
        return val

    def create_metric(self, text, layout):
        block = QWidget()
        l = QVBoxLayout(block)
        l.setContentsMargins(0, 0, 0, 0)
        lbl = QLabel(text)
        val = QLabel("--")
        val.setObjectName("ValueLabel")
        l.addWidget(lbl)
        l.addWidget(val)
        layout.addWidget(block, 1)
        return val

    def update_metrics(self, online, ping, timestamp):
        state = "good" if online and ping < PING_GOOD else "warn" if online and ping < PING_WARN else "bad"
        
        # Update the dot and ping label inside the draggable monitor
        for w in [self.monitor_container.dot, self.monitor_container.ping_val]:
            if w:
                w.setProperty("state", state)
                w.style().unpolish(w)
                w.style().polish(w)
        
        if self.monitor_container.ping_val:
            self.monitor_container.ping_val.setText(f"{int(ping)}ms")
        if self.monitor_container.down_val:
            self.monitor_container.down_val.setText("12.4")
        if self.monitor_container.up_val:
            self.monitor_container.up_val.setText("2.1")
            
        self.monitor_container.spark.add_sample(ping, state)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = IntegratedExperiment()
    window.showFullScreen()
    sys.exit(app.exec())
