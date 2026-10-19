"""Keep a locked Windows session in the foreground until the user logs in."""

import sys

import ctypes
from ctypes import wintypes

WH_KEYBOARD_LL = 13
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_SYSKEYDOWN = 0x0104
WM_SYSKEYUP = 0x0105
LLKHF_ALTDOWN = 0x20

VK_TAB = 0x09
VK_ESCAPE = 0x1B
VK_SPACE = 0x20
VK_F4 = 0x73
VK_SHIFT = 0x10
VK_CONTROL = 0x11
VK_MENU = 0x12
VK_LWIN = 0x5B
VK_RWIN = 0x5C

_KEY_EVENTS = (WM_KEYDOWN, WM_KEYUP, WM_SYSKEYDOWN, WM_SYSKEYUP)


def should_block_key(vk, alt, ctrl, shift):
    """Keys that leave or close the app while it is locked."""
    if vk in (VK_LWIN, VK_RWIN):
        return True
    if alt and vk in (VK_TAB, VK_ESCAPE, VK_F4, VK_SPACE):
        return True
    if ctrl and vk == VK_ESCAPE and shift:
        return True
    if ctrl and vk == VK_ESCAPE:
        return True
    return False


class SessionGuard:
    def __init__(self):
        self._hook = None
        self._proc = None
        self._user32 = None

    @property
    def active(self):
        return self._hook is not None

    def set_enabled(self, enabled):
        if enabled:
            self._install()
        else:
            self._remove()

    def force_foreground(self, hwnd):
        if sys.platform != "win32" or not hwnd or self._user32 is None:
            return
        user32 = self._user32
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        foreground = user32.GetForegroundWindow()
        if foreground == hwnd:
            return
        current = kernel32.GetCurrentThreadId()
        target = user32.GetWindowThreadProcessId(foreground, None)
        attached = False
        if target and target != current:
            attached = bool(user32.AttachThreadInput(current, target, True))
        user32.ShowWindow(hwnd, 9)  # SW_RESTORE
        user32.SetForegroundWindow(hwnd)
        user32.BringWindowToTop(hwnd)
        if attached:
            user32.AttachThreadInput(current, target, False)

    def _install(self):
        if sys.platform != "win32" or self._hook is not None:
            return

        user32 = ctypes.WinDLL("user32", use_last_error=True)
        lresult = ctypes.c_ssize_t
        hook_proc = ctypes.WINFUNCTYPE(lresult, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)

        class KBDLLHOOKSTRUCT(ctypes.Structure):
            _fields_ = [
                ("vkCode", wintypes.DWORD),
                ("scanCode", wintypes.DWORD),
                ("flags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.c_void_p),
            ]

        user32.CallNextHookEx.restype = lresult
        user32.CallNextHookEx.argtypes = [
            wintypes.HHOOK,
            ctypes.c_int,
            wintypes.WPARAM,
            wintypes.LPARAM,
        ]
        user32.SetWindowsHookExW.restype = wintypes.HHOOK
        user32.SetWindowsHookExW.argtypes = [
            ctypes.c_int,
            hook_proc,
            wintypes.HINSTANCE,
            wintypes.DWORD,
        ]
        user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
        user32.GetAsyncKeyState.restype = ctypes.c_short
        user32.UnhookWindowsHookEx.argtypes = [wintypes.HHOOK]
        user32.UnhookWindowsHookEx.restype = wintypes.BOOL
        user32.GetForegroundWindow.restype = wintypes.HWND
        user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.c_void_p]
        user32.GetWindowThreadProcessId.restype = wintypes.DWORD
        user32.AttachThreadInput.argtypes = [wintypes.DWORD, wintypes.DWORD, wintypes.BOOL]
        user32.AttachThreadInput.restype = wintypes.BOOL
        user32.SetForegroundWindow.argtypes = [wintypes.HWND]
        user32.SetForegroundWindow.restype = wintypes.BOOL
        user32.BringWindowToTop.argtypes = [wintypes.HWND]
        user32.BringWindowToTop.restype = wintypes.BOOL
        user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
        user32.ShowWindow.restype = wintypes.BOOL

        def pressed(vk):
            return bool(user32.GetAsyncKeyState(vk) & 0x8000)

        def handler(n_code, w_param, l_param):
            if n_code == 0 and w_param in _KEY_EVENTS:
                info = ctypes.cast(l_param, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
                alt = bool(info.flags & LLKHF_ALTDOWN) or pressed(VK_MENU)
                if should_block_key(info.vkCode, alt, pressed(VK_CONTROL), pressed(VK_SHIFT)):
                    return 1
            return user32.CallNextHookEx(None, n_code, w_param, l_param)

        self._proc = hook_proc(handler)
        self._hook = user32.SetWindowsHookExW(WH_KEYBOARD_LL, self._proc, None, 0)
        self._user32 = user32
        if not self._hook:
            self._proc = None
            self._user32 = None

    def _remove(self):
        if self._hook is not None and self._user32 is not None:
            self._user32.UnhookWindowsHookEx(self._hook)
        self._hook = None
        self._proc = None
