"""
Main application window assembling Header, Tabs, Controls, Carousel, and Action Bar.
Free-floating dark metallic UI with dark neon blue highlights.
Handles file picking, OS drag-and-drop, worker threads, and file conversions.
"""

import os
import subprocess
from typing import List
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFileDialog,
    QMessageBox, QApplication, QFrame, QPushButton, QSystemTrayIcon, QMenu
)
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QColor, QIcon

from core.file_item import FileItem, FileStatus
from core.pdf_engine import PDFEngine
from core.worker import TaskWorker
from core.app_icon import get_app_icon

from .tabs_bar import TabsBar, ToolMode
from .carousel_view import CarouselView
from .action_bar import ActionBar
from .output_view import OutputView

import sys
if sys.platform == "win32":
    import ctypes
    import ctypes.wintypes

    WM_DROPFILES = 0x0233
    WM_COPYDATA = 0x004A
    WM_COPYGLOBALDATA = 0x0049
    MSGFLT_ALLOW = 1

    class WinMSG(ctypes.Structure):
        _fields_ = [
            ("hwnd",    ctypes.wintypes.HWND),
            ("message", ctypes.c_uint),
            ("wParam",  ctypes.wintypes.WPARAM),
            ("lParam",  ctypes.wintypes.LPARAM),
            ("time",    ctypes.wintypes.DWORD),
            ("pt",      ctypes.wintypes.POINT),
        ]

    try:
        user32 = ctypes.windll.user32
        shell32 = ctypes.windll.shell32

        if hasattr(user32, "ChangeWindowMessageFilterEx"):
            user32.ChangeWindowMessageFilterEx.argtypes = [
                ctypes.wintypes.HWND,
                ctypes.wintypes.UINT,
                ctypes.wintypes.DWORD,
                ctypes.c_void_p
            ]
            user32.ChangeWindowMessageFilterEx.restype = ctypes.wintypes.BOOL

        shell32.DragAcceptFiles.argtypes = [ctypes.wintypes.HWND, ctypes.wintypes.BOOL]
        shell32.DragAcceptFiles.restype = None

        shell32.DragQueryFileW.argtypes = [
            ctypes.wintypes.WPARAM,
            ctypes.wintypes.UINT,
            ctypes.wintypes.LPWSTR,
            ctypes.wintypes.UINT
        ]
        shell32.DragQueryFileW.restype = ctypes.wintypes.UINT

        shell32.DragFinish.argtypes = [ctypes.wintypes.WPARAM]
        shell32.DragFinish.restype = None
    except Exception:
        pass


class MainWindow(QMainWindow):
    """OmniMesh main application window featuring a free-floating dark metallic interface."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("OmniMesh - Advanced File Manipulator")
        self.setMinimumWidth(940)
        self.setFixedHeight(420) # Lock vertical resize, make it very slim
        self.resize(1350, 420)

        # Set window icon (taskbar / quickbar / titlebar)
        app_icon = get_app_icon()
        if not app_icon.isNull():
            self.setWindowIcon(app_icon)

        self.current_mode = ToolMode.COMBINE_PDF
        self.file_items: List[FileItem] = []
        self.worker: TaskWorker = None
        self._drag_pos: QPoint = None

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self.setAcceptDrops(True)
        self._dnd_registered = False

        self._setup_ui()
        
        self.particle_cursor = self._get_particle_cursor()
        self.setCursor(self.particle_cursor)
        
        # Install a global event filter to seamlessly handle cursor changes on edges
        from PyQt6.QtCore import QCoreApplication
        QCoreApplication.instance().installEventFilter(self)

        # NOTE: _bypass_uipi_for_drag_drop is intentionally NOT called here.
        # It must run AFTER show() so it can override Qt's OLE DnD registration.
        # See showEvent().

    def showEvent(self, event):
        """Register WM_DROPFILES AFTER Qt has finished its internal OLE DnD setup."""
        super().showEvent(event)
        if not self._dnd_registered:
            # Defer by one event-loop cycle so RegisterDragDrop has fully completed
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(50, self._bypass_uipi_for_drag_drop)

    def _bypass_uipi_for_drag_drop(self):
        """Register HWND as a shell drop target via WM_DROPFILES and bypass UIPI.

        On Windows, Qt registers an OLE IDropTarget during show().  OLE drag-and-drop
        is blocked by UIPI when our process is elevated and the drag source (Explorer)
        is not.  We work around this by:
          1. Revoking Qt's OLE drop target
          2. Allowing WM_DROPFILES through the UIPI message filter
          3. Registering for the legacy WM_DROPFILES mechanism via DragAcceptFiles
        """
        if sys.platform != "win32" or self._dnd_registered:
            return
        try:
            hwnd = int(self.winId())

            # Step 1: Revoke Qt's OLE drop target so DragAcceptFiles can take over
            try:
                ole32 = ctypes.windll.ole32
                ole32.RevokeDragDrop.argtypes = [ctypes.wintypes.HWND]
                ole32.RevokeDragDrop.restype = ctypes.wintypes.LONG
                ole32.RevokeDragDrop(hwnd)
            except Exception:
                pass

            # Step 2: Punch through UIPI for drop-related messages
            if hasattr(user32, "ChangeWindowMessageFilterEx"):
                user32.ChangeWindowMessageFilterEx(hwnd, WM_DROPFILES, MSGFLT_ALLOW, None)
                user32.ChangeWindowMessageFilterEx(hwnd, WM_COPYDATA, MSGFLT_ALLOW, None)
                user32.ChangeWindowMessageFilterEx(hwnd, WM_COPYGLOBALDATA, MSGFLT_ALLOW, None)

            # Step 3: Register for WM_DROPFILES
            shell32.DragAcceptFiles(hwnd, True)
            self._dnd_registered = True
        except Exception as e:
            print(f"Drop registration failed: {e}")

    def nativeEvent(self, event_type, message):
        """Process Win32 WM_DROPFILES messages sent by Explorer / the shell."""
        if sys.platform == "win32":
            try:
                raw_type = bytes(event_type) if hasattr(event_type, "data") else event_type
                if raw_type in (b"windows_generic_MSG", "windows_generic_MSG"):
                    msg = WinMSG.from_address(int(message))
                    if msg.message == WM_DROPFILES:
                        hDrop = msg.wParam
                        count = shell32.DragQueryFileW(hDrop, 0xFFFFFFFF, None, 0)
                        paths = []
                        for i in range(count):
                            buf_len = shell32.DragQueryFileW(hDrop, i, None, 0) + 1
                            buf = ctypes.create_unicode_buffer(buf_len)
                            shell32.DragQueryFileW(hDrop, i, buf, buf_len)
                            paths.append(buf.value)
                        shell32.DragFinish(hDrop)
                        if paths:
                            self._add_files(paths)
                        return True, 0
            except Exception as e:
                print(f"nativeEvent drop error: {e}")

        return False, 0

    def eventFilter(self, obj, event):
        # We only care about mouse moves for updating the edge-resizing cursors
        if event.type() == event.Type.MouseMove:
            # Respect global override cursors and mouse grabs (e.g. BlankCursor during card drag)
            from PyQt6.QtWidgets import QApplication, QWidget
            if QApplication.overrideCursor() is not None or QWidget.mouseGrabber() is not None:
                return super().eventFilter(obj, event)
            # Map the global cursor position to window coordinates
            from PyQt6.QtGui import QCursor
            pos = self.mapFromGlobal(QCursor.pos())
            
            # Check if we are hovering over an edge
            edge = self._get_edge(pos)
            if edge == Qt.Edge.LeftEdge or edge == Qt.Edge.RightEdge:
                self.setCursor(Qt.CursorShape.SizeHorCursor)
            else:
                if hasattr(self, 'particle_cursor'):
                    self.setCursor(self.particle_cursor)
                else:
                    self.setCursor(Qt.CursorShape.ArrowCursor)
                
        return super().eventFilter(obj, event)

    def _get_edge(self, pos: QPoint) -> Qt.Edge:
        edge = Qt.Edge(0)
        margin = 15 # Include the 10px transparent padding + 5px grab area
        
        if pos.x() <= margin:
            edge |= Qt.Edge.LeftEdge
        elif pos.x() >= self.width() - margin:
            edge |= Qt.Edge.RightEdge
            
        # Vertical resizing is disabled, so we only return horizontal edges
        return edge

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            edge = self._get_edge(event.pos())
            if edge != Qt.Edge(0):
                self.windowHandle().startSystemResize(edge)
                return
            
            self._drag_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        from PyQt6.QtWidgets import QApplication, QWidget
        if QApplication.overrideCursor() is not None or QWidget.mouseGrabber() is not None:
            if self._drag_pos is not None:
                delta = event.globalPosition().toPoint() - self._drag_pos
                self.move(self.pos() + delta)
                self._drag_pos = event.globalPosition().toPoint()
            return

        # Update cursor based on hover position
        edge = self._get_edge(event.pos())
        if edge == Qt.Edge.LeftEdge or edge == Qt.Edge.RightEdge:
            self.setCursor(Qt.CursorShape.SizeHorCursor)
        else:
            if hasattr(self, 'particle_cursor'):
                self.setCursor(self.particle_cursor)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)

        # Handle moving the window
        if self._drag_pos is not None:
            delta = event.globalPosition().toPoint() - self._drag_pos
            self.move(self.pos() + delta)
            self._drag_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = None

    def changeEvent(self, event):
        if event.type() == event.Type.WindowStateChange:
            if self.isMinimized():
                self.hide()
                self.setWindowState(self.windowState() & ~Qt.WindowState.WindowMinimized)
                event.ignore()
                return
            super().changeEvent(event)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            from ui.cursor_fx import get_file_drag_cursor
            if QApplication.overrideCursor() is None:
                QApplication.setOverrideCursor(get_file_drag_cursor())
            event.acceptProposedAction()
            if hasattr(self, 'carousel') and self.carousel.isVisible():
                self.carousel._set_drag_style(True)
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        while QApplication.overrideCursor() is not None:
            QApplication.restoreOverrideCursor()
        if hasattr(self, 'carousel') and self.carousel.isVisible():
            self.carousel._set_drag_style(False)
        super().dragLeaveEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        while QApplication.overrideCursor() is not None:
            QApplication.restoreOverrideCursor()
        if hasattr(self, 'carousel') and self.carousel.isVisible():
            self.carousel._set_drag_style(False)

        if event.mimeData().hasUrls():
            paths = [u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()]
            if paths:
                self._add_files(paths)
                event.acceptProposedAction()

    def _get_particle_cursor(self):
        from PyQt6.QtGui import QCursor, QPixmap, QPainter, QColor
        from PyQt6.QtCore import Qt, QPointF
        
        size = 24
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        cx, cy = size / 2, size / 2
        
        # Subtle cyan outer glow
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(140, 230, 255, 120))
        painter.drawEllipse(QPointF(cx, cy), 5.0, 5.0)
        
        # Bright white particle core
        painter.setBrush(QColor(255, 255, 255, 255))
        painter.drawEllipse(QPointF(cx, cy), 2.0, 2.0)
        
        painter.end()
        return QCursor(pixmap, int(cx), int(cy))

    def _setup_ui(self):
        # Global dark dialog styling
        self.setStyleSheet("""
            QMessageBox {
                background-color: #11151f;
                color: #f0f6fc;
                border: 1px solid #1f2737;
            }
            QMessageBox QLabel {
                color: #f0f6fc;
                font-size: 13px;
            }
            QMessageBox QPushButton {
                background-color: #162438;
                color: #00e5ff;
                border: 1px solid #00d2ff;
                border-radius: 6px;
                padding: 6px 18px;
                font-size: 12px;
                font-weight: 700;
            }
            QMessageBox QPushButton:hover {
                background-color: #0077b6;
                color: #ffffff;
            }
            QFileDialog {
                background-color: #0d1117;
                color: #c9d1d9;
            }
            QFileDialog QWidget {
                background-color: #0d1117;
                color: #c9d1d9;
            }
            QFileDialog QListView, QFileDialog QTreeView {
                background-color: #161b22;
                color: #f0f6fc;
                border: 1px solid #2d333b;
                border-radius: 6px;
            }
            QFileDialog QHeaderView::section {
                background-color: #21262d;
                color: #8b949e;
                border: none;
                border-bottom: 1px solid #30363d;
                padding: 4px;
            }
            QFileDialog QPushButton {
                background-color: #162438;
                color: #00e5ff;
                border: 1px solid #00d2ff;
                border-radius: 6px;
                padding: 6px 18px;
                font-size: 12px;
                font-weight: 700;
            }
            QFileDialog QPushButton:hover {
                background-color: #1b304f;
                color: #ffffff;
            }
            QFileDialog QComboBox, QFileDialog QLineEdit {
                background-color: #161b22;
                color: #f0f6fc;
                border: 1px solid #30363d;
                border-radius: 4px;
                padding: 4px;
            }
            QFileDialog QLabel {
                color: #8b949e;
            }
        """)

        central_widget = QWidget()
        central_widget.setMouseTracking(True)
        base_layout = QVBoxLayout(central_widget)
        base_layout.setContentsMargins(10, 10, 10, 10) # Padding for the shadow/cut effect

        self.container_frame = QFrame()
        self.container_frame.setMouseTracking(True)
        self.container_frame.setObjectName("container_frame")
        self.container_frame.setStyleSheet("""
            #container_frame {
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
        """)
        
        # Premium drop shadow for the free-floating borderless effect
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 4)
        self.container_frame.setGraphicsEffect(shadow)
        
        # Center the window seamlessly on the primary display
        if app := QApplication.instance():
            screen = app.primaryScreen().geometry()
            self.move(
                (screen.width() - self.width()) // 2,
                (screen.height() - self.height()) // 2
            )
        
        main_layout = QVBoxLayout(self.container_frame)
        main_layout.setContentsMargins(16, 8, 16, 12)
        main_layout.setSpacing(8)

        # Custom window controls (Minimize and Close buttons)
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(0, 0, 0, 10)
        top_bar.setSpacing(8)
        top_bar.addStretch()
        
        min_btn = QPushButton("─")
        min_btn.setFixedSize(26, 26)
        min_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #8b949e;
                border: none;
                font-size: 14px;
                font-weight: bold;
                border-radius: 16px;
            }
            QPushButton:hover {
                background-color: #21262d;
                color: #ffffff;
            }
        """)
        min_btn.clicked.connect(self._animate_minimize_to_tray)
        
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(26, 26)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #8b949e;
                border: none;
                font-size: 16px;
                font-weight: bold;
                border-radius: 16px;
            }
            QPushButton:hover {
                background-color: #c53030;
                color: white;
            }
        """)
        close_btn.clicked.connect(self.close)
        
        top_bar.addWidget(min_btn)
        top_bar.addWidget(close_btn)
        main_layout.addLayout(top_bar)



        # 2. Free-floating Tabs Bar
        self.tabs_bar = TabsBar(self)
        self.tabs_bar.mode_changed.connect(self._on_mode_changed)
        main_layout.addWidget(self.tabs_bar)

        # 3. Free-floating File Cards Carousel & Clean Dropzone
        self.carousel = CarouselView(self)
        self.carousel.files_dropped.connect(self._add_files)
        self.carousel.file_removed.connect(self._on_file_removed)
        self.carousel.files_reordered.connect(self._on_files_reordered)
        main_layout.addWidget(self.carousel, 1)

        # Output View (Hidden by default)
        self.output_view = OutputView(self)
        self.output_view.start_over_clicked.connect(self._start_over)
        self.output_view.hide()
        main_layout.addWidget(self.output_view, 1)

        self.action_bar = ActionBar(self)
        self.action_bar.action_triggered.connect(self._execute_action)
        self.action_bar.upload_clicked.connect(self._open_file_dialog)
        self.action_bar.clear_clicked.connect(self._clear_files)
        self.action_bar.action_hovered.connect(self._on_action_hovered)
        main_layout.addWidget(self.action_bar)

        # Merge particle overlay for hover pull, collapse, and dramatic transition flash
        from ui.merge_particles import MergeParticleOverlay
        self.particle_overlay = MergeParticleOverlay(self)

        base_layout.addWidget(self.container_frame)
        self.setCentralWidget(central_widget)
        
        # System Tray Integration
        self.tray_icon = QSystemTrayIcon(self)
        from core.app_icon import get_tray_icon
        tray_icon = get_tray_icon()
        if not tray_icon.isNull():
            self.tray_icon.setIcon(tray_icon)
        self.tray_icon.setToolTip("OmniMesh")
        
        tray_menu = QMenu(self)
        tray_menu.setStyleSheet("""
            QMenu {
                background-color: #11151f;
                color: #f0f6fc;
                border: 1px solid #1f2737;
            }
            QMenu::item:selected {
                background-color: #0077b6;
            }
        """)
        show_action = tray_menu.addAction("Show OmniMesh")
        show_action.triggered.connect(self._show_from_tray)
        
        self.startup_action = tray_menu.addAction("Run on Startup")
        self.startup_action.setCheckable(True)
        self.startup_action.setChecked(self._check_startup_enabled())
        self.startup_action.triggered.connect(self._toggle_startup)
        
        tray_menu.addSeparator()
        
        quit_action = tray_menu.addAction("Quit")
        quit_action.triggered.connect(QApplication.instance().quit)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()

    def _check_startup_enabled(self) -> bool:
        import winreg
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ)
            value, _ = winreg.QueryValueEx(key, "OmniMesh")
            winreg.CloseKey(key)
            return True
        except WindowsError:
            return False

    def _toggle_startup(self, checked: bool):
        import winreg, sys, os
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_ALL_ACCESS)
            if checked:
                exe_path = sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(sys.argv[0])
                winreg.SetValueEx(key, "OmniMesh", 0, winreg.REG_SZ, f'"{exe_path}"')
            else:
                winreg.DeleteValue(key, "OmniMesh")
            winreg.CloseKey(key)
        except Exception as e:
            print(f"Failed to set startup: {e}")

    def _show_from_tray(self):
        # Prevent double triggering
        if getattr(self, '_is_restoring', False):
            return
        self._is_restoring = True
        
        from ui.minimize_animation import RestoreAnimationOverlay
        from PyQt6.QtCore import QPoint
        
        tray_geom = self.tray_icon.geometry()
        if tray_geom.isNull():
            screen = QApplication.primaryScreen().geometry()
            start_pt = QPoint(screen.width() - 50, screen.height() - 50)
        else:
            start_pt = tray_geom.center()
            
        def on_anim_finished():
            self.showNormal()
            self.activateWindow()
            self._is_restoring = False
            
        self._restore_anim = RestoreAnimationOverlay(start_pt, self.geometry(), on_anim_finished)
        self._restore_anim.show()

    def _animate_minimize_to_tray(self):
        from ui.minimize_animation import MinimizeAnimationOverlay
        from PyQt6.QtCore import QPoint
        
        tray_geom = self.tray_icon.geometry()
        if tray_geom.isNull():
            screen = QApplication.primaryScreen().geometry()
            target_pt = QPoint(screen.width() - 50, screen.height() - 50)
        else:
            target_pt = tray_geom.center()
            
        self.hide()
        
        # Save a reference so the animation isn't garbage collected
        self._minimize_anim = MinimizeAnimationOverlay(self.geometry(), target_pt, None)
        self._minimize_anim.show()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._show_from_tray()

    def _on_mode_changed(self, mode: ToolMode):
        """Handle tab switching and update UI action text and badge."""
        self.current_mode = mode
        if mode == ToolMode.COMBINE_PDF:
            self.action_bar.set_action_title("MERGE")
        elif mode == ToolMode.JPG_TO_PDF:
            self.action_bar.set_action_title("CONVERT TO PDF")
        elif mode == ToolMode.PDF_TO_JPG:
            self.action_bar.set_action_title("EXTRACT TO JPG")
        elif mode == ToolMode.COMPRESS_PDF:
            self.action_bar.set_action_title("COMPRESS")
        elif mode == ToolMode.PDF_TO_DOCX:
            self.action_bar.set_action_title("CONVERT TO DOCX")
        elif mode == ToolMode.SPLIT_PDF:
            self.action_bar.set_action_title("SPLIT")
        elif mode == ToolMode.BOOKMARK:
            self.action_bar.set_action_title("BOOKMARK")

        self.action_bar.update_count(len(self.file_items))

    def _get_file_filters(self) -> str:
        """Return file dialog filter based on active tool mode."""
        if self.current_mode == ToolMode.COMBINE_PDF:
            return "Documents & Images (*.pdf *.jpg *.jpeg *.png *.webp *.bmp *.txt);;PDF Files (*.pdf);;Text Files (*.txt);;Images (*.jpg *.png);;All Files (*.*)"
        elif self.current_mode == ToolMode.JPG_TO_PDF:
            return "Images (*.jpg *.jpeg *.png *.webp *.bmp);;All Files (*.*)"
        elif self.current_mode in [ToolMode.PDF_TO_JPG, ToolMode.COMPRESS_PDF, ToolMode.PDF_TO_DOCX, ToolMode.SPLIT_PDF, ToolMode.BOOKMARK]:
            return "PDF Files (*.pdf);;All Files (*.*)"
        return "All Files (*.*)"

    def _open_file_dialog(self):
        """Open custom file explorer with built-in semantic search."""
        from .file_dialog import CustomFileDialog
        dialog = CustomFileDialog(self)
        if dialog.exec():
            files = dialog.selected_files
            if files:
                self._add_files(files)

    MAX_FILE_LIMIT = 5000

    def _add_files(self, paths: List[str]):
        """Add newly selected files to the queue, recursively expanding any dropped folders."""
        import re
        def natural_sort_key(s):
            return [int(text) if text.isdigit() else text.lower() for text in re.split('([0-9]+)', s)]

        expanded_paths = []
        for p in paths:
            if not p:
                continue
            p = os.path.normpath(p)
            if os.path.isdir(p):
                for root, _, files in os.walk(p):
                    for f in sorted(files, key=natural_sort_key):
                        expanded_paths.append(os.path.join(root, f))
            elif os.path.isfile(p):
                expanded_paths.append(p)

        if not expanded_paths:
            return

        # Sort the entire incoming batch naturally so multi-file selections arrive ordered
        expanded_paths = sorted(expanded_paths, key=natural_sort_key)

        added_count = 0
        existing_paths = {item.file_path for item in self.file_items}

        for path in expanded_paths:
            if len(self.file_items) >= self.MAX_FILE_LIMIT:
                QMessageBox.information(
                    self,
                    "Batch Limit",
                    f"You can select up to {self.MAX_FILE_LIMIT} files at a time."
                )
                break

            # Fast O(1) duplicate check
            if path in existing_paths:
                continue

            try:
                item = FileItem(path)
                self.file_items.append(item)
                existing_paths.add(path)
                added_count += 1
            except Exception as e:
                print(f"Error loading file {path}: {e}")

        if added_count > 0:
            self.carousel.set_items(self.file_items)
            self.action_bar.update_count(len(self.file_items))

    def _clear_files(self):
        """Clear all files from the queue and reset the view."""
        self.file_items.clear()
        self.carousel.set_items(self.file_items)
        self.action_bar.update_count(0)
        self.action_bar.hide_progress()
        self.output_view.hide()
        self.carousel.show()
        self.action_bar.show()
        if hasattr(self, 'particle_overlay'):
            self.particle_overlay.clear_all()

    def _on_file_removed(self, item: FileItem):
        self.action_bar.update_count(len(self.file_items))

    def _on_files_reordered(self):
        # Update references
        self.file_items = self.carousel.file_items

    def _on_action_hovered(self, is_hovered: bool, global_pos: QPoint):
        """Start or stop pulling file particles into the merge button on hover."""
        if not hasattr(self, 'particle_overlay'):
            return

        # Crucial: the merge particle animation must ONLY occur on the file selection screen (carousel visible),
        # NEVER on the merge result screen (output_view visible).
        if hasattr(self, 'output_view') and self.output_view.isVisible():
            self.particle_overlay.clear_all()
            return
        if hasattr(self, 'carousel') and not self.carousel.isVisible():
            self.particle_overlay.clear_all()
            return

        if is_hovered and self.file_items:
            local_pos = self.mapFromGlobal(global_pos)
            if self.particle_overlay.hover_active:
                self.particle_overlay.update_target_pos(local_pos)
            else:
                self.particle_overlay.start_hover_pull(local_pos)
        else:
            self.particle_overlay.stop_hover_pull()

    def _execute_action(self):
        """Execute the primary operation depending on active tab."""
        if not self.file_items:
            return

        single_file_modes = [ToolMode.PDF_TO_JPG, ToolMode.SPLIT_PDF, ToolMode.COMPRESS_PDF, ToolMode.PDF_TO_DOCX, ToolMode.BOOKMARK]
        if self.current_mode in single_file_modes and len(self.file_items) > 1:
            QMessageBox.information(
                self,
                "Batch Limit",
                f"{self.current_mode.value} only processes one file at a time. Only the first file ({self.file_items[0].file_name}) will be processed."
            )

        # Trigger hyper-speed collapse of file particles into the merge button center!
        if hasattr(self, 'particle_overlay'):
            self.particle_overlay.trigger_hyper_collapse()

        import tempfile
        temp_dir = tempfile.gettempdir()

        if self.current_mode == ToolMode.COMBINE_PDF:
            output_file = os.path.join(temp_dir, "omnimesh_merged.pdf")
            self._start_task(target=PDFEngine.combine_files, file_items=self.file_items, output_path=output_file)
        elif self.current_mode == ToolMode.JPG_TO_PDF:
            output_file = os.path.join(temp_dir, "omnimesh_converted.pdf")
            self._start_task(target=PDFEngine.convert_jpg_to_pdf, image_items=self.file_items, output_path=output_file)
        elif self.current_mode == ToolMode.PDF_TO_JPG:
            import shutil
            output_dir = os.path.join(temp_dir, "omnimesh_jpg_export")
            if os.path.exists(output_dir): shutil.rmtree(output_dir)
            os.makedirs(output_dir)
            self._start_task(target=PDFEngine.convert_pdf_to_jpg, pdf_item=self.file_items[0], output_dir=output_dir, dpi=200)
            self.temp_dir_to_zip = output_dir
        elif self.current_mode == ToolMode.SPLIT_PDF:
            import shutil
            output_dir = os.path.join(temp_dir, "omnimesh_split_export")
            if os.path.exists(output_dir): shutil.rmtree(output_dir)
            os.makedirs(output_dir)
            self._start_task(target=PDFEngine.split_pdf, pdf_item=self.file_items[0], output_dir=output_dir)
            self.temp_dir_to_zip = output_dir
        elif self.current_mode == ToolMode.COMPRESS_PDF:
            base_name = os.path.splitext(self.file_items[0].file_name)[0]
            output_file = os.path.join(temp_dir, f"{base_name}_compressed.pdf")
            self._start_task(target=PDFEngine.compress_pdf, pdf_item=self.file_items[0], output_path=output_file)
        elif self.current_mode == ToolMode.PDF_TO_DOCX:
            base_name = os.path.splitext(self.file_items[0].file_name)[0]
            output_file = os.path.join(temp_dir, f"{base_name}.docx")
            self._start_task(target=PDFEngine.convert_pdf_to_docx, pdf_item=self.file_items[0], output_path=output_file)
        elif self.current_mode == ToolMode.BOOKMARK:
            base_name = os.path.splitext(self.file_items[0].file_name)[0]
            output_file = os.path.join(temp_dir, f"{base_name}_bookmarked.pdf")
            self._start_task(target=PDFEngine.bookmark, pdf_item=self.file_items[0], output_path=output_file)

    def _start_task(self, target, **kwargs):
        """Starts worker thread and connects UI feedback signals."""
        self.action_bar.upload_btn.setEnabled(False)
        self.action_bar.clear_btn.setEnabled(False)
        self.action_bar.action_btn.setEnabled(False)
        self.action_bar.show_progress(0, "Processing task...")

        self.worker = TaskWorker(target, **kwargs)
        self.worker.progress.connect(self._on_worker_progress)
        self.worker.finished.connect(self._on_worker_finished)
        self.worker.error.connect(self._on_worker_error)
        
        # Delay the actual start of the intensive worker thread to guarantee 
        # that the cinematic particle collapse animation finishes rendering at 
        # 60 FPS without being starved by Python's Global Interpreter Lock (GIL).
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(1000, self.worker.start)

    def _on_worker_progress(self, pct: int, msg: str):
        self.action_bar.show_progress(pct, msg)

    def _on_worker_finished(self, result):
        self.action_bar.upload_btn.setEnabled(True)
        self.action_bar.clear_btn.setEnabled(True)
        self.action_bar.action_btn.setEnabled(True)
        self.action_bar.show_progress(100, "Completed successfully!")
        
        final_result = result
        # If PDF to JPG or Split PDF, pass the output directory instead of the list of files or a zip
        if self.current_mode in [ToolMode.PDF_TO_JPG, ToolMode.SPLIT_PDF] and hasattr(self, 'temp_dir_to_zip'):
            final_result = self.temp_dir_to_zip

        def perform_screen_swap():
            self.carousel.hide()
            self.action_bar.hide()
            self.output_view.show_output(final_result)
            if hasattr(self, 'particle_overlay'):
                self.particle_overlay.clear_all()

        # Trigger dramatic cinematic flash & shockwave transition into the merge screen!
        if hasattr(self, 'particle_overlay'):
            btn_center = self.action_bar.action_btn.mapTo(self, self.action_bar.action_btn.rect().center())
            self.particle_overlay.trigger_dramatic_flash(btn_center, on_peak_callback=perform_screen_swap)
        else:
            perform_screen_swap()

    def _start_over(self):
        self._clear_files()
        self.output_view.hide()
        self.carousel.show()
        self.action_bar.show()
        self.action_bar.hide_progress()
        if hasattr(self, 'particle_overlay'):
            self.particle_overlay.clear_all()

    def _on_worker_error(self, err_msg: str):
        self.action_bar.upload_btn.setEnabled(True)
        self.action_bar.clear_btn.setEnabled(True)
        self.action_bar.action_btn.setEnabled(True)
        self.action_bar.hide_progress()

        QMessageBox.critical(
            self,
            "Error - OmniMesh",
            f"An error occurred while processing:\n\n{err_msg}"
        )
