import os
from typing import List, Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLineEdit,
    QTreeView, QListView, QSplitter, QLabel, QAbstractItemView, QMessageBox,
    QFrame, QApplication, QGraphicsDropShadowEffect, QScrollArea
)
from PyQt6.QtCore import Qt, QDir, QModelIndex, QPoint, QSize, QStandardPaths, QSettings
from PyQt6.QtGui import QFileSystemModel, QColor
from .icons import get_svg_pixmap, get_icon


def get_windows_quick_access_links() -> List[dict]:
    """Retrieve Windows Quick Access pinned, frequent, and standard shell directories."""
    links = []
    seen = set()

    def add(name, path, icon_type="folder"):
        if not path:
            return
        try:
            norm = os.path.normpath(path)
        except Exception:
            return
        lower = norm.lower()
        if lower in seen or not os.path.isdir(norm):
            return
        # Exclude temporary, cache, internal hidden app data
        appdata = os.path.expandvars(r"%APPDATA%").lower()
        localappdata = os.path.expandvars(r"%LOCALAPPDATA%").lower()
        if (lower.startswith(localappdata) or lower.startswith(appdata)) and not lower.endswith("desktop"):
            return
        if "$recycle.bin" in lower or "system volume information" in lower:
            return

        seen.add(lower)
        links.append({"name": name, "path": norm, "icon": icon_type})

    # 1. Standard Windows User folders
    std_folders = [
        ("Desktop", QStandardPaths.StandardLocation.DesktopLocation, "desktop"),
        ("Downloads", QStandardPaths.StandardLocation.DownloadLocation, "download"),
        ("Documents", QStandardPaths.StandardLocation.DocumentsLocation, "document"),
        ("Pictures", QStandardPaths.StandardLocation.PicturesLocation, "image"),
        ("Videos", QStandardPaths.StandardLocation.MoviesLocation, "video"),
        ("Music", QStandardPaths.StandardLocation.MusicLocation, "music"),
    ]
    for name, loc, icon_type in std_folders:
        try:
            p = QStandardPaths.writableLocation(loc)
            add(name, p, icon_type)
        except Exception:
            pass

    # 2. Windows Quick Access pinned & frequent items from AutomaticDestinations
    auto_file = os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Recent\AutomaticDestinations\f01b4d95cf55d32a.automaticDestinations-ms")
    if os.path.exists(auto_file):
        try:
            import re
            with open(auto_file, "rb") as f:
                data = f.read()
            text = data.decode("utf-16le", errors="ignore")
            matches = re.findall(r"[A-Za-z]:\\[^\x00\r\n\"<>|?*]{2,}", text)
            for m in matches:
                p = m.strip()
                if os.path.isdir(p):
                    base = os.path.basename(p) or p
                    if base.lower() == "desktop" and not p.lower().startswith("c:"):
                        drive = os.path.splitdrive(p)[0]
                        base = f"{drive} Desktop"
                    add(base, p, "pin")
        except Exception:
            pass

    return links


def get_mru_directories() -> List[str]:
    """Retrieve list of most recently used directories, persisting across sessions."""
    settings = QSettings("OmniMesh", "OmniMesh")
    stored = settings.value("recent_directories", [])
    if isinstance(stored, str):
        stored = [stored] if stored else []

    valid = []
    seen = set()
    for p in stored:
        try:
            norm = os.path.normpath(p)
            lower = norm.lower()
            if os.path.isdir(norm) and lower not in seen:
                seen.add(lower)
                valid.append(norm)
        except Exception:
            pass

    # If empty, seed from Windows recent or common locations
    if not valid:
        auto_file = os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Recent\AutomaticDestinations\f01b4d95cf55d32a.automaticDestinations-ms")
        if os.path.exists(auto_file):
            try:
                import re
                with open(auto_file, "rb") as f:
                    data = f.read()
                text = data.decode("utf-16le", errors="ignore")
                matches = re.findall(r"[A-Za-z]:\\[^\x00\r\n\"<>|?*]{2,}", text)
                for m in matches:
                    p = os.path.normpath(m.strip())
                    lower = p.lower()
                    if os.path.isdir(p) and lower not in seen:
                        seen.add(lower)
                        valid.append(p)
            except Exception:
                pass

        if not valid:
            home = os.path.expanduser("~")
            if os.path.isdir(home):
                valid.append(os.path.normpath(home))

    return valid[:10]


def record_mru_directory(path: str):
    """Record a directory as the most recently used, moving it to the top."""
    if not path or not os.path.isdir(path):
        return
    norm = os.path.normpath(path)
    settings = QSettings("OmniMesh", "OmniMesh")
    stored = settings.value("recent_directories", [])
    if isinstance(stored, str):
        stored = [stored] if stored else []

    updated = [norm]
    for p in stored:
        try:
            p_norm = os.path.normpath(p)
            if p_norm.lower() != norm.lower() and os.path.isdir(p_norm):
                updated.append(p_norm)
        except Exception:
            pass
    settings.setValue("recent_directories", updated[:10])


class HorizontalScrollArea(QScrollArea):
    """Horizontal scroll area that responds directly to vertical mouse wheel for smooth scrolling."""
    def wheelEvent(self, event):
        delta = event.angleDelta().y() or event.angleDelta().x()
        if delta:
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta)
            event.accept()
        else:
            super().wheelEvent(event)


class DraggableTitleBar(QWidget):
    """Header title bar that enables moving the parent dialog by dragging anywhere on it."""
    def __init__(self, dialog: 'CustomFileDialog', parent=None):
        super().__init__(parent)
        self.dialog = dialog
        self.setMouseTracking(True)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dialog.start_window_drag(event.globalPosition().toPoint())
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.dialog._drag_pos is not None:
            self.dialog.update_window_drag(event.globalPosition().toPoint())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dialog.end_window_drag()
            event.accept()
            return
        super().mouseReleaseEvent(event)


class DraggableFrame(QFrame):
    """Container frame that renders the metallic translucent background and allows window dragging."""
    def __init__(self, dialog: 'CustomFileDialog', parent=None):
        super().__init__(parent)
        self.dialog = dialog
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setMouseTracking(True)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dialog.start_window_drag(event.globalPosition().toPoint())
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.dialog._drag_pos is not None:
            self.dialog.update_window_drag(event.globalPosition().toPoint())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dialog.end_window_drag()
            event.accept()
            return
        super().mouseReleaseEvent(event)


class CustomFileDialog(QDialog):
    """
    A custom file explorer dialog matching the OmniMesh theme, transparency, movement,
    with Windows Quick Access links and Most Recently Used directory entries below the main file system window.
    """
    def __init__(self, parent=None, start_dir=None):
        super().__init__(parent)
        self.setWindowTitle("OmniMesh - File Explorer")
        self.setMinimumSize(940, 620)
        self.resize(1020, 680)
        self._drag_pos: Optional[QPoint] = None
        self._qa_buttons: List[QPushButton] = []
        self._mru_list: List[str] = get_mru_directories()

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMouseTracking(True)

        self.selected_files: List[str] = []
        self.current_dir = start_dir or (self._mru_list[0] if self._mru_list else os.path.expanduser("~"))

        self._setup_ui()
        self._set_directory(self.current_dir, scroll_tree=False)
        self.tree_view.collapseAll()
        self._center_dialog(parent)

    def showEvent(self, event):
        super().showEvent(event)
        self.tree_view.collapseAll()

    def _center_dialog(self, parent=None):
        if parent and hasattr(parent, 'geometry') and parent.isVisible():
            p_geo = parent.geometry()
            self.move(
                p_geo.x() + (p_geo.width() - self.width()) // 2,
                p_geo.y() + (p_geo.height() - self.height()) // 2
            )
        elif app := QApplication.instance():
            screen = app.primaryScreen().geometry()
            self.move(
                (screen.width() - self.width()) // 2,
                (screen.height() - self.height()) // 2
            )

    def start_window_drag(self, global_pos: QPoint):
        """Initiate window dragging using global coordinates."""
        self._drag_pos = global_pos

    def update_window_drag(self, global_pos: QPoint):
        """Update window position during manual drag."""
        if self._drag_pos is not None:
            delta = global_pos - self._drag_pos
            self.move(self.pos() + delta)
            self._drag_pos = global_pos

    def end_window_drag(self):
        """End window drag."""
        self._drag_pos = None

    def _get_edge(self, pos: QPoint) -> Qt.Edge:
        edge = Qt.Edge(0)
        margin = 12
        if pos.x() <= margin:
            edge |= Qt.Edge.LeftEdge
        elif pos.x() >= self.width() - margin:
            edge |= Qt.Edge.RightEdge
        if pos.y() <= margin:
            edge |= Qt.Edge.TopEdge
        elif pos.y() >= self.height() - margin:
            edge |= Qt.Edge.BottomEdge
        return edge

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            edge = self._get_edge(event.pos())
            if edge != Qt.Edge(0):
                wh = self.windowHandle()
                if wh and hasattr(wh, "startSystemResize"):
                    try:
                        wh.startSystemResize(edge)
                        return
                    except Exception:
                        pass
            self.start_window_drag(event.globalPosition().toPoint())
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        edge = self._get_edge(event.pos())
        if edge in (Qt.Edge.LeftEdge, Qt.Edge.RightEdge):
            self.setCursor(Qt.CursorShape.SizeHorCursor)
        elif edge in (Qt.Edge.TopEdge, Qt.Edge.BottomEdge):
            self.setCursor(Qt.CursorShape.SizeVerCursor)
        elif edge in (Qt.Edge.LeftEdge | Qt.Edge.TopEdge, Qt.Edge.RightEdge | Qt.Edge.BottomEdge):
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        elif edge in (Qt.Edge.RightEdge | Qt.Edge.TopEdge, Qt.Edge.LeftEdge | Qt.Edge.BottomEdge):
            self.setCursor(Qt.CursorShape.SizeBDiagCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)

        if self._drag_pos is not None:
            self.update_window_drag(event.globalPosition().toPoint())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.end_window_drag()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def _setup_ui(self):
        self.setStyleSheet("""
            QDialog { background: transparent; }
            #main_frame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(28, 33, 43, 230), stop:0.5 rgba(16, 20, 28, 220), stop:1 rgba(8, 10, 15, 230));
                border-top: 1.5px solid rgba(255, 255, 255, 40);
                border-left: 1.5px solid rgba(255, 255, 255, 30);
                border-right: 1.5px solid rgba(0, 210, 255, 150);
                border-bottom: 1.5px solid rgba(0, 210, 255, 150);
                border-top-left-radius: 40px;
                border-top-right-radius: 8px;
                border-bottom-left-radius: 8px;
                border-bottom-right-radius: 40px;
            }
            QTreeView, QListView {
                background-color: rgba(17, 21, 31, 200);
                color: #c9d1d9;
                border: 1px solid rgba(48, 54, 61, 180);
                border-radius: 8px;
                outline: 0;
                padding: 4px;
            }
            QTreeView::item, QListView::item {
                padding: 4px 6px;
                border-radius: 4px;
            }
            QTreeView::item:selected, QListView::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(0, 168, 204, 180), stop:1 rgba(15, 36, 56, 200));
                color: #ffffff;
                border: 1px solid rgba(0, 210, 255, 150);
            }
            QTreeView::item:hover:!selected, QListView::item:hover:!selected {
                background-color: rgba(33, 38, 45, 180);
                color: #f0f6fc;
            }
            QHeaderView::section {
                background-color: rgba(22, 27, 34, 220);
                color: #8b949e;
                border: none;
                border-bottom: 1px solid rgba(48, 54, 61, 180);
                padding: 6px 8px;
                font-weight: 600;
            }
            QLineEdit {
                background-color: rgba(17, 21, 31, 200);
                color: #f0f6fc;
                border: 1px solid rgba(48, 54, 61, 180);
                border-radius: 6px;
                padding: 7px 10px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1.5px solid #00d2ff;
                background-color: rgba(22, 27, 34, 230);
            }
            QPushButton {
                background-color: #162438;
                color: #c9d1d9;
                border: 1px solid #1f2737;
                border-radius: 6px;
                padding: 7px 18px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #1f3350;
                border-color: #38bdf8;
                color: #ffffff;
            }
            #primary_btn {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0f2438, stop:1 #091724);
                color: #00e5ff;
                border: 1.5px solid #00d2ff;
                border-radius: 6px;
                padding: 7px 20px;
                font-weight: 700;
                font-size: 12px;
                letter-spacing: 0.5px;
            }
            #primary_btn:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #153754, stop:1 #0d253b);
                border: 1.5px solid #38bdf8;
                color: #ffffff;
            }
            QScrollBar:vertical {
                background: rgba(13, 17, 23, 100);
                width: 10px;
                margin: 0;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: rgba(56, 189, 248, 80);
                min-height: 24px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(0, 210, 255, 180);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
            QScrollBar:horizontal {
                background: rgba(13, 17, 23, 100);
                height: 8px;
                margin: 0;
                border-radius: 4px;
            }
            QScrollBar::handle:horizontal {
                background: rgba(56, 189, 248, 80);
                min-width: 24px;
                border-radius: 4px;
            }
            QScrollBar::handle:horizontal:hover {
                background: rgba(0, 210, 255, 180);
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0;
            }
            QSplitter::handle {
                background-color: rgba(48, 54, 61, 80);
                width: 3px;
                border-radius: 1px;
            }
            QSplitter::handle:hover {
                background-color: #00d2ff;
            }
            #qa_container, #recent_container {
                background-color: rgba(17, 21, 31, 180);
                border: 1px solid rgba(48, 54, 61, 150);
                border-radius: 8px;
            }
            #qa_title, #recent_title {
                color: #00d2ff;
                font-size: 11px;
                font-weight: 800;
                letter-spacing: 0.8px;
            }
            QScrollArea {
                background: transparent;
                border: none;
            }
            QPushButton#qa_btn {
                background-color: rgba(22, 27, 34, 210);
                color: #c9d1d9;
                border: 1px solid rgba(48, 54, 61, 180);
                border-radius: 5px;
                padding: 3px 8px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton#qa_btn:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #153754, stop:1 #0d253b);
                border: 1px solid #00d2ff;
                color: #ffffff;
            }
            QPushButton#qa_btn[active="true"] {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0f2438, stop:1 #091724);
                border: 1.5px solid #00d2ff;
                color: #00e5ff;
                font-weight: 700;
            }
            QLineEdit#recent_edit {
                background-color: rgba(22, 27, 34, 220);
                color: #00e5ff;
                border: 1px solid rgba(48, 54, 61, 180);
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 12px;
            }
            QLineEdit#recent_edit:focus {
                border: 1.5px solid #00d2ff;
                background-color: rgba(22, 27, 34, 240);
                color: #ffffff;
            }
            QPushButton#recent_go_btn {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0f2438, stop:1 #091724);
                color: #00e5ff;
                border: 1px solid #00d2ff;
                border-radius: 6px;
                padding: 4px 16px;
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 0.5px;
            }
            QPushButton#recent_go_btn:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #153754, stop:1 #0d253b);
                border: 1.5px solid #38bdf8;
                color: #ffffff;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        main_frame = DraggableFrame(self, self)
        main_frame.setObjectName("main_frame")

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 4)
        main_frame.setGraphicsEffect(shadow)

        main_layout = QVBoxLayout(main_frame)
        main_layout.setContentsMargins(20, 16, 20, 20)
        main_layout.setSpacing(10)

        # Draggable Top Title Bar
        title_bar_widget = DraggableTitleBar(self, main_frame)
        title_bar = QHBoxLayout(title_bar_widget)
        title_bar.setContentsMargins(0, 0, 0, 4)
        title_bar.setSpacing(8)
        title_bar.addStretch()

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #8b949e;
                border: none;
                font-size: 15px;
                font-weight: bold;
                border-radius: 14px;
                padding: 0;
            }
            QPushButton:hover {
                background-color: #c53030;
                color: #ffffff;
            }
        """)
        close_btn.clicked.connect(self.reject)
        title_bar.addWidget(close_btn)

        main_layout.addWidget(title_bar_widget)

        # Header / Navigation
        nav_layout = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setText(self.current_dir)
        self.path_edit.returnPressed.connect(self._on_path_entered)

        path_lbl = QLabel("<span style='color:#8b949e; font-weight:bold;'>Path:</span>")
        path_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        nav_layout.addWidget(path_lbl)
        nav_layout.addWidget(self.path_edit, 1)

        self.up_btn = QPushButton("Up")
        self.up_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.up_btn.clicked.connect(self._go_up)
        nav_layout.addWidget(self.up_btn)

        main_layout.addLayout(nav_layout)

        # Splitter for Tree and List (Main File System Window)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # File System Models
        self.dir_model = QFileSystemModel()
        self.dir_model.setFilter(QDir.Filter.NoDotAndDotDot | QDir.Filter.AllDirs)
        self.dir_model.setRootPath(QDir.rootPath())

        self.file_model = QFileSystemModel()
        self.file_model.setFilter(QDir.Filter.NoDotAndDotDot | QDir.Filter.AllDirs | QDir.Filter.Files)
        self.file_model.setRootPath(QDir.rootPath())

        # Tree View (Directories)
        self.tree_view = QTreeView()
        self.tree_view.setModel(self.dir_model)
        self.tree_view.setHeaderHidden(True)
        self.tree_view.setColumnHidden(1, True)
        self.tree_view.setColumnHidden(2, True)
        self.tree_view.setColumnHidden(3, True)
        self.tree_view.clicked.connect(self._on_tree_clicked)

        # List View (Files in directory)
        self.list_view = QListView()
        self.list_view.setModel(self.file_model)
        self.list_view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.list_view.doubleClicked.connect(self._on_list_double_clicked)

        splitter.addWidget(self.tree_view)
        splitter.addWidget(self.list_view)
        splitter.setSizes([300, 660])
        main_layout.addWidget(splitter, 1)

        # 1. Quick Access Section (Positioned directly below the main file system window)
        qa_container = QFrame()
        qa_container.setObjectName("qa_container")
        qa_container_layout = QHBoxLayout(qa_container)
        qa_container_layout.setContentsMargins(10, 4, 10, 4)
        qa_container_layout.setSpacing(10)

        qa_header = QHBoxLayout()
        qa_header.setSpacing(6)
        qa_icon = QLabel()
        qa_icon.setPixmap(get_svg_pixmap("pin", 14, "#00d2ff"))
        qa_icon.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        qa_header.addWidget(qa_icon)

        qa_title = QLabel("QUICK ACCESS")
        qa_title.setObjectName("qa_title")
        qa_title.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        qa_header.addWidget(qa_title)
        qa_container_layout.addLayout(qa_header)

        # Smooth horizontal scroll area for quick access buttons (scrollbar hidden to fit seamlessly)
        qa_scroll = HorizontalScrollArea()
        qa_scroll.setWidgetResizable(True)
        qa_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        qa_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        qa_scroll.setFixedHeight(30)
        qa_scroll.setFrameShape(QFrame.Shape.NoFrame)

        qa_scroll_content = QWidget()
        qa_buttons_layout = QHBoxLayout(qa_scroll_content)
        qa_buttons_layout.setContentsMargins(0, 0, 0, 0)
        qa_buttons_layout.setSpacing(4)

        self._qa_buttons = []
        for item in get_windows_quick_access_links():
            btn = QPushButton(f" {item['name']}")
            btn.setObjectName("qa_btn")
            btn.setProperty("path", item["path"])
            icon_color = "#00d2ff" if item["icon"] in ("pin", "desktop") else "#8b949e"
            btn.setIcon(get_icon(item["icon"], icon_color))
            btn.setIconSize(QSize(13, 13))
            btn.setToolTip(item["path"])
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, p=item["path"]: self._on_quick_access_clicked(p))
            qa_buttons_layout.addWidget(btn)
            self._qa_buttons.append(btn)

        qa_buttons_layout.addStretch()
        qa_scroll.setWidget(qa_scroll_content)
        qa_container_layout.addWidget(qa_scroll, 1)

        main_layout.addWidget(qa_container)

        # 2. Most Recently Used Directory Section (Singular field entry without extra pill extensions)
        recent_container = QFrame()
        recent_container.setObjectName("recent_container")
        recent_container_layout = QHBoxLayout(recent_container)
        recent_container_layout.setContentsMargins(10, 4, 10, 4)
        recent_container_layout.setSpacing(10)

        recent_header = QHBoxLayout()
        recent_header.setSpacing(6)
        recent_icon = QLabel()
        recent_icon.setPixmap(get_svg_pixmap("clock", 14, "#00d2ff"))
        recent_icon.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        recent_header.addWidget(recent_icon)

        recent_title = QLabel("RECENT")
        recent_title.setObjectName("recent_title")
        recent_title.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        recent_header.addWidget(recent_title)
        recent_container_layout.addLayout(recent_header)

        # Singular path field entry displaying the most recently used directory
        self.recent_dir_edit = QLineEdit()
        self.recent_dir_edit.setObjectName("recent_edit")
        most_recent = self._mru_list[0] if self._mru_list else self.current_dir
        self.recent_dir_edit.setText(most_recent)
        self.recent_dir_edit.setPlaceholderText("Most recently used directory path...")
        self.recent_dir_edit.returnPressed.connect(self._on_recent_go_clicked)
        recent_container_layout.addWidget(self.recent_dir_edit, 1)

        self.recent_go_btn = QPushButton("Go")
        self.recent_go_btn.setObjectName("recent_go_btn")
        self.recent_go_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.recent_go_btn.clicked.connect(self._on_recent_go_clicked)
        recent_container_layout.addWidget(self.recent_go_btn)

        main_layout.addWidget(recent_container)

        # Footer Buttons
        footer_layout = QHBoxLayout()
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_btn.clicked.connect(self.reject)

        self.open_btn = QPushButton("Open Selected")
        self.open_btn.setObjectName("primary_btn")
        self.open_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.open_btn.clicked.connect(self._accept_selection)

        footer_layout.addStretch()
        footer_layout.addWidget(self.cancel_btn)
        footer_layout.addWidget(self.open_btn)
        main_layout.addLayout(footer_layout)

        layout.addWidget(main_frame)

    def _on_quick_access_clicked(self, path: str):
        if os.path.isdir(path):
            self._set_directory(path, scroll_tree=True)

    def _on_recent_go_clicked(self):
        path = self.recent_dir_edit.text().strip()
        if os.path.exists(path) and os.path.isdir(path):
            self._set_directory(path, scroll_tree=True)
            record_mru_directory(path)
        else:
            QMessageBox.warning(self, "Invalid Path", "The specified recent path does not exist.")

    def _update_qa_active_state(self):
        curr_norm = os.path.normpath(self.current_dir).lower()
        for btn in self._qa_buttons:
            btn_path = os.path.normpath(btn.property("path") or "").lower()
            if curr_norm == btn_path:
                btn.setProperty("active", "true")
            else:
                btn.setProperty("active", "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def _set_directory(self, path: str, scroll_tree: bool = True):
        if os.path.isdir(path):
            self.current_dir = os.path.normpath(path)
            self.path_edit.setText(self.current_dir)
            if hasattr(self, "recent_dir_edit"):
                self.recent_dir_edit.setText(self.current_dir)

            record_mru_directory(self.current_dir)

            tree_idx = self.dir_model.index(self.current_dir)
            self.tree_view.setCurrentIndex(tree_idx)
            if scroll_tree:
                self.tree_view.scrollTo(tree_idx)

            list_idx = self.file_model.index(self.current_dir)
            self.list_view.setRootIndex(list_idx)

            self._update_qa_active_state()

    def _on_path_entered(self):
        path = self.path_edit.text()
        if os.path.exists(path):
            if os.path.isdir(path):
                self._set_directory(path)
        else:
            QMessageBox.warning(self, "Invalid Path", "The specified path does not exist.")

    def _go_up(self):
        parent_dir = os.path.dirname(self.current_dir)
        if parent_dir and os.path.exists(parent_dir):
            self._set_directory(parent_dir)

    def _on_tree_clicked(self, index: QModelIndex):
        path = self.dir_model.filePath(index)
        self._set_directory(path)

    def _on_list_double_clicked(self, index: QModelIndex):
        path = self.file_model.filePath(index)
        if os.path.isdir(path):
            self._set_directory(path)
        else:
            self.selected_files = [path]
            self.accept()

    def _accept_selection(self):
        indexes = self.list_view.selectionModel().selectedIndexes()
        paths = set()
        for idx in indexes:
            paths.add(self.file_model.filePath(idx))

        valid_paths = [p for p in paths if os.path.isfile(p)]
        if valid_paths:
            self.selected_files = valid_paths
            # Record directory as most recently used
            first_dir = os.path.dirname(valid_paths[0])
            record_mru_directory(first_dir)
            self.accept()
        else:
            QMessageBox.information(self, "No Files", "Please select at least one file to open.")
