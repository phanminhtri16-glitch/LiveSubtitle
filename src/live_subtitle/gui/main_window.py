from PyQt6.QtCore import QRect, Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from config.settings import AppSettings
from src.live_subtitle.audio.device_manager import list_output_devices
from src.live_subtitle.engine.pipeline_worker import PipelineWorker
from src.live_subtitle.gui.snip_tool import SnipTool
from src.live_subtitle.gui.styles import MAIN_WINDOW_STYLE
from src.live_subtitle.gui.subtitle_overlay import SubtitleOverlay
from src.live_subtitle.utils.logger import logger
from src.live_subtitle.utils.system_info import detect_hardware

LANGUAGES = [
    ("Auto Detect", "auto"),
    ("English", "en"),
    ("Vietnamese", "vi"),
    ("Japanese", "ja"),
    ("Spanish", "es"),
    ("Chinese", "zh"),
    ("French", "fr"),
    ("German", "de"),
    ("Korean", "ko"),
    ("Russian", "ru"),
    ("Italian", "it"),
    ("Portuguese", "pt"),
]

class MainWindow(QMainWindow):
    """
    Main controller dashboard for LiveSubtitle desktop application.
    """

    def __init__(self, test_mode: bool = False, parent=None):
        super().__init__(parent)
        self.test_mode = test_mode
        self.settings = AppSettings()
        self.selected_frame: QRect | None = None
        self.is_active = False

        self.snip_tool: SnipTool | None = None
        self.overlay = SubtitleOverlay()

        # Pipeline worker
        saved_model = self.settings.get_model()
        saved_task = self.settings.get_task()
        saved_lang = self.settings.get_language()
        self.worker = PipelineWorker(
            model_size=saved_model,
            task=saved_task,
            language=saved_lang,
            load_model=not self.test_mode,
            test_mode=self.test_mode,
        )

        self._init_ui()
        self._connect_signals()

    def _init_ui(self) -> None:
        self.setWindowTitle("LiveSubtitle - Real-Time Local Captions")
        self.resize(520, 680)
        self.setStyleSheet(MAIN_WINDOW_STYLE)

        central = QWidget(self)
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(24, 20, 24, 20)
        root_layout.setSpacing(16)

        # 1. Header & Hardware Status
        header_layout = QHBoxLayout()
        title_label = QLabel("LiveSubtitle 🎙️")
        title_label.setObjectName("HeaderTitle")
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        hw = detect_hardware()
        badge_text = (
            f"⚡ CUDA: {hw['device_name']} ({hw['vram_gb']}GB)"
            if hw["has_cuda"]
            else f"⚙️ CPU: {hw['cpu_cores']} Cores (INT8)"
        )
        self.hw_badge = QLabel(badge_text)
        self.hw_badge.setObjectName("HardwareBadge")
        header_layout.addWidget(self.hw_badge)
        root_layout.addLayout(header_layout)

        # 2. Screen Frame Snip Section
        frame_group = QGroupBox("Target Video Frame")
        frame_layout = QVBoxLayout(frame_group)

        frame_top_layout = QHBoxLayout()
        self.btn_select_frame = QPushButton("🎯 Select Video Frame")
        self.btn_select_frame.clicked.connect(self.launch_snip_tool)
        frame_top_layout.addWidget(self.btn_select_frame)

        self.lbl_frame_info = QLabel("Fullscreen / Default")
        self.lbl_frame_info.setStyleSheet("color: #94a3b8; font-size: 12px;")
        frame_top_layout.addWidget(self.lbl_frame_info)
        frame_layout.addLayout(frame_top_layout)
        root_layout.addWidget(frame_group)

        # 3. Primary Action & Live Audio Level
        action_group = QGroupBox("Live Transcription Control")
        action_layout = QVBoxLayout(action_group)

        self.btn_toggle_captions = QPushButton("▶ Start Captions")
        self.btn_toggle_captions.setObjectName("ActionBtnPrimary")
        self.btn_toggle_captions.setFixedHeight(46)
        self.btn_toggle_captions.clicked.connect(self.toggle_captions)
        action_layout.addWidget(self.btn_toggle_captions)

        # Audio level indicator
        level_layout = QHBoxLayout()
        level_label = QLabel("Audio Level:")
        level_label.setStyleSheet("color: #94a3b8; font-size: 12px;")
        self.progress_audio = QProgressBar()
        self.progress_audio.setRange(0, 100)
        self.progress_audio.setValue(0)
        self.progress_audio.setTextVisible(False)
        self.progress_audio.setFixedHeight(8)
        level_layout.addWidget(level_label)
        level_layout.addWidget(self.progress_audio)
        action_layout.addLayout(level_layout)

        self.lbl_status = QLabel("Status: Ready")
        self.lbl_status.setStyleSheet("color: #38bdf8; font-size: 12px;")
        action_layout.addWidget(self.lbl_status)
        root_layout.addWidget(action_group)

        # 4. Speech Recognition Settings
        model_group = QGroupBox("Speech Model & Language")
        model_layout = QGridLayout(model_group)
        model_layout.setSpacing(12)

        model_layout.addWidget(QLabel("Whisper Model:"), 0, 0)
        self.combo_model = QComboBox()
        self.combo_model.addItems(["tiny", "base", "small"])
        self.combo_model.setCurrentText(self.settings.get_model())
        self.combo_model.currentTextChanged.connect(self._on_model_changed)
        model_layout.addWidget(self.combo_model, 0, 1)

        model_layout.addWidget(QLabel("Spoken Language:"), 1, 0)
        self.combo_language = QComboBox()
        for name, code in LANGUAGES:
            self.combo_language.addItem(name, code)
        # Select current
        current_lang = self.settings.get_language()
        idx = max(0, self.combo_language.findData(current_lang))
        self.combo_language.setCurrentIndex(idx)
        self.combo_language.currentIndexChanged.connect(self._on_language_changed)
        model_layout.addWidget(self.combo_language, 1, 1)

        self.chk_translate = QCheckBox("Translate to English (Whisper)")
        self.chk_translate.setChecked(self.settings.get_task() == "translate")
        self.chk_translate.toggled.connect(self._on_translate_toggled)
        model_layout.addWidget(self.chk_translate, 2, 0, 1, 2)
        root_layout.addWidget(model_group)

        # 5. Subtitle Appearance Settings
        appearance_group = QGroupBox("Subtitle Display Customization")
        app_layout = QGridLayout(appearance_group)
        app_layout.setSpacing(12)

        # Font size
        app_layout.addWidget(QLabel("Font Size:"), 0, 0)
        self.slider_font = QSlider(Qt.Orientation.Horizontal)
        self.slider_font.setRange(14, 38)
        self.slider_font.setValue(self.settings.get_font_size())
        self.lbl_font_val = QLabel(f"{self.settings.get_font_size()} px")
        self.slider_font.valueChanged.connect(self._on_font_size_changed)
        app_layout.addWidget(self.slider_font, 0, 1)
        app_layout.addWidget(self.lbl_font_val, 0, 2)

        # Opacity
        app_layout.addWidget(QLabel("Background Opacity:"), 1, 0)
        self.slider_opacity = QSlider(Qt.Orientation.Horizontal)
        self.slider_opacity.setRange(20, 100)
        self.slider_opacity.setValue(int(self.settings.get_opacity() * 100))
        self.lbl_opacity_val = QLabel(f"{int(self.settings.get_opacity() * 100)} %")
        self.slider_opacity.valueChanged.connect(self._on_opacity_changed)
        app_layout.addWidget(self.slider_opacity, 1, 1)
        app_layout.addWidget(self.lbl_opacity_val, 1, 2)
        root_layout.addWidget(appearance_group)

        root_layout.addStretch()

        # Apply saved overlay settings
        self.overlay.set_appearance(
            font_size=self.settings.get_font_size(),
            opacity=self.settings.get_opacity(),
            text_color=self.settings.get_text_color(),
        )

    def _connect_signals(self) -> None:
        self.worker.subtitle_ready.connect(self.on_subtitle_ready)
        self.worker.status_changed.connect(self.on_status_changed)
        self.worker.error_occurred.connect(self.on_error_occurred)
        self.worker.audio_level.connect(self.on_audio_level)

    def launch_snip_tool(self) -> None:
        """Opens fullscreen frame selector."""
        self.snip_tool = SnipTool()
        self.snip_tool.frame_selected.connect(self.on_frame_selected)
        self.snip_tool.showFullScreen()

    def on_frame_selected(self, rect: QRect) -> None:
        """Anchors overlay to the user's selected video frame."""
        self.selected_frame = rect
        self.lbl_frame_info.setText(f"{rect.width()} × {rect.height()} px")
        self.overlay.snap_to_rect(rect)

    def toggle_captions(self) -> None:
        """Starts or stops live captioning pipeline."""
        if not self.is_active:
            self.is_active = True
            self.btn_toggle_captions.setText("⏹ Stop Captions")
            self.btn_toggle_captions.setObjectName("ActionBtnStop")
            self.btn_toggle_captions.setStyle(self.btn_toggle_captions.style())

            if self.selected_frame is not None:
                self.overlay.snap_to_rect(self.selected_frame)
            else:
                # Default positioning
                self.overlay.move(400, 600)

            self.overlay.update_subtitle("Listening for speech...")
            self.overlay.show()

            self.worker.start_capture(test_mode=self.test_mode)
        else:
            self.is_active = False
            self.btn_toggle_captions.setText("▶ Start Captions")
            self.btn_toggle_captions.setObjectName("ActionBtnPrimary")
            self.btn_toggle_captions.setStyle(self.btn_toggle_captions.style())

            self.worker.stop_capture()
            self.overlay.hide()
            self.progress_audio.setValue(0)
            self.lbl_status.setText("Status: Stopped")

    def on_subtitle_ready(self, text: str) -> None:
        """Updates subtitle overlay on GUI thread."""
        self.overlay.update_subtitle(text)

    def on_status_changed(self, status: str) -> None:
        self.lbl_status.setText(f"Status: {status}")

    def on_audio_level(self, level: float) -> None:
        val = int(min(1.0, max(0.0, level)) * 100)
        self.progress_audio.setValue(val)

    def on_error_occurred(self, err: str) -> None:
        self.lbl_status.setText(f"Error: {err}")
        QMessageBox.warning(self, "Audio Capture Error", err)

    def _on_model_changed(self, model_name: str) -> None:
        self.settings.set_model(model_name)
        self.worker.set_model(model_name)

    def _on_language_changed(self, index: int) -> None:
        lang_code = self.combo_language.itemData(index)
        self.settings.set_language(lang_code)
        self.worker.set_language(lang_code)

    def _on_translate_toggled(self, checked: bool) -> None:
        task = "translate" if checked else "transcribe"
        self.settings.set_task(task)
        self.worker.set_task(task)

    def _on_font_size_changed(self, val: int) -> None:
        self.lbl_font_val.setText(f"{val} px")
        self.settings.set_font_size(val)
        self.overlay.set_appearance(
            font_size=val,
            opacity=self.overlay.opacity,
            text_color=self.overlay.text_color,
        )

    def _on_opacity_changed(self, val: int) -> None:
        self.lbl_opacity_val.setText(f"{val} %")
        opacity_float = val / 100.0
        self.settings.set_opacity(opacity_float)
        self.overlay.set_appearance(
            font_size=self.overlay.font_size,
            opacity=opacity_float,
            text_color=self.overlay.text_color,
        )

    def closeEvent(self, event):
        """Clean shutdown of background threads and overlays on window close."""
        self.worker.stop_capture()
        if self.worker.isRunning():
            self.worker.wait(2000)
        self.overlay.close()
        event.accept()
