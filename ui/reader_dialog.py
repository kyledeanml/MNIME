from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QMessageBox, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem,
    QSplitter, QTreeWidget, QTreeWidgetItem, QComboBox, QFileDialog
)
from PyQt6.QtCore import Qt, QRectF, QRect, QPoint, pyqtSignal
from PyQt6.QtGui import QPixmap, QPainter, QColor, QPen, QImage
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog

class ReaderPageView(QGraphicsView):
    prev_page_requested = pyqtSignal()
    next_page_requested = pyqtSignal()

    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)
        self.current_page = None
        self.zoom_factor = 4.0
        self.scale(1.0, 1.0)

    def set_page(self, page, pixmap):
        self.current_page = page
        self.scene().clear()
        self.pixmap_item = QGraphicsPixmapItem(pixmap)
        self.pixmap_item.setTransformationMode(Qt.TransformationMode.SmoothTransformation)
        self.scene().addItem(self.pixmap_item)
        self.scene().setSceneRect(QRectF(pixmap.rect()))
        
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(10, self._fit_to_view)
        
    def _fit_to_view(self):
        if self.scene() and not self.scene().sceneRect().isEmpty():
            self.fitInView(self.scene().sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
            self.scale(0.95, 0.95)

    def wheelEvent(self, event):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if event.angleDelta().y() > 0:
                factor = 1.15
            else:
                factor = 1 / 1.15
            self.scale(factor, factor)
        else:
            if event.angleDelta().y() > 0:
                self.prev_page_requested.emit()
            else:
                self.next_page_requested.emit()
            event.accept()

class ReaderDialog(QDialog):
    def __init__(self, file_items, parent=None, update_callback=None):
        super().__init__(parent)
        self.update_callback = update_callback
        self.file_items = file_items
        self.setWindowTitle("OMNIME - READER")
        self.setMinimumSize(800, 600)
        self.resize(1200, 900)
        
        # Frameless dark metallic UI
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.doc = None
        self.page_idx = 0
        self._drag_pos = None
        
        # Match OMNIME styling
        self.setStyleSheet("""
            ReaderDialog { background: transparent; }
            QWidget { color: #f0f6fc; }
            QPushButton { 
                background-color: #162438; color: #00e5ff; 
                border: 1px solid #00d2ff; border-radius: 6px; 
                padding: 6px 12px; font-weight: bold; 
            }
            QPushButton:hover { background-color: #0077b6; color: #ffffff; }
            QLabel { color: #8b949e; font-size: 13px; }
            QComboBox { 
                background-color: #161b22; color: #f0f6fc; 
                border: 1px solid #30363d; border-radius: 4px; padding: 4px; 
            }
            QTreeWidget { 
                background-color: #0a0d14; color: #c9d1d9; 
                border: 1px solid #1f2737; border-radius: 6px; padding: 5px; 
            }
            QTreeWidget::item:selected { background-color: #162438; color: #00d2ff; }
            QSplitter::handle { background-color: #1f2737; }
        """)
        
        self._setup_ui()
        if self.file_items:
            self.file_combo.setCurrentIndex(0)
            self._on_file_selected(0)

    def _setup_ui(self):
        from PyQt6.QtWidgets import QFrame, QGraphicsDropShadowEffect
        central_layout = QVBoxLayout(self)
        central_layout.setContentsMargins(10, 10, 10, 10)
        
        class WatermarkFrame(QFrame):
            def paintEvent(self, event):
                super().paintEvent(event)
                from PyQt6.QtGui import QPainter, QFont, QPen, QColor
                from PyQt6.QtCore import Qt
                painter = QPainter(self)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                font = QFont("Segoe UI Black", 80, QFont.Weight.Black)
                font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 15.0)
                painter.setFont(font)
                painter.setPen(QPen(QColor(255, 255, 255, 4)))
                text = "OMNIME        " * 20
                y_offset = 80
                while y_offset < self.height() + 100:
                    painter.drawText(-100, y_offset, text)
                    y_offset += 180

        self.container_frame = WatermarkFrame()
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
        
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 4)
        self.container_frame.setGraphicsEffect(shadow)
        
        central_layout.addWidget(self.container_frame)
        
        self.setMouseTracking(True)
        self.container_frame.setMouseTracking(True)
        
        main_layout = QVBoxLayout(self.container_frame)
        main_layout.setContentsMargins(16, 8, 16, 16)
        main_layout.setSpacing(8)
        
        # Add a proper QSizeGrip overlay to handle bottom-right resizing natively
        from PyQt6.QtWidgets import QSizeGrip
        size_grip_layout = QHBoxLayout()
        size_grip_layout.setContentsMargins(0, 0, 0, 0)
        size_grip_layout.addStretch()
        self.size_grip = QSizeGrip(self.container_frame)
        self.size_grip.setFixedSize(16, 16)
        self.size_grip.setStyleSheet("background: transparent;")
        size_grip_layout.addWidget(self.size_grip)
        
        # Unified Tools & Title Bar
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(0, 0, 0, 10)
        
        title_label = QLabel("READER")
        title_label.setStyleSheet("color: #00d2ff; font-family: 'Segoe UI Black'; font-weight: 900; font-size: 14px; letter-spacing: 1px;")
        
        # Floating Close Button matching OMNIME Theme
        self.close_btn = QPushButton("✕", self.container_frame)
        self.close_btn.setFixedSize(32, 32)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: #162438;
                color: #00e5ff;
                border: 1px solid #00d2ff;
                border-radius: 16px;
                font-size: 16px;
                font-weight: 900;
            }
            QPushButton:hover {
                background-color: #00d2ff;
                color: #000000;
            }
        """)
        self.close_btn.clicked.connect(self.close)
        
        self.file_combo = QComboBox()
        self.file_combo.setMaximumWidth(800)
        for item in self.file_items:
            self.file_combo.addItem(item.file_name, item)
        self.file_combo.currentIndexChanged.connect(self._on_file_selected)
        
        self.add_files_btn = QPushButton("Add Files")
        self.add_files_btn.clicked.connect(self._open_file_dialog)
        
        self.print_btn = QPushButton("Print Document")
        self.print_btn.clicked.connect(self._print_document)
        
        top_bar.addWidget(title_label)
        top_bar.addSpacing(20)
        top_bar.addWidget(QLabel("Select File:"))
        top_bar.addWidget(self.file_combo)
        top_bar.addStretch()
        top_bar.addWidget(self.add_files_btn)
        top_bar.addWidget(self.print_btn)
        top_bar.addSpacing(15)
        top_bar.addWidget(self.close_btn)
        
        main_layout.addLayout(top_bar)
        
        # Splitter for Side Pane (Bookmarks/TOC) and Viewer
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left: TOC
        left_widget = QTreeWidget()
        left_widget.setHeaderHidden(True)
        self.toc_tree = left_widget
        self.toc_tree.itemClicked.connect(self._on_toc_clicked)
        splitter.addWidget(left_widget)
        
        # Right: Viewer
        from PyQt6.QtWidgets import QWidget
        right_widget = QWidget() # simple container
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        self.scene = QGraphicsScene(self)
        self.view = ReaderPageView(self.scene, self)
        self.view.setStyleSheet("background-color: #0a0d14; border: 1px solid #1f2737;")
        self.view.prev_page_requested.connect(self._prev_page)
        self.view.next_page_requested.connect(self._next_page)
        right_layout.addWidget(self.view, 1)
        
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
        right_layout.addLayout(nav_layout)
        splitter.addWidget(right_widget)
        splitter.setSizes([250, 800])
        main_layout.addWidget(splitter, 1)
        
        # Add the size grip layout to the very bottom
        main_layout.addLayout(size_grip_layout)

        self.installEventFilter(self)

    def _open_file_dialog(self):
        from ui.file_dialog import CustomFileDialog
        dialog = CustomFileDialog(self)
        if dialog.exec():
            selected = dialog.selected_files
            if selected:
                if self.update_callback:
                    self.update_callback(selected)
                    
                    self.file_combo.blockSignals(True)
                    self.file_combo.clear()
                    for item in self.file_items:
                        self.file_combo.addItem(item.file_name, item)
                    self.file_combo.blockSignals(False)
                    
                    if self.file_items:
                        self.file_combo.setCurrentIndex(0)
                        self._on_file_selected(0)
                    else:
                        self.scene.clear()
                        self.doc = None

    def _on_file_selected(self, index):
        if index < 0 or index >= len(self.file_items):
            return
        item = self.file_items[index]
        self._load_doc(item)

    def _load_doc(self, file_item):
        if self.doc:
            try:
                self.doc.close()
            except:
                pass
            self.doc = None
        
        self.toc_tree.clear()
        
        if file_item.extension == ".pdf":
            try:
                import pymupdf
                self.doc = pymupdf.open(file_item.file_path)
                self.page_idx = 0
                self._load_toc()
                self._render_page()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to open PDF: {e}")
        elif file_item.extension in [".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff"]:
            self.page_label.setText("Image")
            pixmap = QPixmap(file_item.file_path)
            self.view.set_page(None, pixmap)
        else:
            self.page_label.setText("Preview not supported for this file type.")
            self.scene.clear()

    def _load_toc(self):
        if not self.doc: return
        try:
            toc = self.doc.get_toc()
            # toc format: [level, title, page, ...]
            # We'll construct a tree
            items_by_level = {}
            for item in toc:
                level, title, page = item[:3]
                tree_item = QTreeWidgetItem([title])
                tree_item.setData(0, Qt.ItemDataRole.UserRole, page - 1) # 0-indexed page
                
                if level == 1:
                    self.toc_tree.addTopLevelItem(tree_item)
                else:
                    parent = items_by_level.get(level - 1)
                    if parent:
                        parent.addChild(tree_item)
                    else:
                        self.toc_tree.addTopLevelItem(tree_item)
                        
                items_by_level[level] = tree_item
            
            if not toc:
                self.toc_tree.addTopLevelItem(QTreeWidgetItem(["No Bookmarks Found"]))
        except:
            pass

    def _on_toc_clicked(self, item, col):
        page = item.data(0, Qt.ItemDataRole.UserRole)
        if page is not None and self.doc:
            self.page_idx = page
            self._render_page()

    def _render_page(self):
        if not self.doc or self.page_idx < 0 or self.page_idx >= len(self.doc): return
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

    def _print_document(self):
        index = self.file_combo.currentIndex()
        if index < 0: return
        file_item = self.file_items[index]
        
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        dialog = QPrintDialog(printer, self)
        if dialog.exec() == QPrintDialog.DialogCode.Accepted:
            # We must print the document
            painter = QPainter()
            painter.begin(printer)
            try:
                if file_item.extension == ".pdf" and self.doc:
                    import pymupdf
                    # Simple rendering of pages to the printer
                    for i in range(len(self.doc)):
                        if i > 0:
                            printer.newPage()
                        page = self.doc[i]
                        # Render page to QImage
                        mat = pymupdf.Matrix(2.0, 2.0)
                        pix = page.get_pixmap(matrix=mat, alpha=False)
                        img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
                        
                        # Scale to fit printer page
                        rect = printer.pageRect(QPrinter.Unit.DevicePixel)
                        scaled_img = img.scaled(rect.width(), rect.height(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                        
                        # Center on page
                        x = int((rect.width() - scaled_img.width()) / 2)
                        y = int((rect.height() - scaled_img.height()) / 2)
                        
                        painter.drawImage(x, y, scaled_img)
                elif file_item.extension in [".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff"]:
                    img = QImage(file_item.file_path)
                    rect = printer.pageRect(QPrinter.Unit.DevicePixel)
                    scaled_img = img.scaled(rect.width(), rect.height(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    x = int((rect.width() - scaled_img.width()) / 2)
                    y = int((rect.height() - scaled_img.height()) / 2)
                    painter.drawImage(x, y, scaled_img)
            finally:
                painter.end()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'size_grip'):
            self.size_grip.move(self.width() - self.size_grip.width(), self.height() - self.size_grip.height())

    def eventFilter(self, obj, event):
        if event.type() == event.Type.MouseMove:
            from PyQt6.QtWidgets import QApplication, QWidget
            if QApplication.overrideCursor() is not None or QWidget.mouseGrabber() is not None:
                return super().eventFilter(obj, event)
            pos = self.mapFromGlobal(event.globalPosition().toPoint())
            edge = self._get_edge(pos)
            if edge == Qt.Edge.LeftEdge or edge == Qt.Edge.RightEdge:
                self.setCursor(Qt.CursorShape.SizeHorCursor)
            elif edge == Qt.Edge.TopEdge or edge == Qt.Edge.BottomEdge:
                self.setCursor(Qt.CursorShape.SizeVerCursor)
            elif edge == (Qt.Edge.TopEdge | Qt.Edge.LeftEdge) or edge == (Qt.Edge.BottomEdge | Qt.Edge.RightEdge):
                self.setCursor(Qt.CursorShape.SizeFDiagCursor)
            elif edge == (Qt.Edge.TopEdge | Qt.Edge.RightEdge) or edge == (Qt.Edge.BottomEdge | Qt.Edge.LeftEdge):
                self.setCursor(Qt.CursorShape.SizeBDiagCursor)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)
        return super().eventFilter(obj, event)

    def _get_edge(self, pos: QPoint) -> Qt.Edge:
        edge = Qt.Edge(0)
        margin = 15
        
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
            # For corners, we'll let the user resize via QSizeGrip or handle them individually.
            # startSystemResize only works reliably with single edge values in some Qt environments.
            if edge == Qt.Edge.BottomEdge | Qt.Edge.RightEdge:
                # Bottom-right is handled natively by QSizeGrip if they click exactly on it
                pass 
            elif edge != Qt.Edge(0):
                self.windowHandle().startSystemResize(edge)
            else:
                self.windowHandle().startSystemMove()

    def closeEvent(self, event):
        if self.doc:
            try:
                self.doc.close()
            except:
                pass
        super().closeEvent(event)
