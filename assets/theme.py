import os
from PyQt6.QtGui import QFontDatabase

# Design Tokens
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

_ASSETS_DIR = os.path.dirname(os.path.abspath(__file__))
_FONTS_DIR = os.path.join(_ASSETS_DIR, "fonts")

def load_fonts():
    fonts = (
        "Inter-Regular.ttf",
        "IBMPlexMono-Regular.ttf",
    )
    for filename in fonts:
        path = os.path.join(_FONTS_DIR, filename)
        if os.path.isfile(path):
            QFontDatabase.addApplicationFont(path)

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
        QLabel#DeviceLabel {{
            color: {TEXT_PRIMARY};
            font-family: 'IBM Plex Mono', 'Consolas', monospace;
            font-size: 12px;
            font-weight: 500;
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
