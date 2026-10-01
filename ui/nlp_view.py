from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextBrowser, 
    QLineEdit, QPushButton, QLabel, QProgressBar
)
from PyQt6.QtCore import pyqtSignal, Qt, QThread
from typing import List, Any
from core.file_item import FileItem
from core.search_engine import SearchEngine
from core.nlp_engine import NLPEngine

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
            settings = QSettings("OmniMesh", "OmniMeshApp")
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
    def __init__(self, parent=None):
        super().__init__(parent)
        self.vectorstore = None
        self._setup_ui()

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
        
        self.index_btn = QPushButton("INDEX FILES")
        self.index_btn.setStyleSheet("""
            QPushButton { background-color: #162438; color: #00e5ff; border: 1px solid #00d2ff; border-radius: 6px; padding: 6px 18px; font-weight: bold; }
            QPushButton:hover { background-color: #0077b6; color: #ffffff; }
        """)
        
        top_layout = QHBoxLayout()
        top_layout.addWidget(self.status_label)
        top_layout.addWidget(self.progress_bar)
        top_layout.addStretch()
        top_layout.addWidget(self.index_btn)
        
        self.history_view = QTextBrowser()
        self.history_view.setStyleSheet("""
            QTextBrowser { background-color: #0a0d14; color: #c9d1d9; border: 1px solid #1f2737; border-radius: 6px; padding: 10px; font-size: 14px; }
        """)
        
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

    def start_indexing(self, file_items: List[FileItem]):
        if not file_items:
            self.status_label.setText("No files to index.")
            return

        self.index_btn.setEnabled(False)
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
        self.index_btn.setEnabled(True)
        self.query_input.setEnabled(True)
        self.query_input.setFocus()
        self.history_view.append("<div style='color:#00e5ff'><b>System:</b> Indexing complete. Ready for queries.</div><br>")

    def _on_index_error(self, err: str):
        self.progress_bar.setVisible(False)
        self.status_label.setText("Error during indexing.")
        self.index_btn.setEnabled(True)
        self.history_view.append(f"<div style='color:#ff5555'><b>Error:</b> {err}</div><br>")

    def _submit_query(self):
        query = self.query_input.text().strip()
        if not query: return
        
        self.query_input.clear()
        self.history_view.append(f"<div style='color:#c9d1d9'><b>You:</b> {query}</div><br>")
        self.query_input.setEnabled(False)
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
        self.history_view.append(f"<div style='color:#00e5ff'><b>NLP:</b> {response_html}</div><br><hr><br>")
        self.query_input.setEnabled(True)
        self.query_input.setFocus()
        self.status_label.setText("Ready.")
