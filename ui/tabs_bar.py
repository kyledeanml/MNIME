"""
Tabs bar widget for switching between different conversion modes:
Merge Files, JPG -> PDF, PDF -> JPG, Compress PDF, PDF -> Word.
"""

from ui.cursor_fx import get_custom_cursor
from enum import Enum
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QButtonGroup, QFrame
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QCursor


class ToolMode(Enum):
    COMBINE_PDF = "MERGE"
    SPLIT_PDF = "SPLIT"
    JPG_TO_PDF = "JPG → PDF"
    PDF_TO_JPG = "PDF → JPG"
    COMPRESS_PDF = "COMPRESS"
    PDF_TO_DOCX = "PDF → DOCX"
    BOOKMARK = "BOOKMARK"


class TabsBar(QWidget):
    """Free-floating dark metallic tab navigation bar with dark neon blue highlights."""

    mode_changed = pyqtSignal(ToolMode)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_mode = ToolMode.COMBINE_PDF
        self._buttons = {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)

        tabs = [
            ToolMode.JPG_TO_PDF,
            ToolMode.COMBINE_PDF,
            ToolMode.SPLIT_PDF,
            ToolMode.COMPRESS_PDF,
            ToolMode.PDF_TO_JPG,
            ToolMode.PDF_TO_DOCX,
            ToolMode.BOOKMARK
        ]

        for idx, mode in enumerate(tabs):
            btn = QPushButton(mode.value)
            btn.setCheckable(True)
            btn.setCursor(get_custom_cursor())
            btn.setFixedHeight(28)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #11151f;
                    color: #8b949e;
                    border: 1px solid #1f2737;
                    border-radius: 10px;
                    padding: 4px 12px;
                    font-size: 11px;
                    font-weight: 600;
                    letter-spacing: 0.3px;
                }
                QPushButton:hover {
                    background-color: #1a2130;
                    color: #c9d1d9;
                    border: 1px solid #2d3748;
                }
                QPushButton:checked {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #16253b, stop:1 #0e1826);
                    color: #00e5ff;
                    border: 1px solid #00d2ff;
                    font-weight: 700;
                }
            """)
            btn.clicked.connect(lambda checked, m=mode: self._on_tab_clicked(m))
            self.button_group.addButton(btn, idx)
            layout.addWidget(btn)
            self._buttons[mode] = btn

        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Set initial active tab
        self._buttons[ToolMode.COMBINE_PDF].setChecked(True)

    def _on_tab_clicked(self, mode: ToolMode):
        if self.current_mode != mode:
            self.current_mode = mode
            self.mode_changed.emit(mode)

    def set_mode(self, mode: ToolMode):
        if mode in self._buttons:
            self._buttons[mode].setChecked(True)
            self._on_tab_clicked(mode)
