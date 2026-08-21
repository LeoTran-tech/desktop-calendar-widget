import sys
import winreg
from pathlib import Path


APP_NAME = "DesktopCalendar"


def _startup_command() -> str:
    # Sau này nếu build thành .exe
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}"'

    # Hiện tại đang chạy Python source
    python_exe = Path(sys.executable)

    pythonw_exe = python_exe.with_name("pythonw.exe")

    app_path = (
        Path(__file__)
        .resolve()
        .parent
        .parent
        / "app.py"
    )

    return f'"{pythonw_exe}" "{app_path}"'


def enable_auto_start() -> None:
    key_path = (
        r"Software\Microsoft\Windows"
        r"\CurrentVersion\Run"
    )

    command = _startup_command()

    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        key_path,
        0,
        winreg.KEY_SET_VALUE,
    ) as key:
        winreg.SetValueEx(
            key,
            APP_NAME,
            0,
            winreg.REG_SZ,
            command,
        )


def disable_auto_start() -> None:
    key_path = (
        r"Software\Microsoft\Windows"
        r"\CurrentVersion\Run"
    )

    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            key_path,
            0,
            winreg.KEY_SET_VALUE,
        ) as key:
            winreg.DeleteValue(
                key,
                APP_NAME,
            )

    except FileNotFoundError:
        pass