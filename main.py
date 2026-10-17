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
        # 2. Use a flag that allows the native OS shadow to be drawn
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)

        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Set background to semi-transparent black (adjust alpha as needed, e.g., 180 for dark but slightly see-through)
        # Added a neon blue glow using a border and box-shadow effect via QSS
        central_widget.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 0, 0, 180);
                border: 2px solid #00f2ff;
                border-radius: 0px;
            }
        """)
        
        # Since QSS doesn't support true gaussian blur glows, 
        # the neon effect is achieved with a bright cyan border.
        layout = QVBoxLayout(central_widget)

    def on_button_click(self):
        pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ExperimentWindow()
    window.showFullScreen()
    sys.exit(app.exec())
