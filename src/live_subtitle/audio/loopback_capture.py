import threading
from typing import Callable
import numpy as np
import pyaudiowpatch as pyaudio
from src.live_subtitle.audio.device_manager import get_default_loopback_device
from src.live_subtitle.utils.logger import logger

def resample_audio(audio_data: np.ndarray, orig_sr: int, target_sr: int = 16000) -> np.ndarray:
    """
    Downmixes multi-channel audio to mono and resamples from orig_sr to target_sr.
    Returns 1D float32 array in range [-1.0, 1.0].
    """
    if len(audio_data) == 0:
        return np.array([], dtype=np.float32)

    # Downmix to mono if multi-channel
    if audio_data.ndim > 1:
        audio_data = np.mean(audio_data, axis=-1)

    audio_data = audio_data.astype(np.float32)

    if orig_sr == target_sr:
        return audio_data

    target_length = int(round(len(audio_data) * target_sr / orig_sr))
    if target_length == 0:
        return np.array([], dtype=np.float32)

    orig_times = np.linspace(0.0, 1.0, len(audio_data), endpoint=False)
    target_times = np.linspace(0.0, 1.0, target_length, endpoint=False)
    resampled = np.interp(target_times, orig_times, audio_data).astype(np.float32)
    return resampled

class LoopbackAudioCapture:
    """
    Captures system output audio via Windows WASAPI Loopback and delivers
    resampled 16kHz mono float32 chunks to a callback.
    """

    def __init__(
        self,
        callback: Callable[[np.ndarray], None],
        sample_rate: int = 16000,
        test_mode: bool = False,
        device_index: int | None = None,
    ):
        self.callback = callback
        self.sample_rate = sample_rate
        self.test_mode = test_mode
        self.device_index = device_index
        self.is_running = False

        self._pyaudio: pyaudio.PyAudio | None = None
        self._stream: pyaudio.Stream | None = None
        self._lock = threading.Lock()
        self._orig_sr = 48000
        self._channels = 2

    def start(self) -> None:
        """Starts capturing loopback audio."""
        with self._lock:
            if self.is_running:
                return

            if self.test_mode:
                self.is_running = True
                logger.info("LoopbackAudioCapture started in test mode.")
                return

            self._pyaudio = pyaudio.PyAudio()

            # Identify target loopback device
            if self.device_index is not None:
                device_info = self._pyaudio.get_device_info_by_index(self.device_index)
            else:
                device_info = get_default_loopback_device(self._pyaudio)

            if device_info is None:
                self._pyaudio.terminate()
                self._pyaudio = None
                raise RuntimeError("No WASAPI loopback audio device found.")

            self._orig_sr = int(device_info["defaultSampleRate"])
            self._channels = int(device_info["maxInputChannels"])
            if self._channels < 1:
                self._channels = 2

            logger.info(
                f"Opening loopback capture on '{device_info['name']}' "
                f"at {self._orig_sr} Hz, {self._channels} channels."
            )

            chunk_size = int(self._orig_sr * 0.05)  # ~50ms chunks

            def stream_callback(in_data, frame_count, time_info, status):
                if in_data and self.is_running:
                    try:
                        # Convert float32 or int16 raw bytes to numpy array
                        audio_raw = np.frombuffer(in_data, dtype=np.float32)
                        if self._channels > 1:
                            audio_raw = audio_raw.reshape(-1, self._channels)

                        resampled = resample_audio(audio_raw, self._orig_sr, self.sample_rate)
                        self.callback(resampled)
                    except Exception as e:
                        logger.error(f"Error processing loopback audio chunk: {e}")
                return (None, pyaudio.paContinue)

            self._stream = self._pyaudio.open(
                format=pyaudio.paFloat32,
                channels=self._channels,
                rate=self._orig_sr,
                input=True,
                input_device_index=device_info["index"],
                frames_per_buffer=chunk_size,
                stream_callback=stream_callback,
            )

            self._stream.start_stream()
            self.is_running = True
            logger.info("WASAPI loopback audio stream started.")

    def stop(self) -> None:
        """Stops capturing and cleans up resources."""
        with self._lock:
            if not self.is_running:
                return

            self.is_running = False

            if self.test_mode:
                logger.info("LoopbackAudioCapture stopped (test mode).")
                return

            try:
                if self._stream is not None:
                    if self._stream.is_active():
                        self._stream.stop_stream()
                    self._stream.close()
                    self._stream = None
            except Exception as e:
                logger.warning(f"Error closing stream: {e}")

            try:
                if self._pyaudio is not None:
                    self._pyaudio.terminate()
                    self._pyaudio = None
            except Exception as e:
                logger.warning(f"Error terminating PyAudio: {e}")

            logger.info("WASAPI loopback audio capture stopped.")

    def feed_test_audio(self, audio: np.ndarray) -> None:
        """Feeds simulated audio chunk in test mode."""
        if self.test_mode and self.is_running:
            self.callback(audio)
