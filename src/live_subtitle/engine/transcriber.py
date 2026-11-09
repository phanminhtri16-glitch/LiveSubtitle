import re
import numpy as np
from faster_whisper import WhisperModel
from src.live_subtitle.utils.logger import logger
from src.live_subtitle.utils.system_info import detect_hardware

class SpeechTranscriber:
    """
    Faster-Whisper local speech-to-text inference wrapper with automatic
    hardware detection (CUDA float16 / CPU int8) and post-processing.
    """

    def __init__(
        self,
        model_size: str = "base",
        task: str = "transcribe",
        language: str | None = None,
        load_model: bool = True,
    ):
        self.model_size = model_size
        self.task = task
        self.language = language if language != "auto" else None
        self._model: WhisperModel | None = None

        if load_model:
            self.load_model_instance(model_size)

    def auto_select_device(self) -> tuple[str, str]:
        """Detects hardware and returns (device, compute_type)."""
        hw = detect_hardware()
        return hw["device"], hw["compute_type"]

    def load_model_instance(self, model_size: str | None = None) -> None:
        """Loads or reloads the WhisperModel."""
        if model_size is not None:
            self.model_size = model_size

        device, compute_type = self.auto_select_device()
        logger.info(f"Loading Faster-Whisper model '{self.model_size}' on {device} ({compute_type})...")

        try:
            self._model = WhisperModel(
                self.model_size,
                device=device,
                compute_type=compute_type,
                cpu_threads=4,
            )
            logger.info(f"Faster-Whisper model '{self.model_size}' loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load Faster-Whisper model on {device}: {e}")
            if device == "cuda":
                logger.info("Attempting fallback to CPU int8...")
                self._model = WhisperModel(
                    self.model_size,
                    device="cpu",
                    compute_type="int8",
                    cpu_threads=4,
                )
                logger.info(f"Faster-Whisper model loaded on CPU fallback.")
            else:
                raise

    def set_task(self, task: str) -> None:
        """Sets task mode: 'transcribe' or 'translate'."""
        if task in ["transcribe", "translate"]:
            self.task = task
            logger.info(f"Transcriber task set to: {task}")

    def set_language(self, language: str | None) -> None:
        """Sets source language code or None for auto detection."""
        self.language = language if language and language != "auto" else None
        logger.info(f"Transcriber language set to: {self.language or 'auto-detect'}")

    def clean_text(self, text: str) -> str:
        """Strips hallucinated sound tokens, timestamps, and redundant whitespace."""
        if not text:
            return ""

        # Remove bracketed tokens like [MUSIC], [APPLAUSE], [BLANK_AUDIO], (music), etc.
        cleaned = re.sub(r"\[[\w\s_-]+\]", "", text, flags=re.IGNORECASE)
        cleaned = re.sub(r"\([\w\s_-]+\)", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        # Filter out standalone punctuation artifacts
        if cleaned in [".", "..", "...", ",", "!", "?", "-", "--"]:
            return ""

        return cleaned

    def transcribe_segment(self, audio_data: np.ndarray) -> str:
        """
        Transcribes a 16kHz float32 audio segment.
        Returns cleaned text string.
        """
        if len(audio_data) == 0:
            return ""

        if self._model is None:
            logger.warning("Whisper model is not loaded.")
            return ""

        if audio_data.ndim > 1:
            audio_data = np.mean(audio_data, axis=-1)

        audio_data = audio_data.astype(np.float32)

        try:
            # beam_size=1 and vad_filter=False for ultra-low latency real-time streaming
            segments, _ = self._model.transcribe(
                audio_data,
                language=self.language,
                task=self.task,
                beam_size=1,
                vad_filter=False,
                temperature=0.0,
            )

            parts = [seg.text for seg in segments if seg.text]
            raw_text = " ".join(parts)
            return self.clean_text(raw_text)
        except Exception as e:
            logger.error(f"Error during transcription: {e}")
            return ""
