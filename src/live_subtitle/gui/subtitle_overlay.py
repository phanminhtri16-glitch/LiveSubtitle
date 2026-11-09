from PyQt6.QtCore import QPoint, QRect, Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QPainterPath
from PyQt6.QtWidgets import (
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

class SubtitleOverlay(QWidget):
    """
    Transparent, always-on-top, click-through subtitle display bar that
    anchors to the user's selected video frame.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        # Enable mouse click-through to underlying video player by default
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        self.font_size = 22
        self.opacity = 0.75
        self.text_color = "#FFFFFF"
        self.current_text = ""

        self._drag_start_pos: QPoint | None = None
        self._is_dragging = False

        self._init_ui()

    def _init_ui(self) -> None:
        self.resize(700, 110)

        # Top drag handle bar (12px height) for manual repositioning
        self.drag_handle = QWidget(self)
        self.drag_handle.setFixedHeight(12)
        self.drag_handle.setCursor(Qt.CursorShape.SizeAllCursor)

        # Subtitle text label
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setWordWrap(True)

        # Subtle text drop shadow for maximum readability over any video background
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(8)
        shadow.setColor(QColor(0, 0, 0, 240))
        shadow.setOffset(1, 2)
        self.label.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 6, 16, 12)
        layout.addWidget(self.drag_handle)
        layout.addWidget(self.label)

        self._apply_styles()

    def _apply_styles(self) -> None:
        font = QFont("Segoe UI", self.font_size, QFont.Weight.Bold)
        self.label.setFont(font)
        self.label.setStyleSheet(f"color: {self.text_color}; background: transparent;")
        self.update()

    def set_appearance(self, font_size: int, opacity: float, text_color: str) -> None:
        """Dynamically updates subtitle font size, pill opacity, and text color."""
        self.font_size = max(12, min(font_size, 48))
        self.opacity = max(0.1, min(opacity, 1.0))
        self.text_color = text_color
        self._apply_styles()

    def update_subtitle(self, text: str) -> None:
        """Updates the displayed subtitle caption."""
        self.current_text = text
        self.label.setText(text)
        # Auto-adjust height to fit multiline text if needed
        self.adjustSize()

    def snap_to_rect(self, target_rect: QRect) -> None:
        """
        Positions and sizes the subtitle overlay at the bottom center of
        the target video frame.
        """
        target_width = max(350, min(target_rect.width() - 40, 1100))
        target_height = max(80, min(int(target_rect.height() * 0.25), 160))

        # Center horizontally, anchor 24px above bottom of target rect
        x = target_rect.x() + (target_rect.width() - target_width) // 2
        y = target_rect.bottom() - target_height - 24

        self.setGeometry(x, y, target_width, target_height)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw rounded pill dark backdrop with custom opacity
        rect = self.rect().adjusted(4, 4, -4, -4)
        path = QPainterPath()
        path.addRoundedRect(float(rect.x()), float(rect.y()), float(rect.width()), float(rect.height()), 12.0, 12.0)

        # Pill background
        alpha = int(self.opacity * 255)
        painter.fillPath(path, QColor(15, 17, 23, alpha))

        # Thin elegant border
        border_color = QColor(255, 255, 255, int(self.opacity * 60))
        painter.setPen(border_color)
        painter.drawPath(path)

        # Subtle drag grip dots on the top handle
        grip_x = self.width() // 2
        painter.setPen(QColor(255, 255, 255, int(self.opacity * 120)))
        painter.drawLine(grip_x - 18, 10, grip_x + 18, 10)
        painter.drawLine(grip_x - 12, 13, grip_x + 12, 13)

    def enable_drag_mode(self, enabled: bool) -> None:
        """Toggles mouse event transparency to allow dragging via handle."""
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, not enabled)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self._is_dragging = True
            event.accept()

    def mouseMoveEvent(self, event):
        if self._is_dragging and self._drag_start_pos:
            self.move(event.globalPosition().toPoint() - self._drag_start_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = False
            event.accept()
