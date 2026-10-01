"""
Tabs bar widget for switching between different conversion modes:
Merge Files, JPG -> PDF, PDF -> JPG, Compress PDF, PDF -> Word.
"""

from ui.cursor_fx import get_custom_cursor
from enum import Enum
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QButtonGroup, QFrame
from PyQt6.QtCore import pyqtSignal, Qt


class ToolMode(Enum):
    EDIT_IMAGE = "EDIT"
    REFERENCE = "REFERENCE"
    BOOKMARK = "BOOKMARK"
    COMBINE_PDF = "MERGE"
    SPLIT_PDF = "SPLIT"
    JPG_TO_PDF = "JPG → PDF"
    PDF_TO_JPG = "PDF → JPG"
    TXT_TO_PDF = "TXT → PDF"
    COMPRESS_PDF = "COMPRESS"
    PDF_TO_DOCX = "PDF → DOCX"
    SETTINGS = "SETTINGS"
    NLP = "NLP"

class TabsBar(QWidget):
    """Free-floating dark metallic tab navigation bar with dark neon blue highlights."""

    mode_changed = pyqtSignal(ToolMode)
    settings_clicked = pyqtSignal()

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

        left_tabs = [ToolMode.EDIT_IMAGE, ToolMode.BOOKMARK, ToolMode.REFERENCE]
        center_tabs = [
            ToolMode.JPG_TO_PDF,
            ToolMode.TXT_TO_PDF,
            ToolMode.COMBINE_PDF,
            ToolMode.SPLIT_PDF,
            ToolMode.COMPRESS_PDF,
            ToolMode.PDF_TO_JPG,
            ToolMode.PDF_TO_DOCX
        ]
        right_tabs = [
            ToolMode.NLP,
            ToolMode.SETTINGS
        ]

        def _add_tab(mode):
            from ui.icons import get_icon
            from PyQt6.QtCore import QSize
            
            icon_map = {
                ToolMode.EDIT_IMAGE: "edit",
                ToolMode.BOOKMARK: "bookmark",
                ToolMode.JPG_TO_PDF: "image",
                ToolMode.TXT_TO_PDF: "file-text",
                ToolMode.COMBINE_PDF: "layers",
                ToolMode.SPLIT_PDF: "razor",
                ToolMode.COMPRESS_PDF: "minimize",
                ToolMode.PDF_TO_JPG: "images",
                ToolMode.PDF_TO_DOCX: "document",
                ToolMode.REFERENCE: "book",
                ToolMode.NLP: "message",
                ToolMode.SETTINGS: "settings"
            }
            
            btn = QPushButton()
            btn.setCheckable(True)
            btn.setCursor(get_custom_cursor())
            btn.setFixedHeight(28)
            # Make width same as height for a clean square/circle look, or just set fixed width
            btn.setFixedWidth(40)
            
            btn.setIcon(get_icon(icon_map.get(mode, "document"), "#00e5ff"))
            btn.setIconSize(QSize(16, 16))
            btn.setToolTip(mode.value)
            
            btn.setStyleSheet("""
                QToolTip {
                    background-color: #0b0f19;
                    color: #00e5ff;
                    border: 1px solid #00d2ff;
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-size: 11px;
                    font-weight: 900;
                    letter-spacing: 1px;
                }
                QPushButton {
                    background-color: #162438;
                    border: 1px solid #1f2737;
                    border-radius: 10px;
                }
                QPushButton:hover {
                    background-color: #0077b6;
                    border: 1px solid #00d2ff;
                }
                QPushButton:checked {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #005f8c, stop:1 #00a8e8);
                    border: 1px solid #00e5ff;
                }
            """)
                
            btn.clicked.connect(lambda checked, m=mode: self._on_tab_clicked(m))
            self.button_group.addButton(btn)
            layout.addWidget(btn)
            self._buttons[mode] = btn

        for mode in left_tabs:
            _add_tab(mode)
            
        layout.addStretch()
        
        for i, mode in enumerate(center_tabs):
            if i > 0:
                layout.addSpacing(15)
            _add_tab(mode)
            
        layout.addStretch()
        
        from PyQt6.QtWidgets import QCheckBox
        from PyQt6.QtCore import QSettings
        self.nlp_checkbox = QCheckBox("NLP Active")
        self.nlp_checkbox.setStyleSheet("""
            QCheckBox { color: #00e5ff; font-weight: bold; font-size: 11px; margin-right: 10px; }
            QCheckBox::indicator { width: 14px; height: 14px; border: 1px solid #00d2ff; border-radius: 3px; background-color: #162438; }
            QCheckBox::indicator:checked { background-color: #00e5ff; }
        """)
        settings = QSettings("OmniMesh", "OmniMeshApp")
        self.nlp_checkbox.setChecked(str(settings.value("nlp_enabled", "true")).lower() == "true")
        self.nlp_checkbox.toggled.connect(self._on_nlp_toggled)
        layout.addWidget(self.nlp_checkbox)
        
        for mode in right_tabs:
            _add_tab(mode)

        # Set initial active tab
        self._buttons[ToolMode.COMBINE_PDF].setChecked(True)

    def _on_nlp_toggled(self, checked):
        from PyQt6.QtCore import QSettings
        settings = QSettings("OmniMesh", "OmniMeshApp")
        settings.setValue("nlp_enabled", checked)

    def _on_tab_clicked(self, mode: ToolMode):
        if mode == ToolMode.SETTINGS:
            self.settings_clicked.emit()
            if self.current_mode in self._buttons:
                self._buttons[self.current_mode].setChecked(True)
            return
            
        if self.current_mode != mode:
            self.current_mode = mode
            self.mode_changed.emit(mode)

    def set_mode(self, mode: ToolMode):
        if mode in self._buttons:
            self._buttons[mode].setChecked(True)
            self._on_tab_clicked(mode)
