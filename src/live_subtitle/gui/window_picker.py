from PyQt6.QtCore import QPoint, QRect, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QCursor, QFont, QGuiApplication, QPainter, QPen
from PyQt6.QtWidgets import QWidget
import win32con
import win32gui

from src.live_subtitle.utils.logger import logger

class WindowPicker(QWidget):
    """
    Interactive fullscreen overlay tool that allows the user to hover over
    any application window on screen, highlights it in real time, and selects
    it upon click.
    """

    window_selected = pyqtSignal(int, str, QRect)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self.setCursor(QCursor(Qt.CursorShape.CrossCursor))

        self.hovered_hwnd: int | None = None
        self.hovered_title: str = ""
        self.hovered_rect: QRect | None = None

        self._cover_virtual_desktop()

    def _cover_virtual_desktop(self) -> None:
        """Spans the picker across all available screens."""
        screens = QGuiApplication.screens()
        if not screens:
            self.setGeometry(0, 0, 1920, 1080)
            return

        combined_rect = QRect()
        for screen in screens:
            combined_rect = combined_rect.united(screen.geometry())

        self.setGeometry(combined_rect)

    def mouseMoveEvent(self, event):
        pos = event.globalPosition().toPoint()
        try:
            hwnd = win32gui.WindowFromPoint((pos.x(), pos.y()))
            if hwnd:
                ancestor = win32gui.GetAncestor(hwnd, win32con.GA_ROOT)
                # Ignore self
                if ancestor and ancestor != int(self.winId()):
                    title = win32gui.GetWindowText(ancestor).strip()
                    rect_tuple = win32gui.GetWindowRect(ancestor)
                    w = rect_tuple[2] - rect_tuple[0]
                    h = rect_tuple[3] - rect_tuple[1]

                    if w > 80 and h > 80:
                        self.hovered_hwnd = ancestor
                        self.hovered_title = title or "Application Window"
                        self.hovered_rect = QRect(rect_tuple[0], rect_tuple[1], w, h)
                        self.update()
                        return
        except Exception:
            pass

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.hovered_hwnd and self.hovered_rect:
                self.select_window(self.hovered_hwnd, self.hovered_title, self.hovered_rect)
            else:
                self.close()

    def select_window(self, hwnd: int, title: str, rect: QRect) -> None:
        """Emits selection signal and closes picker."""
        logger.info(f"Window selected via picker: '{title}' (HWND {hwnd})")
        self.window_selected.emit(hwnd, title, rect)
        self.close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Subtle dark veil across screen
        painter.fillRect(self.rect(), QColor(0, 0, 0, 40))

        if self.hovered_rect:
            local_tl = self.mapFromGlobal(self.hovered_rect.topLeft())
            target_rect = QRect(local_tl, self.hovered_rect.size())

            # Highlight border around target window
            pen = QPen(QColor(16, 185, 129), 3, Qt.PenStyle.SolidLine)
            painter.setPen(pen)
            painter.drawRect(target_rect)

            # Title badge above window
            badge_text = f" 🎯 {self.hovered_title[:45]} "
            painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            badge_y = max(10, target_rect.top() - 28)
            badge_rect = QRect(target_rect.left(), badge_y, 320, 24)

            painter.fillRect(badge_rect, QColor(15, 23, 42, 230))
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(badge_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, badge_text)
