"""
Background worker thread using PyQt6 QThread for asynchronous processing.
Keeps the desktop GUI completely smooth and responsive during heavy conversions.
"""

from typing import Callable, Any
from PyQt6.QtCore import QThread, pyqtSignal

from core.logging_setup import get_logger

log = get_logger("worker")


class TaskCancelled(BaseException):
    """Raised inside the worker when cancel() was requested.

    Derives from BaseException on purpose so that the broad ``except Exception``
    blocks inside the engines cannot swallow a cancellation.
    """


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
                if self._is_cancelled:
                    raise TaskCancelled()
                self.progress.emit(pct, msg)

            self.kwargs["progress_callback"] = _progress_cb
            result = self.target_function(*self.args, **self.kwargs)
            if not self._is_cancelled:
                self.finished.emit(result)
        except TaskCancelled:
            log.info("Task cancelled: %s", getattr(self.target_function, "__name__", self.target_function))
        except Exception as e:
            log.exception("Task failed: %s", getattr(self.target_function, "__name__", self.target_function))
            if not self._is_cancelled:
                self.error.emit(str(e))

    def cancel(self):
        self._is_cancelled = True
