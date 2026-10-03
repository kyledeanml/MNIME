import pytest
import os
import pymupdf
from PyQt6.QtCore import QThread, QCoreApplication
from PyQt6.QtWidgets import QApplication

from core.file_item import FileItem
from core.search_engine import SearchEngine


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_build_index_in_qthread_with_pdf(tmp_path, qapp):
    """Verify that PDF indexing inside a QThread does not hang with QApplication active."""
    # Create sample PDF
    pdf_path = str(tmp_path / "sample_indexing_test.pdf")
    doc = pymupdf.open()
    page = doc.new_page(width=400, height=300)
    page.insert_text(pymupdf.Point(50, 50), "MNIME local AI indexing test content.")
    doc.save(pdf_path)
    doc.close()

    item = FileItem(pdf_path)
    results = {}

    class TestWorker(QThread):
        def run(self):
            try:
                vstore = SearchEngine.build_index([item])
                results["vstore"] = vstore
            except Exception as e:
                results["error"] = e

    worker = TestWorker()
    worker.start()
    finished = worker.wait(15000)  # Wait up to 15 seconds

    assert finished, "Indexing in QThread hung and timed out"
    assert "error" not in results, f"Indexing failed with error: {results.get('error')}"
    assert results.get("vstore") is not None, "Vectorstore was not created"

    # Verify search
    hits = SearchEngine.search(results["vstore"], "indexing test", k=1)
    assert len(hits) == 1
    assert "MNIME local AI" in hits[0]["content"]
