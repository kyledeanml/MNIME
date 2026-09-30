from PyQt6.QtGui import QCursor, QPixmap, QPainter, QColor, QRadialGradient, QBrush
from PyQt6.QtCore import Qt

_cached_cursor = None

def get_custom_cursor() -> QCursor:
    global _cached_cursor
    if _cached_cursor is not None:
        return _cached_cursor
        
    size = 40
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    
    # Draw neon cyan glow
    gradient = QRadialGradient(size/2, size/2, size/2)
    gradient.setColorAt(0.0, QColor(0, 210, 255, 180)) # bright cyan core glow
    gradient.setColorAt(0.4, QColor(0, 210, 255, 80))
    gradient.setColorAt(1.0, QColor(0, 210, 255, 0))   # transparent edge
    
    painter.setBrush(QBrush(gradient))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(0, 0, size, size)
    
    # Draw solid white core dot
    painter.setBrush(QColor(255, 255, 255, 255))
    painter.drawEllipse(int(size/2 - 3), int(size/2 - 3), 6, 6)
    
    painter.end()
    
    # Set hotspot exactly to the center of the glow
    _cached_cursor = QCursor(pixmap, hotX=int(size/2), hotY=int(size/2))
    return _cached_cursor


_cached_file_pixmap = {}
_cached_file_cursor = {}

def get_file_drag_pixmap(size: int = 32, color: str = "#00d2ff") -> QPixmap:
    """Generate a crisp, high-contrast custom blue file icon pixmap for dragging."""
    cache_key = (size, color)
    if cache_key in _cached_file_pixmap:
        return _cached_file_pixmap[cache_key]

    from ui.icons import get_svg_pixmap
    from PyQt6.QtGui import QPainterPath
    from PyQt6.QtCore import QPointF

    icon_pm = get_svg_pixmap("document", size, color)

    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Scale document backing shape to match 24x24 viewBox: 6,2 -> 14,2 -> 20,8 -> 20,22 -> 6,22
    s = size / 24.0
    poly = [
        QPointF(6 * s, 2 * s),
        QPointF(14 * s, 2 * s),
        QPointF(20 * s, 8 * s),
        QPointF(20 * s, 22 * s),
        QPointF(6 * s, 22 * s),
    ]
    path = QPainterPath()
    path.moveTo(poly[0])
    for pt in poly[1:]:
        path.lineTo(pt)
    path.closeSubpath()

    # Opaque dark slate fill so cursor is clearly legible on any background/desktop
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(13, 17, 23, 240))
    painter.drawPath(path)

    # Draw the SVG document icon on top
    painter.drawPixmap(0, 0, icon_pm)
    painter.end()

    _cached_file_pixmap[cache_key] = pixmap
    return _cached_file_pixmap[cache_key]


def get_file_drag_cursor(size: int = 32, color: str = "#00d2ff") -> QCursor:
    """Return a custom QCursor showing the blue file icon."""
    cache_key = (size, color)
    if cache_key in _cached_file_cursor:
        return _cached_file_cursor[cache_key]

    pm = get_file_drag_pixmap(size, color)
    # Centered hotspot
    cursor = QCursor(pm, hotX=int(size / 2), hotY=int(size / 2))
    _cached_file_cursor[cache_key] = cursor
    return cursor

