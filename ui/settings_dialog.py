from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QFileDialog, QMessageBox,
    QSlider, QComboBox, QSpinBox, QCheckBox, QGroupBox, QFormLayout
)
from PyQt6.QtCore import Qt, QSettings
from core.nlp_engine import NLPEngine

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("NLP Model & Hardware Settings")
        self.setMinimumWidth(750)
        self.settings = QSettings("OmniMesh", "OmniMeshApp")
        
        self.setStyleSheet("""
            QDialog {
                background-color: #11151f;
                color: #f0f6fc;
            }
            QLabel {
                font-size: 13px;
            }
            QLineEdit, QComboBox, QSpinBox {
                background-color: #161b22;
                color: #f0f6fc;
                border: 1px solid #30363d;
                border-radius: 4px;
                padding: 6px;
            }
            QGroupBox {
                border: 1px solid #30363d;
                border-radius: 6px;
                margin-top: 10px;
                font-weight: bold;
                color: #8b949e;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
            }
            QPushButton {
                background-color: #162438;
                color: #00e5ff;
                border: 1px solid #00d2ff;
                border-radius: 6px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0077b6;
                color: #ffffff;
            }
        """)
        
        self._setup_ui()
        self._load_settings()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # --- Model Path Section ---
        model_group = QGroupBox("LLM Model Source")
        model_layout = QVBoxLayout(model_group)
        
        info_label = QLabel(
            "OmniMesh NLP features require a local GGUF model.\n"
            "Download a model (e.g., Qwen3.5-4B-Q4_K_M.gguf) and select it below."
        )
        info_label.setWordWrap(True)
        model_layout.addWidget(info_label)
        
        path_layout = QHBoxLayout()
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("Select model path... (OmniMesh is highly optimized for Qwen3.5-4B-Q4_K_M)")
        
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self._browse)
        
        path_layout.addWidget(self.path_input)
        path_layout.addWidget(browse_btn)
        model_layout.addLayout(path_layout)
        layout.addWidget(model_group)

        # --- Hardware & Performance Section ---
        hw_group = QGroupBox("Performance & Hardware (Requires Model Reload)")
        hw_layout = QFormLayout(hw_group)
        hw_layout.setSpacing(12)

        # GPU Layers
        self.gpu_layers_slider = QSlider(Qt.Orientation.Horizontal)
        self.gpu_layers_slider.setRange(-1, 100)
        self.gpu_layers_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.gpu_layers_slider.setTickInterval(10)
        
        self.gpu_layers_label = QLabel()
        self.gpu_layers_slider.valueChanged.connect(self._on_gpu_layers_changed)
        
        gpu_slider_layout = QHBoxLayout()
        gpu_slider_layout.addWidget(self.gpu_layers_slider)
        gpu_slider_layout.addWidget(self.gpu_layers_label)
        hw_layout.addRow("VRAM Offload (Layers):", gpu_slider_layout)

        # Context Window
        self.ctx_combo = QComboBox()
        self.ctx_combo.addItems(["2048", "4096", "8192", "16384", "32768"])
        hw_layout.addRow("Context Window (Tokens):", self.ctx_combo)

        import subprocess
        
        # GPU Device ID (NVIDIA Auto-Detect)
        self.gpu_id_combo = QComboBox()
        gpu_list = self._detect_nvidia_gpus()
        
        if gpu_list:
            for gpu in gpu_list:
                self.gpu_id_combo.addItem(f"{gpu['index']}: {gpu['name']} ({gpu['vram']} MB)", userData=gpu['index'])
        else:
            self.gpu_id_combo.addItem("0: Default / CPU Only", userData=0)
            
        hw_layout.addRow("GPU Device:", self.gpu_id_combo)

        # Flash Attention
        self.flash_attn_check = QCheckBox("Enable Flash Attention (Accelerates long documents)")
        hw_layout.addRow("", self.flash_attn_check)

        # KV Cache Quantization
        self.kv_quant_check = QCheckBox("Enable VRAM Memory Saver (Quantized KV Cache)")
        hw_layout.addRow("", self.kv_quant_check)

        # Smart Semantic Indexing (From CodeEyes)
        self.smart_index_check = QCheckBox("Enable Smart Semantic Indexing (FAISS Optimization)")
        hw_layout.addRow("", self.smart_index_check)

        layout.addWidget(hw_group)
        
        # --- Buttons ---
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        save_btn = QPushButton("Save & Reload")
        save_btn.clicked.connect(self._save)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def _detect_nvidia_gpus(self):
        """Attempts to run nvidia-smi and parse available GPUs and VRAM."""
        import subprocess
        gpus = []
        try:
            # Output format: index, name, memory.total
            # Example: 0, NVIDIA GeForce RTX 3060, 12288 MiB
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=index,name,memory.total", "--format=csv,noheader"],
                capture_output=True, text=True, check=True, creationflags=subprocess.CREATE_NO_WINDOW
            )
            for line in result.stdout.strip().split('\n'):
                if not line: continue
                parts = [p.strip() for p in line.split(',')]
                if len(parts) >= 3:
                    idx = int(parts[0])
                    name = parts[1]
                    vram_str = parts[2].replace(' MiB', '')
                    gpus.append({'index': idx, 'name': name, 'vram': vram_str})
        except Exception:
            pass # Fallback to empty list
        return gpus

    def _on_gpu_layers_changed(self, val):
        if val == -1:
            self.gpu_layers_label.setText("Max (All)")
        else:
            self.gpu_layers_label.setText(str(val))

    def _load_settings(self):
        self.path_input.setText(self.settings.value("gguf_model_path", ""))
        
        gpu_layers = int(self.settings.value("nlp_gpu_layers", -1))
        self.gpu_layers_slider.setValue(gpu_layers)
        self._on_gpu_layers_changed(gpu_layers)
        
        ctx_window = str(self.settings.value("nlp_ctx_window", "4096"))
        idx = self.ctx_combo.findText(ctx_window)
        if idx >= 0:
            self.ctx_combo.setCurrentIndex(idx)
            
        saved_gpu_id = int(self.settings.value("nlp_gpu_id", 0))
        found_idx = -1
        for i in range(self.gpu_id_combo.count()):
            if self.gpu_id_combo.itemData(i) == saved_gpu_id:
                found_idx = i
                break
        if found_idx >= 0:
            self.gpu_id_combo.setCurrentIndex(found_idx)
        else:
            self.gpu_id_combo.setCurrentIndex(0)
        
        flash_val = str(self.settings.value("nlp_flash_attn", "true")).lower() == "true"
        self.flash_attn_check.setChecked(flash_val)
        
        kv_val = str(self.settings.value("nlp_kv_quant", "false")).lower() == "true"
        self.kv_quant_check.setChecked(kv_val)
        
        smart_val = str(self.settings.value("nlp_smart_indexing", "true")).lower() == "true"
        self.smart_index_check.setChecked(smart_val)

    def _browse(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Select GGUF Model", "", "GGUF Models (*.gguf);;All Files (*.*)"
        )
        if file_name:
            self.path_input.setText(file_name)

    def _save(self):
        path = self.path_input.text().strip()
        if path and not path.endswith(".gguf"):
            QMessageBox.warning(self, "Invalid File", "Please select a .gguf file.")
            return
            
        # Save values
        self.settings.setValue("gguf_model_path", path)
        self.settings.setValue("nlp_gpu_layers", self.gpu_layers_slider.value())
        self.settings.setValue("nlp_ctx_window", self.ctx_combo.currentText())
        
        # safely read userData
        gpu_id_data = self.gpu_id_combo.currentData()
        if gpu_id_data is None:
            gpu_id_data = 0
        self.settings.setValue("nlp_gpu_id", int(gpu_id_data))
        
        self.settings.setValue("nlp_flash_attn", self.flash_attn_check.isChecked())
        self.settings.setValue("nlp_kv_quant", self.kv_quant_check.isChecked())
        self.settings.setValue("nlp_smart_indexing", self.smart_index_check.isChecked())
        
        # Apply to engine
        engine = NLPEngine.get_instance()
        engine.set_model_path(path) # This triggers reload_model()
        
        if engine.is_loaded:
            QMessageBox.information(self, "Success", "Model loaded successfully with new hardware settings!")
            self.accept()
        else:
            QMessageBox.warning(
                self, "Error", 
                f"Failed to load model:\n{engine.error}\n\nSettings saved, but NLP features may not work."
            )
            self.accept()
