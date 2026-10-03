import os
import sys
import shutil
import math
import random
import time

# Ensure PyQt6 path during development (skip if compiled)
if not getattr(sys, 'frozen', False):
    venv_base = os.path.dirname(os.path.dirname(sys.executable))
    plugin_base = os.path.join(venv_base, "Lib", "site-packages", "PyQt6", "Qt6", "plugins")
    os.environ["QT_PLUGIN_PATH"] = plugin_base
    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = os.path.join(plugin_base, "platforms")

from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtGui import (QFont, QPainter, QLinearGradient, QColor,
                         QFontMetrics, QPen, QBrush, QPixmap, QPolygonF, QPainterPath)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QPointF

class InstallWorker(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal()
    
    def run(self):
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
            source_dir = os.path.join(base_path, 'app_files')
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
            source_dir = os.path.join(base_path, 'dist', 'MNIME')
            
        install_dir = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Programs', 'MNIME')
        
        self.progress.emit(2, "Initializing installer UI...")
        time.sleep(1.0)
        
        if os.path.exists(source_dir):
            if os.path.exists(install_dir):
                self.progress.emit(5, "Removing old version...")
                try:
                    shutil.rmtree(install_dir)
                except:
                    pass
            
            os.makedirs(install_dir, exist_ok=True)
            
            all_files = []
            for root, dirs, files in os.walk(source_dir):
                for file in files:
                    all_files.append(os.path.join(root, file))
                    
            total_files = len(all_files)
            if total_files > 0:
                for i, file_path in enumerate(all_files):
                    rel_path = os.path.relpath(file_path, source_dir)
                    dest_path = os.path.join(install_dir, rel_path)
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                    try:
                        shutil.copy2(file_path, dest_path)
                    except:
                        pass
                    
                    if i % max(1, (total_files // 100)) == 0:
                        pct = 5 + int((i / total_files) * 85)
                        self.progress.emit(pct, f"Installing: {os.path.basename(file_path)}")
                        time.sleep(0.01)
            
            # Create icon explicitly if it didn't copy
            if not os.path.exists(os.path.join(install_dir, "MN.ico")):
                try:
                    shutil.copy2("MN.ico", os.path.join(install_dir, "MN.ico"))
                except: pass
        else:
            self.progress.emit(0, "Error: Application build files not found (dist/MNIME). Please build before running installer.")
            time.sleep(2.0)
            self.finished.emit()
            return
                
        self.progress.emit(92, "Creating shortcuts...")
        
        # Shortcut Creation
        try:
            import win32com.client
            shell = win32com.client.Dispatch("WScript.Shell")
            desktop = os.path.join(os.environ['USERPROFILE'], 'Desktop', 'MNIME.lnk')
            start_menu = os.path.join(os.environ['APPDATA'], 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'MNIME.lnk')
            target = os.path.join(install_dir, 'MNIME.exe')
            icon = os.path.join(install_dir, 'MN.ico')
            
            for lnk in [desktop, start_menu]:
                shortcut = shell.CreateShortCut(lnk)
                shortcut.Targetpath = target
                shortcut.WorkingDirectory = install_dir
                shortcut.IconLocation = f"{icon},0"
                shortcut.save()
        except ImportError:
            self.progress.emit(95, "pywin32 not found. Skipping shortcuts...")
            time.sleep(0.5)
        except Exception:
            pass
            
        self.progress.emit(100, "Installation Complete!")
        time.sleep(1.5)
        self.finished.emit()


class LittleFile:
    def __init__(self, start_x, start_y, target_x, target_y):
        self.start_x = start_x
        self.start_y = start_y
        self.target_x = target_x
        self.target_y = target_y
        
        # Control point for arc trajectory
        self.ctrl_x = (start_x + target_x) / 2 + random.uniform(-100, 100)
        self.ctrl_y = (start_y + target_y) / 2 - random.uniform(50, 200)
        
        self.t = 0.0
        self.speed = random.uniform(0.015, 0.03)
        self.rotation = random.uniform(0, 360)
        self.rot_speed = random.uniform(-15, 15)
        self.size = random.uniform(0.7, 1.2)
        
        self.cx = start_x
        self.cy = start_y
        
    def update(self):
        self.t += self.speed
        if self.t > 1.0:
            self.t = 1.0
        u = 1 - self.t
        self.cx = u*u*self.start_x + 2*u*self.t*self.ctrl_x + self.t*self.t*self.target_x
        self.cy = u*u*self.start_y + 2*u*self.t*self.ctrl_y + self.t*self.t*self.target_y
        self.rotation += self.rot_speed


class InstallerUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(650, 450)
        
        self.progress_val = 0
        self.status_text = "Initializing installer..."
        
        self.swirl_angle = 0.0
        self.little_files = []
        
        # The tiny files
        self.tiny_file_pixmap = self.create_file_pixmap(QColor(140, 230, 255), 16)
        
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self.update_anim)
        self.anim_timer.start(16)
        
        self.worker = InstallWorker()
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_finished)
        
        QTimer.singleShot(1000, self.worker.start)

    def create_file_pixmap(self, color, size=48):
        pix = QPixmap(size, size)
        pix.fill(Qt.GlobalColor.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        scale = size / 24.0
        poly = QPolygonF([
            QPointF(4*scale, 2*scale), QPointF(14*scale, 2*scale), 
            QPointF(20*scale, 8*scale), QPointF(20*scale, 22*scale), 
            QPointF(4*scale, 22*scale)
        ])
        
        # File body
        p.setPen(QPen(color, max(1.5, 2 * scale)))
        brush_color = QColor(color.red(), color.green(), color.blue(), 50)
        p.setBrush(brush_color)
        p.drawPolygon(poly)
        
        # Folded corner
        p.drawLine(QPointF(14*scale, 2*scale), QPointF(14*scale, 8*scale))
        p.drawLine(QPointF(14*scale, 8*scale), QPointF(20*scale, 8*scale))
        
        
        p.end()
        return pix

    def on_progress(self, val, text):
        old_val = self.progress_val
        self.progress_val = val
        self.status_text = text
        
        if val > old_val and val < 100:
            # Spawn little files from left off-screen flying to the progress bar
            num_spawn = min((val - old_val) * 2, 10)
            for _ in range(num_spawn):
                sx = -30
                sy = random.uniform(50, self.height() - 50)
                tx = 50 + (val / 100.0) * 550
                ty = 350 # Progress bar Y position
                self.little_files.append(LittleFile(sx, sy, tx, ty))

    def on_finished(self):
        sys.exit(0)

    def update_anim(self):
        self.swirl_angle += 1.25
        for lf in self.little_files:
            lf.update()
        self.little_files = [lf for lf in self.little_files if lf.t < 1.0]
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 1. Main Background
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 20, 20)
        p.fillPath(path, QColor(13, 17, 23, 245))
        p.setPen(QPen(QColor(48, 54, 61), 2))
        p.drawPath(path)
        
        cx, cy = self.width() // 2, self.height() // 2 - 30
        
        # 2. Tasteful MNIME Text
        font = QFont("Segoe UI Black", 48, QFont.Weight.Black)
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 6.0)
        p.setFont(font)
        
        fm = QFontMetrics(font)
        text = "MNIME"
        tr = fm.boundingRect(text)
        x = cx - tr.width() // 2
        y = cy + tr.height() // 2
        
        glow = QColor(0, 210, 255, 30)
        p.setPen(glow)
        for offset in [3, 6]:
            p.drawText(x-offset, y-offset, text)
            p.drawText(x+offset, y+offset, text)
            p.drawText(x-offset, y+offset, text)
            p.drawText(x+offset, y-offset, text)
            
        p.setPen(QColor(0, 0, 0, 150))
        p.drawText(x+4, y+4, text)
        
        grad = QLinearGradient(x, y-tr.height(), x, y)
        grad.setColorAt(0.0, QColor("#ffffff"))
        grad.setColorAt(0.5, QColor("#8b949e"))
        grad.setColorAt(1.0, QColor("#161b22"))
        pen = QPen()
        pen.setBrush(QBrush(grad))
        p.setPen(pen)
        p.drawText(x, y, text)
        
        # 3. Logo Placement (Above Title)
        fx = cx
        fy = cy - 80
        
        from core.app_icon import get_logo_pixmap
        animated_logo = get_logo_pixmap(80, math.radians(self.swirl_angle * 2.0))
        
        p.save()
        p.translate(fx, fy)
        # Gentle bobbing
        p.translate(0, math.sin(math.radians(self.swirl_angle * 3)) * 5)
        p.drawPixmap(-40, -40, 80, 80, animated_logo)
        p.restore()
        
        # 4. Progress Bar Background
        bar_x = 50
        bar_y = 350
        bar_w = 550
        bar_h = 12
        p.setPen(QPen(QColor(48, 54, 61), 1))
        p.setBrush(QColor(1, 4, 9))
        p.drawRoundedRect(bar_x, bar_y, bar_w, bar_h, 6, 6)
        
        # Progress Bar Fill
        fill_w = (self.progress_val / 100.0) * bar_w
        if fill_w > 0:
            fill_grad = QLinearGradient(bar_x, bar_y, bar_x + fill_w, bar_y)
            fill_grad.setColorAt(0, QColor(0, 150, 255))
            fill_grad.setColorAt(1, QColor(0, 255, 200))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(fill_grad))
            p.drawRoundedRect(bar_x, bar_y, int(fill_w), bar_h, 6, 6)
            
            # Draw a bright glowing head at the end of the progress bar
            p.setBrush(QColor(255, 255, 255, 200))
            p.drawEllipse(QPointF(bar_x + fill_w, bar_y + bar_h/2), 6, 6)
            
        # 5. Little Files Piling In
        for lf in self.little_files:
            p.save()
            p.translate(lf.cx, lf.cy)
            p.rotate(lf.rotation)
            p.scale(lf.size, lf.size)
            p.drawPixmap(-8, -8, 16, 16, self.tiny_file_pixmap)
            p.restore()
            
        # 6. Status Text
        p.setFont(QFont("Segoe UI", 10))
        p.setPen(QColor(139, 148, 158))
        p.drawText(bar_x, bar_y - 10, self.status_text)
        p.drawText(bar_x + bar_w - 35, bar_y - 10, f"{self.progress_val}%")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = InstallerUI()
    win.show()
    sys.exit(app.exec())
