@echo off
title OMNIME Version 99 Builder and Installer
cd /d "%~dp0"

echo ========================================================
echo OMNIME - Build and Install Script
echo Building... All output is being logged to build_log.txt
echo ========================================================
call :main > build_log.txt 2>&1
echo Build finished! Please provide the build_log.txt file.
pause
exit /b

:main
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
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
:: Build as a single directory application using OMNIME.spec
"%PYINSTALLER_EXE%" --clean --noconfirm "OMNIME.spec"
if %errorlevel% neq 0 (
    echo.
    echo ERROR: PyInstaller failed to build the executable!
    exit /b %errorlevel%
)
if exist "OMN.ico" copy /Y "OMN.ico" "dist\OMNIME\" >nul
if exist "OMNIME_reimagined_alpha.png" copy /Y "OMNIME_reimagined_alpha.png" "dist\OMNIME\" >nul

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
    
    if exist "OMNIMECert.pfx" (
        if defined SIGNTOOL_PATH (
            echo Found OMNIMECert.pfx and signtool.exe, configuring digital signature...
            "%ISCC_PATH%" /DSignInstaller /S"MySignTool=$q%SIGNTOOL_PATH%$q sign /f $q%~dp0OMNIMECert.pfx$q /p $qomnime123$q /tr http://timestamp.digicert.com /td sha256 /fd sha256 $f" "OMNIME.iss"
        ) else (
            echo Warning: signtool.exe not found in Windows Kits. Building without signature.
            "%ISCC_PATH%" "OMNIME.iss"
        )
    ) else (
        echo Note: OMNIMECert.pfx not found. Building installer without digital signature.
        "%ISCC_PATH%" "OMNIME.iss"
    )
    echo.
    echo ========================================================
    echo Build complete! Your standalone installer is ready in:
    echo %~dp0installer\OMNIME_Setup_v99.exe
    echo ========================================================
) else (
    echo.
    echo ========================================================
    echo Build complete! You can find the standalone app in:
    echo %~dp0dist\OMNIME\
    echo.
    echo NOTE: To generate the standard Windows installer (OMNIME_Setup.exe),
    echo please install 'Inno Setup 6' and run this script again.
    echo ========================================================
)
