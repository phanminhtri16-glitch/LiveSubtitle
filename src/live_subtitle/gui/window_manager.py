from typing import Any, Callable
from PyQt6.QtCore import QObject, QRect, QTimer, pyqtSignal
import win32gui
from src.live_subtitle.utils.logger import logger

def list_visible_windows() -> list[dict[str, Any]]:
    """
    Enumerates all visible, interactive application windows on the desktop.
    Returns a list of dicts with 'hwnd', 'title', and 'rect'.
    """
    windows: list[dict[str, Any]] = []

    def enum_handler(hwnd: int, _extra: Any) -> bool:
        if not win32gui.IsWindowVisible(hwnd):
            return True

        title = win32gui.GetWindowText(hwnd).strip()
        if not title:
            return True

        # Exclude owned popup / tooltip windows
        if win32gui.GetWindow(hwnd, win32gui.GW_OWNER) != 0:
            return True

        try:
            rect = win32gui.GetWindowRect(hwnd)
            w = rect[2] - rect[0]
            h = rect[3] - rect[1]

            # Exclude tiny or invisible helper windows
            if w >= 80 and h >= 80:
                windows.append({
                    "hwnd": hwnd,
                    "title": title,
                    "rect": QRect(rect[0], rect[1], w, h),
                })
        except Exception:
            pass

        return True

    try:
        win32gui.EnumWindows(enum_handler, None)
    except Exception as e:
        logger.warning(f"Error enumerating windows: {e}")

    # Sort alphabetically by title
    windows.sort(key=lambda item: item["title"].lower())
    return windows

def get_window_geometry(hwnd: int) -> tuple[QRect | None, bool]:
    """
    Retrieves the current geometry and minimized state of a window.
    Returns (rect, is_minimized). If window is invalid or destroyed, returns (None, False).
    """
    try:
        if not win32gui.IsWindow(hwnd):
            return None, False

        is_minimized = bool(win32gui.IsIconic(hwnd))
        rect = win32gui.GetWindowRect(hwnd)
        w = rect[2] - rect[0]
        h = rect[3] - rect[1]
        return QRect(rect[0], rect[1], w, h), is_minimized
    except Exception:
        return None, False

class WindowTracker(QObject):
    """
    Monitors a target window's position and visibility via lightweight polling
    and emits signals when the window is moved, resized, or minimized.
    """

    geometry_changed = pyqtSignal(QRect)
    visibility_changed = pyqtSignal(bool)

    def __init__(
        self,
        poll_interval_ms: int = 100,
        geometry_fn: Callable[[int], tuple[QRect | None, bool]] = get_window_geometry,
        parent=None,
    ):
        super().__init__(parent)
        self.poll_interval_ms = poll_interval_ms
        self.geometry_fn = geometry_fn
        self.is_tracking = False
        self._target_hwnd: int | None = None
        self._last_rect: QRect | None = None
        self._last_visible: bool | None = None

        self._timer = QTimer(self)
        self._timer.setInterval(self.poll_interval_ms)
        self._timer.timeout.connect(self.poll_geometry)

    def track_window(self, hwnd: int) -> None:
        """Starts tracking the specified window handle."""
        self._target_hwnd = hwnd
        self._last_rect = None
        self._last_visible = None
        self.is_tracking = True
        self._timer.start()
        self.poll_geometry()

    def stop(self) -> None:
        """Stops tracking."""
        self._timer.stop()
        self.is_tracking = False
        self._target_hwnd = None
        self._last_rect = None
        self._last_visible = None

    def poll_geometry(self) -> None:
        """Checks the target window's status and emits update signals if changed."""
        if not self.is_tracking or self._target_hwnd is None:
            return

        rect, is_minimized = self.geometry_fn(self._target_hwnd)

        # Window closed or destroyed
        if rect is None:
            logger.info("Tracked window was closed or is no longer valid.")
            self.visibility_changed.emit(False)
            self.stop()
            return

        is_visible = not is_minimized

        if self._last_visible != is_visible:
            self._last_visible = is_visible
            self.visibility_changed.emit(is_visible)

        if is_visible and (self._last_rect is None or self._last_rect != rect):
            self._last_rect = rect
            self.geometry_changed.emit(rect)
