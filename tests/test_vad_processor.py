import numpy as np
import pytest
from src.live_subtitle.engine.vad_processor import VadProcessor

def test_silence_produces_no_speech_segments():
    vad = VadProcessor(sample_rate=16000, silence_ms=280, max_chunk_s=2.0)
    # 1 second of pure silence
    silence = np.zeros(16000, dtype=np.float32)
    segments = vad.process_audio_chunk(silence)
    assert len(segments) == 0

def test_speech_segment_flushed_on_pause():
    vad = VadProcessor(sample_rate=16000, silence_ms=280, max_chunk_s=2.0)
    # 500ms of simulated speech tone
    t = np.linspace(0, 0.5, 8000, False)
    speech = (np.sin(2 * np.pi * 300 * t) * 0.8).astype(np.float32)
    
    # 400ms of silence (exceeds silence_ms=280ms)
    silence = np.zeros(6400, dtype=np.float32)

    seg1 = vad.process_audio_chunk(speech)
    seg2 = vad.process_audio_chunk(silence)
    
    total_segments = seg1 + seg2
    assert len(total_segments) >= 1
    assert len(total_segments[0]) >= 4000  # contains the speech

def test_speech_segment_flushed_on_max_chunk_limit():
    vad = VadProcessor(sample_rate=16000, silence_ms=280, max_chunk_s=1.0)
    # 2.5 seconds of continuous simulated speech
    t = np.linspace(0, 2.5, int(16000 * 2.5), False)
    speech = (np.sin(2 * np.pi * 300 * t) * 0.8).astype(np.float32)

    segments = []
    # Feed in 100ms slices (1600 samples)
    slice_size = 1600
    for i in range(0, len(speech), slice_size):
        chunk = speech[i : i + slice_size]
        segs = vad.process_audio_chunk(chunk)
        segments.extend(segs)

    # Should have triggered at least 2 chunk cuts due to max_chunk_s=1.0s
    assert len(segments) >= 2

def test_pre_speech_padding_retained():
    pre_speech_ms = 160  # 5 frames * 32ms = 160ms (2560 samples)
    vad = VadProcessor(sample_rate=16000, silence_ms=280, max_chunk_s=2.0, pre_speech_ms=pre_speech_ms)

    # 1. Feed 300ms of identifiable low-level audio (marker: constant 0.005)
    marker_audio = np.full(4800, 0.005, dtype=np.float32)
    vad.process_audio_chunk(marker_audio)

    # 2. Feed 500ms of speech (amplitude 0.8)
    t = np.linspace(0, 0.5, 8000, False)
    speech = (np.sin(2 * np.pi * 300 * t) * 0.8).astype(np.float32)
    vad.process_audio_chunk(speech)

    # 3. Feed 400ms of silence to flush segment
    silence = np.zeros(6400, dtype=np.float32)
    segments = vad.process_audio_chunk(silence)

    assert len(segments) == 1
    segment = segments[0]
    # The segment must have prepended pre_speech samples (around 2560 samples) containing our 0.005 marker
    expected_pre_samples = int((pre_speech_ms / 1000.0) * 16000)
    pre_part = segment[:expected_pre_samples]
    assert np.allclose(pre_part, 0.005, atol=1e-4)

def test_vad_reset():
    vad = VadProcessor(sample_rate=16000, silence_ms=280, max_chunk_s=2.0)
    t = np.linspace(0, 0.4, 6400, False)
    speech = (np.sin(2 * np.pi * 300 * t) * 0.8).astype(np.float32)
    vad.process_audio_chunk(speech)
    vad.reset()
    silence = np.zeros(6400, dtype=np.float32)
    segments = vad.process_audio_chunk(silence)
    assert len(segments) == 0
