import pytest
from src.live_subtitle.utils.system_info import detect_hardware
from config.settings import AppSettings

def test_detect_hardware():
    hw = detect_hardware()
    assert "device" in hw
    assert hw["device"] in ["cuda", "cpu"]
    assert "compute_type" in hw
    assert hw["compute_type"] in ["float16", "int8"]
    assert "cpu_cores" in hw
    assert hw["cpu_cores"] > 0

def test_settings_defaults():
    settings = AppSettings(organization="TestOrg", application="TestLiveSubtitle")
    assert settings.get_model() in ["tiny", "base", "small"]
    assert settings.get_font_size() > 0
    assert 0.0 <= settings.get_opacity() <= 1.0
    assert settings.get_task() in ["transcribe", "translate"]

def test_settings_mutation():
    settings = AppSettings(organization="TestOrg", application="TestLiveSubtitle")
    settings.set_model("small")
    assert settings.get_model() == "small"
    settings.set_font_size(28)
    assert settings.get_font_size() == 28
    settings.set_opacity(0.85)
    assert abs(settings.get_opacity() - 0.85) < 1e-4
    settings.set_task("translate")
    assert settings.get_task() == "translate"
