from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextBrowser, 
    QLineEdit, QPushButton, QLabel, QProgressBar, QDialog, QFrame
)
from PyQt6.QtCore import pyqtSignal, Qt, QThread
from typing import List, Any
from core.file_item import FileItem
from core.search_engine import SearchEngine
from core.nlp_engine import NLPEngine

class ClickableTextBrowser(QTextBrowser):
    doubleClicked = pyqtSignal()
    def mouseDoubleClickEvent(self, event):
        self.doubleClicked.emit()
        super().mouseDoubleClickEvent(event)

class ExpandedNLPDialog(QDialog):
    def __init__(self, parent_view, parent=None):
        super().__init__(parent)
        self.parent_view = parent_view
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(850, 650)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        
        frame = QFrame()
        frame.setStyleSheet("QFrame { background-color: rgba(11, 15, 25, 240); border: 2px solid #00d2ff; border-radius: 12px; }")
        frame_layout = QVBoxLayout(frame)
        
        header_layout = QHBoxLayout()
        title = QLabel("MNIME")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #00e5ff; font-size: 18px; font-weight: bold; border: none; background: transparent;")
        
        close_btn = QPushButton("CLOSE")
        close_btn.setStyleSheet("QPushButton { background-color: transparent; color: #00e5ff; font-weight: bold; border: none; font-size: 14px; } QPushButton:hover { color: #ffffff; }")
        close_btn.clicked.connect(self.close)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(close_btn)
        
        self.history_view = QTextBrowser()
        self.history_view.setStyleSheet("""
            QTextBrowser { background-color: transparent; color: #c9d1d9; border: none; font-size: 16px; }
            QScrollBar:vertical { background: transparent; width: 10px; margin: 0px 0px 0px 0px; }
            QScrollBar::handle:vertical { background: #1f2737; min-height: 20px; border-radius: 5px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
        """)
        
        self.query_input = QLineEdit()
        self.query_input.setPlaceholderText("Ask a question...")
        self.query_input.setStyleSheet("""
            QLineEdit { background-color: rgba(22, 27, 34, 180); color: #f0f6fc; border: 1px solid #30363d; border-radius: 6px; padding: 15px; font-size: 16px; }
        """)
        self.query_input.returnPressed.connect(self._submit_query)
        
        frame_layout.addLayout(header_layout)
        frame_layout.addWidget(self.history_view)
        frame_layout.addWidget(self.query_input)
        layout.addWidget(frame)
        
        self.parent_view.window().installEventFilter(self)
        
    def center_on_parent(self):
        parent_rect = self.parent_view.window().geometry()
        x = parent_rect.x() + (parent_rect.width() - self.width()) // 2
        y = parent_rect.y() + (parent_rect.height() - self.height()) // 2
        self.move(x, y)
        
    def eventFilter(self, obj, event):
        if obj is self.parent_view.window() and event.type() in (event.Type.Move, event.Type.Resize):
            self.center_on_parent()
        return super().eventFilter(obj, event)

    def _submit_query(self):
        query = self.query_input.text().strip()
        if not query: return
        self.query_input.clear()
        self.parent_view.query_input.setText(query)
        self.parent_view._submit_query()
        
    def append_html(self, html: str):
        self.history_view.append(html)
        
    def set_input_enabled(self, enabled: bool):
        self.query_input.setEnabled(enabled)
        if enabled:
            self.query_input.setFocus()

class IndexWorker(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, file_items: List[FileItem]):
        super().__init__()
        self.file_items = file_items

    def run(self):
        try:
            from PyQt6.QtCore import QSettings
            settings = QSettings("MNIME", "MNIMEApp")
            smart_sampling = str(settings.value("nlp_smart_indexing", "true")).lower() == "true"
            
            vectorstore = SearchEngine.build_index(
                self.file_items, 
                use_smart_sampling=smart_sampling, 
                progress_callback=self._emit_progress
            )
            self.finished.emit(vectorstore)
        except Exception as e:
            self.error.emit(str(e))

    def _emit_progress(self, pct: int, msg: str):
        self.progress.emit(pct, msg)


class NLPQueryWorker(QThread):
    finished = pyqtSignal(str)

    def __init__(self, query: str, context_docs: list):
        super().__init__()
        self.query = query
        self.context_docs = context_docs

    def run(self):
        try:
            response = NLPEngine.get_instance().generate_response(self.query, self.context_docs)
            self.finished.emit(response)
        except Exception as e:
            self.finished.emit(f"Error: {e}")


class NLPView(QWidget):
    start_over_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.vectorstore = None
        self.expanded_dialog = None
        self._setup_ui()
        
        import atexit, sys
        atexit.register(self.clear_index)
        self._old_excepthook = sys.excepthook
        sys.excepthook = self._crash_hook

    def _crash_hook(self, exctype, value, traceback):
        self.clear_index()
        if self._old_excepthook:
            self._old_excepthook(exctype, value, traceback)

    def clear_index(self):
        if self.vectorstore:
            del self.vectorstore
            self.vectorstore = None
            import gc
            gc.collect()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.status_label = QLabel("Drop files in carousel and click 'INDEX FILES' to start.")
        self.status_label.setStyleSheet("color: #8b949e; font-size: 13px;")
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar { border: 1px solid #1f2737; border-radius: 4px; text-align: center; color: white; background-color: #0d1117;}
            QProgressBar::chunk { background-color: #00e5ff; }
        """)
        
        self.start_over_btn = QPushButton("START OVER")
        self.start_over_btn.setStyleSheet("""
            QPushButton { background-color: #162438; color: #00e5ff; border: 1px solid #00d2ff; border-radius: 4px; padding: 4px 12px; font-weight: bold; font-size: 11px; }
            QPushButton:hover { background-color: #0077b6; color: #ffffff; }
        """)
        self.start_over_btn.clicked.connect(self.start_over_clicked.emit)
        
        top_layout = QHBoxLayout()
        top_layout.addWidget(self.status_label)
        top_layout.addWidget(self.progress_bar)
        top_layout.addStretch()
        top_layout.addWidget(self.start_over_btn)
        
        self.history_view = ClickableTextBrowser()
        self.history_view.setStyleSheet("""
            QTextBrowser { background-color: #0a0d14; color: #c9d1d9; border: 1px solid #1f2737; border-radius: 6px; padding: 10px; font-size: 14px; }
        """)
        self.history_view.setToolTip("Double click for expanded view")
        self.history_view.doubleClicked.connect(self._on_history_double_clicked)
        
        self.query_input = QLineEdit()
        self.query_input.setPlaceholderText("Ask a question about your documents...")
        self.query_input.setStyleSheet("""
            QLineEdit { background-color: #161b22; color: #f0f6fc; border: 1px solid #30363d; border-radius: 6px; padding: 10px; font-size: 14px; }
        """)
        self.query_input.returnPressed.connect(self._submit_query)
        self.query_input.setEnabled(False)
        
        layout.addLayout(top_layout)
        layout.addWidget(self.history_view)
        layout.addWidget(self.query_input)

    def _on_history_double_clicked(self):
        if not self.expanded_dialog:
            self.expanded_dialog = ExpandedNLPDialog(self, self.window())
        self.expanded_dialog.history_view.setHtml(self.history_view.toHtml())
        self.expanded_dialog.set_input_enabled(self.query_input.isEnabled())
        
        # Center on parent window
        self.expanded_dialog.center_on_parent()
        self.expanded_dialog.show()

    def _append_history(self, html_msg: str):
        self.history_view.append(html_msg)
        if self.expanded_dialog and self.expanded_dialog.isVisible():
            self.expanded_dialog.append_html(html_msg)
            
    def _set_input_enabled(self, enabled: bool):
        self.query_input.setEnabled(enabled)
        if self.expanded_dialog and self.expanded_dialog.isVisible():
            self.expanded_dialog.set_input_enabled(enabled)

    def start_indexing(self, file_items: List[FileItem]):
        if not file_items:
            self.status_label.setText("No files to index.")
            return

        self.start_over_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Indexing...")
        
        self.worker = IndexWorker(file_items)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_index_finished)
        self.worker.error.connect(self._on_index_error)
        self.worker.start()

    def _on_progress(self, pct: int, msg: str):
        self.progress_bar.setValue(pct)
        self.status_label.setText(msg)

    def _on_index_finished(self, vectorstore):
        self.vectorstore = vectorstore
        self.progress_bar.setVisible(False)
        self.status_label.setText("Indexing complete! Ask a question below.")
        self.start_over_btn.setEnabled(True)
        self._set_input_enabled(True)
        self.query_input.setFocus()
        self._append_history("<div style='color:#00e5ff'><b>System:</b> Indexing complete. Ready for queries.</div><br>")

    def _on_index_error(self, err: str):
        self.progress_bar.setVisible(False)
        self.status_label.setText("Error during indexing.")
        self.start_over_btn.setEnabled(True)
        self._append_history(f"<div style='color:#ff5555'><b>Error:</b> {err}</div><br>")

    def _submit_query(self):
        query = self.query_input.text().strip()
        if not query: return
        
        self.query_input.clear()
        self._append_history(f"<div style='color:#c9d1d9'><b>You:</b> {query}</div><br>")
        self._set_input_enabled(False)
        self.status_label.setText("Generating answer...")
        
        # 1. Semantic Search
        context_docs = SearchEngine.search(self.vectorstore, query, k=5)
        
        # 2. LLM Generation
        self.query_worker = NLPQueryWorker(query, context_docs)
        self.query_worker.finished.connect(self._on_query_response)
        self.query_worker.start()

    def _on_query_response(self, response: str):
        # Format response with line breaks
        response_html = response.replace("\n", "<br>")
        self._append_history(f"<div style='color:#00e5ff'><b>MNIME:</b> {response_html}</div><br><hr><br>")
        self._set_input_enabled(True)
        self.query_input.setFocus()
        self.status_label.setText("Ready.")
