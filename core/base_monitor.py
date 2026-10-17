from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, QPoint, QRect
from PyQt6.QtGui import QPainter, QPen, QColor
from assets.theme import get_monitor_stylesheet, TEXT_PRIMARY
import json
import os

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(_PROJECT_ROOT, "config.json")

class BaseMonitor(QWidget):
    def __init__(self, parent=None, monitor_id="default"):
        super().__init__(parent)
        self.monitor_id = monitor_id
        self.setObjectName(self.monitor_id)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(280, 180)
        self.setStyleSheet(get_monitor_stylesheet())
        self.is_locked = False
        self.position_loaded = False
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        
        self._drag_pos = QPoint()
        self._dragging = False

    def toggle_lock(self):
        self.is_locked = not self.is_locked
        if hasattr(self, 'lock_btn'):
            self.lock_btn.setText("🔒" if self.is_locked else "🔓")
            self.lock_btn.setStyleSheet(f"background: transparent; color: {'#FAFAFA' if self.is_locked else '#8A8A8A'}; font-size: 12px; border: none;")
        self.update_border()
        self.save_all_positions()

    def update_border(self):
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.is_locked:
            return
        painter = QPainter(self)
        pen = QPen(QColor(TEXT_PRIMARY))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(self.rect().adjusted(1, 1, -1, -1))

    def _sibling_monitors(self):
        parent = self.parent()
        if parent is None:
            return []
        return [
            w for w in parent.findChildren(BaseMonitor)
            if w is not self and w.parent() is parent
        ]

    @staticmethod
    def monitors_in(root):
        if root is None:
            return []
        return [w for w in root.findChildren(BaseMonitor) if w.parent() is root]

    def _constrain_to_parent(self, pos: QPoint) -> QPoint:
        parent = self.parent()
        if parent is None:
            return pos
        max_x = max(0, parent.width() - self.width())
        max_y = max(0, parent.height() - self.height())
        return QPoint(max(0, min(pos.x(), max_x)), max(0, min(pos.y(), max_y)))

    def _avoid_overlaps(self, pos: QPoint) -> QPoint:
        """Push pos so this monitor does not overlap sibling monitors."""
        for _ in range(16):
            proposed = QRect(pos.x(), pos.y(), self.width(), self.height())
            collided = False
            for sibling in self._sibling_monitors():
                other = sibling.geometry()
                if not proposed.intersects(other):
                    continue
                collided = True
                inter = proposed.intersected(other)
                if inter.width() <= inter.height():
                    if proposed.center().x() <= other.center().x():
                        pos.setX(other.x() - self.width())
                    else:
                        pos.setX(other.x() + other.width())
                else:
                    if proposed.center().y() <= other.center().y():
                        pos.setY(other.y() - self.height())
                    else:
                        pos.setY(other.y() + other.height())
                pos = self._constrain_to_parent(pos)
                break
            if not collided:
                return pos

        proposed = QRect(pos.x(), pos.y(), self.width(), self.height())
        for sibling in self._sibling_monitors():
            if proposed.intersects(sibling.geometry()):
                return QPoint(self.x(), self.y())
        return pos

    @classmethod
    def save_all(cls, root):
        """Write every monitor container under root into config.json."""
        try:
            config = {}
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, "r") as f:
                    config = json.load(f)

            monitors = {}
            for monitor in cls.monitors_in(root):
                monitors[monitor.monitor_id] = monitor.to_config()

            config["monitors"] = monitors
            # Drop legacy single-monitor keys
            for legacy in ("internet_monitor", "clock_monitor", "default"):
                config.pop(legacy, None)

            with open(CONFIG_PATH, "w") as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"Error saving positions: {e}")

    def to_config(self):
        return {
            "x": self.x(),
            "y": self.y(),
            "locked": self.is_locked,
        }

    def apply_config(self, data):
        if "x" in data and "y" in data:
            resolved = self._avoid_overlaps(
                self._constrain_to_parent(QPoint(data["x"], data["y"]))
            )
            self.move(resolved)
            self.position_loaded = True
        if "locked" in data:
            self.is_locked = data["locked"]
            if hasattr(self, 'lock_btn'):
                self.lock_btn.setText("🔒" if self.is_locked else "🔓")
                self.lock_btn.setStyleSheet(
                    f"background: transparent; color: {'#FAFAFA' if self.is_locked else '#8A8A8A'}; "
                    f"font-size: 12px; border: none;"
                )
        self.update_border()

    def save_all_positions(self):
        self.save_all(self.parent())

    def load_position(self):
        try:
            if not os.path.exists(CONFIG_PATH):
                return
            with open(CONFIG_PATH, "r") as f:
                config = json.load(f)

            data = None
            if "monitors" in config and self.monitor_id in config["monitors"]:
                data = config["monitors"][self.monitor_id]
            elif self.monitor_id in config:
                data = config[self.monitor_id]

            if data:
                self.apply_config(data)
        except Exception as e:
            print(f"Error loading position: {e}")

    def mousePressEvent(self, event):
        if self.is_locked:
            return
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self.is_locked or not self._dragging:
            return
        if event.buttons() == Qt.MouseButton.LeftButton:
            new_pos = event.globalPosition().toPoint() - self._drag_pos
            new_pos = self._constrain_to_parent(new_pos)
            new_pos = self._avoid_overlaps(new_pos)
            self.move(new_pos)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._dragging:
            self._dragging = False
            self.save_all_positions()
