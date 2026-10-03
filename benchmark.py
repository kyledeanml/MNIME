"""
MNIME Empirical Benchmark Utility & Stats Console.
Standalone graphical runner for on-device performance telemetry,
interactive benchmarking, and dynamic line chart generation.
"""

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from ui.nerds import StatsForNerdsDialog


def main():
    app = QApplication(sys.argv)
    
    try:
        from core.app_icon import get_app_icon
        app.setWindowIcon(get_app_icon())
    except ImportError:
        pass

    dialog = StatsForNerdsDialog()
    dialog.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
