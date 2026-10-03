import sys
import time
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QPushButton, QTextEdit, QLabel)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

class BenchmarkThread(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(dict)
    
    def run(self):
        try:
            from llama_cpp import Llama
        except ImportError:
            self.progress.emit("Error: llama-cpp-python not installed.")
            return

        model_path = os.path.join("models", "MNIME-Core-1.5B-Q4_K_M.gguf")
        if not os.path.exists(model_path):
            self.progress.emit(f"Error: Model not found at {model_path}.")
            return

        self.progress.emit("Loading model (offloading to GPU)...\n")
        start_load = time.time()
        
        try:
            llm = Llama(
                model_path=model_path,
                n_gpu_layers=-1,
                n_ctx=2048,
                verbose=False
            )
        except Exception as e:
            self.progress.emit(f"Failed to load model: {e}")
            return
            
        load_time = time.time() - start_load
        self.progress.emit(f"Model loaded in {load_time:.2f} seconds.\n\n")
        
        prompt = "Q: Summarize the key benefits of local document processing.\nA:"
        self.progress.emit(f"Prompt: {prompt}\nGenerating response...\n\n")
        
        start_gen = time.time()
        first_token_time = None
        token_count = 0
        
        stream = llm(
            prompt,
            max_tokens=150,
            stop=["Q:", "\n"],
            echo=False,
            stream=True
        )
        
        for output in stream:
            if first_token_time is None:
                first_token_time = time.time() - start_gen
                self.progress.emit(f"[First token latency: {first_token_time:.2f}s] ")
            token = output['choices'][0]['text']
            self.progress.emit(token)
            token_count += 1
            
        end_gen = time.time()
        total_gen_time = end_gen - start_gen
        
        throughput = 0
        if token_count > 0:
            throughput = token_count / total_gen_time
            
        self.progress.emit(f"\n\n--- Benchmark Complete ---\n")
        self.progress.emit(f"Total tokens generated: {token_count}\n")
        self.progress.emit(f"Total generation time: {total_gen_time:.2f} seconds\n")
        self.progress.emit(f"Sustained throughput: {throughput:.2f} tokens/second\n")
        
        self.finished.emit({
            'load_time': load_time,
            'first_token': first_token_time,
            'throughput': throughput
        })


class BenchmarkUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MNIME Empirical Benchmark Utility")
        self.setFixedSize(700, 550)
        
        # UI Styling (MNIME Theme)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0d1117;
            }
            QLabel {
                color: #c9d1d9;
                font-family: "Segoe UI";
                font-size: 14px;
            }
            QTextEdit {
                background-color: #161b22;
                color: #58a6ff;
                border: 1px solid #30363d;
                border-radius: 8px;
                padding: 12px;
                font-family: "Consolas", monospace;
                font-size: 14px;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #005c8a, stop:1 #0096c7);
                color: white;
                border: 1px solid #00d2ff;
                border-radius: 8px;
                padding: 10px 20px;
                font-family: "Segoe UI";
                font-size: 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0077b6, stop:1 #00b4d8);
                border: 1px solid #38bdf8;
            }
            QPushButton:disabled {
                background: #30363d;
                color: #8b949e;
                border: 1px solid #484f58;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)
        
        title = QLabel("<b>MNIME-Core NLP Empirical Benchmark</b>")
        title.setStyleSheet("color: white; font-size: 20px;")
        layout.addWidget(title)
        
        desc = QLabel("This utility empirically validates the theoretical projections stated in the MNIME research paper. It measures real-world on-device inference latency and throughput for the bundled MNIME-Core 1.5B model.")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        layout.addWidget(self.log_output)
        
        self.run_btn = QPushButton("Run Empirical Benchmark")
        self.run_btn.clicked.connect(self.start_benchmark)
        layout.addWidget(self.run_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        
    def start_benchmark(self):
        self.run_btn.setDisabled(True)
        self.run_btn.setText("Benchmarking (Please Wait)...")
        self.log_output.clear()
        
        self.thread = BenchmarkThread()
        self.thread.progress.connect(self.update_log)
        self.thread.finished.connect(self.benchmark_complete)
        self.thread.start()
        
    def update_log(self, text):
        cursor = self.log_output.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertText(text)
        self.log_output.setTextCursor(cursor)
        self.log_output.ensureCursorVisible()
        
    def benchmark_complete(self, results):
        self.run_btn.setDisabled(False)
        self.run_btn.setText("Run Empirical Benchmark")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    try:
        from core.app_icon import get_app_icon
        app.setWindowIcon(get_app_icon())
    except ImportError:
        pass
        
    window = BenchmarkUI()
    window.show()
    sys.exit(app.exec())
