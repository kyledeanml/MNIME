@echo off
title OmniMesh Builder and Installer
cd /d "%~dp0"

echo ========================================================
echo OmniMesh - Build and Install Script
echo [1/3] Setting up Python environment...
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
) else (
    echo Using existing .venv environment...
)
set "PYTHON_EXE=.venv\Scripts\python.exe"
set "PIP_EXE=.venv\Scripts\pip.exe"
set "PYINSTALLER_EXE=.venv\Scripts\pyinstaller.exe"

echo [2/3] Installing build dependencies and generating App Icon...
"%PYTHON_EXE%" -m pip install --upgrade pip
"%PIP_EXE%" install -r requirements.txt
"%PIP_EXE%" install pyinstaller pillow pymupdf pypdf pdf2docx
"%PYTHON_EXE%" -c "from core.app_icon import ensure_ico_file; ensure_ico_file()"

echo [3/4] Compiling Executable...
:: Build as a single directory application using OmniMesh.spec
"%PYINSTALLER_EXE%" --clean --noconfirm "OmniMesh.spec"
if exist "OMN.ico" copy /Y "OMN.ico" "dist\OmniMesh\" >nul
if exist "OMN.jpg" copy /Y "OMN.jpg" "dist\OmniMesh\" >nul

echo [4/4] Building Standalone Installer...
set ISCC_PATH=
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set "ISCC_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if exist "C:\Program Files\Inno Setup 6\ISCC.exe" set "ISCC_PATH=C:\Program Files\Inno Setup 6\ISCC.exe"
if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" set "ISCC_PATH=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"

if defined ISCC_PATH (
    :: Define signtool path (look in Windows Kits)
    set "SIGNTOOL_PATH="
    for /d %%i in ("C:\Program Files (x86)\Windows Kits\10\bin\*") do (
        if exist "%%i\x64\signtool.exe" set "SIGNTOOL_PATH=%%i\x64\signtool.exe"
    )
    
    if exist "OmniMeshCert.pfx" (
        if defined SIGNTOOL_PATH (
            echo Found OmniMeshCert.pfx and signtool.exe, configuring digital signature...
            "%ISCC_PATH%" /DSignInstaller /S"MySignTool=$q%SIGNTOOL_PATH%$q sign /f $q%~dp0OmniMeshCert.pfx$q /p $qomnimesh123$q /tr http://timestamp.digicert.com /td sha256 /fd sha256 $f" "OmniMesh.iss"
        ) else (
            echo Warning: signtool.exe not found in Windows Kits. Building without signature.
            "%ISCC_PATH%" "OmniMesh.iss"
        )
    ) else (
        echo Note: OmniMeshCert.pfx not found. Building installer without digital signature.
        "%ISCC_PATH%" "OmniMesh.iss"
    )
    echo.
    echo ========================================================
    echo Build complete! Your standalone installer is ready in:
    echo %~dp0installer\OmniMesh_Setup.exe
    echo ========================================================
) else (
    echo.
    echo ========================================================
    echo Build complete! You can find the standalone app in:
    echo %~dp0dist\OmniMesh\
    echo.
    echo NOTE: To generate the standard Windows installer (OmniMesh_Setup.exe),
    echo please install 'Inno Setup 6' and run this script again.
    echo ========================================================
)
