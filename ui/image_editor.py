import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QMessageBox, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem
)
from PyQt6.QtCore import Qt, QRectF, QRect, QPoint, pyqtSignal
from PyQt6.QtGui import QPixmap, QPainter, QColor, QPen, QTransform
from core.file_item import FileItem
from PIL import Image

class ImageCropView(QGraphicsView):
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.rubber_band = QRect()
        self.start_pos = QPoint()
        self.is_drawing = False

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
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_drawing = False
        super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self.rubber_band.isEmpty():
            painter = QPainter(self.viewport())
            pen = QPen(QColor(0, 210, 255))
            pen.setWidth(2)
            painter.setPen(pen)
            painter.drawRect(self.rubber_band)

    def get_crop_rect(self):
        if self.rubber_band.isEmpty():
            return None
        # Convert rubber band (viewport coords) to scene coords
        top_left = self.mapToScene(self.rubber_band.topLeft())
        bottom_right = self.mapToScene(self.rubber_band.bottomRight())
        return QRectF(top_left, bottom_right)

class ImageEditorDialog(QDialog):
    def __init__(self, file_item: FileItem, parent=None):
        super().__init__(parent)
        self.file_item = file_item
        self.setWindowTitle("Edit Image")
        self.setMinimumSize(800, 600)
        
        # Load image via PIL to manage rotation and cropping
        try:
            self.pil_image = Image.open(file_item.file_path)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not open image: {e}")
            self.reject()
            return
            
        self.current_rotation = 0
        
        self.setStyleSheet("""
            QDialog {
                background-color: #11151f;
                color: #f0f6fc;
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
        """)
        
        self.setup_ui()
        self.update_image_display()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        self.scene = QGraphicsScene(self)
        self.view = ImageCropView(self.scene, self)
        self.view.setStyleSheet("background-color: #0a0d14; border: 1px solid #1f2737;")
        layout.addWidget(self.view, 1)
        
        controls_layout = QHBoxLayout()
        
        self.rotate_btn = QPushButton("Rotate 90°")
        self.rotate_btn.clicked.connect(self.rotate_image)
        
        self.crop_btn = QPushButton("Crop")
        self.crop_btn.clicked.connect(self.crop_image)
        
        self.save_btn = QPushButton("Save && Replace")
        self.save_btn.clicked.connect(self.save_image)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        
        controls_layout.addWidget(self.rotate_btn)
        controls_layout.addWidget(self.crop_btn)
        controls_layout.addStretch()
        controls_layout.addWidget(self.save_btn)
        controls_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(controls_layout)
        
    def update_image_display(self):
        self.scene.clear()
        
        # Save temp to load into QPixmap
        import tempfile, os
        fd, temp_path = tempfile.mkstemp(suffix=".png")
        os.close(fd)
        self.pil_image.save(temp_path)
        
        pixmap = QPixmap(temp_path)
        os.remove(temp_path)
        
        self.pixmap_item = QGraphicsPixmapItem(pixmap)
        self.scene.addItem(self.pixmap_item)
        self.scene.setSceneRect(QRectF(pixmap.rect()))
        
        self.view.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        self.view.rubber_band = QRect()

    def rotate_image(self):
        self.pil_image = self.pil_image.rotate(-90, expand=True)
        self.update_image_display()
        
    def crop_image(self):
        rect = self.view.get_crop_rect()
        if not rect:
            QMessageBox.warning(self, "No crop area", "Please draw a crop rectangle first.")
            return
            
        x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()
        # Bound to image size
        x = max(0, x)
        y = max(0, y)
        w = min(self.pil_image.width - x, w)
        h = min(self.pil_image.height - y, h)
        
        if w > 0 and h > 0:
            self.pil_image = self.pil_image.crop((x, y, x+w, y+h))
            self.update_image_display()
        
    def save_image(self):
        self.pil_image.save(self.file_item.file_path)
        self.accept()
