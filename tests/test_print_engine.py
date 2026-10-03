import pytest
import pymupdf
from PyQt6.QtCore import QSizeF
from PyQt6.QtPrintSupport import QPrinter
from core.print_engine import _fit

def test_fit_maths():
    # Fit landscape image into portrait page
    # Image: 2000x1000. Page: 1000x2000
    src = QSizeF(2000, 1000)
    dst = QSizeF(1000, 2000)
    rect = _fit(src.width(), src.height(), int(dst.width()), int(dst.height()), allow_upscale=False)
    # Scale factor should be 1000/2000 = 0.5
    # Width becomes 1000, Height becomes 500
    assert abs(rect[0] - 1000) < 1.0
    assert abs(rect[1] - 500) < 1.0

def test_fit_maths_portrait_into_landscape():
    # Image: 1000x2000. Page: 2000x1000
    src = QSizeF(1000, 2000)
    dst = QSizeF(2000, 1000)
    rect = _fit(src.width(), src.height(), int(dst.width()), int(dst.height()), allow_upscale=False)
    # Scale factor = 1000/2000 = 0.5
    # Width becomes 500, Height becomes 1000
    assert abs(rect[0] - 500) < 1.0
    assert abs(rect[1] - 1000) < 1.0

