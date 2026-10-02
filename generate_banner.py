import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPixmap, QPainter, QFont, QColor
from PyQt6.QtCore import Qt, QRect
from core.app_icon import get_tray_icon

app = QApplication(sys.argv)

# Define sizes
logo_size = 400
banner_width = 500
banner_height = 550

# Create a transparent pixmap
pixmap = QPixmap(banner_width, banner_height)
pixmap.fill(Qt.GlobalColor.transparent)

painter = QPainter(pixmap)
painter.setRenderHint(QPainter.RenderHint.Antialiasing)
painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

# Draw the logo
icon = get_tray_icon(logo_size)
logo_pixmap = icon.pixmap(logo_size, logo_size)
logo_x = (banner_width - logo_size) // 2
painter.drawPixmap(logo_x, 0, logo_pixmap)

# Draw the typography
font = QFont("Segoe UI", 36, QFont.Weight.Black)
font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 10.0)
painter.setFont(font)
painter.setPen(QColor(176, 196, 222))  # #b0c4de

text_rect = QRect(0, logo_size, banner_width, banner_height - logo_size)
painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, "OMNIME")

painter.end()

pixmap.save('OMNIME_banner.png')
print("Saved OMNIME_banner.png")
