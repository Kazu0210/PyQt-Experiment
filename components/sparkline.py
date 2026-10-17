from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QPen, QColor
from assets.theme import TEXT_SECONDARY, GOOD, WARN, BAD

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

from PyQt6.QtCore import QPoint # Fixed missing import
