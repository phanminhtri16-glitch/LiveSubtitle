import os
os.environ["QT_QPA_PLATFORM"] = "offscreen"

import pytest
from PyQt6.QtCore import QRect
from PyQt6.QtWidgets import QApplication

from src.live_subtitle.gui.window_manager import (
    get_window_geometry,
    list_visible_windows,
    WindowTracker,
)

@pytest.fixture(scope="session")
def qapp():
    return QApplication.instance() or QApplication([])

def test_list_visible_windows_structure(qapp):
    windows = list_visible_windows()
    assert isinstance(windows, list)
    for win in windows:
        assert "hwnd" in win
        assert "title" in win
        assert "rect" in win
        assert isinstance(win["rect"], QRect)
        assert len(win["title"].strip()) > 0

def test_get_window_geometry_invalid_hwnd():
    rect, is_minimized = get_window_geometry(999999999)
    assert rect is None
    assert is_minimized is False

def test_window_tracker_mocked_flow(qapp):
    mock_state = {
        "rect": QRect(100, 100, 800, 600),
        "is_minimized": False,
    }

    def mock_geometry(hwnd):
        if hwnd != 12345:
            return None, False
        if mock_state["rect"] is None:
            return None, False
        return mock_state["rect"], mock_state["is_minimized"]

    tracker = WindowTracker(poll_interval_ms=50, geometry_fn=mock_geometry)
    assert not tracker.is_tracking

    geo_events = []
    vis_events = []
    tracker.geometry_changed.connect(lambda r: geo_events.append(r))
    tracker.visibility_changed.connect(lambda v: vis_events.append(v))

    # 1. Start tracking window
    tracker.track_window(12345)
    assert tracker.is_tracking
    assert len(geo_events) == 1
    assert geo_events[-1] == QRect(100, 100, 800, 600)
    assert len(vis_events) == 1
    assert vis_events[-1] is True

    # 2. Window moves
    mock_state["rect"] = QRect(200, 250, 800, 600)
    tracker.poll_geometry()
    assert len(geo_events) == 2
    assert geo_events[-1] == QRect(200, 250, 800, 600)

    # 3. Window is minimized
    mock_state["is_minimized"] = True
    tracker.poll_geometry()
    assert len(vis_events) == 2
    assert vis_events[-1] is False

    # 4. Window is restored
    mock_state["is_minimized"] = False
    tracker.poll_geometry()
    assert len(vis_events) == 3
    assert vis_events[-1] is True

    # 5. Window closed
    mock_state["rect"] = None
    tracker.poll_geometry()
    assert len(vis_events) == 4
    assert vis_events[-1] is False
    assert not tracker.is_tracking

def test_window_tracker_invalid_hwnd_stops_immediately(qapp):
    tracker = WindowTracker(poll_interval_ms=50)
    tracker.track_window(999999999)
    # Target was invalid, so poll_geometry detected None rect and stopped
    assert not tracker.is_tracking
