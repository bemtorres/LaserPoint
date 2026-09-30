from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from . import APP_ID, APP_NAME

SERVICE_NAME = "LaserPoint"
LAUNCH_AGENT = "com.laserpoint.plist"


def entry_script() -> Path:
    return Path(__file__).resolve().parent.parent / "main.py"


def _pythonw() -> str:
    executable = Path(sys.executable)
    if sys.platform == "win32":
        candidate = executable.with_name("pythonw.exe")
        if candidate.exists():
            return str(candidate)
    return str(executable)


def _run(args: list[str], timeout: float = 20.0) -> bool:
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        return result.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def _windows_command() -> str:
    return '"%s" "%s"' % (_pythonw(), entry_script())


def _macos_plist_path() -> Path:
    return Path.home() / "Library" / "LaunchAgents" / LAUNCH_AGENT


def _macos_plist() -> str:
    program = entry_script()
    return """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{label}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{python}</string>
        <string>{entry}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>ProcessType</key>
    <string>Interactive</string>
</dict>
</plist>
""".format(
        label=LAUNCH_AGENT[:-6],
        python=sys.executable,
        entry=str(program),
    )


def _linux_desktop_path() -> Path:
    return Path.home() / ".config" / "autostart" / (APP_ID + ".desktop")


def _linux_desktop() -> str:
    return "\n".join(
        [
            "[Desktop Entry]",
            "Type=Application",
            "Name=%s" % APP_NAME,
            "Exec=%s %s" % (sys.executable, entry_script()),
            "Terminal=false",
            "Categories=Utility;",
            "X-GNOME-Autostart-enabled=true",
            "",
        ]
    )


def is_enabled() -> bool:
    if sys.platform == "win32":
        try:
            import winreg

            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_READ,
            ) as key:
                value, _ = winreg.QueryValueEx(key, SERVICE_NAME)
            return bool(value)
        except OSError:
            return False
    if sys.platform == "darwin":
        return _macos_plist_path().exists()
    return _linux_desktop_path().exists()


def set_enabled(enabled: bool) -> bool:
    if sys.platform == "win32":
        return _set_windows(enabled)
    if sys.platform == "darwin":
        return _set_macos(enabled)
    return _set_linux(enabled)


def _set_windows(enabled: bool) -> bool:
    try:
        import winreg

        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE,
        ) as key:
            if enabled:
                winreg.SetValueEx(key, SERVICE_NAME, 0, winreg.REG_SZ, _windows_command())
            else:
                try:
                    winreg.DeleteValue(key, SERVICE_NAME)
                except FileNotFoundError:
                    pass
        return True
    except OSError:
        return False


def _set_macos(enabled: bool) -> bool:
    path = _macos_plist_path()
    if enabled:
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            path.write_text(_macos_plist(), encoding="utf-8")
        except OSError:
            return False
        _run(["launchctl", "unload", "-w", str(path)])
        return _run(["launchctl", "load", "-w", str(path)])
    _run(["launchctl", "unload", "-w", str(path)])
    try:
        if path.exists():
            path.unlink()
    except OSError:
        return False
    return True


def _set_linux(enabled: bool) -> bool:
    path = _linux_desktop_path()
    if enabled:
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            path.write_text(_linux_desktop(), encoding="utf-8")
        except OSError:
            return False
        return True
    try:
        if path.exists():
            path.unlink()
    except OSError:
        return False
    return True
