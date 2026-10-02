import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from core.app_icon import get_logo_pixmap

app = QApplication(sys.argv)
# Generate a high-res 512x512 vector icon directly
pixmap = get_logo_pixmap(512)
pixmap.save('OMNIME_reimagined_alpha.png')
print("Saved OMNIME_reimagined_alpha.png")
