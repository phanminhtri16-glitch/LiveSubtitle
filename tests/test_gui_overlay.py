import os
os.environ["QT_QPA_PLATFORM"] = "offscreen"

import pytest
from PyQt6.QtCore import QRect, Qt
from PyQt6.QtWidgets import QApplication
from src.live_subtitle.gui.subtitle_overlay import SubtitleOverlay
from src.live_subtitle.gui.snip_tool import SnipTool

@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app

def test_subtitle_overlay_snap_and_text(qapp):
    overlay = SubtitleOverlay()
    target_rect = QRect(100, 100, 800, 600)
    overlay.snap_to_rect(target_rect)
    
    # Check that overlay is positioned near the bottom of target_rect
    assert overlay.x() >= target_rect.x()
    assert overlay.y() > target_rect.y()
    assert overlay.y() + overlay.height() <= target_rect.bottom() + 10

    overlay.update_subtitle("Live subtitle testing dialogue")
    assert overlay.current_text == "Live subtitle testing dialogue"

def test_subtitle_overlay_appearance(qapp):
    overlay = SubtitleOverlay()
    overlay.set_appearance(font_size=26, opacity=0.8, text_color="#00FFCC")
    assert overlay.font_size == 26
    assert abs(overlay.opacity - 0.8) < 1e-4
    assert overlay.text_color == "#00FFCC"

def test_subtitle_overlay_window_flags(qapp):
    overlay = SubtitleOverlay()
    flags = overlay.windowFlags()
    assert bool(flags & Qt.WindowType.FramelessWindowHint)
    assert bool(flags & Qt.WindowType.WindowStaysOnTopHint)

def test_snip_tool_initialization(qapp):
    snip = SnipTool()
    assert snip.windowFlags() & Qt.WindowType.FramelessWindowHint
    assert snip.cursor().shape() == Qt.CursorShape.CrossCursor
