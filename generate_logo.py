import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPixmap, QImage
from core.app_icon import _draw_logo_pixmap
from PIL import Image

app = QApplication(sys.argv)

# Generate a high-res 256x256 logo for the .ico
pixmap = _draw_logo_pixmap(256, rotation=0.5, is_tray=True) # Use 3D cube for cleaner small icons
image = pixmap.toImage().convertToFormat(QImage.Format.Format_RGBA8888)

width = image.width()
height = image.height()
ptr = image.bits()
ptr.setsize(height * width * 4)
arr = bytearray(ptr)

pil_img = Image.frombytes("RGBA", (width, height), arr)
pil_img.save("OMN.ico", format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
print("Saved procedural OMN.ico")
