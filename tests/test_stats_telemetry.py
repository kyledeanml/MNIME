import sys
import os
import pytest
from PyQt6.QtWidgets import QApplication, QPushButton, QLabel, QWidget
from PyQt6.QtCore import Qt

from ui.nerds import StatsBenchmarkWorker, StatsForNerdsDialog


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_stats_vector_benchmark(qapp):
    """Verify that the FAISS vector telemetry test executes properly and generates metrics."""
    worker = StatsBenchmarkWorker(mode="vector")
    
    logs = []
    points = []
    stats_list = []
    
    worker.log_message.connect(lambda msg, tag: logs.append((msg, tag)))
    worker.point_generated.connect(lambda x, y, m: points.append((x, y, m)))
    worker.stats_updated.connect(lambda s: stats_list.append(s))
    
    res = worker._run_vector_benchmark()
    
    assert res.get("mode") == "vector"
    assert res.get("queries") > 0
    assert res.get("vectors") > 0
    assert res.get("avg_latency_ms") > 0
    assert res.get("throughput_avg") > 0
    assert any("FAISS VECTOR RETRIEVAL BENCHMARK COMPLETE" in l[0] for l in logs)
    assert len(points) > 0
    assert len(stats_list) > 0


def test_stats_dialog_moveable_and_non_modal(qapp):
    """Verify that StatsForNerdsDialog is non-modal and has draggable regions."""
    dialog = StatsForNerdsDialog()
    assert dialog.header_widget is not None
    assert dialog.header_widget.cursor().shape() == Qt.CursorShape.SizeAllCursor
    
    # Test interactive filtering
    btn = QPushButton("TestBtn", dialog)
    lbl = QLabel("TestLabel", dialog.header_widget)
    
    assert dialog._is_interactive(btn) is True
    assert dialog._is_interactive(lbl) is False
    assert dialog._is_interactive(dialog.header_widget) is False
    
    # Non-modal test
    dialog.show()
    assert dialog.isModal() is False
    assert dialog.isVisible() is True
    dialog.close()
