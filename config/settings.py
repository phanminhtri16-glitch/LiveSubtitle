from PyQt6.QtCore import QSettings

class AppSettings:
    """Manages persistent application configuration using QSettings."""

    def __init__(self, organization: str = "LiveSubtitle", application: str = "LiveSubtitle"):
        self._settings = QSettings(organization, application)

    def get_model(self) -> str:
        return self._settings.value("model", "base", type=str)

    def set_model(self, model: str) -> None:
        self._settings.setValue("model", model)

    def get_language(self) -> str:
        return self._settings.value("language", "auto", type=str)

    def set_language(self, lang: str) -> None:
        self._settings.setValue("language", lang)

    def get_task(self) -> str:
        return self._settings.value("task", "transcribe", type=str)

    def set_task(self, task: str) -> None:
        self._settings.setValue("task", task)

    def get_font_size(self) -> int:
        return int(self._settings.value("font_size", 22, type=int))

    def set_font_size(self, size: int) -> None:
        self._settings.setValue("font_size", size)

    def get_opacity(self) -> float:
        return float(self._settings.value("opacity", 0.75, type=float))

    def set_opacity(self, opacity: float) -> None:
        self._settings.setValue("opacity", opacity)

    def get_text_color(self) -> str:
        return self._settings.value("text_color", "#FFFFFF", type=str)

    def set_text_color(self, color: str) -> None:
        self._settings.setValue("text_color", color)

    def clear(self) -> None:
        self._settings.clear()
