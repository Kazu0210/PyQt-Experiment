import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
from PyQt6.QtCore import Qt, QPoint, QTimer

from assets.theme import load_fonts, NEON_BLUE, PING_GOOD, PING_WARN
from core.base_monitor import BaseMonitor
from core.network_worker import NetworkWorker
from components.internet_monitor import InternetMonitor
from components.clock_monitor import ClockMonitor
from components.devices_monitor import DevicesMonitor
from core.device_worker import DeviceWorker

class IntegratedExperiment(QMainWindow):
    def __init__(self):
        super().__init__()
        load_fonts()
        self.setWindowTitle("Pulse Integrated Experiment")
        self._layout_restored = False
        
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)

        self.shell = QWidget()
        self.setCentralWidget(self.shell)
        self.shell.setStyleSheet(f"background-color: rgba(0, 0, 0, 180); border: 2px solid {NEON_BLUE};")
        
        self.main_layout = QVBoxLayout(self.shell)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.internet_monitor = InternetMonitor(parent=self.shell, monitor_id="internet")
        self.internet_monitor.setup_metrics("PING", "DOWN", "UP")

        self.clock_monitor = ClockMonitor(parent=self.shell, monitor_id="clock")

        self.devices_monitor = DevicesMonitor(parent=self.shell, monitor_id="devices")

        self.worker = NetworkWorker()
        self.worker.status_updated.connect(self.update_metrics)
        self.worker.start()

        self.device_worker = DeviceWorker()
        self.device_worker.devices_updated.connect(self.devices_monitor.update_devices)
        self.device_worker.start()

    def showEvent(self, event):
        super().showEvent(event)
        if not self._layout_restored:
            # Wait until the fullscreen shell has a real size before loading/saving.
            QTimer.singleShot(0, self.restore_monitor_layout)

    def restore_monitor_layout(self):
        if self._layout_restored:
            return
        self._layout_restored = True

        placements = (
            (self.internet_monitor, 0),
            (self.clock_monitor, 200),
            (self.devices_monitor, 400),
        )
        for monitor, y_offset in placements:
            monitor.load_position()
            if not monitor.position_loaded:
                pos = QPoint(
                    (self.shell.width() - monitor.width()) // 2,
                    (self.shell.height() - monitor.height()) // 2 + y_offset,
                )
                monitor.move(monitor._avoid_overlaps(pos))

        BaseMonitor.save_all(self.shell)

    def closeEvent(self, event):
        BaseMonitor.save_all(self.shell)
        self.device_worker.stop()
        if not self.device_worker.wait(1500):
            self.device_worker.terminate()
            self.device_worker.wait(500)
        self.worker.terminate()
        self.worker.wait(500)
        event.accept()

    def update_metrics(self, online, ping, timestamp):
        state = "good" if online and ping < PING_GOOD else "warn" if online and ping < PING_WARN else "bad"
        
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
