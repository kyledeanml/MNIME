# OmniMesh

A modern, ultra-fast, and private desktop document suite engineered with Python and PyQt6. Runs 100% locally and offline on your machine with zero external uploads.

---

## 🌟 Key Features

1. **Merge Files**: Select up to 5000 PDF and image files, drag and drop to reorder, and merge them sequentially into a single PDF document.
2. **JPG → PDF**: Convert image files (`.jpg`, `.jpeg`, `.png`, `.webp`, `.bmp`) into a crisp, unified PDF document.
3. **PDF → Images**: Extract all pages from a PDF document into high-resolution JPG images.
4. **Compress PDF**: Optimize and reduce PDF file size by compressing content streams and duplicate objects.
5. **PDF → DOCX**: Convert PDF pages and text layout into editable Microsoft Word (`.docx`) documents.
6. **Smart Bookmarks**: Intelligently analyze PDF typography, font sizes, and chapter headings to automatically generate a full Table of Contents.

### 🎨 Visual & Aesthetic Highlights
- **Free-Floating Dark Metallic Design**: Seamless obsidian and brushed gunmetal interface without boxy enclosing containers.
- **Whispy Metallic Branding & Neon Blue Glow**: Custom high-resolution metallic logo with electric cyan and dark neon blue highlights.
- **Clean Minimalist Dropzone**: Modern, distraction-free file drop canvas with real-time drag-and-drop feedback.
- **Interactive File Carousel**: Horizontal card slider with smooth scroll arrows and status badges.
- **Advanced File Explorer Dialog**: A custom, fully integrated PyQt6 file manager that replaces the generic OS popup, featuring a directory tree and clean list view matching the app's dark metallic theme.
- **Cinematic Transitions & VFX**: Features an interactive, physics-based particle simulation with an infinitely looping high-speed file vortex during background processing, capped off with a screen-flash transition.
- **Drag-and-Drop Reordering**: Rearrange file cards by dragging them left or right to change the processing order.
- **Card Thumbnails & Previews**: Real-time page rendering, file names, status overlays (`Waiting...`, `Processing...`, `Ready`), and remove buttons (`X`).
### ⚡ High-Performance Engine & Optimizations
- **C-Accelerated PyMuPDF Core**: Multi-file merging, image extraction, and compression run through native C-level PyMuPDF routines (up to 50x faster than pure-Python libraries with negligible RAM footprint).
- **O(1) Carousel Layout Operations**: Drag-and-drop card reordering and card removal execute via surgical layout index shifts rather than tearing down and rebuilding hundreds of widgets.
- **In-Memory Pixmap & Icon Caching**: Thumbnails and vector SVG icons are rasterized and pre-scaled once, eliminating CPU resampling during continuous scroll and hover events.
- **Lightweight Hardware-Accelerated Cards**: Replaced heavy drop shadow bitmap textures with pure stylesheet hardware borders, keeping UI scrolling silky smooth even with 5000 files loaded.
- **Non-blocking Background Processing**: Smooth 60 FPS UI using `QThread` workers with real-time progress bars.

---

## 🚀 Running the Application

### 1. Launch via 1-Click Runner:
Double-click `run.bat` at any time.

### 2. Pin to Windows Quickbar / Taskbar:
Run `create_shortcut.bat` to create an `OmniMesh` shortcut on your Desktop and in the project folder, then right-click and choose **Pin to taskbar**.

### 3. Launch via Command Line:
```bash
# Run with virtual environment
.\.venv\Scripts\python.exe main.py
```

---

### 4. Create a stand-alone installer
Run the build_app.bat with Inno Setup 6 installed

## 📁 Project Architecture

```
v:/New folder/
├── core/                  # Core processing engine & system integration
│   ├── __init__.py
│   ├── app_icon.py        # Windows AppUserModelID, ICO generator, & shortcuts
│   ├── file_item.py       # Data model, metadata reader & thumbnail generator
│   ├── pdf_engine.py      # PDF merge, convert, compress, & DOCX export logic
│   └── worker.py          # Asynchronous QThread background worker
├── ui/                    # Desktop GUI components (PyQt6)
│   ├── __init__.py
│   ├── main_window.py     # Free-floating dark metallic window coordinator
│   ├── file_dialog.py     # Custom native-feeling dark-mode file explorer
│   ├── header_view.py     # Top branding with whispy metallic logo and neon accents
│   ├── tabs_bar.py        # Mode switcher (Merge, Images->PDF, PDF->Images, Compress, DOCX)
│   ├── controls_bar.py    # Primary action buttons ("UPLOAD FILES", "CLEAR")
│   ├── carousel_view.py   # Reorderable horizontal file card carousel & clean dropzone
│   ├── file_card.py       # Individual file cards with status, progress, & drag-and-drop
│   ├── action_bar.py      # Execution button ("MERGE FILES") with badge count and progress
│   └── icons.py           # Resolution-independent vector SVG icons
├── OmniMeshLogo.jpg       # High-resolution whispy metallic logo
├── OmniMeshLogo.ico       # Multi-resolution native Windows icon
├── main.py                # Main application entry point
├── create_shortcut.bat    # 1-click Quickbar / Desktop shortcut generator
├── run.bat                # 1-click Windows runner
├── setup.bat              # 1-click Windows installer
├── pyproject.toml         # Build & package configuration
├── requirements.txt       # Python dependencies list
└── README.md              # Project documentation
```
