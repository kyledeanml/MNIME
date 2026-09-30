"""
Core business logic and processing engines for OmniMesh Desktop.
"""

from .file_item import FileItem, FileStatus
from .pdf_engine import PDFEngine
from .worker import TaskWorker
from .app_icon import get_app_icon, setup_app_user_model_id, get_logo_pixmap, get_resource_path, create_windows_shortcuts

__all__ = ["FileItem", "FileStatus", "PDFEngine", "TaskWorker", "get_app_icon", "setup_app_user_model_id", "get_logo_pixmap", "get_resource_path", "create_windows_shortcuts"]

