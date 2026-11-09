import queue
import threading
import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal

from src.live_subtitle.audio.loopback_capture import LoopbackAudioCapture
from src.live_subtitle.engine.transcriber import SpeechTranscriber
from src.live_subtitle.engine.vad_processor import VadProcessor
from src.live_subtitle.utils.logger import logger

class PipelineWorker(QThread):
    """
    Background worker thread orchestrating the audio capture -> VAD segmentation ->
    Whisper speech transcription pipeline and posting results to the GUI via signals.
    """

    subtitle_ready = pyqtSignal(str)
    status_changed = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    audio_level = pyqtSignal(float)

    def __init__(
        self,
        model_size: str = "base",
        task: str = "transcribe",
        language: str | None = None,
        load_model: bool = True,
        test_mode: bool = False,
        parent=None,
    ):
        super().__init__(parent)
        self.model_size = model_size
        self.task = task
        self.language = language
        self.load_model = load_model
        self.test_mode = test_mode

        self.audio_queue: queue.Queue[np.ndarray] = queue.Queue(maxsize=200)
        self._stop_event = threading.Event()
        self.is_capturing = False

        self.vad = VadProcessor(sample_rate=16000, silence_ms=280, max_chunk_s=2.0)
        self.transcriber = SpeechTranscriber(
            model_size=self.model_size,
            task=self.task,
            language=self.language,
            load_model=self.load_model,
        )
        self.capture: LoopbackAudioCapture | None = None

    def _on_audio_chunk(self, chunk: np.ndarray) -> None:
        """Callback invoked from audio capture thread."""
        if self.is_capturing and not self._stop_event.is_set():
            try:
                self.audio_queue.put_nowait(chunk)
            except queue.Full:
                pass

    def feed_audio(self, chunk: np.ndarray) -> None:
        """Manually feed an audio chunk (useful for testing)."""
        self._on_audio_chunk(chunk)

    def start_capture(self, device_index: int | None = None, test_mode: bool | None = None) -> None:
        """Starts loopback audio stream and processing thread."""
        if self.is_capturing:
            return

        mode = self.test_mode if test_mode is None else test_mode
        self._stop_event.clear()
        self.vad.reset()

        # Empty any stale queue items
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break

        try:
            self.capture = LoopbackAudioCapture(
                callback=self._on_audio_chunk,
                sample_rate=16000,
                test_mode=mode,
                device_index=device_index,
            )
            self.capture.start()
            self.is_capturing = True
            self.status_changed.emit("Listening to audio...")

            if not self.isRunning():
                self.start()

            logger.info("PipelineWorker audio capture started.")
        except Exception as e:
            err_msg = f"Failed to start audio loopback: {e}"
            logger.error(err_msg)
            self.error_occurred.emit(err_msg)
            self.is_capturing = False

    def stop_capture(self) -> None:
        """Stops audio stream and processing."""
        if not self.is_capturing:
            return

        self.is_capturing = False
        self._stop_event.set()

        if self.capture is not None:
            self.capture.stop()
            self.capture = None

        if self.isRunning():
            self.wait(2000)

        self.status_changed.emit("Stopped")
        logger.info("PipelineWorker audio capture stopped.")

    def set_model(self, model_size: str) -> None:
        """Changes the Whisper model size."""
        if self.model_size != model_size:
            self.model_size = model_size
            if self.load_model:
                self.transcriber.load_model_instance(model_size)

    def set_task(self, task: str) -> None:
        """Switches transcription / translation mode."""
        self.task = task
        self.transcriber.set_task(task)

    def set_language(self, language: str | None) -> None:
        """Sets source language."""
        self.language = language
        self.transcriber.set_language(language)

    def run(self) -> None:
        """Main consumer loop executing VAD chunking and Whisper inference."""
        logger.info("PipelineWorker processing thread started.")

        while not self._stop_event.is_set():
            try:
                chunk = self.audio_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            # Compute approximate RMS level for live audio indicator
            rms = float(np.sqrt(np.mean(chunk**2))) if len(chunk) > 0 else 0.0
            self.audio_level.emit(min(1.0, rms * 5.0))

            # Run VAD speech slicer
            speech_segments = self.vad.process_audio_chunk(chunk)

            for seg in speech_segments:
                if self._stop_event.is_set():
                    break

                self.status_changed.emit("Transcribing...")
                text = self.transcriber.transcribe_segment(seg)

                if text:
                    logger.debug(f"Subtitle: {text}")
                    self.subtitle_ready.emit(text)

                self.status_changed.emit("Listening to audio...")

        logger.info("PipelineWorker processing thread exited.")
