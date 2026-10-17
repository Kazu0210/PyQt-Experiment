import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton
from PyQt6.QtCore import Qt

class ExperimentWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Pulse Experiment Window")
        self.setMinimumSize(400, 300)
        
        # 1. Required for transparency on most OS
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        # 2. Window frames often force an opaque background; remove it to see the effect
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)

        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Set a semi-transparent background color
        central_widget.setStyleSheet("background-color: rgba(0, 0, 0, 50);")
        
        layout = QVBoxLayout(central_widget)

        # Label
        self.label = QLabel("Hello from the PyQt Experiment!", self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(self.label)

    def on_button_click(self):
        pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ExperimentWindow()
    window.setWindowState(Qt.WindowState.WindowMaximized)
    window.show()
    sys.exit(app.exec())
