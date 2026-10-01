@echo off
title Install OMNIME
cd /d "%~dp0"

echo ========================================================
echo Installing OMNIME Application
echo ========================================================
echo.

if not exist "dist\OMNIME\OMNIME.exe" (
    echo ERROR: Could not find compiled application!
    echo Please run build_app.bat first.
    pause
    exit /b 1
)

set "INSTALL_DIR=%LOCALAPPDATA%\Programs\OMNIME"

if exist "%INSTALL_DIR%" (
    echo Removing old installation...
    rmdir /S /Q "%INSTALL_DIR%"
)

echo Copying application files to %INSTALL_DIR% ...
mkdir "%INSTALL_DIR%"
xcopy /E /I /Q /Y "dist\OMNIME\*" "%INSTALL_DIR%\"
if exist "OMN.ico" copy /Y "OMN.ico" "%INSTALL_DIR%\" >nul

echo.
echo Creating Desktop and Start Menu shortcuts...

set "DESKTOP_LNK=%USERPROFILE%\Desktop\OMNIME.lnk"
set "STARTMENU_LNK=%APPDATA%\Microsoft\Windows\Start Menu\Programs\OMNIME.lnk"
set "EXE_PATH=%INSTALL_DIR%\OMNIME.exe"
set "ICON_PATH=%INSTALL_DIR%\OMN.ico"

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
echo ========================================================
echo OMNIME has been successfully installed!
echo You can now launch it from your Desktop or Start Menu.
echo ========================================================
pause
