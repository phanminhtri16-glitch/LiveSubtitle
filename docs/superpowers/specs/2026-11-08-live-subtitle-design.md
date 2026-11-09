# Design Document: Real-Time Local Live Subtitle Desktop App

**Date:** 2026-11-08  
**Status:** Draft for Review  
**Target Platform:** Windows 10 / 11 (64-bit)  
**Primary Stack:** Python 3.10+, PyQt6, Faster-Whisper, PyAudioWPatch, Silero VAD  

---

## 1. Intent & Why
Many users watch videos (lectures, live streams, raw movie clips, video podcasts, meetings) that lack subtitles or closed captions. Cloud-based transcription services introduce latency, cost, and privacy risks. The user wants a standalone, local desktop application on Windows that allows them to select a video area on their screen ("the frame") and displays live, low-latency subtitles directly over that frame by transcribing the audio playing from the video in real time.

---

## 2. Goals, Non-Goals, and Anti-Goals

### Goals
- **Screen Frame Selection:** Provide a visual snip/marquee selector where the user drags a box over the video region on screen.
- **Floating Subtitle Overlay:** Anchor a transparent, always-on-top, click-through subtitle display within or directly beneath the selected video frame.
- **Zero Physical Mic Dependency:** Capture internal system audio directly via Windows WASAPI Loopback so that the audio played by any video player, browser, or media player is captured cleanly without background room noise.
- **Local Speech-to-Text:** Run fully locally on the user's PC using `faster-whisper` without external API calls or internet dependence.
- **Hardware Agility:** Automatically use NVIDIA GPU acceleration (CUDA, `float16`) if present; seamlessly fall back to multi-threaded CPU execution (`int8`) if no CUDA device is found.
- **Low Latency:** Utilize Voice Activity Detection (Silero VAD) to segment audio into spoken sentences and minimize speech-to-display delay (~500ms – 1.2s).

### Non-Goals
- Translating audio into different languages on the fly during phase 1 (the initial focus is native transcription; Whisper's built-in translate-to-English can be enabled as an option).
- Video-file recording or re-encoding.
- Cloud storage or cloud sync of transcripts.

### Anti-Goals
- Do not hog 100% of CPU or GPU resources while idle: when no speech is playing, processing must drop to near-zero via VAD.
- Do not block user interaction with the underlying video player: the subtitle overlay must allow mouse clicks to pass through to the video player underneath.

---

## 3. Approaches Considered & Trade-Offs

### Approach 1: Visual Screen-Frame OCR (Read text directly from the video)
- **Description:** Screen capture loop running ONNX OCR (RapidOCR/PaddleOCR) on the bounding box to extract existing subtitles burned into video frames.
- **Trade-offs:** Fast (<50ms) and lightweight, but only works if subtitles are already visually displayed in the video.
- **Verdict:** Ruled out by user requirement (the user explicitly wants to transcribe spoken audio into subtitles).

### Approach 2: System Audio Live Captions via Local Faster-Whisper [SELECTED]
- **Description:** Capture PC audio loopback (WASAPI), run real-time local Faster-Whisper with Silero VAD, and project subtitles onto a floating overlay snapped to the user's selected frame.
- **Trade-offs:** Requires ~1.5GB RAM and moderate compute, but works universally for any video with sound, with no reliance on existing subtitles.
- **Verdict:** Selected approach.

### Approach 3: Dual-Engine App (Audio ASR + Screen OCR)
- **Description:** Combine both OCR and Audio ASR into a single heavyweight tool.
- **Trade-offs:** Adds unnecessary architectural complexity and dependencies for the initial product.
- **Verdict:** Can be a future enhancement, deferred for Phase 1.

---

## 4. Architecture & Component Design

```
+--------------------------------------------------------------------------------+
|                                Windows Desktop                                 |
|                                                                                |
|  [ Video Player / Browser Window ]                                             |
|  +--------------------------------------------------------------------------+  |
|  | [User Selected Frame]                                                    |  |
|  |                                                                          |  |
|  |   +------------------------------------------------------------------+   |  |
|  |   | [Transparent Click-Through Overlay Window (PyQt6)]              |   |  |
|  |   | "Welcome back to the channel, today we are building..."          |   |  |
|  |   +------------------------------------------------------------------+   |  |
|  +--------------------------------------------------------------------------+  |
|                                                                                |
+--------------------------------------------------------------------------------+
                                       ^
                                       | Signals / Text Update
                                       |
+---------------------+      +---------------------+      +----------------------+
| Windows WASAPI      | ---> | Silero VAD          | ---> | Faster-Whisper       |
| Loopback Capture    |      | (Audio Slicer &     |      | (CTranslate2 Engine: |
| (PyAudioWPatch)     |      | Silence Filter)     |      | CUDA or CPU INT8)    |
+---------------------+      +---------------------+      +----------------------+
```

### Component 1: Audio Capture Subsystem (`audio_capture.py`)
- Uses `PyAudioWPatch` to query WASAPI loopback devices (the default render endpoint e.g., Speakers or Headphones).
- Captures 16kHz, 16-bit Mono PCM audio in streaming chunks (~30ms buffer).
- Streams raw PCM frames into an in-memory thread-safe audio queue (`queue.Queue`).

### Component 2: Voice Activity Detection & Low-Latency Chunking (`vad_stream.py`)
- Employs `silero-vad` (ONNX runtime) on 30ms-50ms frames.
- **Low-Latency Segmentation Strategy (Builder Decision):**
  - Rather than waiting for long pauses or 5-second batches, the audio buffer is dispatched to the transcriber when either:
    1. A natural speech pause occurs (silence >= 280ms), OR
    2. Continuous speech duration reaches 2.0 seconds.
  - This ensures subtitles appear with sub-second to ~1.5s latency without high-frequency duplicate inference or text flickering.

### Component 3: Speech-to-Text Engine (`transcriber.py`)
- Built on `faster-whisper.WhisperModel`.
- **Hardware Strategy:**
  - Check `torch.cuda.is_available()`.
  - If CUDA available: initialize `WhisperModel(model_size, device="cuda", compute_type="float16")`.
  - Else: initialize `WhisperModel(model_size, device="cpu", compute_type="int8", cpu_threads=4)`.
- Default model: `tiny` (for ultra-low latency) or `base` (balanced accuracy/latency).
- **Task Modes (Builder Decision):**
  - Supports `task="transcribe"` (outputs speech in the source language) and `task="translate"` (translates foreign spoken speech into English subtitles using Whisper's built-in translation).
  - Mode toggle is exposed directly in the control panel UI.
- Emits decoded text tokens via PyQt signals to the UI thread.

### Component 4: GUI & Overlays (`gui/`)
- **Main Controller Window (`main_window.py`):**
  - Controls: "Select Video Frame", "Start / Stop Captions", Model Size dropdown (`tiny`, `base`, `small`), Source Language dropdown, "Translate to English" checkbox, Font Size slider, Overlay Background Opacity slider.
- **Screen Snip Selector (`snip_tool.py`):**
  - Fullscreen semi-transparent overlay widget (`Qt.WindowType.FramelessWindowHint`).
  - Crosshair cursor; `mousePressEvent`, `mouseMoveEvent`, `mouseReleaseEvent` to draw a rubber-band selection rectangle.
  - On mouse release, stores `(x, y, width, height)` and closes itself.
- **Subtitle Overlay Bar (`subtitle_overlay.py`):**
  - Positioned automatically at the bottom of the selected video frame rectangle.
  - **Flexibility & Mobility (Builder Decision):** Snaps to the frame, but also features a subtle top grip bar allowing the user to freely drag and reposition or resize it anywhere if the video player is moved, without needing brittle Win32 hook listeners.
  - Flags: `Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool`.
  - Mouse transparency: Body has `WA_TransparentForMouseEvents` so clicks pass to the video; hovering over the grip bar enables drag-positioning.
  - Render style: Semi-translucent dark pill background, crisp white typography with text outline / drop shadow for readability over bright or dark video scenes.

---

## 5. Concurrency & Thread Management
1. **GUI Thread (Main Qt Loop):** Handles UI interaction, settings, drawing the overlay.
2. **Audio Worker Thread:** Continuously pulls from WASAPI loopback without blocking the UI.
3. **Transcription Worker Thread:** Consumes speech segments from VAD, executes Faster-Whisper inference, and posts the resulting string back to the GUI via `PyQt6.QtCore.pyqtSignal(str)`.

---

## 6. What's Left to the Builder
- Selection of default model (`base` vs `tiny.en`).
- Specific CSS/QSS styling of the control panel and subtitle pill.
- Handling edge cases such as default audio device changes or headphones disconnect during playback.
- Graceful shutdown of audio loopback streams on app exit.
