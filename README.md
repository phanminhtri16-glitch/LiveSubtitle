# 🎙️ LiveSubtitle

> **A 100% free, local Windows desktop application that captures internal PC audio and generates live, real-time subtitles directly over a selected video frame.**

---

## 📖 Overview

**LiveSubtitle** solves the problem of watching videos, lectures, streams, podcasts, or foreign-language media that lack built-in subtitles or closed captions. 

Instead of relying on paid cloud transcription services or physical microphone recording, **LiveSubtitle** runs completely locally on your PC. It captures internal system sound via **Windows WASAPI Loopback** (recording exactly what plays through your speakers or headphones), transcribes dialogue in real time using **Faster-Whisper**, and displays clean, high-contrast subtitles in a transparent, click-through overlay anchored to whatever video player or browser window you select.

---

## ✨ Key Features

* 🎯 **Screen Frame Selector:** A snip-and-drag tool lets you highlight any video player, browser, or media window on your screen to anchor the subtitle overlay.
* 🎧 **Zero-Mic Internal Audio Capture:** Uses Windows WASAPI Loopback (`PyAudioWPatch`) to capture clean internal audio without picking up background room noise or typing sounds.
* ⚡ **Ultra-Low Latency:** Incorporates **Silero VAD** (Voice Activity Detection) running on ONNX to detect pauses (~280ms) and slice continuous speech every 2.0s max, delivering live subtitles in ~1.0s to 1.5s.
* 🔒 **100% Free & Offline:** Zero cloud API keys, zero usage limits, and zero recurring fees. All speech models run entirely on your local hardware.
* 🚀 **Auto Hardware Acceleration:** Automatically detects and utilizes NVIDIA GPUs (CUDA `float16`). If no dedicated GPU is available, it seamlessly falls back to optimized multi-threaded CPU execution with `int8` quantization.
* 🖱️ **Click-Through Transparent Overlay:** The subtitle window is always-on-top and transparent to mouse clicks (`WA_TransparentForMouseEvents`), allowing you to pause, play, or scrub the video underneath without interference.
* 🌐 **Transcription & Translation Modes:** Transcribe speech in the original spoken language (English, Vietnamese, Japanese, etc.) or use Whisper's built-in engine to translate foreign audio directly into English subtitles.

---

## 🏗️ Architecture & Pipeline

```text
[ Windows Audio Subsystem (WASAPI Loopback) ]
                     │
                     ▼ (16kHz Mono PCM Audio Stream)
      [ audio/loopback_capture.py ]
                     │
                     ▼ (Audio Buffer Queue)
      [ engine/vad_processor.py ]
      ├── Filters silence & background noise
      └── Slices speech on pauses (>=280ms) or 2.0s limit
                     │
                     ▼ (Speech Segments)
      [ engine/transcriber.py ]
      ├── Faster-Whisper (CTranslate2)
      └── Auto CUDA (float16) / CPU (int8)
                     │
                     ▼ (PyQt Signals)
      [ gui/subtitle_overlay.py ]
      └── High-contrast, transparent, click-through subtitle bar
```

---

## 📁 Project Structure

```text
LiveSubtitle/
│
├── config/                          # App configuration & persistence
│   ├── __init__.py
│   └── settings.py                  # User preferences (model, font size, opacity, language)
│
├── src/                             # Core application package
│   └── live_subtitle/
│       ├── __init__.py
│       │
│       ├── audio/                   # 1. Hardware & Audio Capture
│       │   ├── __init__.py
│       │   ├── loopback_capture.py  # WASAPI loopback audio capture
│       │   └── device_manager.py    # Output device enumeration (Speakers/Headphones)
│       │
│       ├── engine/                  # 2. AI Speech Processing Pipeline
│       │   ├── __init__.py
│       │   ├── vad_processor.py     # Silero VAD speech chunker
│       │   ├── transcriber.py       # Faster-Whisper ASR inference
│       │   └── pipeline_worker.py   # Multi-threaded pipeline coordinator
│       │
│       ├── gui/                     # 3. PyQt6 User Interface & Overlays
│       │   ├── __init__.py
│       │   ├── main_window.py       # Dashboard controls & settings
│       │   ├── snip_tool.py         # Fullscreen drag-to-select frame tool
│       │   ├── subtitle_overlay.py  # Pinned click-through subtitle display
│       │   └── styles.py            # Dark theme, typography, & styling
│       │
│       └── utils/                   # 4. Utilities
│           ├── __init__.py
│           ├── logger.py            # Logging configuration
│           └── system_info.py       # GPU / CUDA capability detection
│
├── tests/                           # 5. Automated Test Suite
│   ├── __init__.py
│   ├── test_environment.py          # Verifies dependencies and environment
│   ├── test_vad_processor.py        # Tests audio chunking and silence cutoff
│   ├── test_transcriber.py          # Tests Whisper loading and inference logic
│   ├── test_audio_capture.py        # Tests audio loopback lifecycle
│   └── test_gui_overlay.py          # Tests overlay snapping and click-through
│
├── docs/                            # Documentation, specs, and plans
├── requirements.txt                 # Python dependencies
├── run.py                           # Application entrypoint launcher
└── README.md                        # Documentation & setup guide
```

---

## 🛠️ Tech Stack & Dependencies

| Component | Library / Framework | Purpose |
| :--- | :--- | :--- |
| **GUI & Overlays** | [PyQt6](https://pypi.org/project/PyQt6/) | High-performance desktop GUI, transparent windows, and frame selection |
| **Speech-to-Text** | [Faster-Whisper](https://github.com/SYSTRAN/faster-whisper) | CTranslate2-accelerated local Whisper engine (up to 4x faster than original Whisper) |
| **Audio Capture** | [PyAudioWPatch](https://github.com/s0d3s/PyAudioWPatch) | Native Windows WASAPI loopback capture for internal system audio |
| **Voice Activity** | [Silero VAD](https://github.com/snakers4/silero-vad) | Sub-5ms voice boundary detection via ONNX runtime |
| **Runtime** | Python 3.10+ | Primary language environment |
| **Testing** | [pytest](https://pytest.org/) | Unit and integration test suite |

---

## 🚀 Getting Started

### 1. Prerequisites
- **Operating System:** Windows 10 or Windows 11 (64-bit)
- **Python:** Python 3.10, 3.11, or 3.12 installed ([Download Python](https://www.python.org/downloads/))
- *(Optional, Recommended)* **NVIDIA GPU:** With CUDA installed for sub-second transcription latency.

### 2. Installation

1. Open PowerShell or Command Prompt in the project folder:
   ```bash
   cd d:\CODING_PROJECTS\LiveSubtitle
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### 3. Running the Application

Launch the desktop app using:
```bash
python run.py
```

---

## 🖥️ How to Use

1. **Select Video Frame:**
   - Click the **"Select Video Frame"** button on the control panel.
   - Click and drag a rectangle over the video playing on your screen (YouTube, media player, etc.).
   - The translucent subtitle bar will automatically anchor to the bottom of that video box.
2. **Choose Model & Language:**
   - **Model:** Choose `tiny` (lowest latency, lowest CPU usage), `base` (recommended balance), or `small` (higher accuracy).
   - **Language:** Leave on `Auto-detect` or select your video's spoken language.
   - **Translate:** Check `Translate to English` if watching foreign audio that you want translated in real-time.
3. **Start Captions:**
   - Click **"Start Captions"**.
   - Play your video. Live subtitles will stream into the overlay window as dialogue occurs.
4. **Move / Resize (Optional):**
   - Use the top grab handle on the subtitle bar if you ever move your video player and want to reposition the subtitles.

---

## 📄 License

This project is licensed under the **MIT License** — 100% free for personal and commercial use.
