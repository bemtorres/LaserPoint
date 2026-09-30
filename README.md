# LaserPoint

A cross-platform on-screen laser pointer for **Windows**, **macOS** and **Linux**.
It draws a glowing pointer that follows the mouse so you can highlight things during
presentations, lessons, streams or screen sharing.

## Features

- **Global hotkey** to turn the pointer on/off from any application (default `Ctrl+Alt+L`).
  Works in *hold* mode (pointer while pressed) or *toggle* mode (press once).
- **Customizable appearance**: color, size, shadow/glow, opacity and shape
  (filled dot, ring or cross).
- **Speed reaction**: the pointer grows and a motion trail appears when you move the
  mouse fast and hard (intensity configurable from 0 % to 200 %).
- **Configurable fade-out time** after the hotkey is released (0 – 3000 ms).
- **System tray icon** (Windows / Linux) or **menu bar icon** (macOS) with a full menu,
  plus an optional **floating control bar** you can drag anywhere on screen.
- **5 tray icon styles**: dot, ring, lightning, star and cursor — the icon adopts the
  pointer color.
- **Start with the system** option (registry on Windows, LaunchAgent on macOS,
  autostart `.desktop` on Linux).
- Configuration stored as JSON, single instance at a time.

## Requirements

- Python 3.10+
- [PySide6](https://pypi.org/project/PySide6/) and [pynput](https://pypi.org/project/pynput/)
  (installed automatically by the installers)

## Install

### Windows

```bat
install.bat
start.bat
```

`install.bat` creates a virtual environment in `.venv`, installs the dependencies,
generates `assets\icon.ico` and adds shortcuts to the Desktop and the Start Menu.

### macOS / Linux

```bash
./install.sh
./start.sh
```

On macOS `install.sh` also builds `LaserPoint.app` (menu bar only, no Dock icon).

> **macOS note:** grant *Accessibility* permission to your terminal (or to
> `LaserPoint.app`) in **System Settings → Privacy & Security → Accessibility**,
> otherwise the global hotkey cannot be captured.

## Usage

| Action | Result |
| --- | --- |
| Press and hold `Ctrl+Alt+L` | Show the laser pointer (default *hold* mode) |
| Double-click the tray/menu bar icon | Open settings |
| Middle-click the tray icon | Toggle the pointer |
| Tray menu → *Puntero encendido* | Keep the pointer on without the hotkey |
| Tray menu → *Floating bar* | Show/hide the drag-and-drop control bar |
| Tray menu → *Start with the system* | Enable/disable autostart |
| Tray menu → *Quit* | Exit the application |

### Settings

Open the settings dialog from the tray icon or the floating bar:

- **Appearance**: color, shape, base size, shadow/glow, opacity, motion trail and tray icon style.
- **Motion & time**: speed boost (how much the pointer grows when you move fast),
  fade-out time and hotkey mode (hold / toggle).
- **Hotkey & system**: click the hotkey field and press the desired key combination,
  plus autostart and floating bar toggles.

A live preview is shown at the top of the dialog.

## Configuration file

Settings are stored in:

| OS | Path |
| --- | --- |
| Windows | `%APPDATA%\laserpoint\config.json` |
| macOS | `~/Library/Application Support/laserpoint/config.json` |
| Linux | `~/.config/laserpoint/config.json` |

Example:

```json
{
  "hotkey": "ctrl+alt+l",
  "mode": "hold",
  "color": "#ff3b30",
  "size": 26,
  "shadow": 70,
  "opacity": 100,
  "shape": "dot",
  "fade_ms": 350,
  "speed_boost": 120,
  "trail": true,
  "tray_icon": "dot",
  "autostart": false,
  "show_widget": true
}
```

Delete this file to restore the default values (or use *Restore Defaults* in the dialog).

## Project layout

```
laserpoint/
  app.py        application controller (tray, hotkey, overlay, settings wiring)
  overlay.py    frameless, click-through laser overlay window
  render.py     shared glow/ring/cross painting routines
  hotkey.py     global hotkey (Windows low-level hook, pynput elsewhere)
  settings.py   settings dialog, live preview and hotkey capture widget
  tray.py       system tray icon and menu
  widget.py     floating control bar
  icons.py      generated tray and button icons
  config.py     JSON configuration storage
  autostart.py  start-with-the-system helpers per OS
main.py         entry point
tools/make_icon.py  builds assets/icon.ico
scripts/make_shortcut.ps1  Windows shortcuts
```

## Development

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt     # .venv\Scripts\pip on Windows
python main.py            # run from source
python main.py --smoke-test   # headless smoke test
python -m pyflakes laserpoint main.py tools   # lint
```

## License

Use and modify freely for personal or commercial projects.
