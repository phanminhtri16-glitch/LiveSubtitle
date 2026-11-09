from collections import deque
import numpy as np
import torch
import silero_vad
from src.live_subtitle.utils.logger import logger

class VadProcessor:
    """
    Real-time Voice Activity Detection and speech chunking engine using Silero VAD (ONNX).
    Segments streaming audio based on natural pauses (silence >= silence_ms) or
    maximum speech duration (max_chunk_s), with pre/post speech ring buffering
    to prevent clipped phonemes.
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        silence_ms: int = 280,
        max_chunk_s: float = 2.0,
        threshold: float = 0.5,
        min_speech_ms: int = 180,
        pre_speech_ms: int = 160,
        use_energy_fallback: bool = True,
        energy_threshold: float = 0.015,
    ):
        self.sample_rate = sample_rate
        self.silence_ms = silence_ms
        self.max_chunk_s = max_chunk_s
        self.threshold = threshold
        self.min_speech_ms = min_speech_ms
        self.pre_speech_ms = pre_speech_ms
        self.use_energy_fallback = use_energy_fallback
        self.energy_threshold = energy_threshold

        self.window_size = 512  # 32ms at 16kHz
        self.pre_speech_frames = max(1, int(round((self.pre_speech_ms / 1000.0) * self.sample_rate / self.window_size)))
        self._pre_speech_ring = deque(maxlen=self.pre_speech_frames)

        self._incoming_buffer = np.array([], dtype=np.float32)
        self._speech_buffer: list[np.ndarray] = []
        self._silence_frames = 0
        self._is_speaking = False

        self._model = None
        self._init_model()

    def _init_model(self) -> None:
        """Initializes Silero VAD ONNX model."""
        try:
            self._model = silero_vad.load_silero_vad(onnx=True)
            logger.info("Silero VAD ONNX model initialized.")
        except Exception as e:
            logger.warning(f"Could not load Silero VAD ONNX model: {e}. Falling back to energy detector.")
            self._model = None

    def reset(self) -> None:
        """Resets all internal audio buffers and VAD states."""
        self._incoming_buffer = np.array([], dtype=np.float32)
        self._pre_speech_ring.clear()
        self._speech_buffer.clear()
        self._silence_frames = 0
        self._is_speaking = False
        if self._model is not None and hasattr(self._model, "reset_states"):
            try:
                self._model.reset_states()
            except Exception:
                pass

    def process_audio_chunk(self, chunk: np.ndarray) -> list[np.ndarray]:
        """
        Processes incoming 16kHz float32 audio chunk and returns any completed
        speech segments.
        """
        if len(chunk) == 0:
            return []

        # Ensure 1D float32
        if chunk.ndim > 1:
            chunk = np.mean(chunk, axis=-1)
        chunk = chunk.astype(np.float32)

        # Append to incoming buffer
        self._incoming_buffer = np.concatenate([self._incoming_buffer, chunk])
        segments: list[np.ndarray] = []

        silence_frame_limit = int(round((self.silence_ms / 1000.0) * self.sample_rate / self.window_size))
        max_frame_limit = int(round(self.max_chunk_s * self.sample_rate / self.window_size))
        min_speech_frames = int(round((self.min_speech_ms / 1000.0) * self.sample_rate / self.window_size))

        while len(self._incoming_buffer) >= self.window_size:
            frame = self._incoming_buffer[: self.window_size]
            self._incoming_buffer = self._incoming_buffer[self.window_size :]

            rms = float(np.sqrt(np.mean(frame**2)))
            prob = 0.0

            if self._model is not None:
                try:
                    tensor_frame = torch.from_numpy(frame).unsqueeze(0)
                    prob = float(self._model(tensor_frame, self.sample_rate).item())
                except Exception as e:
                    logger.debug(f"VAD model evaluation error: {e}")
                    prob = 0.0

            is_speech = prob >= self.threshold
            if not is_speech and self.use_energy_fallback:
                is_speech = rms >= self.energy_threshold

            if is_speech:
                if not self._is_speaking:
                    self._is_speaking = True
                    # Prepend pre-speech ring buffer frames to preserve initial phonemes
                    self._speech_buffer.extend(self._pre_speech_ring)
                    self._pre_speech_ring.clear()

                self._silence_frames = 0
                self._speech_buffer.append(frame)

                # Check if speech duration has reached max chunk limit
                if len(self._speech_buffer) >= max_frame_limit:
                    full_segment = np.concatenate(self._speech_buffer)
                    segments.append(full_segment)
                    self._speech_buffer.clear()
                    self._is_speaking = False
                    self._silence_frames = 0
            else:
                if self._is_speaking:
                    self._silence_frames += 1
                    self._speech_buffer.append(frame)

                    if self._silence_frames >= silence_frame_limit:
                        # Natural pause reached
                        if len(self._speech_buffer) >= min_speech_frames:
                            full_segment = np.concatenate(self._speech_buffer)
                            segments.append(full_segment)

                        self._speech_buffer.clear()
                        self._is_speaking = False
                        self._silence_frames = 0
                else:
                    # Non-speech: accumulate in pre-speech ring buffer
                    self._pre_speech_ring.append(frame)

        return segments
