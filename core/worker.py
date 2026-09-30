"""
Background worker thread using PyQt6 QThread for asynchronous processing.
Keeps the desktop GUI completely smooth and responsive during heavy conversions.
"""

from typing import Callable, Any
from PyQt6.QtCore import QThread, pyqtSignal


class TaskWorker(QThread):
    """Generic worker thread that executes a callable in the background."""

    progress = pyqtSignal(int, str)       # (percentage, status_text)
    finished = pyqtSignal(object)         # result object (path, list, etc.)
    error = pyqtSignal(str)              # error message

    def __init__(self, target_function: Callable, *args, **kwargs):
        super().__init__()
        self.target_function = target_function
        self.args = args
        self.kwargs = kwargs
        self._is_cancelled = False

    def run(self):
        try:
            # Inject our progress callback into kwargs if expected
            def _progress_cb(pct: int, msg: str):
                if not self._is_cancelled:
                    self.progress.emit(pct, msg)

            self.kwargs["progress_callback"] = _progress_cb
            result = self.target_function(*self.args, **self.kwargs)
            if not self._is_cancelled:
                self.finished.emit(result)
        except Exception as e:
            if not self._is_cancelled:
                self.error.emit(str(e))

    def cancel(self):
        self._is_cancelled = True
