import os
import fitz
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QMessageBox, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem
)
from PyQt6.QtCore import Qt, QRectF, QRect, QPoint
from PyQt6.QtGui import QPixmap, QPainter, QColor, QPen, QImage
from core.file_item import FileItem
from ui.image_editor import ImageCropView

class PDFEditorDialog(QDialog):
    def __init__(self, file_item: FileItem, parent=None):
        super().__init__(parent)
        self.file_item = file_item
        self.setWindowTitle(f"Edit PDF - {file_item.file_name}")
        self.setMinimumSize(800, 600)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        try:
            self.doc = fitz.open(file_item.file_path)
            if self.doc.page_count == 0:
                raise ValueError("PDF has no pages.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not open PDF: {e}")
            self.reject()
            return
            
        from PyQt6.QtWidgets import QFrame, QGraphicsDropShadowEffect
        self.container_frame = QFrame(self)
        self.container_frame.setStyleSheet("""
            QFrame {
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
            QPushButton {
                background-color: #162438;
                color: #00e5ff;
                border: 1px solid #00d2ff;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #0077b6;
                color: #ffffff;
            }
            QLabel { color: #8b949e; font-weight: bold; border: none; background: transparent; }
        """)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 4)
        self.container_frame.setGraphicsEffect(shadow)
        
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.container_frame)
        
        self.setup_ui()
        self.update_pdf_display()

    def setup_ui(self):
        layout = QVBoxLayout(self.container_frame)
        layout.setContentsMargins(16, 16, 16, 16)
        
        top_bar = QHBoxLayout()
        title = QLabel(f"EDIT PDF - {self.file_item.file_name}")
        title.setStyleSheet("color: #00d2ff; font-family: 'Segoe UI Black'; font-size: 14px; letter-spacing: 1px;")
        
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(32, 32)
        close_btn.setStyleSheet("""
            QPushButton { background-color: #162438; color: #00e5ff; border: 1px solid #00d2ff; border-radius: 16px; font-size: 16px; font-weight: 900; }
            QPushButton:hover { background-color: #00d2ff; color: #000000; }
        """)
        close_btn.clicked.connect(self.reject)
        
        top_bar.addWidget(title)
        top_bar.addStretch()
        top_bar.addWidget(close_btn)
        layout.addLayout(top_bar)
        
        # We'll preview Page 0 for crop/rotate operations
        self.info_label = QLabel("Previewing Page 1. Rotation and cropping will apply to ALL pages.")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.info_label)
        
        self.scene = QGraphicsScene(self)
        self.view = ImageCropView(self.scene, self)
        self.view.setStyleSheet("background-color: #0a0d14; border: 1px solid #1f2737;")
        layout.addWidget(self.view, 1)
        
        controls_layout = QHBoxLayout()
        
        self.rotate_btn = QPushButton("Rotate 90° (All Pages)")
        from ui.cursor_fx import get_custom_cursor
        self.rotate_btn.setCursor(get_custom_cursor())
        self.rotate_btn.clicked.connect(self.rotate_pdf)
        
        self.crop_btn = QPushButton("Crop (All Pages)")
        self.crop_btn.setCursor(get_custom_cursor())
        self.crop_btn.clicked.connect(self.crop_pdf)
        
        self.save_btn = QPushButton("Save && Replace")
        self.save_btn.setCursor(get_custom_cursor())
        self.save_btn.clicked.connect(self.save_pdf)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setCursor(get_custom_cursor())
        self.cancel_btn.clicked.connect(self.reject)
        
        controls_layout.addWidget(self.rotate_btn)
        controls_layout.addWidget(self.crop_btn)
        controls_layout.addStretch()
        controls_layout.addWidget(self.save_btn)
        controls_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(controls_layout)
        
    def update_pdf_display(self):
        self.scene.clear()
        
        # Render the first page
        page = self.doc[0]
        # Use a high zoom for Retina-like sharp preview
        zoom = 4.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        
        # Convert fitz pixmap to QImage
        fmt = QImage.Format.Format_RGBA8888 if pix.alpha else QImage.Format.Format_RGB888
        img = QImage(pix.samples, pix.width, pix.height, pix.stride, fmt)
        qpixmap = QPixmap.fromImage(img)
        
        self.pix_width = pix.width
        self.pix_height = pix.height
        self.page_rect = page.rect
        
        self.pixmap_item = QGraphicsPixmapItem(qpixmap)
        self.pixmap_item.setTransformationMode(Qt.TransformationMode.SmoothTransformation)
        self.scene.addItem(self.pixmap_item)
        self.scene.setSceneRect(QRectF(qpixmap.rect()))
        
        self.view.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        self.view.rubber_band = QRect()

    def rotate_pdf(self):
        for page in self.doc:
            page.set_rotation((page.rotation + 90) % 360)
        self.update_pdf_display()
        
    def crop_pdf(self):
        rect = self.view.get_crop_rect()
        if not rect:
            QMessageBox.warning(self, "No crop area", "Please draw a crop rectangle first.")
            return
            
        # Map pixel coordinates back to PDF points
        x_scale = self.page_rect.width / self.pix_width
        y_scale = self.page_rect.height / self.pix_height
        
        x0 = self.page_rect.x0 + rect.x() * x_scale
        y0 = self.page_rect.y0 + rect.y() * y_scale
        x1 = self.page_rect.x0 + (rect.x() + rect.width()) * x_scale
        y1 = self.page_rect.y0 + (rect.y() + rect.height()) * y_scale
        
        crop_rect = fitz.Rect(x0, y0, x1, y1)
        
        for page in self.doc:
            page.set_cropbox(crop_rect)
            
        self.update_pdf_display()
        
    def save_pdf(self):
        # Save replacing the original file
        temp_path = self.file_item.file_path + ".tmp.pdf"
        self.doc.save(temp_path, garbage=4, deflate=True)
        self.doc.close()
        
        # Replace original
        try:
            os.replace(temp_path, self.file_item.file_path)
            self.accept()
        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            QMessageBox.critical(self, "Save Error", f"Failed to save PDF: {e}")
            self.reject()
