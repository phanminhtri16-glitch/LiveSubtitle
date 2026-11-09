import os
os.environ["QT_QPA_PLATFORM"] = "offscreen"

import time
import numpy as np
import pytest
from PyQt6.QtCore import QRect
from PyQt6.QtWidgets import QApplication

from src.live_subtitle.engine.pipeline_worker import PipelineWorker
from src.live_subtitle.gui.main_window import MainWindow

@pytest.fixture(scope="session")
def qapp():
    return QApplication.instance() or QApplication([])

def test_pipeline_worker_lifecycle(qapp):
    worker = PipelineWorker(model_size="tiny", load_model=False, test_mode=True)
    worker.start_capture()
    assert worker.is_capturing

    # Feed test audio chunk
    test_chunk = np.zeros(1600, dtype=np.float32)
    worker.feed_audio(test_chunk)

    worker.stop_capture()
    assert not worker.is_capturing

def test_main_window_components(qapp):
    window = MainWindow(test_mode=True)
    assert window.btn_toggle_captions is not None
    assert window.overlay is not None
    assert window.settings is not None
    assert window.combo_windows is not None
    assert window.btn_refresh_windows is not None
    assert window.btn_pick_window is not None
    assert window.chk_auto_track is not None

    # Test toggling captions
    assert not window.is_active
    window.toggle_captions()
    assert window.is_active
    assert window.overlay.isVisible()

    window.toggle_captions()
    assert not window.is_active
    assert not window.overlay.isVisible()

def test_main_window_window_selection_and_tracking(qapp):
    window = MainWindow(test_mode=True)
    mock_hwnd = 12345
    mock_title = "VLC media player"
    mock_rect = QRect(200, 200, 900, 600)

    # Trigger window selection
    window.on_window_selected(mock_hwnd, mock_title, mock_rect)
    assert window.target_hwnd == mock_hwnd
    assert window.target_title == mock_title
    assert window.overlay.geometry().y() > mock_rect.y()

    # Activate captions so overlay is visible
    window.toggle_captions()
    assert window.overlay.isVisible()

    # Simulate tracked window moved
    new_rect = QRect(300, 350, 900, 600)
    window.on_tracked_geometry_changed(new_rect)
    assert window.overlay.geometry().x() >= new_rect.x()

    # Simulate tracked window minimized
    window.on_tracked_visibility_changed(False)
    assert not window.overlay.isVisible()

    # Simulate tracked window restored
    window.on_tracked_visibility_changed(True)
    assert window.overlay.isVisible()

    window.toggle_captions()
