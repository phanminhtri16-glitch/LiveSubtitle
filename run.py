"""
LiveSubtitle Application Entry Point
Captures system audio loopback and displays live subtitles over any video frame.
"""

import sys
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from src.live_subtitle.gui.main_window import MainWindow
from src.live_subtitle.utils.logger import logger

def main():
    # Enable High DPI pixmaps
    if hasattr(Qt.ApplicationAttribute, "AA_EnableHighDpiScaling"):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    if hasattr(Qt.ApplicationAttribute, "AA_UseHighDpiPixmaps"):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("LiveSubtitle")
    app.setOrganizationName("LiveSubtitle")

    logger.info("Starting LiveSubtitle application...")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
