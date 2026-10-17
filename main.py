import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
from PyQt6.QtCore import Qt

from assets.theme import load_fonts, NEON_BLUE, PING_GOOD, PING_WARN
from core.network_worker import NetworkWorker
from components.internet_monitor import InternetMonitor
from components.clock_monitor import ClockMonitor

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

        # Internet Monitor
        self.internet_monitor = InternetMonitor(parent=self.shell, monitor_id="internet")
        self.internet_monitor.setup_metrics("PING", "DOWN", "UP")
        self.internet_monitor.load_position()
        
        if self.internet_monitor.x() == 0 and self.internet_monitor.y() == 0:
            self.internet_monitor.move(
                (self.shell.width() - self.internet_monitor.width()) // 2,
                (self.shell.height() - self.internet_monitor.height()) // 2
            )

        # Clock Monitor
        self.clock_monitor = ClockMonitor(parent=self.shell, monitor_id="clock")
        self.clock_monitor.load_position()
        
        if self.clock_monitor.x() == 0 and self.clock_monitor.y() == 0:
            self.clock_monitor.move(
                (self.shell.width() - self.clock_monitor.width()) // 2,
                (self.shell.height() - self.clock_monitor.height()) // 2 + 200
            )

        self.worker = NetworkWorker()
        self.worker.status_updated.connect(self.update_metrics)
        self.worker.start()

    def update_metrics(self, online, ping, timestamp):
        state = "good" if online and ping < PING_GOOD else "warn" if online and ping < PING_WARN else "bad"
        
        # Update the dot and ping label
        for w in [self.internet_monitor.dot, self.internet_monitor.ping_val]:
            if w:
                w.setProperty("state", state)
                w.style().unpolish(w)
                w.style().polish(w)
        
        if self.internet_monitor.ping_val:
            self.internet_monitor.ping_val.setText(f"{int(ping)}ms")
        if self.internet_monitor.down_val:
            self.internet_monitor.down_val.setText("12.4")
        if self.internet_monitor.up_val:
            self.internet_monitor.up_val.setText("2.1")
            
        self.internet_monitor.spark.add_sample(ping, state)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = IntegratedExperiment()
    window.showFullScreen()
    sys.exit(app.exec())
