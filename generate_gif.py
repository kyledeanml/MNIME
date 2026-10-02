import sys
import math
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPixmap, QPainter, QFont, QColor
from PyQt6.QtCore import Qt, QRect
from PIL import Image

app = QApplication(sys.argv)

logo_size = 400
banner_width = 500
banner_height = 550

frames = []
num_frames = 720
max_rotation = 4 * math.pi

for i in range(num_frames):
    rotation = (i / num_frames) * max_rotation
    
    pixmap = QPixmap(banner_width, banner_height)
    # Use a dark background to match the README (since GIFs don't do partial transparency well)
    pixmap.fill(QColor(13, 17, 23)) # GitHub dark mode background roughly
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
    
    # Draw logo
    from core.app_icon import get_logo_pixmap
    logo_pixmap = get_logo_pixmap(logo_size, rotation)
    logo_x = (banner_width - logo_size) // 2
    painter.drawPixmap(logo_x, 0, logo_pixmap)
    
    # Draw typography
    font = QFont("Segoe UI", 36, QFont.Weight.Black)
    font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 10.0)
    painter.setFont(font)
    painter.setPen(QColor(176, 196, 222))
    
    text_rect = QRect(0, logo_size - 20, banner_width, banner_height - logo_size + 20)
    painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, "MNIME")
    
    painter.end()
    
    # Convert QPixmap to PIL Image
    image = pixmap.toImage()
    # image format is Format_ARGB32_Premultiplied
    width = image.width()
    height = image.height()
    
    # Convert to standard RGBA bytes
    image = image.convertToFormat(image.Format.Format_RGBA8888)
    
    ptr = image.bits()
    ptr.setsize(height * width * 4)
    arr = bytearray(ptr)
    
    pil_img = Image.frombytes("RGBA", (width, height), arr)
    frames.append(pil_img)

# Save as GIF
frames[0].save(
    "MNIME_banner.gif",
    save_all=True,
    append_images=frames[1:],
    optimize=False,
    duration=33, # 33ms per frame = 30 fps for a slow smooth crawl
    loop=0
)
print("Saved MNIME_banner.gif")
