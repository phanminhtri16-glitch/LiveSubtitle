import numpy as np
import pytest
from src.live_subtitle.audio.loopback_capture import LoopbackAudioCapture, resample_audio
from src.live_subtitle.audio.device_manager import get_default_loopback_device, list_output_devices

def test_audio_resampling_stereo_to_mono():
    # 1 second of 48kHz stereo sine wave
    t = np.linspace(0, 1, 48000, False)
    stereo_48k = np.column_stack([np.sin(2 * np.pi * 440 * t), np.sin(2 * np.pi * 440 * t)]).astype(np.float32)
    mono_16k = resample_audio(stereo_48k, orig_sr=48000, target_sr=16000)
    assert mono_16k.ndim == 1
    assert len(mono_16k) == 16000
    assert mono_16k.dtype == np.float32

def test_audio_resampling_already_16k_mono():
    data = np.ones(1600, dtype=np.float32) * 0.5
    resampled = resample_audio(data, orig_sr=16000, target_sr=16000)
    assert np.array_equal(data, resampled)

def test_audio_resampling_empty():
    empty = np.array([], dtype=np.float32)
    assert len(resample_audio(empty, orig_sr=48000, target_sr=16000)) == 0

def test_loopback_capture_lifecycle_test_mode():
    received = []
    capture = LoopbackAudioCapture(callback=lambda data: received.append(data), test_mode=True)
    assert not capture.is_running
    capture.start()
    assert capture.is_running
    # Feed test audio in test mode
    capture.feed_test_audio(np.zeros(1600, dtype=np.float32))
    assert len(received) == 1
    capture.stop()
    assert not capture.is_running

def test_device_manager_queries():
    # Should not raise exception
    devices = list_output_devices()
    assert isinstance(devices, list)
    # Default device query
    dev = get_default_loopback_device()
    # If a real sound card exists, dev is a dict; if in headless CI, may be None
    if dev is not None:
        assert "name" in dev
        assert "index" in dev
