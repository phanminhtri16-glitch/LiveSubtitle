from PyQt6.QtCore import QPoint, QRect, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QCursor, QGuiApplication, QPainter, QPen
from PyQt6.QtWidgets import QWidget

class SnipTool(QWidget):
    """
    Fullscreen translucent marquee snip selector that allows the user to
    drag a bounding box over any video frame on screen.
    """

    frame_selected = pyqtSignal(QRect)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(QCursor(Qt.CursorShape.CrossCursor))

        self.start_pos: QPoint | None = None
        self.current_pos: QPoint | None = None
        self.is_selecting = False

        self._cover_virtual_desktop()

    def _cover_virtual_desktop(self) -> None:
        """Spans the snip overlay across all available screens."""
        screens = QGuiApplication.screens()
        if not screens:
            self.setGeometry(0, 0, 1920, 1080)
            return

        combined_rect = QRect()
        for screen in screens:
            combined_rect = combined_rect.united(screen.geometry())

        self.setGeometry(combined_rect)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_pos = event.globalPosition().toPoint()
            self.current_pos = self.start_pos
            self.is_selecting = True
            self.update()

    def mouseMoveEvent(self, event):
        if self.is_selecting:
            self.current_pos = event.globalPosition().toPoint()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.is_selecting:
            self.is_selecting = False
            self.current_pos = event.globalPosition().toPoint()

            if self.start_pos and self.current_pos:
                rect = QRect(self.start_pos, self.current_pos).normalized()
                if rect.width() >= 30 and rect.height() >= 30:
                    self.frame_selected.emit(rect)

            self.close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Semi-transparent dark tint across entire screen
        painter.fillRect(self.rect(), QColor(0, 0, 0, 140))

        if self.is_selecting and self.start_pos and self.current_pos:
            # Map global coordinates to local widget coordinates
            local_start = self.mapFromGlobal(self.start_pos)
            local_current = self.mapFromGlobal(self.current_pos)
            select_rect = QRect(local_start, local_current).normalized()

            # Punch clear hole through the overlay so video underneath is crisp
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            painter.fillRect(select_rect, Qt.GlobalColor.transparent)

            # Draw glowing marquee border
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            pen = QPen(QColor(56, 189, 248), 2, Qt.PenStyle.SolidLine)
            painter.setPen(pen)
            painter.drawRect(select_rect)

            # Dimensions badge
            dim_text = f" {select_rect.width()} × {select_rect.height()} px "
            painter.setPen(QColor(255, 255, 255))
            painter.fillRect(
                QRect(select_rect.left(), max(0, select_rect.top() - 22), 120, 20),
                QColor(15, 23, 42, 220),
            )
            painter.drawText(
                QRect(select_rect.left(), max(0, select_rect.top() - 22), 120, 20),
                Qt.AlignmentFlag.AlignCenter,
                dim_text,
            )
