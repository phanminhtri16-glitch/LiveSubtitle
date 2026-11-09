import pytest

def test_dependencies_importable():
    import numpy as np
    import PyQt6
    import faster_whisper
    import pyaudiowpatch
    import onnxruntime
    import silero_vad
    assert np is not None
    assert PyQt6 is not None
    assert faster_whisper is not None
    assert pyaudiowpatch is not None
    assert onnxruntime is not None
    assert silero_vad is not None
