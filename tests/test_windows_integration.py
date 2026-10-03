"""
Tests for Windows integration, PDF document page preview registration,
and clean uninstallation handlers.
"""

import sys
import winreg
import pytest
from core.windows_integration import (
    ensure_pdf_page_preview,
    notify_shell_refresh,
    DOCUMENT_PAGE_ICON,
    PDF_PREVIEW_HANDLER_CLSID,
)


def test_ensure_pdf_page_preview():
    """Verify that ensure_pdf_page_preview registers document preview icon and Treatment=2."""
    if sys.platform != "win32":
        pytest.skip("Windows-specific integration test")

    result = ensure_pdf_page_preview()
    assert result is True

    # Validate registry entries under HKCU\Software\Classes\Applications\MNIME.exe
    app_key_path = r"Software\Classes\Applications\MNIME.exe"
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, app_key_path) as k:
        treatment, _ = winreg.QueryValueEx(k, "Treatment")
        assert treatment == 2
        app_name, _ = winreg.QueryValueEx(k, "FriendlyAppName")
        assert app_name == "MNIME"

    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, rf"{app_key_path}\DefaultIcon") as k:
        icon, _ = winreg.QueryValueEx(k, "")
        assert icon == DOCUMENT_PAGE_ICON

    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, rf"{app_key_path}\SupportedTypes") as k:
        val, _ = winreg.QueryValueEx(k, ".pdf")
        assert val == ""

    shellex_path = rf"{app_key_path}\ShellEx\{{8895b1c6-b41f-4c1c-a562-0d564250836f}}"
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, shellex_path) as k:
        clsid, _ = winreg.QueryValueEx(k, "")
        assert clsid == PDF_PREVIEW_HANDLER_CLSID


def test_notify_shell_refresh():
    """Verify that shell refresh runs cleanly without raising errors."""
    notify_shell_refresh()
