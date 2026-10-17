from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, QPoint
from assets.theme import get_monitor_stylesheet
import json
import os

CONFIG_PATH = "config.json"

class BaseMonitor(QWidget):
    def __init__(self, parent=None, monitor_id="default"):
        super().__init__(parent)
        self.monitor_id = monitor_id
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(280, 180)
        self.setStyleSheet(get_monitor_stylesheet())
        self.is_locked = False
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        
        self._drag_pos = QPoint()

    def toggle_lock(self):
        self.is_locked = not self.is_locked
        if hasattr(self, 'lock_btn'):
            self.lock_btn.setText("🔒" if self.is_locked else "🔓")
            self.lock_btn.setStyleSheet(f"background: transparent; color: {'#FAFAFA' if self.is_locked else '#8A8A8A'}; font-size: 12px; border: none;")
        self.save_position()

    def save_position(self):
        try:
            config = {}
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, "r") as f:
                    config = json.load(f)
            
            if "monitors" not in config:
                config["monitors"] = {}
                
            config["monitors"][self.monitor_id] = {
                "x": self.x(),
                "y": self.y(),
                "locked": self.is_locked
            }
            
            with open(CONFIG_PATH, "w") as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"Error saving position: {e}")

    def load_position(self):
        try:
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, "r") as f:
                    config = json.load(f)
                
                # Support both old and new JSON formats
                pos = None
                if "monitors" in config and self.monitor_id in config["monitors"]:
                    pos = config["monitors"][self.monitor_id]
                elif self.monitor_id in config:
                    pos = config[self.monitor_id]
                
                if pos:
                    self.move(pos["x"], pos["y"])
                    if "locked" in pos:
                        self.is_locked = pos["locked"]
                        if hasattr(self, 'lock_btn'):
                            self.lock_btn.setText("🔒" if self.is_locked else "🔓")
                            self.lock_btn.setStyleSheet(f"background: transparent; color: {'#FAFAFA' if self.is_locked else '#8A8A8A'}; font-size: 12px; border: none;")
        except Exception as e:
            print(f"Error loading position: {e}")

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
            elif new_pos.x() > (self.parent().width() - self.width()) if self.parent() else 0:
                new_pos.setX(self.parent().width() - self.width())
                
            # Constrain Y axis
            if new_pos.y() < 0:
                new_pos.setY(0)
            elif new_pos.y() > (self.parent().height() - self.height()) if self.parent() else 0:
                new_pos.setY(self.parent().height() - self.height())
                
            self.move(new_pos)
            self.save_position()
