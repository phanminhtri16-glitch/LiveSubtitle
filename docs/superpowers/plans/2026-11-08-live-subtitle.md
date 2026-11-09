# Live Subtitle Desktop App Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a 100% local, free, low-latency Windows desktop app that lets users select a video frame on their screen and displays live floating subtitles transcribed from the video's internal audio.

**Architecture:** A Python PyQt6 desktop application capturing internal PC audio via Windows WASAPI Loopback (`PyAudioWPatch`), segmenting spoken phrases via `silero-vad` ONNX under 280ms pause / 2.0s chunk limits, transcribing in real time with `faster-whisper` (auto CUDA / CPU INT8 fallback), and displaying captions on a transparent, always-on-top, click-through overlay anchored to the selected video frame.

**Tech Stack:** Python 3.10+, PyQt6, PyAudioWPatch, Silero VAD (ONNX runtime), Faster-Whisper (CTranslate2), NumPy, pytest.

**Spec:** [2026-11-08-live-subtitle-design.md](file:///d:/CODING_PROJECTS/LiveSubtitle/docs/superpowers/specs/2026-11-08-live-subtitle-design.md)

## Global Constraints
- **Platform:** Windows 10/11 (x64) with native WASAPI loopback support.
- **Cost & Dependencies:** 100% free and open-source; zero cloud API keys or external paid services.
- **Offline Capable:** Runs fully offline after local model download.
- **Hardware Agnostic:** Auto-detects NVIDIA CUDA; falls back to multi-threaded CPU INT8 compute automatically.
- **Latency Target:** Subtitles update within ~1.0s – 1.5s of spoken audio.

## Review Focus
1. **Loopback device absence / unplugged audio:** When no default playback device is active or headphones are unplugged, audio capture must fail gracefully with a friendly user error instead of crashing.
2. **Audio resampling:** Native WASAPI device sample rates (44.1kHz, 48kHz, stereo) must be cleanly resampled and downmixed to 16kHz mono float32 for VAD and Whisper.
3. **Silence / non-speech video scenes:** During silent video scenes or background music with no speech, VAD must prevent hallucinated Whisper output and keep overlay clean.
4. **Multi-monitor and DPI scaling:** When selecting a frame on a high-DPI or secondary monitor, the snip tool coordinates and overlay placement must align precisely with the video.
5. **Mouse click-through integrity:** The subtitle overlay must not intercept clicks intended for the video player's play/pause/scrub controls underneath.
6. **Thread shutdown on exit:** Closing the application must cleanly stop WASAPI loopback streams and worker threads without hanging the process.

---

### Task 1: Environment & Dependency Installation

**Files:**
- Modify: `requirements.txt`
- Create: `src/live_subtitle/__init__.py`
- Test: `tests/test_environment.py`

**Interfaces:**
- Produces: Verified working Python environment with PyQt6, faster-whisper, PyAudioWPatch, silero-vad, onnxruntime, numpy.

- [ ] **Step 1: Write/Update the test**
```python
def test_dependencies_importable():
    import numpy as np
    import PyQt6
    import faster_whisper
    import pyaudiowpatch
    assert np is not None
    assert PyQt6 is not None
    assert faster_whisper is not None
    assert pyaudiowpatch is not None
```

- [ ] **Step 2: Run test to verify failure status**
Run: `pytest tests/test_environment.py`
Expected: FAIL (missing PyQt6 or other dependencies)

- [ ] **Step 3: Install dependencies**
Run: `pip install -r requirements.txt`

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/test_environment.py -v`
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add requirements.txt src/live_subtitle/__init__.py tests/test_environment.py
git commit -m "chore: setup dependencies and project skeleton"
```

---

### Task 2: Core Utilities & Hardware Detection

**Files:**
- Create: `src/live_subtitle/utils/__init__.py`
- Create: `src/live_subtitle/utils/logger.py`
- Create: `src/live_subtitle/utils/system_info.py`
- Create: `config/__init__.py`
- Create: `config/settings.py`
- Test: `tests/test_utils.py`

**Interfaces:**
- Produces:
  - `detect_hardware() -> dict`: Returns `{"has_cuda": bool, "device": str, "compute_type": str, "vram_gb": float, "cpu_cores": int}`
  - `AppSettings`: QSettings wrapper for saving user preferences (model, font size, opacity, task mode).

- [ ] **Step 1: Write the failing test**
```python
from src.live_subtitle.utils.system_info import detect_hardware
from config.settings import AppSettings

def test_detect_hardware():
    hw = detect_hardware()
    assert "device" in hw
    assert hw["device"] in ["cuda", "cpu"]
    assert "compute_type" in hw

def test_settings_defaults():
    settings = AppSettings()
    assert settings.get_model() in ["tiny", "base", "small"]
    assert settings.get_font_size() > 0
```

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/test_utils.py`
Expected: FAIL

- [ ] **Step 3: Implement `system_info.py`, `logger.py`, and `config/settings.py`**

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/test_utils.py -v`
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add src/live_subtitle/utils/ config/ tests/test_utils.py
git commit -m "feat: implement hardware detection and settings management"
```

---

### Task 3: Audio Resampling & WASAPI Loopback Capture

**Files:**
- Create: `src/live_subtitle/audio/__init__.py`
- Create: `src/live_subtitle/audio/device_manager.py`
- Create: `src/live_subtitle/audio/loopback_capture.py`
- Test: `tests/test_audio_capture.py`

**Interfaces:**
- Consumes: Windows WASAPI audio streams via `pyaudiowpatch`.
- Produces:
  - `get_default_loopback_device() -> dict`
  - `resample_audio(audio_data: np.ndarray, orig_sr: int, target_sr: int = 16000) -> np.ndarray`
  - `class LoopbackAudioCapture(callback: Callable[[np.ndarray], None], sample_rate: int = 16000)`: Streams normalized 16kHz float32 audio chunks.

- [ ] **Step 1: Write the failing test**
```python
import numpy as np
from src.live_subtitle.audio.loopback_capture import LoopbackAudioCapture, resample_audio

def test_audio_resampling():
    t = np.linspace(0, 1, 48000, False)
    stereo_48k = np.column_stack([np.sin(2 * np.pi * 440 * t), np.sin(2 * np.pi * 440 * t)])
    mono_16k = resample_audio(stereo_48k, orig_sr=48000, target_sr=16000)
    assert mono_16k.ndim == 1
    assert len(mono_16k) == 16000

def test_loopback_capture_mocked():
    received = []
    capture = LoopbackAudioCapture(callback=lambda data: received.append(data), test_mode=True)
    capture.start()
    assert capture.is_running
    capture.stop()
    assert not capture.is_running
```

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/test_audio_capture.py`
Expected: FAIL

- [ ] **Step 3: Implement `device_manager.py` and `loopback_capture.py`**

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/test_audio_capture.py -v`
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add src/live_subtitle/audio/ tests/test_audio_capture.py
git commit -m "feat: implement WASAPI audio loopback capture with resampling"
```

---

### Task 4: Low-Latency VAD Audio Segmentation Engine

**Files:**
- Create: `src/live_subtitle/engine/__init__.py`
- Create: `src/live_subtitle/engine/vad_processor.py`
- Test: `tests/test_vad_processor.py`

**Interfaces:**
- Consumes: Normalized 16kHz float32 audio chunks.
- Produces: `class VadProcessor(sample_rate: int = 16000, silence_ms: int = 280, max_chunk_s: float = 2.0)`
  - `process_audio_chunk(chunk: np.ndarray) -> list[np.ndarray]`: Returns complete speech segments ready for Whisper inference.

- [ ] **Step 1: Write the failing test**
```python
import numpy as np
from src.live_subtitle.engine.vad_processor import VadProcessor

def test_silence_produces_no_speech_segments():
    vad = VadProcessor(sample_rate=16000, silence_ms=280)
    silence = np.zeros(16000, dtype=np.float32)
    segments = vad.process_audio_chunk(silence)
    assert len(segments) == 0

def test_speech_segment_flushed_on_pause():
    vad = VadProcessor(sample_rate=16000, silence_ms=280, max_chunk_s=2.0)
    t = np.linspace(0, 1, 16000, False)
    speech = np.sin(2 * np.pi * 440 * t).astype(np.float32) * 0.5
    silence = np.zeros(6000, dtype=np.float32)
    _ = vad.process_audio_chunk(speech)
    segments = vad.process_audio_chunk(silence)
    assert len(segments) >= 1
```

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/test_vad_processor.py`
Expected: FAIL

- [ ] **Step 3: Implement `VadProcessor` in `src/live_subtitle/engine/vad_processor.py`**

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/test_vad_processor.py -v`
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add src/live_subtitle/engine/vad_processor.py tests/test_vad_processor.py
git commit -m "feat: implement low-latency VAD speech segmenter"
```

---

### Task 5: Faster-Whisper Speech Transcriber

**Files:**
- Create: `src/live_subtitle/engine/transcriber.py`
- Test: `tests/test_transcriber.py`

**Interfaces:**
- Consumes: 16kHz float32 speech arrays from `VadProcessor`.
- Produces: `class SpeechTranscriber(model_size: str = "base", task: str = "transcribe", language: str | None = None)`
  - `transcribe_segment(audio_data: np.ndarray) -> str`
  - `set_task(task: str)`: "transcribe" or "translate"
  - `set_language(language: str | None)`

- [ ] **Step 1: Write the failing test**
```python
import numpy as np
from src.live_subtitle.engine.transcriber import SpeechTranscriber

def test_transcriber_initialization_no_load():
    transcriber = SpeechTranscriber(model_size="tiny", load_model=False)
    assert transcriber.model_size == "tiny"
    assert transcriber.task == "transcribe"

def test_transcribe_empty_returns_empty():
    transcriber = SpeechTranscriber(model_size="tiny", load_model=False)
    assert transcriber.transcribe_segment(np.array([], dtype=np.float32)) == ""
```

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/test_transcriber.py`
Expected: FAIL

- [ ] **Step 3: Implement `SpeechTranscriber` in `src/live_subtitle/engine/transcriber.py`**

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/test_transcriber.py -v`
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add src/live_subtitle/engine/transcriber.py tests/test_transcriber.py
git commit -m "feat: implement Faster-Whisper speech transcriber"
```

---

### Task 6: Snip Tool & Subtitle Overlay UI

**Files:**
- Create: `src/live_subtitle/gui/__init__.py`
- Create: `src/live_subtitle/gui/styles.py`
- Create: `src/live_subtitle/gui/snip_tool.py`
- Create: `src/live_subtitle/gui/subtitle_overlay.py`
- Test: `tests/test_gui_overlay.py`

**Interfaces:**
- Produces:
  - `SnipTool(on_selected: Callable[[QRect], None])`
  - `SubtitleOverlay`: Transparent frameless window with `snap_to_rect(rect: QRect)`, `update_subtitle(text: str)`, and mouse click-through behavior.

- [ ] **Step 1: Write the failing test**
```python
from PyQt6.QtCore import QRect
from PyQt6.QtWidgets import QApplication
import pytest
from src.live_subtitle.gui.subtitle_overlay import SubtitleOverlay

@pytest.fixture(scope="session")
def qapp():
    return QApplication.instance() or QApplication([])

def test_subtitle_overlay_snap_and_text(qapp):
    overlay = SubtitleOverlay()
    target = QRect(100, 100, 800, 500)
    overlay.snap_to_rect(target)
    assert overlay.y() >= target.y()
    overlay.update_subtitle("Live subtitle testing")
    assert overlay.current_text == "Live subtitle testing"
```

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/test_gui_overlay.py`
Expected: FAIL

- [ ] **Step 3: Implement `styles.py`, `snip_tool.py`, and `subtitle_overlay.py`**

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/test_gui_overlay.py -v`
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add src/live_subtitle/gui/ tests/test_gui_overlay.py
git commit -m "feat: implement frame snip selector and transparent subtitle overlay"
```

---

### Task 7: Pipeline Coordinator, Main Dashboard & Launcher

**Files:**
- Create: `src/live_subtitle/engine/pipeline_worker.py`
- Create: `src/live_subtitle/gui/main_window.py`
- Create: `run.py`
- Test: `tests/test_pipeline_integration.py`

**Interfaces:**
- Connects loopback audio capture -> VAD -> Transcriber worker thread -> SubtitleOverlay display.
- Controls UI buttons, sliders, model loaders, and graceful exit.

- [ ] **Step 1: Write the failing test**
```python
from PyQt6.QtWidgets import QApplication
from src.live_subtitle.gui.main_window import MainWindow

def test_main_window_controls():
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    assert window.btn_select_frame is not None
    assert window.btn_toggle_captions is not None
```

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/test_pipeline_integration.py`
Expected: FAIL

- [ ] **Step 3: Implement `pipeline_worker.py`, `main_window.py`, and `run.py`**

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/test_pipeline_integration.py -v`
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add src/live_subtitle/engine/pipeline_worker.py src/live_subtitle/gui/main_window.py run.py tests/test_pipeline_integration.py
git commit -m "feat: integrate pipeline coordinator, main window, and app launcher"
```
