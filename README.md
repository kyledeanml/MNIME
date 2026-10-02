<p align="center">
  <img src="MNIME_banner.gif" alt="MNIME Banner" width="350">
</p>

## MNIME v1.0

A modern, ultra-fast, and private desktop document suite engineered with Python and PyQt6. Runs 100% locally and offline on your machine with zero external uploads.

---

## Key Features

1. **Merge Files**: Select up to 5000 PDF and image files, drag and drop to reorder, and merge them sequentially into a single PDF document.
2. **Edit Suite (Images & PDFs)**: Visually crop and rotate images and all pages within PDF documents seamlessly within the app.
3. **JPG → PDF**: Convert image files (`.jpg`, `.jpeg`, `.png`, `.webp`, `.bmp`) into a crisp, unified PDF document.
4. **PDF → Images**: Extract all pages from a PDF document into high-resolution JPG images.
5. **Compress PDF**: Optimize and reduce PDF file size by compressing content streams and duplicate objects.
6. **PDF → DOCX**: Convert PDF pages and text layout into editable .docx documents.
7. **Semantic Bookmarks**: Intelligently analyze PDF typography and use the local NLP engine to automatically generate verbose, context-aware chapter summaries.
8. **Local NLP Engine & Semantic Search (RAG)**: Query across all open PDFs locally with your own offline GGUF language model.
9. **Smart Document Cross-Referencing**: Highlight sections in a PDF to automatically synthesize an NLP comparative brief against other documents.
10. **Expanded Translucent Pop-out Chat**: Double-click the NLP console to spawn a magnetic, translucent floating chat window perfectly synced with the main app.

### Visual & Aesthetic Highlights
- **Free-Floating Dark Metallic Design**: Seamless obsidian and brushed gunmetal interface without boxy enclosing containers.
- **Whispy Metallic Branding**: Custom procedurally generated metallic silver and chrome logo, featuring a mathematically precise 5D Penteract projection with true depth-sorting.
- **Clean Minimalist Dropzone**: Modern, distraction-free file drop canvas with real-time drag-and-drop feedback.
- **Interactive File Carousel**: Horizontal card slider with smooth scroll arrows and status badges.
- **Advanced File Explorer Dialog**: A custom, fully integrated PyQt6 file manager that replaces the generic OS popup, featuring a directory tree and clean list view matching the app's dark metallic theme.
- **Cinematic Transitions & VFX**: Features an interactive, physics-based particle simulation with an infinitely looping high-speed file vortex during background processing, capped off with a screen-flash transition. Plus, a playful neon green file orbiting independently in 3D around the 5D core.
- **Drag-and-Drop Reordering**: Rearrange file cards by dragging them left or right to change the processing order.
- **Card Thumbnails & Previews**: Real-time page rendering, file names, status overlays (`Waiting...`, `Processing...`, `Ready`), and remove buttons (`X`).
### High-Performance Engine & Optimizations
- **C-Accelerated PyMuPDF Core**: Multi-file merging, image extraction, and compression run through native C-level PyMuPDF routines (up to 50x faster than pure-Python libraries with negligible RAM footprint).
- **O(1) Carousel Layout Operations**: Drag-and-drop card reordering and card removal execute via surgical layout index shifts rather than tearing down and rebuilding hundreds of widgets.
- **Dynamic AI Memory Management**: The GGUF model and FAISS vector index are completely cleared from memory the moment NLP is toggled off or the app closes, preventing background memory hoarding.
- **Manual NLP Control**: NLP models no longer force-load on startup. They wait idly until you explicitly click the "Reload NLP" button, keeping startup times instant.
- **In-Memory Pixmap & Icon Caching**: Thumbnails and vector SVG icons are rasterized and pre-scaled once, eliminating CPU resampling during continuous scroll and hover events.
- **Lightweight Hardware-Accelerated Cards**: Replaced heavy drop shadow bitmap textures with pure stylesheet hardware borders, keeping UI scrolling silky smooth even with 5000 files loaded.
- **Non-blocking Background Processing**: Smooth 60 FPS UI using `QThread` workers with real-time progress bars.

### AI & NLP Hardware Tuning
MNIME puts you in complete control of your AI hardware acceleration via the Settings gear:
- **LLM Model Source**: Manually point MNIME to any local `.gguf` model file on your drive (e.g., Qwen3.5-4B-Q4_K_M.gguf) to act as the core engine.
- **VRAM Offload (GPU Layers)**: Use the slider to explicitly allocate how much of the model runs on your graphics card. Set it to `Max (All)` for blazing-fast generation on high-end GPUs, `0` for pure CPU processing, or somewhere in the middle to prevent "Out of Memory" crashes on smaller GPUs by splitting the workload.
- **Context Window**: Tune the maximum token limit (e.g., 2048 to 32768) depending on how large your PDFs are and how much VRAM you have available.
- **GPU Device Selection**: MNIME auto-detects NVIDIA graphics cards. If you have multiple GPUs, you can explicitly select which one powers the local AI engine.
- **Flash Attention**: Toggle this on to massively accelerate the processing of long documents. It optimizes memory reads and scales much better when you crank up the Context Window.
- **VRAM Memory Saver (KV Quantization)**: If you are running out of VRAM, toggle this on to compress the model's short-term memory (KV cache) to 8-bit. This allows you to run much larger context windows on GPUs with limited memory without sacrificing noticeable accuracy.
- **Lock Model in RAM (mlock)**: For machines with fast, abundant system RAM. This prevents the operating system from paging the AI model to your hard drive, explicitly reserving space in RAM for zero-latency memory reads.

---

## Setup & Installation

### 1. Initial Setup (Required)
Run `setup.bat` to automatically create a Python virtual environment and install all required dependencies from `requirements.txt`.

---

## Running the Application

### 1. Launch via 1-Click Runner:
Double-click `run.bat` at any time.

### 2. Pin to Windows Quickbar / Taskbar:
Run `create_shortcut.bat` to create an `MNIME` shortcut on your Desktop and in the project folder, then right-click and choose **Pin to taskbar**.

### 3. Launch via Command Line:
```bash
# Run with virtual environment
.\.venv\Scripts\python.exe MNIME.py
```

---

## Building the Application

### 1. Create a Stand-Alone Installer:
Run `build_app.bat` with Inno Setup 6 installed to compile the application and generate a Windows installer.

### 2. Local Installation:
After building, you can run `install_MNIME.bat` to install the application locally to your system and create Start Menu shortcuts.

---

## Changelog

### MNIME — UI & UX Complete Overhaul
- **Added**: Procedurally generated 5D Penteract branding logo with true mathematical 3D depth-sorting and an independent orbiting neon file.
- **Added**: Advanced High-Resolution 4.0x Retina rendering pipeline for the PDF Reader and Edit UIs, producing razor-sharp vector text.
- **Added**: Fluid `Ctrl+Scroll` mouse wheel zoom capabilities across all document viewer and editor viewports.
- **Improved**: The Reader UI has been completely decoupled from the main window, featuring its own independent resizable frameless dark metallic window, automatic document fitting with margin padding, native smooth diagonal resizing, and integrated file-explorer connectivity.
- **Improved**: The Image and PDF Edit UIs have been fully upgraded to the MNIME translucent dark metallic theme, matching the rest of the application's premium aesthetic.

### Version 2.1 — Compatibility & Stability
- **Fixed**: Model loading crash on Python 3.13+ caused by a `longdouble` overflow in NumPy 1.x `getlimits.py` (`OverflowError: cannot convert longdouble infinity to integer` / `arange: cannot compute length`).
- **Updated**: NumPy dependency bumped from `<2.0.0` → `>=2.0.0` (now ships with NumPy 2.5.x). NumPy 2.x resolves the broken `_register_known_types` initialization on Windows with Python 3.13+.
- **Updated**: `pyproject.toml` now correctly lists `numpy>=2.0.0` and `llama-cpp-python>=0.2.75` as explicit dependencies.
- **Updated**: Installer output renamed to `MNIME_Setup.exe` for clarity.

### Version 2.0 — Initial Public Release
- Full feature set: Merge, Edit, JPG↔PDF, Compress, DOCX export, Semantic Bookmarks, NLP/RAG chat, Cross-Reference engine.
- Free-floating dark metallic PyQt6 UI with physics particle transitions.
- Local offline GGUF model integration via `llama-cpp-python`.

---

## 📁 Project Architecture

```
MNIME/
├── core/                  # Core processing engine & system integration
│   ├── __init__.py
│   ├── app_icon.py        # Windows AppUserModelID, ICO generator, & shortcuts
│   ├── file_item.py       # Data model, metadata reader & thumbnail generator
│   ├── nlp_engine.py      # Local LLM integration for GGUF models
│   ├── pdf_engine.py      # PDF merge, convert, compress, & DOCX export logic
│   ├── search_engine.py   # Advanced file and document search engine
│   └── worker.py          # Asynchronous QThread background worker
├── ui/                    # Desktop GUI components (PyQt6)
│   ├── __init__.py
│   ├── action_bar.py      # Primary execution button and actions
│   ├── carousel_view.py   # Reorderable horizontal file card carousel & clean dropzone
│   ├── cursor_fx.py       # Custom cursor effects
│   ├── document_viewer.py # Document visualizer for REFERENCE tasks
│   ├── file_card.py       # Individual file cards with status, progress, & drag-and-drop
│   ├── file_dialog.py     # Custom native-feeling dark-mode file explorer
│   ├── icons.py           # Resolution-independent vector SVG icons
│   ├── image_editor.py    # Image editor UI
│   ├── main_window.py     # Free-floating dark metallic window coordinator
│   ├── merge_particles.py # Physics-based particle simulation for transitions
│   ├── minimize_animation.py # Custom minimize animations
│   ├── nlp_view.py        # NLP/RAG interface
│   ├── output_view.py     # Log or output view component
│   ├── pdf_editor.py      # PDF editor UI
│   ├── reader_dialog.py   # Independent frameless document reader UI
│   ├── settings_dialog.py # Model configuration UI
│   └── tabs_bar.py        # Mode switcher (Merge, Images->PDF, PDF->Images, Compress, Bookmark, DOCX)
├── MNIME_reimagined_alpha.png# High-resolution perfectly transparent neon logo
├── MN.ico                # Multi-resolution native Windows icon
├── MNIME.py              # Main application entry point
├── create_shortcut.bat    # 1-click Quickbar / Desktop shortcut generator
├── run.bat                # 1-click Windows runner
├── setup.bat              # 1-click Python setup / VENV
├── build_app.bat          # App packaging script
├── install_MNIME.bat   # 1-click Windows installer
├── MNIME.iss           # Inno Setup compiler script
├── pyproject.toml         # Build & package configuration
├── requirements.txt       # Python dependencies list
├── LICENSE                # Open source license
└── README.md              # Project documentation
```

---

## Help & User Guide

Welcome to **MNIME**, your next-generation, private, high-performance offline document suite. Designed with a premium dark-metallic and neon-blue aesthetic, MNIME provides blazing-fast document processing entirely offline, utilizing hardware acceleration and optimized local models.

### Core Capabilities

MNIME provides a wide array of document processing tools, all accessible from the top **Tabs Bar**. As you hover over the tabs, stylized neon text will guide you.

- **Combine PDF**: Merge multiple PDF documents into a single file.
- **JPG to PDF**: Convert image files into a high-quality PDF.
- **TXT to PDF**: Rapidly convert raw text files into searchable, native vector PDFs using a high-speed rendering engine.
- **PDF to JPG**: Export pages of a PDF into high-resolution JPG images.
- **Split PDF**: Separate a multi-page PDF into individual files. Features NLP powered Smart Naming that reads page content to automatically generate unique, highly relevant filenames.
- **Compress PDF**: Reduce the file size of heavy PDF documents.
- **PDF to DOCX**: Convert PDFs into editable Word documents.
- **Bookmark**: Add structured bookmarks to your PDF using either fast native heuristics or NLP powered semantic chapter summaries.

### NLP & Reference Engine

MNIME is deeply integrated with local Natural Language Processing (NLP) to help you understand your documents better, entirely offline.

- **NLP**: Engage with your documents using a conversational interface. **Optimized specifically for the `Qwen3.5-4B-Q4_K_M.gguf` model**, ensuring fast inference on NVIDIA GPUs.
- **Reference**: Generate synthesized briefs and cross-reference information across multiple uploaded documents.

> **Note**: To use the NLP and Reference features, you must first configure the correct model path in the **Settings** menu.

### Interface Guide

The MNIME interface is designed to be sleek, intuitive, and highly responsive.

#### 1. The Drop Zone (Right Side)
Permanently docked on the right side of the screen is the **MNIME Drop Zone**.
- **Drag and Drop**: Simply drag your files over the MNIME logo to queue them for processing.
- **Add Files Button**: Click the neon-outlined `ADD FILES` button directly underneath the logo to open a file browser.

#### 2. Gallery Carousel (Left Side)
Once files are added, they appear as interactive cards in the **Gallery Carousel** on the left.
- **Scroll & Reorder**: Scroll horizontally to view all queued files. You can click and drag cards to reorder them before merging.
- **Clear All**: In the bottom corner of the gallery, you will find a custom neon-red **"X"** icon. Click this to instantly clear your entire file queue.

#### 3. Action Bar & Global Toggles
The bottom of the screen houses the **Action Bar**, which is laser-focused on execution.
- **Primary Action Button**: Depending on your selected mode (e.g., `MERGE FILES`), this button will initiate the high-speed processing engine.
- **Progress Indicator**: A sleek progress bar will appear to keep you updated on the task's status.
- **Global NLP Toggle**: Located in the top Tabs Bar, the **"NLP Active"** checkbox acts as a master killswitch. Turn it off to instantly disable all NLP features and run the app in ultra-lightweight mode.

#### 4. Settings
Click the **Gear Icon** (located next to the NLP tab) to open the Hardware & Model Settings.
- Configure your local model paths.
- Adjust thread counts and GPU offloading parameters (optimized for NVIDIA hardware) to maximize processing speed.

#### 5. Document Reader & Editor
MNIME includes a built-in high-resolution **Document Reader** and **Edit UI**.
- **High-Res Rendering**: Documents and images are rendered internally at 4.0x Retina pixel density for ultra-sharp, anti-aliased visual clarity.
- **Fluid Zooming**: Use `Ctrl + Mouse Scroll` to smoothly zoom in and out of documents in both the Reader and the Edit viewports.
- **Independent Windows**: The Reader and Editor run as fully independent, resizable, frameless dark metallic windows that seamlessly synchronize with your main MNIME file queue.

### Error Handling & Validation
MNIME is built with robust safety nets. If you attempt to run a tool with the wrong file type (e.g., trying to run `TXT to PDF` on an image), or try to execute a task with an empty queue, the application will intelligently intercept the action and provide a helpful prompt without crashing.


_MNIME_ - '26kb
