"""
Application Icon and Windows Taskbar/Quickbar Integration Module.
Handles Windows AppUserModelID registration, multi-resolution ICO generation,
QIcon creation, and Windows shortcut creation for taskbar/quickbar pinning.
"""

import os
import sys
import ctypes
import subprocess
from typing import Optional
from PyQt6.QtGui import QIcon, QPixmap

APP_USER_MODEL_ID = "OMNIME.Desktop.1.5"


def get_resource_path(relative_path: str) -> str:
    """Get absolute path to resource, working across dev and PyInstaller onedir/onefile builds."""
    if hasattr(sys, "_MEIPASS"):
        meipass_path = os.path.join(sys._MEIPASS, relative_path)
        if os.path.exists(meipass_path):
            return meipass_path

    if getattr(sys, "frozen", False):
        exe_dir = os.path.dirname(sys.executable)
        exe_path = os.path.join(exe_dir, relative_path)
        if os.path.exists(exe_path):
            return exe_path
        internal_path = os.path.join(exe_dir, "_internal", relative_path)
        if os.path.exists(internal_path):
            return internal_path

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dev_path = os.path.join(project_root, relative_path)
    if os.path.exists(dev_path):
        return dev_path

    return os.path.join(os.getcwd(), relative_path)


def get_ico_path() -> str:
    return get_resource_path("OMN.ico")


def get_png_path() -> str:
    return get_resource_path("OMNIME_reimagined_alpha.png")


def setup_app_user_model_id() -> bool:
    """
    Sets the explicit Application User Model ID on Windows.
    This prevents Windows from grouping the app under python.exe and
    ensures the taskbar / quickbar displays the custom OMNIME logo.
    """
    if sys.platform == "win32":
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_USER_MODEL_ID)
            return True
        except Exception as e:
            print(f"Warning: Failed to set AppUserModelID: {e}")
            return False
    return False


def ensure_ico_file() -> Optional[str]:
    """
    Ensures that a multi-resolution Windows ICO file exists.
    If OMN.ico does not exist, it converts OMNIME_reimagined_alpha.png using Pillow.
    """
    ico_path = get_ico_path()
    if os.path.exists(ico_path):
        return ico_path

    png_path = get_png_path()
    if not os.path.exists(png_path):
        return None

    try:
        from PIL import Image

        img = Image.open(png_path)
        w, h = img.size

        # Center-crop to 1:1 square to maintain the circular emblem's aspect ratio
        crop_dim = min(w, h)
        left = (w - crop_dim) // 2
        top = (h - crop_dim) // 2
        square_crop = img.crop((left, top, left + crop_dim, top + crop_dim))

        # Save standard Windows icon sizes (16, 24, 32, 48, 64, 128, 256)
        icon_sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        square_crop.save(ico_path, format="ICO", sizes=icon_sizes)
        return ico_path
    except Exception as e:
        print(f"Warning: Could not create ICO file: {e}")
        return None


_CACHED_APP_ICON: Optional[QIcon] = None
_CACHED_LOGO_PIXMAPS: dict = {}


def get_app_icon() -> QIcon:
    """
    Returns the QIcon for the application (cached).
    Uses the pure programmatic vector logo (origami geometric pattern).
    """
    global _CACHED_APP_ICON
    if _CACHED_APP_ICON is not None and not _CACHED_APP_ICON.isNull():
        return _CACHED_APP_ICON

    _CACHED_APP_ICON = get_tray_icon()
    return _CACHED_APP_ICON


def _draw_logo_pixmap(size: int = 64, rotation: float = 0.0) -> QPixmap:
    """
    Draws the logo and returns a QPixmap.
    """
    from PyQt6.QtGui import QPixmap, QPainter, QPen, QColor
    from PyQt6.QtCore import Qt, QPointF
    import math
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    center = QPointF(size / 2, size / 2)
    # Using 0.35 to give plenty of room without hitting edges
    radius = size * 0.35

    # Points for a dynamic swirling mesh (electrons around nucleus)
    points = []
    for i in range(6):
        base_angle = math.radians(60 * i - 30)
        # Slow down the speed multipliers for a more elegant swirl (and multiple of 0.5 for seamless looping)
        speed_mult = 0.5 + (i % 3) * 0.5 
        dir_mult = 1 if i % 2 == 0 else -1
        
        dyn_radius = radius + math.sin(rotation * 2 + i) * (radius * 0.15)
        angle = base_angle + rotation * speed_mult * dir_mult
        
        points.append(QPointF(
            center.x() + dyn_radius * math.cos(angle),
            center.y() + dyn_radius * math.sin(angle)
        ))

    # Draw the glowing mesh
    # 1. Outer glow (Metallic)
    outer_glow_width = max(1.0, 4.0 * (size / 64.0))
    painter.setPen(QPen(QColor(160, 170, 180, 100), outer_glow_width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    for i in range(6):
        for j in range(i + 1, 6):
            if (j - i) in [1, 3, 5]:
                painter.drawLine(points[i], points[j])
            
    # 2. Bright inner core lines (Silver/Chrome)
    inner_core_width = max(1.0, 1.5 * (size / 64.0))
    painter.setPen(QPen(QColor(230, 240, 250, 255), inner_core_width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    for i in range(6):
        for j in range(i + 1, 6):
            if (j - i) in [1, 3, 5]: 
                painter.drawLine(points[i], points[j])
                
    # Add a glowing central node
    painter.setBrush(QColor(255, 255, 255, 255))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(center, radius * 0.15, radius * 0.15)
    
    # Node dots (Cute little blue file icons)
    from ui.icons import get_svg_pixmap
    icon_w = int(radius * 0.25)
    icon_h = int(radius * 0.25)
    file_pixmap = get_svg_pixmap("file", size=icon_w, color="#00e5ff")
    if not file_pixmap.isNull():
        for p in points:
            painter.drawPixmap(int(p.x() - icon_w / 2), int(p.y() - icon_h / 2), file_pixmap)
    else:
        painter.setBrush(QColor(0, 229, 255, 255))
        painter.setPen(Qt.PenStyle.NoPen)
        for p in points:
            painter.drawEllipse(p, radius * 0.12, radius * 0.12)

    painter.end()
    return pixmap


def get_tray_icon(size: int = 64, rotation: float = 0.0):
    from PyQt6.QtGui import QIcon
    return QIcon(_draw_logo_pixmap(size, rotation))

def get_logo_pixmap(size: int = 48, rotation: float = 0.0):
    """
    Returns a smooth QPixmap of the logo sized to (size, size).
    Cached only if rotation is 0.0.
    """
    if rotation == 0.0 and size in _CACHED_LOGO_PIXMAPS:
        return _CACHED_LOGO_PIXMAPS[size]

    pixmap = _draw_logo_pixmap(size, rotation)
    if rotation == 0.0:
        _CACHED_LOGO_PIXMAPS[size] = pixmap
    return pixmap



def create_windows_shortcuts() -> bool:
    """
    Creates Windows shortcuts on the Desktop and in the project directory,
    pointing to run.bat with the custom OMN.ico icon.
    """
    if sys.platform != "win32":
        return False

    try:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        target_path = os.path.join(project_root, "run.bat")
        ensure_ico_file()
        icon_path = get_ico_path()
        desktop_dir = os.path.normpath(os.path.expanduser("~/Desktop"))
        desktop_lnk = os.path.join(desktop_dir, "OMNIME.lnk")
        project_lnk = os.path.join(project_root, "OMNIME.lnk")

        ps_script = f"""
$WshShell = New-Object -ComObject WScript.Shell
$s1 = $WshShell.CreateShortcut('{desktop_lnk}')
$s1.TargetPath = '{target_path}'
$s1.WorkingDirectory = '{project_root}'
$s1.IconLocation = '{icon_path},0'
$s1.Save()

$s2 = $WshShell.CreateShortcut('{project_lnk}')
$s2.TargetPath = '{target_path}'
$s2.WorkingDirectory = '{project_root}'
$s2.IconLocation = '{icon_path},0'
$s2.Save()
"""
        subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], check=True, capture_output=True)
        return True
    except Exception as e:
        print(f"Failed to create shortcuts: {e}")
        return False
