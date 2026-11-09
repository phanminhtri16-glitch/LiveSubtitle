import numpy as np
import pytest
from src.live_subtitle.engine.transcriber import SpeechTranscriber

def test_transcriber_initialization_no_load():
    transcriber = SpeechTranscriber(model_size="tiny", load_model=False)
    assert transcriber.model_size == "tiny"
    assert transcriber.task == "transcribe"
    assert transcriber.language is None
    assert transcriber.initial_prompt is not None

    device, compute_type = transcriber.auto_select_device()
    assert device in ["cuda", "cpu"]
    assert compute_type in ["float16", "int8"]

def test_transcribe_empty_returns_empty():
    transcriber = SpeechTranscriber(model_size="tiny", load_model=False)
    assert transcriber.transcribe_segment(np.array([], dtype=np.float32)) == ""

def test_set_task_and_language():
    transcriber = SpeechTranscriber(model_size="tiny", load_model=False)
    transcriber.set_task("translate")
    assert transcriber.task == "translate"
    transcriber.set_language("ja")
    assert transcriber.language == "ja"
    transcriber.set_language("auto")
    assert transcriber.language is None

def test_initial_prompt_customization():
    transcriber = SpeechTranscriber(model_size="tiny", load_model=False)
    transcriber.set_initial_prompt("Custom domain prompt: LiveSubtitle.")
    assert transcriber.initial_prompt == "Custom domain prompt: LiveSubtitle."
    transcriber.set_initial_prompt(None)
    assert transcriber.initial_prompt is None

def test_cpu_threads_scaling():
    transcriber = SpeechTranscriber(model_size="tiny", load_model=False)
    threads = transcriber.get_optimal_cpu_threads()
    assert 1 <= threads <= 8

def test_clean_transcription_text():
    transcriber = SpeechTranscriber(model_size="tiny", load_model=False)
    assert transcriber.clean_text(" [MUSIC] Hello World! ") == "Hello World!"
    assert transcriber.clean_text("[APPLAUSE]") == ""
    assert transcriber.clean_text("   Thank you very much.   ") == "Thank you very much."
