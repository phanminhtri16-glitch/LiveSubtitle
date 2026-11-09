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
    assert window.btn_select_frame is not None
    assert window.btn_toggle_captions is not None
    assert window.overlay is not None
    assert window.settings is not None

    # Test toggling captions
    assert not window.is_active
    window.toggle_captions()
    assert window.is_active
    assert window.overlay.isVisible()

    window.toggle_captions()
    assert not window.is_active
    assert not window.overlay.isVisible()

def test_main_window_frame_selection(qapp):
    window = MainWindow(test_mode=True)
    test_frame = QRect(200, 200, 600, 400)
    window.on_frame_selected(test_frame)
    assert window.selected_frame == test_frame
    assert "600 × 400" in window.lbl_frame_info.text()
