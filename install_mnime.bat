@echo off
title Install MNIME
cd /d "%~dp0"

echo ========================================================
echo Installing MNIME Application
echo ========================================================
echo.

:: -------------------------------------------------------
:: Stale-build check: compare dist exe timestamp against
:: the most recently modified source file in core\ and ui\
:: If source is newer than the exe, force a rebuild first.
:: -------------------------------------------------------
set "EXE=dist\MNIME\MNIME.exe"
set "NEED_BUILD=0"

if not exist "%EXE%" (
    echo No compiled application found. Will build first.
    set "NEED_BUILD=1"
    goto :maybe_build
)

:: Use PowerShell to compare timestamps
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$exe = Get-Item '%EXE%'; " ^
    "$src = Get-ChildItem -Recurse -Include *.py 'core','ui' | Sort-Object LastWriteTime -Descending | Select-Object -First 1; " ^
    "if ($src -and $src.LastWriteTime -gt $exe.LastWriteTime) { exit 1 } else { exit 0 }"

if %errorlevel% equ 1 (
    echo Source files are newer than the compiled exe. Rebuilding...
    set "NEED_BUILD=1"
)

:maybe_build
if "%NEED_BUILD%"=="1" (
    echo.
    echo ========================================================
    echo Running build_app.bat to compile latest changes...
    echo ========================================================
    call build_app.bat
    if %errorlevel% neq 0 (
        echo.
        echo ERROR: Build failed. Installation aborted.
        pause
        exit /b %errorlevel%
    )
)

if not exist "%EXE%" (
    echo ERROR: Could not find compiled application after build!
    pause
    exit /b 1
)

set "INSTALL_DIR=%LOCALAPPDATA%\Programs\MNIME"

if exist "%INSTALL_DIR%" (
    echo Removing old installation...
    rmdir /S /Q "%INSTALL_DIR%"
)

echo Copying application files to %INSTALL_DIR% ...
mkdir "%INSTALL_DIR%"
xcopy /E /I /Q /Y "dist\MNIME\*" "%INSTALL_DIR%\"
if exist "MN.ico" copy /Y "MN.ico" "%INSTALL_DIR%\" >nul

echo.
echo Creating Desktop and Start Menu shortcuts...

set "DESKTOP_LNK=%USERPROFILE%\Desktop\MNIME.lnk"
set "STARTMENU_LNK=%APPDATA%\Microsoft\Windows\Start Menu\Programs\MNIME.lnk"
set "EXE_PATH=%INSTALL_DIR%\MNIME.exe"
set "ICON_PATH=%INSTALL_DIR%\MN.ico"

:: We write a temporary powershell script and execute it
echo $WshShell = New-Object -ComObject WScript.Shell > create_links.ps1
echo $Shortcut = $WshShell.CreateShortcut('%DESKTOP_LNK%') >> create_links.ps1
echo $Shortcut.TargetPath = '%EXE_PATH%' >> create_links.ps1
echo $Shortcut.WorkingDirectory = '%INSTALL_DIR%' >> create_links.ps1
echo $Shortcut.IconLocation = '%ICON_PATH%,0' >> create_links.ps1
echo $Shortcut.Save() >> create_links.ps1
echo $Shortcut2 = $WshShell.CreateShortcut('%STARTMENU_LNK%') >> create_links.ps1
echo $Shortcut2.TargetPath = '%EXE_PATH%' >> create_links.ps1
echo $Shortcut2.WorkingDirectory = '%INSTALL_DIR%' >> create_links.ps1
echo $Shortcut2.IconLocation = '%ICON_PATH%,0' >> create_links.ps1
echo $Shortcut2.Save() >> create_links.ps1

powershell -NoProfile -ExecutionPolicy Bypass -File create_links.ps1
del create_links.ps1

echo.
echo Registering uninstall entry in Add/Remove Programs...

set "UNINST_KEY=HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\MNIME"
set "UNINST_BAT=%INSTALL_DIR%\uninstall_mnime.bat"

:: Write uninstaller script into the install dir
(
    echo @echo off
    echo title Uninstall MNIME
    echo echo Removing MNIME...
    echo reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\MNIME" /f ^>nul 2^>^&1
    echo if exist "%DESKTOP_LNK%" del /f /q "%DESKTOP_LNK%"
    echo if exist "%STARTMENU_LNK%" del /f /q "%STARTMENU_LNK%"
    echo rmdir /S /Q "%INSTALL_DIR%"
    echo echo MNIME has been uninstalled.
    echo pause
) > "%UNINST_BAT%"

reg add "%UNINST_KEY%" /v "DisplayName"     /t REG_SZ /d "MNIME"                    /f >nul
reg add "%UNINST_KEY%" /v "DisplayVersion"  /t REG_SZ /d "2.1.0"                        /f >nul
reg add "%UNINST_KEY%" /v "Publisher"       /t REG_SZ /d "MNIME"                     /f >nul
reg add "%UNINST_KEY%" /v "InstallLocation" /t REG_SZ /d "%INSTALL_DIR%"             /f >nul
reg add "%UNINST_KEY%" /v "DisplayIcon"     /t REG_SZ /d "%ICON_PATH%,0"             /f >nul
reg add "%UNINST_KEY%" /v "UninstallString" /t REG_SZ /d "\"%UNINST_BAT%\""          /f >nul
reg add "%UNINST_KEY%" /v "NoModify"        /t REG_DWORD /d 1                         /f >nul
reg add "%UNINST_KEY%" /v "NoRepair"        /t REG_DWORD /d 1                         /f >nul

echo.
echo ========================================================
echo MNIME has been successfully installed!
echo It now appears in Add/Remove Programs for clean removal.
echo You can now launch it from your Desktop or Start Menu.
echo ========================================================
pause
