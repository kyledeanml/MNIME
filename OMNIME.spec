# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from PyInstaller.utils.hooks import collect_all

datas = [('OMNIME_reimagined_alpha.png', '.'), ('OMN.ico', '.')]
binaries = []
hiddenimports = [
    'fitz',
    'pymupdf',
    'pypdf',
    'PIL',
    'PIL.Image',
    'PIL.ImageDraw',
    'pdf2docx',
    'docx',
    'PyQt6',
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'core',
    'core.app_icon',
    'core.file_item',
    'core.nlp_engine',
    'core.pdf_engine',
    'core.search_engine',
    'core.worker',
    'ui',
    'ui.action_bar',
    'ui.carousel_view',
    'ui.cursor_fx',
    'ui.document_viewer',
    'ui.file_card',
    'ui.file_dialog',
    'ui.icons',
    'ui.image_editor',
    'ui.main_window',
    'ui.merge_particles',
    'ui.minimize_animation',
    'ui.nlp_view',
    'ui.output_view',
    'ui.pdf_editor',
    'ui.reader_dialog',
    'ui.settings_dialog',
    'ui.tabs_bar',
]

for pkg in ['pymupdf', 'pdf2docx', 'pypdf', 'langchain', 'langchain_community', 'sentence_transformers', 'faiss', 'llama_cpp']:
    try:
        pkg_datas, pkg_binaries, pkg_hiddenimports = collect_all(pkg)
        datas += pkg_datas
        binaries += pkg_binaries
        hiddenimports += pkg_hiddenimports
    except Exception:
        pass

a = Analysis(
    ['OMNIME.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'tensorflow', 'nltk', 'IPython', 'spacy'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='OMNIME',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['OMN.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='OMNIME',
)
