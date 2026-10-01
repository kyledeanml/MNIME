"""
Bottom action bar containing the primary execution button (e.g. MERGE FILES) with badge count
and task progress indicator.
Styled with OMNIME dark metal and dark neon blue highlights.
"""

from ui.cursor_fx import get_custom_cursor
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel,
    QProgressBar, QFrame
)
from PyQt6.QtCore import pyqtSignal, Qt, QPoint, QEvent
from .icons import get_icon


class ActionBar(QWidget):
    """Execution bar with main action button, item badge, and progress indicators."""

    action_triggered = pyqtSignal()
    action_hovered = pyqtSignal(bool, object)  # (is_hovered, global_pos: QPoint)


    def __init__(self, parent=None):
        super().__init__(parent)
        self.item_count = 0
        self.action_title = "MERGE FILES"
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 4, 0, 4)
        main_layout.setSpacing(10)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Center row with primary action button
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(40, 0, 40, 0)
        btn_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        btn_row.setSpacing(14)


        self.action_btn = QPushButton("  MERGE FILES")
        self.action_btn.setIcon(get_icon("download", "#ffffff"))
        self.action_btn.setCursor(get_custom_cursor())
        self.action_btn.setFixedHeight(24)
        self.action_btn.setStyleSheet("""
            QPushButton {
                background-color: #11151f;
                color: #485263;
                border: 1px solid #1f2737;
                border-radius: 8px;
                font-size: 12px;
                font-weight: 700;
                letter-spacing: 0.8px;
                padding: 0 22px;
            }
            QPushButton:enabled {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #005a8f, stop:0.5 #0077b6, stop:1 #0096c7);
                border: 1.5px solid #00d2ff;
                color: #ffffff;
            }
            QPushButton:enabled:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #006fae, stop:0.5 #008cc7, stop:1 #00b4d8);
                border: 1.5px solid #38bdf8;
            }
            QPushButton:enabled:pressed {
                background: #004d7a;
                border: 1.5px solid #0096c7;
            }
            QPushButton:disabled {
                background-color: #0e121a;
                border: 1px solid #1a202c;
                color: #3b4452;
            }
        """)
        self.action_btn.clicked.connect(self.action_triggered.emit)
        self.action_btn.setEnabled(False)
        self.action_btn.installEventFilter(self)

        btn_row.addWidget(self.action_btn)
        main_layout.addLayout(btn_row)

        # Progress bar & status message
        self.progress_container = QWidget()
        prog_layout = QVBoxLayout(self.progress_container)
        prog_layout.setContentsMargins(40, 0, 40, 0)
        prog_layout.setSpacing(6)

        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #00e5ff; font-size: 12px; font-weight: 600; letter-spacing: 0.3px;")

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #10141e;
                border: 1px solid #1c2333;
                border-radius: 3px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0077b6, stop:1 #00e5ff);
                border-radius: 3px;
            }
        """)
        prog_layout.addWidget(self.status_label)
        prog_layout.addWidget(self.progress_bar)

        self.progress_container.setVisible(False)
        main_layout.addWidget(self.progress_container)

    def set_action_title(self, title: str):
        self.action_title = title
        self.action_btn.setText(f"  {title}")

    def update_count(self, count: int):
        self.item_count = count

        if count > 0:
            self.action_btn.setEnabled(True)
        else:
            self.action_btn.setEnabled(False)
            self.action_hovered.emit(False, QPoint())

    def eventFilter(self, obj, event):
        if obj is self.action_btn:
            if event.type() == QEvent.Type.Enter:
                if self.action_btn.isEnabled():
                    btn_center = self.action_btn.mapToGlobal(self.action_btn.rect().center())
                    self.action_hovered.emit(True, btn_center)
            elif event.type() == QEvent.Type.Leave:
                self.action_hovered.emit(False, QPoint())
            elif event.type() == QEvent.Type.MouseMove:
                if self.action_btn.isEnabled():
                    global_pos = self.action_btn.mapToGlobal(event.pos())
                    self.action_hovered.emit(True, global_pos)
        return super().eventFilter(obj, event)

    def show_progress(self, percentage: int, message: str):
        self.progress_container.setVisible(True)
        self.progress_bar.setValue(percentage)
        self.status_label.setText(message)

    def hide_progress(self):
        self.progress_container.setVisible(False)
        self.progress_bar.setValue(0)
        self.status_label.setText("")
