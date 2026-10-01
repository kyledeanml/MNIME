from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QMessageBox, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem,
    QTextBrowser
)
from PyQt6.QtCore import Qt, QRectF, QRect, QPoint, pyqtSignal
from PyQt6.QtGui import QPixmap, QPainter, QColor, QPen, QImage
from core.file_item import FileItem

class PDFPageView(QGraphicsView):
    text_selected = pyqtSignal(str)

    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.rubber_band = QRect()
        self.start_pos = QPoint()
        self.is_drawing = False
        self.current_page = None
        self.zoom_factor = 2.0

    def set_page(self, page, pixmap):
        self.current_page = page
        self.scene().clear()
        self.pixmap_item = QGraphicsPixmapItem(pixmap)
        self.scene().addItem(self.pixmap_item)
        self.scene().setSceneRect(QRectF(pixmap.rect()))
        # Removed fitInView to prevent it from shrinking to a tiny box on layout initialization
        self.rubber_band = QRect()

    def wheelEvent(self, event):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if event.angleDelta().y() > 0:
                factor = 1.15
            else:
                factor = 1 / 1.15
            self.scale(factor, factor)
        else:
            super().wheelEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_pos = event.pos()
            self.rubber_band = QRect(self.start_pos, self.start_pos)
            self.is_drawing = True
            self.viewport().update()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.is_drawing:
            self.rubber_band = QRect(self.start_pos, event.pos()).normalized()
            self.viewport().update()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.is_drawing:
            self.is_drawing = False
            self._extract_text()
        super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self.rubber_band.isEmpty():
            painter = QPainter(self.viewport())
            pen = QPen(QColor(255, 210, 0, 150))
            pen.setWidth(2)
            painter.setPen(pen)
            painter.setBrush(QColor(255, 210, 0, 50))
            painter.drawRect(self.rubber_band)

    def _extract_text(self):
        if not self.current_page or self.rubber_band.isEmpty():
            return
            
        top_left = self.mapToScene(self.rubber_band.topLeft())
        bottom_right = self.mapToScene(self.rubber_band.bottomRight())
        
        # Scale back to original PDF coordinates
        import pymupdf
        rect = pymupdf.Rect(
            top_left.x() / self.zoom_factor,
            top_left.y() / self.zoom_factor,
            bottom_right.x() / self.zoom_factor,
            bottom_right.y() / self.zoom_factor
        )
        
        text = self.current_page.get_text("text", clip=rect).strip()
        if text:
            self.text_selected.emit(text)

class DocumentViewer(QDialog):
    def __init__(self, file_item: FileItem, parent=None):
        super().__init__(parent)
        self.file_item = file_item
        self.setWindowTitle(f"Reference - {file_item.file_name}")
        self.setMinimumSize(1000, 700)
        
        self.doc = None
        self.page_idx = 0
        
        self.setStyleSheet("""
            QDialog { background-color: #11151f; color: #f0f6fc; }
            QPushButton { background-color: #162438; color: #00e5ff; border: 1px solid #00d2ff; border-radius: 6px; padding: 6px 12px; font-weight: bold; }
            QPushButton:hover { background-color: #0077b6; color: #ffffff; }
            QLabel { color: #8b949e; font-size: 13px; }
            QTextBrowser { background-color: #0a0d14; color: #c9d1d9; border: 1px solid #1f2737; border-radius: 6px; padding: 10px; font-size: 14px; }
        """)
        
        self._load_doc()
        self._setup_ui()
        self._render_page()

    def _load_doc(self):
        try:
            import pymupdf
            self.doc = pymupdf.open(self.file_item.file_path)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open PDF: {e}")
            self.reject()

    def _setup_ui(self):
        main_layout = QHBoxLayout(self)
        
        # Left side: PDF Viewer
        left_layout = QVBoxLayout()
        self.scene = QGraphicsScene(self)
        self.view = PDFPageView(self.scene, self)
        self.view.setStyleSheet("background-color: #0a0d14; border: 1px solid #1f2737;")
        self.view.text_selected.connect(self._on_text_selected)
        left_layout.addWidget(self.view, 1)
        
        nav_layout = QHBoxLayout()
        self.prev_btn = QPushButton("Prev Page")
        self.prev_btn.clicked.connect(self._prev_page)
        self.next_btn = QPushButton("Next Page")
        self.next_btn.clicked.connect(self._next_page)
        self.page_label = QLabel()
        nav_layout.addWidget(self.prev_btn)
        nav_layout.addStretch()
        nav_layout.addWidget(self.page_label)
        nav_layout.addStretch()
        nav_layout.addWidget(self.next_btn)
        left_layout.addLayout(nav_layout)
        
        # Right side: Context and Results
        right_layout = QVBoxLayout()
        
        info_label = QLabel("Highlight text on the page to automatically reference against other indexed documents in your workspace.")
        info_label.setWordWrap(True)
        right_layout.addWidget(info_label)
        
        self.source_text_view = QTextBrowser()
        self.source_text_view.setPlaceholderText("Highlighted text will appear here...")
        self.source_text_view.setMaximumHeight(150)
        right_layout.addWidget(QLabel("Source Text:"))
        right_layout.addWidget(self.source_text_view)
        
        self.reference_btn = QPushButton("REFERENCE")
        self.reference_btn.setEnabled(False)
        self.reference_btn.clicked.connect(self._trigger_reference)
        right_layout.addWidget(self.reference_btn)
        
        self.result_view = QTextBrowser()
        self.result_view.setPlaceholderText("NLP Analysis will appear here...")
        right_layout.addWidget(QLabel("NLP Comparative Brief:"))
        right_layout.addWidget(self.result_view, 1)
        
        main_layout.addLayout(left_layout, 2)
        main_layout.addLayout(right_layout, 1)

    def _render_page(self):
        if not self.doc or self.page_idx >= len(self.doc): return
        self.page_label.setText(f"Page {self.page_idx + 1} of {len(self.doc)}")
        
        page = self.doc[self.page_idx]
        import pymupdf
        mat = pymupdf.Matrix(self.view.zoom_factor, self.view.zoom_factor)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        
        img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
        qpixmap = QPixmap.fromImage(img)
        self.view.set_page(page, qpixmap)

    def _prev_page(self):
        if self.page_idx > 0:
            self.page_idx -= 1
            self._render_page()

    def _next_page(self):
        if self.doc and self.page_idx < len(self.doc) - 1:
            self.page_idx += 1
            self._render_page()

    def _on_text_selected(self, text: str):
        self.source_text_view.setText(text)
        self.reference_btn.setEnabled(True)

    def _trigger_reference(self):
        text = self.source_text_view.toPlainText().strip()
        if not text: return
        self.reference_btn.setEnabled(False)
        self.result_view.setText("Synthesizing comparative brief...\n(This may take a moment depending on your local model.)")
        
        # Trigger parent window to run the reference worker
        self.parent()._run_reference(text, self)

    def set_result(self, text: str):
        self.result_view.setText(text)
        self.reference_btn.setEnabled(True)

    def closeEvent(self, event):
        if self.doc:
            self.doc.close()
        super().closeEvent(event)
