"""
MNIME Desktop - MULTIMODAL NEURAL INTERFACE MACHINE EXTENSION
Next-generation private, high-performance offline document suite.
"""

import os
import sys

# Ensure the root project directory is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Fix for "Could not find the Qt platform plugin 'windows'" and broken image formats
venv_base = os.path.dirname(os.path.dirname(sys.executable))
plugin_base = os.path.join(venv_base, "Lib", "site-packages", "PyQt6", "Qt6", "plugins")
os.environ["QT_PLUGIN_PATH"] = plugin_base
os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = os.path.join(plugin_base, "platforms")

# Configure Windows AppUserModelID early so taskbar/quickbar pinning groups correctly
from core.app_icon import setup_app_user_model_id, get_app_icon
setup_app_user_model_id()

import math
import random

from PyQt6.QtWidgets import QApplication, QWidget, QGraphicsOpacityEffect
from PyQt6.QtGui import (QFont, QPainter, QLinearGradient, QColor,
                         QFontMetrics, QPen, QBrush, QPixmap, QPolygonF)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QPointF



class Particle:
    def __init__(self, cx, cy):
        # Spawn around the MNIME text area
        self.x = cx + random.uniform(-50, 50)
        self.y = cy + random.uniform(-50, 50)
        
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(10, 40)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        
        self.trail = []
        self.max_trail = random.randint(10, 25)
        self.size = random.uniform(0.5, 1.5)
        self.cx = cx
        self.cy = cy - 40 # slightly above the text for the merge point
        self.phase = 1
        self.active = True

    def update(self):
        if not self.active:
            return
            
        self.trail.append((self.x, self.y))
        if len(self.trail) > self.max_trail:
            self.trail.pop(0)
            
        if self.phase == 1:
            # Random erratic movement (shoot around)
            self.vx += random.uniform(-8, 8)
            self.vy += random.uniform(-8, 8)
            # Gentle drag
            self.vx *= 0.95
            self.vy *= 0.95
        elif self.phase == 2:
            # Merge into one large file at center
            dx = self.cx - self.x
            dy = self.cy - self.y
            dist = math.hypot(dx, dy)
            if dist < 15:
                self.active = False
                return
            
            # Strong attraction to center
            if dist > 0:
                self.vx += (dx / dist) * 6.0
                self.vy += (dy / dist) * 6.0
            self.vx *= 0.90
            self.vy *= 0.90
            
        self.x += self.vx
        self.y += self.vy

from ui.main_window import MainWindow

class MetalSplashScreen(QWidget):
    """A completely borderless, transparent widget that displays the MNIME title in dark metal with a rotating 5D Penteract."""
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.SplashScreen
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        screen = QApplication.primaryScreen().geometry()
        w, h = screen.width(), screen.height()
        self.setFixedSize(w, h)
        
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        
        self.rotation = 0.0
        self.logo_scale = 0.0
        
        # Initialize massive full-screen Particle System
        self.particles = [Particle(w/2, h/2) for _ in range(300)]
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._update_animation)
        
        # Create tiny glowing file icon pixmap cache for particles
        self.file_pixmap = QPixmap(24, 24)
        self.file_pixmap.fill(Qt.GlobalColor.transparent)
        p = QPainter(self.file_pixmap)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        poly = QPolygonF([
            QPointF(4, 2), QPointF(14, 2), QPointF(20, 8),
            QPointF(20, 22), QPointF(4, 22)
        ])
        
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(140, 230, 255, 80))
        p.drawEllipse(0, 0, 24, 24)
        
        p.setPen(QPen(QColor(0, 210, 255, 255), 1.5))
        p.setBrush(QColor(255, 255, 255, 255))
        p.drawPolygon(poly)
        
        p.setPen(QPen(QColor(0, 210, 255, 255), 1.5))
        p.drawLine(QPointF(14, 2), QPointF(14, 8))
        p.drawLine(QPointF(14, 8), QPointF(20, 8))
        
        p.end()

        self.anim_timer.start(16)
        
        self.phase = 1
        self.central_file_scale = 0.0
        
        # Switch to merge phase after 1.5s
        self.phase_timer = QTimer(self)
        self.phase_timer.setSingleShot(True)
        self.phase_timer.timeout.connect(self._trigger_merge)
        self.phase_timer.start(1500)
        
    def _trigger_merge(self):
        self.phase = 2
        for p in self.particles:
            p.phase = 2

    def _update_animation(self):
        self.rotation += 0.03
        if self.logo_scale < 1.0:
            self.logo_scale = min(1.0, self.logo_scale + 0.03)
            
        arrived = 0
        for p in self.particles:
            p.update()
            if not p.active:
                arrived += 1
                
        if self.phase == 2:
            self.central_file_scale = min(1.0, arrived / len(self.particles))
            
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        
        cx = self.width() // 2
        cy = self.height() // 2
        
        # 0. Draw Particle System
        for p in self.particles:
            if not p.active:
                continue
                
            if len(p.trail) > 1:
                trail_pen = QPen(QColor(140, 230, 255, 60))
                trail_pen.setWidthF(p.size)
                trail_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                painter.setPen(trail_pen)
                points = [QPointF(x, y) for x, y in p.trail]
                painter.drawPolyline(QPolygonF(points))
            
            icon_size = max(14.0, p.size * 10.0)
            painter.drawPixmap(
                int(p.x - icon_size / 2),
                int(p.y - icon_size / 2),
                int(icon_size),
                int(icon_size),
                self.file_pixmap
            )
        
        # 1. Draw Massive 5D Penteract in Background
        if self.logo_scale > 0:
            from core.app_icon import get_logo_pixmap
            logo_size = int(600 * self.logo_scale)
            pixmap = get_logo_pixmap(logo_size, self.rotation)
            
            painter.setOpacity(min(1.0, self.logo_scale))
            painter.drawPixmap(
                int(cx - logo_size / 2),
                int(cy - logo_size / 2 - 40),
                pixmap
            )
            painter.setOpacity(1.0)
        
        # 2. Sleek, modern, and official corporate font
        font = QFont("Segoe UI Black", 85, QFont.Weight.Black)
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 5.0)
        painter.setFont(font)
        
        fm = QFontMetrics(font)
        text_rect = fm.boundingRect("MNIME")
        
        x = cx - text_rect.width() // 2
        y = cy + text_rect.height() // 2 - fm.descent()
        
        # 3. Intense neon blue ambient glow
        glow_color = QColor(0, 210, 255, 25)
        painter.setPen(glow_color)
        for offset in [3, 6]:
            painter.drawText(x - offset, y - offset, "MNIME")
            painter.drawText(x + offset, y - offset, "MNIME")
            painter.drawText(x - offset, y + offset, "MNIME")
            painter.drawText(x + offset, y + offset, "MNIME")
        
        # 4. Deep drop shadow for desktop separation
        painter.setPen(QColor(0, 0, 0, 200))
        painter.drawText(x + 5, y + 5, "MNIME")
        
        # 5. Dark Metallic Gradient Core
        gradient = QLinearGradient(x, y - text_rect.height(), x, y)
        gradient.setColorAt(0.0, QColor("#ffffff")) # Bright top edge highlight
        gradient.setColorAt(0.2, QColor("#e1e4e8")) # Light silver
        gradient.setColorAt(0.5, QColor("#8b949e")) # Mid titanium
        gradient.setColorAt(0.6, QColor("#161b22")) # Sharp dark metal cut
        gradient.setColorAt(1.0, QColor("#484f58")) # Bottom rim reflection
        
        pen = QPen()
        pen.setBrush(QBrush(gradient))
        painter.setPen(pen)
        painter.drawText(x, y, "MNIME")
        
        painter.end()

def main():
    # Enable high-DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("MNIME")
    app.setOrganizationName("MNIME")

    # Set application icon for taskbar, quickbar, window titlebar, and system dialogs
    app_icon = get_app_icon()
    if not app_icon.isNull():
        app.setWindowIcon(app_icon)

    # Set modern clean font
    app_font = QFont("Segoe UI", 10)
    app.setFont(app_font)

    app.main_window = MainWindow()

    # 1. Show Splash Screen
    splash = MetalSplashScreen()
    splash.show()

    # 3. Setup Fade Out Animation
    animation = QPropertyAnimation(splash.opacity_effect, b"opacity")
    animation.setDuration(1200)  # 1.2 second fade out
    animation.setStartValue(1.0)
    animation.setEndValue(0.0)
    
    def on_fade_finished():
        splash.close()
        # Always start minimized to the tray after splash
        app.main_window.hide()
        
    animation.finished.connect(on_fade_finished)
    
    # Wait 3.5 seconds on desktop before triggering the fade
    # (1.5s random shooting + 1.0s merging + 1.0s hold)
    QTimer.singleShot(3500, animation.start)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
