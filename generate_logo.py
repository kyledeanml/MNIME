import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from core.app_icon import get_tray_icon

app = QApplication(sys.argv)
# Generate a high-res 512x512 vector icon directly
icon = get_tray_icon(512)
pixmap = icon.pixmap(512, 512)
pixmap.save('OMNIME_reimagined_alpha.png')
print("Saved OMNIME_reimagined_alpha.png")
