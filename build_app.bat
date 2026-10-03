@echo off
title MNIME Builder and Installer
cd /d "%~dp0"

echo ========================================================
echo MNIME - Build and Install Script
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

echo [2/3] Installing build dependencies, generating App Icon and Changelog PDF...
"%PYTHON_EXE%" -m pip install --upgrade pip
"%PIP_EXE%" install -r requirements.txt
"%PIP_EXE%" install pyinstaller pillow pymupdf pypdf pdf2docx reportlab
"%PYTHON_EXE%" -c "from core.app_icon import ensure_ico_file; ensure_ico_file()"
if exist "scripts\generate_changelog_pdf.py" (
    echo Generating interactive Change Log PDF from CHANGE_LOG.txt...
    "%PYTHON_EXE%" scripts\generate_changelog_pdf.py
)

echo [3/4] Compiling Executable...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
:: Build as a single directory application using MNIME.spec
"%PYINSTALLER_EXE%" --clean --noconfirm "MNIME.spec"
if %errorlevel% neq 0 (
    echo.
    echo ERROR: PyInstaller failed to build the executable!
    exit /b %errorlevel%
)
if exist "MN.ico" copy /Y "MN.ico" "dist\MNIME\" >nul
if exist "MNIME_reimagined_alpha.png" copy /Y "MNIME_reimagined_alpha.png" "dist\MNIME\" >nul
if exist "MNIME_Change_Log.pdf" copy /Y "MNIME_Change_Log.pdf" "dist\MNIME\" >nul
if exist "CHANGE_LOG.txt" copy /Y "CHANGE_LOG.txt" "dist\MNIME\" >nul

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
        
        if exist "MNIMECert.pfx" (
            if not defined MNIME_CERT_PASSWORD (
                echo Warning: MNIME_CERT_PASSWORD environment variable not set. Building without signature.
                "%ISCC_PATH%" "MNIME.iss"
            ) else if defined SIGNTOOL_PATH (
                echo Found MNIMECert.pfx and signtool.exe, configuring digital signature...
                "%ISCC_PATH%" /DSignInstaller /S"MySignTool=$q%SIGNTOOL_PATH%$q sign /f $q%~dp0MNIMECert.pfx$q /p $q%MNIME_CERT_PASSWORD%$q /tr http://timestamp.digicert.com /td sha256 /fd sha256 $f" "MNIME.iss"
            ) else (
                echo Warning: signtool.exe not found in Windows Kits. Building without signature.
                "%ISCC_PATH%" "MNIME.iss"
            )
        ) else (
            echo Note: MNIMECert.pfx not found. Building installer without digital signature.
            "%ISCC_PATH%" "MNIME.iss"
        )
        echo.
        echo ========================================================
        echo Build complete! Your Inno Setup installer is ready in:
        echo %~dp0installer\MNIME_Setup.exe
        echo ========================================================
    ) else (
        echo Skipping Inno Setup...
    )

    echo.
    echo [5/5] Compiling Custom Animated Installer...
    if exist "custom_installer.py" (
        "%PYINSTALLER_EXE%" --clean --noconfirm "MNIME_installer.spec"
        if exist "dist\MNIME_installer.exe" (
            if not exist "installer" mkdir "installer"
            move /Y "dist\MNIME_installer.exe" "installer\" >nul
            echo.
            echo ========================================================
            echo Build complete! Your modern animated installer is ready at:
            echo %~dp0installer\MNIME_installer.exe
            echo ========================================================
        )
    )
