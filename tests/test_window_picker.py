import os
os.environ["QT_QPA_PLATFORM"] = "offscreen"

import pytest
from PyQt6.QtCore import QPoint, QRect, Qt
from PyQt6.QtWidgets import QApplication

from src.live_subtitle.gui.window_picker import WindowPicker

@pytest.fixture(scope="session")
def qapp():
    return QApplication.instance() or QApplication([])

def test_window_picker_init(qapp):
    picker = WindowPicker()
    assert picker.windowFlags() & Qt.WindowType.FramelessWindowHint
    assert picker.cursor().shape() == Qt.CursorShape.CrossCursor

def test_window_picker_mock_selection(qapp):
    picker = WindowPicker()
    selected_payload = []
    picker.window_selected.connect(lambda hwnd, title, rect: selected_payload.append((hwnd, title, rect)))

    # Simulate selecting a window programmatically
    mock_hwnd = 1001
    mock_title = "YouTube - Google Chrome"
    mock_rect = QRect(100, 100, 1280, 720)

    picker.select_window(mock_hwnd, mock_title, mock_rect)
    assert len(selected_payload) == 1
    assert selected_payload[0] == (mock_hwnd, mock_title, mock_rect)
