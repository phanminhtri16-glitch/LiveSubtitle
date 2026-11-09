"""Application visual design system and Qt Style Sheets."""

MAIN_WINDOW_STYLE = """
QMainWindow {
    background-color: #121316;
}

QWidget {
    color: #e5e7eb;
    font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    font-size: 13px;
}

QGroupBox {
    border: 1px solid #27272a;
    border-radius: 8px;
    margin-top: 18px;
    padding-top: 14px;
    font-weight: 600;
    color: #94a3b8;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    left: 10px;
}

QLabel {
    color: #e2e8f0;
}

QLabel#HeaderTitle {
    font-size: 18px;
    font-weight: 700;
    color: #ffffff;
}

QLabel#HardwareBadge {
    background-color: #1e293b;
    color: #38bdf8;
    border: 1px solid #0284c7;
    border-radius: 4px;
    padding: 3px 8px;
    font-size: 11px;
    font-weight: 600;
}

QPushButton {
    background-color: #27272a;
    color: #f8fafc;
    border: 1px solid #3f3f46;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #3f3f46;
    border-color: #52525b;
}

QPushButton:pressed {
    background-color: #18181b;
}

QPushButton#ActionBtnPrimary {
    background-color: #2563eb;
    border-color: #1d4ed8;
    color: #ffffff;
}

QPushButton#ActionBtnPrimary:hover {
    background-color: #1d4ed8;
}

QPushButton#ActionBtnStop {
    background-color: #dc2626;
    border-color: #b91c1c;
    color: #ffffff;
}

QPushButton#ActionBtnStop:hover {
    background-color: #b91c1c;
}

QComboBox {
    background-color: #1e1e24;
    border: 1px solid #3f3f46;
    border-radius: 6px;
    padding: 6px 12px;
    color: #f1f5f9;
}

QComboBox:hover {
    border-color: #60a5fa;
}

QComboBox::drop-down {
    border: none;
    padding-right: 8px;
}

QComboBox QAbstractItemView {
    background-color: #18181b;
    border: 1px solid #3f3f46;
    selection-background-color: #2563eb;
    selection-color: #ffffff;
    color: #e2e8f0;
}

QSlider::groove:horizontal {
    height: 6px;
    background: #27272a;
    border-radius: 3px;
}

QSlider::sub-page:horizontal {
    background: #3b82f6;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: #ffffff;
    border: 1px solid #94a3b8;
    width: 14px;
    margin-top: -4px;
    margin-bottom: -4px;
    border-radius: 7px;
}

QSlider::handle:horizontal:hover {
    background: #60a5fa;
}

QCheckBox {
    spacing: 8px;
    color: #e2e8f0;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid #3f3f46;
    background-color: #1e1e24;
}

QCheckBox::indicator:checked {
    background-color: #2563eb;
    border-color: #3b82f6;
}
"""
