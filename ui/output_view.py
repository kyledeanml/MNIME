import os
import shutil
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QFrame
)
from PyQt6.QtCore import Qt, QMimeData, QUrl, pyqtSignal
from PyQt6.QtGui import QDrag

from ui.cursor_fx import get_custom_cursor
from ui.icons import get_icon

class DraggableFileIcon(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.file_path = ""
        self.setPixmap(get_icon("pdf", "#00e5ff").pixmap(64, 64))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCursor(get_custom_cursor())
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_pos = event.pos()

    def mouseMoveEvent(self, event):
        if not self.file_path or not os.path.exists(self.file_path):
            return
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        if not hasattr(self, 'drag_start_pos') or self.drag_start_pos is None:
            return
        if (event.pos() - self.drag_start_pos).manhattanLength() < 5:
            return

        drag = QDrag(self)
        mime = QMimeData()
        mime.setUrls([QUrl.fromLocalFile(self.file_path)])
        drag.setMimeData(mime)

        from ui.cursor_fx import get_file_drag_pixmap
        from PyQt6.QtCore import QPoint
        cursor_pm = get_file_drag_pixmap(32)

        # Override the Windows OLE drag cursor for ALL drop actions!
        # This tells Windows OLE that we handle cursor rendering, replacing the standard
        # Windows system bounding-box cursor with our blue file icon directly.
        for action in (
            Qt.DropAction.CopyAction,
            Qt.DropAction.MoveAction,
            Qt.DropAction.LinkAction,
            Qt.DropAction.IgnoreAction,
            Qt.DropAction.TargetMoveAction,
        ):
            drag.setDragCursor(cursor_pm, action)

        drag.setHotSpot(QPoint(16, 16))

        # Do NOT call drag.setPixmap(...) with an image.
        # Calling drag.setPixmap attaches an offset drag image preview.
        # By omitting setPixmap, ONLY the custom cursor is rendered, turning the mouse itself
        # into the custom blue file icon without any offset or system cursor.
        drag.exec(Qt.DropAction.CopyAction)

class OutputView(QWidget):
    start_over_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.file_path = ""
        self.default_dir = os.path.normpath(os.path.expanduser("~/Desktop"))
        
        main_layout = QHBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.setSpacing(20)
        
        # Left Card: Success Message & Drag Icon
        self.left_card = QFrame()
        self.left_card.setStyleSheet("""
            QFrame {
                background-color: rgba(22, 27, 34, 180);
                border: 1px solid #30363d;
                border-radius: 12px;
            }
        """)
        self.left_card.setFixedSize(320, 160)
        left_layout = QVBoxLayout(self.left_card)
        left_layout.setContentsMargins(15, 15, 15, 15)
        left_layout.setSpacing(10)
        
        self.title_label = QLabel("File Successfully Created!")
        self.title_label.setStyleSheet("color: #00e5ff; font-size: 16px; font-weight: 800; border: none; background: transparent;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(self.title_label)
        
        self.sub_label = QLabel("Drag the icon below to your desktop")
        self.sub_label.setStyleSheet("color: #8b949e; font-size: 12px; border: none; background: transparent;")
        self.sub_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(self.sub_label)
        
        self.icon_label = DraggableFileIcon()
        self.icon_label.setStyleSheet("border: none; background: transparent;")
        left_layout.addWidget(self.icon_label)
        left_layout.addStretch()
        
        main_layout.addWidget(self.left_card)
        
        # Right Card: Form Fields & Buttons
        self.right_card = QFrame()
        self.right_card.setStyleSheet("""
            QFrame {
                background-color: rgba(22, 27, 34, 180);
                border: 1px solid #30363d;
                border-radius: 12px;
            }
        """)
        self.right_card.setFixedSize(400, 160)
        right_layout = QVBoxLayout(self.right_card)
        right_layout.setContentsMargins(20, 15, 20, 15)
        right_layout.setSpacing(10)
        
        # Form layout for name and location
        form_layout = QVBoxLayout()
        form_layout.setSpacing(8)
        
        # Name row
        name_row = QHBoxLayout()
        name_lbl = QLabel("Name:")
        name_lbl.setFixedWidth(55)
        name_lbl.setStyleSheet("color: #c9d1d9; font-weight: bold; border: none; background: transparent; font-size: 12px;")
        self.name_edit = QLineEdit()
        self.name_edit.setStyleSheet("""
            QLineEdit {
                background: #0d1117; color: #00e5ff; border: 1px solid #30363d; border-radius: 4px; padding: 6px 8px; font-size: 12px;
            }
            QLineEdit:focus { border: 1px solid #00d2ff; }
        """)
        self.name_edit.textChanged.connect(self._on_name_changed)
        name_row.addWidget(name_lbl)
        name_row.addWidget(self.name_edit)
        form_layout.addLayout(name_row)
        
        # Location row
        loc_row = QHBoxLayout()
        loc_lbl = QLabel("Location:")
        loc_lbl.setFixedWidth(55)
        loc_lbl.setStyleSheet("color: #c9d1d9; font-weight: bold; border: none; background: transparent; font-size: 12px;")
        
        self.loc_display = QLineEdit(self.default_dir)
        self.loc_display.setReadOnly(True)
        self.loc_display.setStyleSheet("background: #0d1117; color: #8b949e; border: 1px solid #30363d; border-radius: 4px; padding: 6px 8px; font-size: 12px;")
        
        self.browse_btn = QPushButton("Browse")
        self.browse_btn.setCursor(get_custom_cursor())
        self.browse_btn.setStyleSheet("""
            QPushButton { background: #21262d; color: #c9d1d9; border: 1px solid #30363d; border-radius: 4px; padding: 6px 12px; font-size: 12px; }
            QPushButton:hover { background: #30363d; border-color: #8b949e; }
        """)
        self.browse_btn.clicked.connect(self._browse_loc)
        
        loc_row.addWidget(loc_lbl)
        loc_row.addWidget(self.loc_display)
        loc_row.addWidget(self.browse_btn)
        form_layout.addLayout(loc_row)
        
        right_layout.addLayout(form_layout)
        right_layout.addStretch()
        
        # Buttons row
        btn_row = QHBoxLayout()
        
        self.reset_btn = QPushButton("Start Over")
        self.reset_btn.setCursor(get_custom_cursor())
        self.reset_btn.setStyleSheet("""
            QPushButton { background: transparent; color: #8b949e; border: 1px solid #30363d; border-radius: 6px; padding: 8px 16px; font-weight: bold; }
            QPushButton:hover { color: #ff6b6b; border: 1px solid #ff6b6b; }
        """)
        self.reset_btn.clicked.connect(self.start_over_clicked.emit)
        
        self.save_btn = QPushButton("Save File")
        self.save_btn.setCursor(get_custom_cursor())
        self.save_btn.setStyleSheet("""
            QPushButton { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0f2438, stop:1 #091724); color: #00e5ff; border: 1.5px solid #00d2ff; border-radius: 6px; padding: 8px 24px; font-weight: bold; }
            QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #153754, stop:1 #0d253b); border: 1.5px solid #38bdf8; color: #ffffff; }
        """)
        self.save_btn.clicked.connect(self._save_file)
        
        btn_row.addWidget(self.reset_btn)
        btn_row.addStretch()
        btn_row.addWidget(self.save_btn)
        
        right_layout.addLayout(btn_row)
        
        main_layout.addWidget(self.right_card)
        
    def show_output(self, file_path):
        self.file_path = file_path
        self.name_edit.blockSignals(True)
        self.name_edit.setText(os.path.basename(file_path))
        self.name_edit.blockSignals(False)
        self.icon_label.file_path = file_path
        if os.path.isdir(file_path):
            self.icon_label.setPixmap(get_icon("folder", "#00e5ff").pixmap(64, 64))
            self.title_label.setText("Folder Successfully Created!")
            self.save_btn.setText("Save Folder")
        else:
            self.title_label.setText("File Successfully Created!")
            self.save_btn.setText("Save File")
            ext = os.path.splitext(file_path)[1].lower()
            if ext in ['.zip', '.rar']:
                self.icon_label.setPixmap(get_icon("compress", "#00e5ff").pixmap(64, 64))
            elif ext in ['.jpg', '.png']:
                self.icon_label.setPixmap(get_icon("image", "#00e5ff").pixmap(64, 64))
            elif ext == '.docx':
                self.icon_label.setPixmap(get_icon("description", "#00e5ff").pixmap(64, 64))
            else:
                self.icon_label.setPixmap(get_icon("pdf", "#00e5ff").pixmap(64, 64))
            
        self.show()
        
    def _on_name_changed(self, text):
        if not self.file_path or not os.path.exists(self.file_path): return
        if not text: return
        dir_name = os.path.dirname(self.file_path)
        new_path = os.path.join(dir_name, text)
        if new_path != self.file_path:
            try:
                os.rename(self.file_path, new_path)
                self.file_path = new_path
                self.icon_label.file_path = new_path
            except Exception:
                pass
                
    def _browse_loc(self):
        d = QFileDialog.getExistingDirectory(self, "Select Save Location", self.default_dir)
        if d:
            self.default_dir = os.path.normpath(d)
            self.loc_display.setText(self.default_dir)
            
    def _save_file(self):
        if not self.file_path or not os.path.exists(self.file_path): return
        dest = os.path.join(self.default_dir, os.path.basename(self.file_path))
        
        # If they haven't explicitly dragged it, we save it here
        try:
            if os.path.abspath(self.file_path) != os.path.abspath(dest):
                if os.path.isdir(self.file_path):
                    if os.path.exists(dest):
                        shutil.rmtree(dest)
                    shutil.copytree(self.file_path, dest)
                    self.title_label.setText("Folder Saved Successfully!")
                else:
                    shutil.copy2(self.file_path, dest)
                    self.title_label.setText("Saved Successfully!")
            else:
                self.title_label.setText("Saved Successfully!")
            self.title_label.setStyleSheet("color: #3fb950; font-size: 18px; font-weight: 800; border: none; background: transparent;")
        except Exception as e:
            self.title_label.setText("Error Saving")
            self.title_label.setStyleSheet("color: #ff4444; font-size: 18px; font-weight: 800; border: none; background: transparent;")
