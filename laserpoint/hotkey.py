from __future__ import annotations

import re
import sys
import threading
import time
from typing import Callable, Dict, FrozenSet, Optional, Tuple

from PySide6.QtCore import QObject, Signal

MOD_ALIASES = {
    "ctrl": "ctrl",
    "control": "ctrl",
    "ctl": "ctrl",
    "shift": "shift",
    "shft": "shift",
    "alt": "alt",
    "option": "alt",
    "opt": "alt",
    "altgr": "alt",
    "cmd": "cmd",
    "command": "cmd",
    "super": "cmd",
    "win": "cmd",
    "windows": "cmd",
    "meta": "cmd",
}

KEY_ALIASES = {
    "esc": "escape",
    "return": "enter",
    "del": "delete",
    "ins": "insert",
    "pgup": "pageup",
    "pgdn": "pagedown",
    "page_up": "pageup",
    "page_down": "pagedown",
    "spacebar": "space",
}

MOD_ORDER = ("ctrl", "alt", "shift", "cmd")


def parse_hotkey(text: str) -> Tuple[FrozenSet[str], str]:
    parts = [part.strip().lower() for part in text.split("+")]
    parts = [part for part in parts if part]
    if not parts:
        raise ValueError("empty hotkey")
    mods: set[str] = set()
    key = ""
    for part in parts:
        part = KEY_ALIASES.get(part, part)
        if part in MOD_ALIASES:
            mods.add(MOD_ALIASES[part])
        else:
            key = part
    if not key:
        raise ValueError("hotkey needs a non-modifier key")
    return frozenset(mods), key


def format_hotkey(mods: FrozenSet[str], key: str) -> str:
    parts = [mod for mod in MOD_ORDER if mod in mods]
    parts.append(key)
    return "+".join(parts)


def display_hotkey(text: str) -> str:
    try:
        mods, key = parse_hotkey(text)
    except ValueError:
        return text
    parts = [mod.upper() if mod != "cmd" else "Win" for mod in MOD_ORDER if mod in mods]
    parts.append(key.upper() if len(key) == 1 else key.upper())
    return " + ".join(parts)


def _pynput_norm(key) -> str:  # type: ignore[no-untyped-def]
    name = getattr(key, "name", None)
    if isinstance(name, str):
        if name in ("ctrl_l", "ctrl_r", "ctrl"):
            return "ctrl"
        if name in ("shift_l", "shift_r", "shift"):
            return "shift"
        if name in ("alt_l", "alt_r", "alt", "alt_gr"):
            return "alt"
        if name in ("cmd_l", "cmd_r", "cmd", "cmd_r"):
            return "cmd"
        if name in ("super_l", "super_r", "super", "meta", "meta_l", "meta_r", "windows"):
            return "cmd"
        return KEY_ALIASES.get(name, name)
    char = getattr(key, "char", None)
    if isinstance(char, str) and char:
        return char.lower()
    return str(key).lower()


class _WindowsHookBackend:
    def __init__(self) -> None:
        self._thread: Optional[threading.Thread] = None
        self._hook = None
        self._tid = 0
        self._proc = None
        self._ready = threading.Event()
        self._stop = threading.Event()
        self._error: Optional[str] = None
        self._mods: FrozenSet[str] = frozenset()
        self._trigger = 0
        self._held = False
        self._on_press: Optional[Callable[[], None]] = None
        self._on_release: Optional[Callable[[], None]] = None

    def start(
        self,
        mods: FrozenSet[str],
        key: str,
        on_press: Callable[[], None],
        on_release: Callable[[], None],
    ) -> bool:
        trigger = _trigger_vk(key)
        if not trigger:
            return False
        self._mods = mods
        self._trigger = trigger
        self._on_press = on_press
        self._on_release = on_release
        self._held = False
        self._error = None
        self._ready.clear()
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="laser-hotkey", daemon=True)
        self._thread.start()
        self._ready.wait(timeout=3.0)
        return self._error is None and self._hook is not None

    def stop(self) -> None:
        self._stop.set()
        if self._tid:
            try:
                import ctypes

                ctypes.windll.user32.PostThreadMessageW(self._tid, 0x0012, 0, 0)
            except Exception:
                pass
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None
        self._tid = 0
        self._hook = None

    def _run(self) -> None:
        import ctypes
        import ctypes.wintypes as wintypes

        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        kernel32.GetModuleHandleW.argtypes = [ctypes.c_wchar_p]
        kernel32.GetModuleHandleW.restype = ctypes.c_void_p
        kernel32.GetCurrentThreadId.restype = ctypes.c_ulong
        hookproc = ctypes.WINFUNCTYPE(
            ctypes.c_size_t, ctypes.c_int, ctypes.c_size_t, ctypes.c_void_p
        )
        user32.SetWindowsHookExW.restype = ctypes.c_void_p
        user32.SetWindowsHookExW.argtypes = [
            ctypes.c_int,
            hookproc,
            ctypes.c_void_p,
            ctypes.c_ulong,
        ]
        user32.CallNextHookEx.restype = ctypes.c_size_t
        user32.CallNextHookEx.argtypes = [
            ctypes.c_size_t,
            ctypes.c_int,
            ctypes.c_size_t,
            ctypes.c_void_p,
        ]

        class KBDLLHOOKSTRUCT(ctypes.Structure):
            _fields_ = [
                ("vkCode", ctypes.c_ulong),
                ("scanCode", ctypes.c_ulong),
                ("flags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", ctypes.c_size_t),
            ]

        pointer = ctypes.POINTER(KBDLLHOOKSTRUCT)

        @hookproc
        def proc(n_code: int, w_param: int, l_param: int):  # type: ignore[no-untyped-def]
            swallow = False
            try:
                if n_code >= 0:
                    info = ctypes.cast(l_param, pointer).contents
                    swallow = self._handle(int(info.vkCode), int(w_param))
            except Exception:
                swallow = False
            if swallow:
                return 1
            return user32.CallNextHookEx(self._hook, n_code, w_param, l_param)

        self._proc = proc
        self._tid = kernel32.GetCurrentThreadId()
        try:
            kernel32.SetLastError(0)
            self._hook = user32.SetWindowsHookExW(
                13, proc, kernel32.GetModuleHandleW(None), 0
            )
            if not self._hook:
                self._error = "SetWindowsHookExW error %d" % kernel32.GetLastError()
        except Exception as exc:
            self._hook = None
            self._error = str(exc)
        if not self._hook and not self._error:
            self._error = "SetWindowsHookExW failed"
        self._ready.set()
        if not self._hook:
            return
        message = wintypes.MSG()
        while not self._stop.is_set():
            result = user32.GetMessageW(ctypes.byref(message), None, 0, 0)
            if result <= 0:
                break
            user32.TranslateMessage(ctypes.byref(message))
            user32.DispatchMessageW(ctypes.byref(message))
        if self._hook:
            user32.UnhookWindowsHookEx(self._hook)
            self._hook = None

    def _handle(self, vk: int, w_param: int) -> bool:
        down = w_param in (0x0100, 0x0104)
        up = w_param in (0x0101, 0x0105)
        if not (down or up):
            return False
        if vk != self._trigger:
            return False
        mods_ok = self._mods_ok()
        if down:
            if mods_ok and not self._held:
                self._held = True
                if self._on_press:
                    self._on_press()
                return True
            return mods_ok
        if self._held:
            self._held = False
            if self._on_release:
                self._on_release()
            return mods_ok
        return False

    def _mods_ok(self) -> bool:
        if not self._mods:
            return True
        import ctypes

        user32 = ctypes.windll.user32
        for mod in self._mods:
            codes = _MOD_VKS.get(mod, ())
            if not any(user32.GetAsyncKeyState(code) & 0x8000 for code in codes):
                return False
        return True


class _PynputBackend:
    def __init__(self) -> None:
        self._listener = None
        self._held = False
        self._pressed: set[str] = set()
        self._mods: FrozenSet[str] = frozenset()
        self._key = ""

    def start(
        self,
        mods: FrozenSet[str],
        key: str,
        on_press: Callable[[], None],
        on_release: Callable[[], None],
    ) -> bool:
        from pynput import keyboard

        self._mods = mods
        self._key = key
        self._held = False
        self._pressed = set()

        def handle_press(raw) -> None:  # type: ignore[no-untyped-def]
            name = _pynput_norm(raw)
            self._pressed.add(name)
            if name != self._key or self._held:
                return
            if all(mod in self._pressed for mod in self._mods):
                self._held = True
                on_press()

        def handle_release(raw) -> None:  # type: ignore[no-untyped-def]
            name = _pynput_norm(raw)
            self._pressed.discard(name)
            if name == self._key and self._held:
                self._held = False
                on_release()

        self._listener = keyboard.Listener(on_press=handle_press, on_release=handle_release)
        self._listener.daemon = True
        self._listener.start()
        time.sleep(0.05)
        return True

    def stop(self) -> None:
        if self._listener is not None:
            try:
                self._listener.stop()
            except Exception:
                pass
            self._listener = None


_MOD_VKS: Dict[str, Tuple[int, ...]] = {
    "ctrl": (0x11,),
    "shift": (0x10,),
    "alt": (0x12,),
    "cmd": (0x5B, 0x5C),
}

_PUNCT_VK = {
    "-": 0xBD,
    "=": 0xBB,
    "[": 0xDB,
    "]": 0xDD,
    "\\": 0xDC,
    ";": 0xBA,
    "'": 0xDE,
    ",": 0xBC,
    ".": 0xBE,
    "/": 0xBF,
    "`": 0xC0,
}

_NAMED_VK = {
    "space": 0x20,
    "tab": 0x09,
    "escape": 0x1B,
    "backspace": 0x08,
    "enter": 0x0D,
    "insert": 0x2D,
    "delete": 0x2E,
    "home": 0x24,
    "end": 0x23,
    "pageup": 0x21,
    "pagedown": 0x22,
    "left": 0x25,
    "up": 0x26,
    "right": 0x27,
    "down": 0x28,
    "printscreen": 0x2C,
    "scrolllock": 0x91,
    "pause": 0x13,
    "capslock": 0x14,
    "numlock": 0x90,
}


def _trigger_vk(key: str) -> int:
    if len(key) == 1:
        upper = key.upper()
        if upper.isalpha() or upper.isdigit():
            return ord(upper)
        return _PUNCT_VK.get(key, 0)
    match = re.fullmatch(r"f(\d{1,2})", key)
    if match:
        number = int(match.group(1))
        if 1 <= number <= 24:
            return 0x70 + number - 1
        return 0
    return _NAMED_VK.get(key, 0)


class HotkeyManager(QObject):
    activated = Signal()
    deactivated = Signal()
    failed = Signal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._backend = None
        self._hotkey = ""

    @property
    def hotkey(self) -> str:
        return self._hotkey

    def set_hotkey(self, text: str) -> bool:
        try:
            mods, key = parse_hotkey(text)
        except ValueError:
            self.failed.emit("Atajo no válido: %s" % text)
            return False
        self.stop()
        normalized = format_hotkey(mods, key)
        self._hotkey = normalized
        backends = []
        if sys.platform == "win32":
            backends.append(_WindowsHookBackend())
        backends.append(_PynputBackend())
        last_error = ""
        for backend in backends:
            try:
                if backend.start(mods, key, self.activated.emit, self.deactivated.emit):
                    self._backend = backend
                    return True
                last_error = "no se pudo registrar el atajo"
            except Exception as exc:
                last_error = str(exc) or exc.__class__.__name__
        self._backend = None
        self.failed.emit(
            "No se pudo activar el atajo %s (%s). Revisa los permisos de accesibilidad."
            % (display_hotkey(normalized), last_error)
        )
        return False

    def stop(self) -> None:
        if self._backend is not None:
            try:
                self._backend.stop()
            except Exception:
                pass
            self._backend = None
