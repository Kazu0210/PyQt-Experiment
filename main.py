import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton
from PyQt6.QtCore import Qt, QPoint, QTimer, QEvent
from PyQt6.QtGui import QShortcut, QKeySequence

from assets.theme import load_fonts, NEON_BLUE, PING_GOOD, PING_WARN
from core.base_monitor import BaseMonitor
from core.network_worker import NetworkWorker
from components.internet_monitor import InternetMonitor
from components.clock_monitor import ClockMonitor
from components.devices_monitor import DevicesMonitor
from components.lock_screen import LockScreen
from core.device_worker import DeviceWorker
from core.session_guard import SessionGuard

class IntegratedExperiment(QMainWindow):
    def __init__(self):
        super().__init__()
        load_fonts()
        self.setWindowTitle("Pulse Integrated Experiment")
        self._layout_restored = False
        
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Window
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self._guard = SessionGuard()
        self._guard.set_enabled(True)
        self._focus_timer = QTimer(self)
        self._focus_timer.setInterval(200)
        self._focus_timer.timeout.connect(self._reclaim_foreground)
        self._focus_timer.start()

        self.shell = QWidget()
        self.setCentralWidget(self.shell)
        self.shell.setStyleSheet(f"background-color: rgba(0, 0, 0, 180); border: 2px solid {NEON_BLUE};")
        
        self.main_layout = QVBoxLayout(self.shell)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.internet_monitor = InternetMonitor(parent=self.shell, monitor_id="internet")
        self.internet_monitor.setup_metrics("PING", "DOWN", "UP")

        self.clock_monitor = ClockMonitor(parent=self.shell, monitor_id="clock")

        self.devices_monitor = DevicesMonitor(parent=self.shell, monitor_id="devices")

        self._locked = True
        self.lock_screen = LockScreen(parent=self.shell)
        self.lock_screen.unlocked.connect(self.unlock_app)

        self.lock_button = QPushButton("LOCK", self.shell)
        self.lock_button.setFixedSize(72, 28)
        self.lock_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.lock_button.setStyleSheet(
            f"QPushButton {{ background: rgba(10, 10, 10, 200); color: {NEON_BLUE}; "
            f"border: 1px solid {NEON_BLUE}; border-radius: 4px; "
            f"font-family: 'Inter', 'Segoe UI', sans-serif; font-size: 11px; letter-spacing: 2px; }}"
            f"QPushButton:hover {{ background: rgba(0, 242, 255, 40); }}"
        )
        self.lock_button.clicked.connect(self.lock_app)
        self.lock_button.hide()
        self.lock_screen.hide_prompt()
        self._forwarding_key = False
        QApplication.instance().installEventFilter(self)

        QShortcut(QKeySequence("Ctrl+L"), self, self.lock_app)

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
        self._position_lock_controls()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._position_lock_controls()

    def _position_lock_controls(self):
        self.lock_screen.setGeometry(self.shell.rect())
        margin = 16
        self.lock_button.move(
            max(0, self.shell.width() - self.lock_button.width() - margin),
            margin,
        )
        if self._locked:
            self.lock_screen.raise_()
        else:
            self.lock_button.raise_()

    def eventFilter(self, obj, event):
        if self._forwarding_key:
            return super().eventFilter(obj, event)
        if self._locked and event.type() == QEvent.Type.KeyPress and not event.isAutoRepeat():
            key = event.key()
            modifiers = event.modifiers()
            alt = bool(modifiers & Qt.KeyboardModifier.AltModifier)
            ctrl = bool(modifiers & Qt.KeyboardModifier.ControlModifier)
            if key in (Qt.Key.Key_Meta, Qt.Key.Key_Super_L, Qt.Key.Key_Super_R):
                return True
            if alt and key in (Qt.Key.Key_Tab, Qt.Key.Key_Backtab, Qt.Key.Key_F4, Qt.Key.Key_Escape, Qt.Key.Key_Space):
                return True
            if ctrl and key == Qt.Key.Key_Escape:
                return True
            if not self.lock_screen.is_prompt_visible():
                if event.key() not in (
                    Qt.Key.Key_Shift,
                    Qt.Key.Key_Control,
                    Qt.Key.Key_Alt,
                    Qt.Key.Key_Meta,
                    Qt.Key.Key_AltGr,
                ):
                    self.lock_screen.show_prompt()
                    return True
            elif QApplication.focusWidget() is not self.lock_screen.password:
                self.lock_screen.focus_password()
                self._forwarding_key = True
                try:
                    QApplication.sendEvent(self.lock_screen.password, event)
                finally:
                    self._forwarding_key = False
                return True
        return super().eventFilter(obj, event)

    def _set_stay_on_top(self, enabled):
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, enabled)
        self.showFullScreen()

    def _reclaim_foreground(self):
        if not self._locked:
            return
        if self.isMinimized() or not self.isActiveWindow():
            self.setWindowState(Qt.WindowState.WindowFullScreen)
            self.showFullScreen()
            self.raise_()
            self.activateWindow()
            self._guard.force_foreground(int(self.winId()))
            self._position_lock_controls()

    def lock_app(self):
        if self._locked:
            return
        self._locked = True
        self._guard.set_enabled(True)
        self._focus_timer.start()
        self._set_stay_on_top(True)
        self.lock_button.hide()
        self.lock_screen.hide_prompt()
        self.lock_screen.show()
        self.lock_screen.raise_()

    def unlock_app(self):
        self._locked = False
        self._focus_timer.stop()
        self._guard.set_enabled(False)
        self._set_stay_on_top(False)
        self.lock_screen.hide()
        self.lock_button.show()
        self.lock_button.raise_()

    def closeEvent(self, event):
        if self._locked:
            event.ignore()
            self._reclaim_foreground()
            return
        self._focus_timer.stop()
        self._guard.set_enabled(False)
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
