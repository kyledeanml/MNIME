"""
Carousel view widget: horizontal scrollable gallery with navigation arrows and drag-and-drop.
Sleek dark metallic styling with clean dropzone and dark neon blue highlights.

NOTE: QScrollArea is intentionally NOT used here. Its internal viewport widget intercepts
drag-and-drop events at the OS level and cannot be fully disabled, breaking inbound file drops.
Instead we use a plain clipped QWidget + manual scroll offset to achieve the same UX.
"""

from ui.cursor_fx import get_custom_cursor
from typing import List
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
    QLabel, QFrame, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QRect
from PyQt6.QtGui import QColor, QPixmap, QPainter, QRegion
import os
from core.file_item import FileItem
from core.app_icon import get_resource_path
from .file_card import FileCard
from .icons import get_svg_pixmap, get_icon


# ---------------------------------------------------------------------------
# ClippedCardsArea – a simple scrollable container with NO QScrollArea
# ---------------------------------------------------------------------------
class ClippedCardsArea(QWidget):
    """A plain widget that lays cards out horizontally and clips them, with a
    manually managed scroll offset. Accepts drops and passes them to parent."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self._scroll_offset = 0
        self._cards: List[FileCard] = []
        self._spacing = 14
        self._margin = 32

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------
    def set_cards(self, cards: List[FileCard]):
        """Replace the current card list and reposition everything."""
        # Detach old cards so they don't render twice
        for c in self._cards:
            c.setParent(None)
        self._cards = cards
        for c in self._cards:
            c.setParent(self)
        self._scroll_offset = 0
        self._reposition()

    def scroll_by(self, delta: int):
        max_offset = max(0, self._content_width() - self.width())
        self._scroll_offset = max(0, min(self._scroll_offset + delta, max_offset))
        self._reposition()

    def scroll_to(self, offset: int):
        max_offset = max(0, self._content_width() - self.width())
        self._scroll_offset = max(0, min(offset, max_offset))
        self._reposition()

    def current_offset(self) -> int:
        return self._scroll_offset

    def max_offset(self) -> int:
        return max(0, self._content_width() - self.width())

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _content_width(self) -> int:
        if not self._cards:
            return 0
        w = self._margin
        for c in self._cards:
            w += c.CARD_WIDTH + self._spacing
        return w

    def _reposition(self):
        x = self._margin - self._scroll_offset
        y = (self.height() - FileCard.CARD_HEIGHT) // 2
        for c in self._cards:
            c.move(x, y)
            c.show()
            x += c.CARD_WIDTH + self._spacing
        self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._reposition()

    # ------------------------------------------------------------------
    # Drag events — accept OS file drops (fallback if OLE DnD is active)
    # Internal card reorder is handled by mouse events, not DnD.
    # ------------------------------------------------------------------
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            from ui.cursor_fx import get_file_drag_cursor
            from PyQt6.QtWidgets import QApplication
            if QApplication.overrideCursor() is None:
                QApplication.setOverrideCursor(get_file_drag_cursor())
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        from PyQt6.QtWidgets import QApplication
        while QApplication.overrideCursor() is not None:
            QApplication.restoreOverrideCursor()
        super().dragLeaveEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        from PyQt6.QtWidgets import QApplication
        while QApplication.overrideCursor() is not None:
            QApplication.restoreOverrideCursor()
        mime = event.mimeData()
        if mime.hasUrls():
            paths = [u.toLocalFile() for u in mime.urls() if u.isLocalFile()]
            if paths:
                p = self.parent()
                while p and not hasattr(p, "files_dropped"):
                    p = p.parent()
                if p:
                    p.files_dropped.emit(paths)
                event.acceptProposedAction()
        else:
            event.ignore()

    def wheelEvent(self, event):
        delta = event.angleDelta().y() or event.angleDelta().x()
        if delta:
            self.scroll_by(-int(delta * 1.5))
            event.accept()
        else:
            super().wheelEvent(event)


# ---------------------------------------------------------------------------
# DropZoneFrame – dedicated drop zone for empty carousel state
# ---------------------------------------------------------------------------
class DropZoneFrame(QFrame):
    """Empty state dropzone that accepts OS files and triggers carousel glow."""

    def __init__(self, carousel, parent=None):
        super().__init__(parent)
        self.carousel = carousel
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            from ui.cursor_fx import get_file_drag_cursor
            from PyQt6.QtWidgets import QApplication
            if QApplication.overrideCursor() is None:
                QApplication.setOverrideCursor(get_file_drag_cursor())
            self.carousel._set_drag_style(True)
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        from PyQt6.QtWidgets import QApplication
        while QApplication.overrideCursor() is not None:
            QApplication.restoreOverrideCursor()
        self.carousel._set_drag_style(False)
        super().dragLeaveEvent(event)

    def dropEvent(self, event):
        from PyQt6.QtWidgets import QApplication
        while QApplication.overrideCursor() is not None:
            QApplication.restoreOverrideCursor()
        self.carousel._set_drag_style(False)
        if event.mimeData().hasUrls():
            paths = [u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()]
            if paths:
                self.carousel.files_dropped.emit(paths)
                event.acceptProposedAction()
        else:
            event.ignore()


# ---------------------------------------------------------------------------
# CarouselView
# ---------------------------------------------------------------------------
class CarouselView(QWidget):
    """Horizontal carousel displaying uploaded file cards with left/right scroll controls."""

    files_reordered = pyqtSignal()
    file_removed = pyqtSignal(object)   # FileItem
    files_dropped = pyqtSignal(list)    # List[str]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.file_items: List[FileItem] = []
        self.cards: List[FileCard] = []

        # CarouselView itself accepts OS drops
        self.setAcceptDrops(True)
        self._setup_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 8, 0, 8)
        main_layout.setSpacing(8)

        # Left scroll button
        self.left_btn = QPushButton()
        self.left_btn.setFixedSize(36, 64)
        self.left_btn.setIcon(get_icon("arrow_left", "#00e5ff"))
        self.left_btn.setCursor(get_custom_cursor())
        self.left_btn.setStyleSheet("""
            QPushButton {
                background-color: #11151f;
                border: 1px solid #1f2737;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #1a2233;
                border: 1px solid #00d2ff;
            }
            QPushButton:disabled {
                background-color: transparent;
                border: 1px solid transparent;
            }
        """)
        self.left_btn.clicked.connect(self._scroll_left)
        main_layout.addWidget(self.left_btn)

        # Center container
        self.center_container = QWidget()
        self.center_container.setObjectName("center_container")
        self.center_layout = QVBoxLayout(self.center_container)
        self.center_layout.setContentsMargins(0, 0, 0, 0)

        # Ambient glow
        self.carousel_glow = QGraphicsDropShadowEffect(self)
        self.carousel_glow.setBlurRadius(25)
        self.carousel_glow.setColor(QColor(0, 210, 255, 50))
        self.carousel_glow.setOffset(0, 0)
        self.center_container.setGraphicsEffect(self.carousel_glow)

        # Empty / drop zone (shown when no files loaded)
        self.empty_zone = DropZoneFrame(self)
        self.empty_zone.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #10141e, stop:1 #0a0d14);
                border: 1.5px solid #212a3d;
                border-radius: 14px;
            }
        """)
        empty_layout = QVBoxLayout(self.empty_zone)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.setSpacing(10)

        cloud_icon = QLabel()
        cloud_icon.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        logo_path = get_resource_path("OMN.jpg")
        original_pixmap = QPixmap(logo_path)
        if not original_pixmap.isNull():
            logo_pixmap = original_pixmap.scaled(
                180, 180,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            cloud_icon.setPixmap(logo_pixmap)
        cloud_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(cloud_icon)

        # Cards area (replaces QScrollArea)
        self.cards_area = ClippedCardsArea()
        self.cards_area.setStyleSheet("background: transparent;")

        self.center_layout.addWidget(self.empty_zone)
        self.center_layout.addWidget(self.cards_area)
        main_layout.addWidget(self.center_container, 1)

        # Right scroll button
        self.right_btn = QPushButton()
        self.right_btn.setFixedSize(36, 64)
        self.right_btn.setIcon(get_icon("arrow_right", "#00e5ff"))
        self.right_btn.setCursor(get_custom_cursor())
        self.right_btn.setStyleSheet("""
            QPushButton {
                background-color: #11151f;
                border: 1px solid #1f2737;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #1a2233;
                border: 1px solid #00d2ff;
            }
            QPushButton:disabled {
                background-color: transparent;
                border: 1px solid transparent;
            }
        """)
        self.right_btn.clicked.connect(self._scroll_right)
        main_layout.addWidget(self.right_btn)

        self.refresh_view()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def set_items(self, items: List[FileItem]):
        """Sets the files to display in the carousel."""
        self.file_items = items
        self.refresh_view()

    def refresh_view(self):
        """Re-renders all cards based on current items list."""
        # Detach and destroy old cards
        for card in self.cards:
            card.deleteLater()
        self.cards.clear()

        if not self.file_items:
            self.empty_zone.setVisible(True)
            self.cards_area.setVisible(False)
            self.left_btn.setEnabled(False)
            self.right_btn.setEnabled(False)
            self.cards_area.set_cards([])
            return

        self.empty_zone.setVisible(False)
        self.cards_area.setVisible(True)
        self.left_btn.setEnabled(True)
        self.right_btn.setEnabled(True)

        for index, item in enumerate(self.file_items):
            card = FileCard(item, index)
            card.remove_requested.connect(self._on_card_removed)
            card.card_moved.connect(self._on_card_reordered)
            self.cards.append(card)

        self.cards_area.set_cards(self.cards)

    # ------------------------------------------------------------------
    # Card event handlers
    # ------------------------------------------------------------------
    def _on_card_removed(self, item: FileItem):
        if item in self.file_items:
            try:
                idx = self.file_items.index(item)
                self.file_items.pop(idx)

                if idx < len(self.cards):
                    card = self.cards.pop(idx)
                    card.deleteLater()

                for i, c in enumerate(self.cards):
                    c.index = i

                if not self.file_items:
                    self.empty_zone.setVisible(True)
                    self.cards_area.setVisible(False)
                    self.left_btn.setEnabled(False)
                    self.right_btn.setEnabled(False)

                self.cards_area.set_cards(self.cards)
                self.file_removed.emit(item)
            except ValueError:
                self.refresh_view()

    def _on_card_reordered(self, from_idx: int, to_idx: int):
        if (0 <= from_idx < len(self.file_items) and
                0 <= to_idx < len(self.file_items) and
                from_idx != to_idx):
            item = self.file_items.pop(from_idx)
            self.file_items.insert(to_idx, item)

            if from_idx < len(self.cards) and to_idx < len(self.cards):
                card = self.cards.pop(from_idx)
                self.cards.insert(to_idx, card)
                for i, c in enumerate(self.cards):
                    c.index = i

            self.cards_area.set_cards(self.cards)
            self.files_reordered.emit()

    # ------------------------------------------------------------------
    # Scroll
    # ------------------------------------------------------------------
    def _scroll_left(self):
        self._animate_scroll(max(0, self.cards_area.current_offset() - 350))

    def _scroll_right(self):
        self._animate_scroll(min(self.cards_area.max_offset(),
                                 self.cards_area.current_offset() + 350))

    def _animate_scroll(self, target: int):
        # We animate a dummy QPropertyAnimation on a proxy property
        # by using a simple timer-based approach on the offset directly.
        from PyQt6.QtCore import QTimeLine
        start = self.cards_area.current_offset()
        delta = target - start
        if delta == 0:
            return
        steps = 20
        self._scroll_step = 0
        self._scroll_target = target
        self._scroll_start = start

        from PyQt6.QtCore import QTimer
        self._scroll_timer = QTimer(self)
        self._scroll_timer.setInterval(16)  # ~60 fps

        def _step():
            self._scroll_step += 1
            t = self._scroll_step / steps
            # Ease out cubic
            t2 = 1 - (1 - t) ** 3
            new_offset = int(self._scroll_start + delta * t2)
            self.cards_area.scroll_to(new_offset)
            if self._scroll_step >= steps:
                self._scroll_timer.stop()

        self._scroll_timer.timeout.connect(_step)
        self._scroll_timer.start()

    def wheelEvent(self, event):
        delta = event.angleDelta().y() or event.angleDelta().x()
        if delta and self.cards_area.isVisible():
            self.cards_area.scroll_by(-int(delta * 1.5))
            event.accept()
        else:
            super().wheelEvent(event)

    # ------------------------------------------------------------------
    # Drag glow helper
    # ------------------------------------------------------------------
    def _set_drag_style(self, active: bool):
        if active:
            self.carousel_glow.setColor(QColor(0, 210, 255, 180))
        else:
            self.carousel_glow.setColor(QColor(0, 210, 255, 50))

    # ------------------------------------------------------------------
    # OS drag-and-drop (inbound: files from Explorer/Desktop → carousel)
    # ------------------------------------------------------------------
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            from ui.cursor_fx import get_file_drag_cursor
            from PyQt6.QtWidgets import QApplication
            if QApplication.overrideCursor() is None:
                QApplication.setOverrideCursor(get_file_drag_cursor())
            self._set_drag_style(True)
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        from PyQt6.QtWidgets import QApplication
        while QApplication.overrideCursor() is not None:
            QApplication.restoreOverrideCursor()
        self._set_drag_style(False)
        super().dragLeaveEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        from PyQt6.QtWidgets import QApplication
        while QApplication.overrideCursor() is not None:
            QApplication.restoreOverrideCursor()
        self._set_drag_style(False)
        if event.mimeData().hasUrls():
            paths = [u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()]
            if paths:
                self.files_dropped.emit(paths)
                event.acceptProposedAction()
