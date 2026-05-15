import time
import win32con
import win32gui
from typing import Optional

# ========== 按键映射表 ==========
VK_MAP = {
    # 功能键
    'esc': win32con.VK_ESCAPE,
    'f1': win32con.VK_F1, 'f2': win32con.VK_F2, 'f3': win32con.VK_F3, 'f4': win32con.VK_F4,
    'f5': win32con.VK_F5, 'f6': win32con.VK_F6, 'f7': win32con.VK_F7, 'f8': win32con.VK_F8,
    'f9': win32con.VK_F9, 'f10': win32con.VK_F10, 'f11': win32con.VK_F11, 'f12': win32con.VK_F12,

    'backspace': win32con.VK_BACK, 'tab': win32con.VK_TAB,
    'enter': win32con.VK_RETURN, 'return': win32con.VK_RETURN,
    'shift': win32con.VK_SHIFT, 'ctrl': win32con.VK_CONTROL, 'alt': win32con.VK_MENU,
    'space': win32con.VK_SPACE,

    'up': win32con.VK_UP, 'down': win32con.VK_DOWN, 'left': win32con.VK_LEFT, 'right': win32con.VK_RIGHT,
    'home': win32con.VK_HOME, 'end': win32con.VK_END, 'insert': win32con.VK_INSERT, 'delete': win32con.VK_DELETE,
    'pageup': win32con.VK_PRIOR, 'pagedown': win32con.VK_NEXT,

    'a': ord('A'), 'b': ord('B'), 'c': ord('C'), 'd': ord('D'),
    'e': ord('E'), 'f': ord('F'), 'g': ord('G'), 'h': ord('H'),
    'i': ord('I'), 'j': ord('J'), 'k': ord('K'), 'l': ord('L'),
    'm': ord('M'), 'n': ord('N'), 'o': ord('O'), 'p': ord('P'),
    'q': ord('Q'), 'r': ord('R'), 's': ord('S'), 't': ord('T'),
    'u': ord('U'), 'v': ord('V'), 'w': ord('W'), 'x': ord('X'),
    'y': ord('Y'), 'z': ord('Z'),

    '0': ord('0'), '1': ord('1'), '2': ord('2'), '3': ord('3'), '4': ord('4'),
    '5': ord('5'), '6': ord('6'), '7': ord('7'), '8': ord('8'), '9': ord('9'),
}

# 假激活常量
WM_LBUTTONDOWN = win32con.WM_LBUTTONDOWN
WM_LBUTTONUP = win32con.WM_LBUTTONUP
WM_RBUTTONDOWN = win32con.WM_RBUTTONDOWN
WM_RBUTTONUP = win32con.WM_RBUTTONUP
WM_MBUTTONDOWN = win32con.WM_MBUTTONDOWN
WM_MBUTTONUP = win32con.WM_MBUTTONUP
MK_LBUTTON = win32con.MK_LBUTTON
MK_RBUTTON = win32con.MK_RBUTTON
MK_MBUTTON = win32con.MK_MBUTTON

# 发送消息时的超时设置（毫秒）
MSG_TIMEOUT = 100


def _get_vk(key: str) -> Optional[int]:

    key_lower = key.lower()
    if key_lower in VK_MAP:
        return VK_MAP[key_lower]
    if len(key) == 1:
        return ord(key.upper())
    return None

# ---------- 键盘操作 ----------
def press(key: str, hwnd: int, times: int = 1, interval: float = 0.1, delay: float = 0.05):

    vk = _get_vk(key)
    if vk is None:
        raise ValueError(f"不支持的键: {key}")
    for _ in range(times):

        # win32gui.SendMessage(hwnd, win32con.WM_ACTIVATE, 1, 0)
        win32gui.PostMessage(hwnd, win32con.WM_KEYDOWN, vk, 0)
        time.sleep(delay)
        win32gui.PostMessage(hwnd, win32con.WM_KEYUP, vk, 0)

        if times > 1:
            time.sleep(interval)


def keydown(key: str, hwnd: int):

    vk = _get_vk(key)
    if vk is None:
        raise ValueError(f"不支持的键: {key}")

    win32gui.SendMessage(hwnd, win32con.WM_KEYDOWN, vk, 0)


def keyup(key: str, hwnd: int):

    vk = _get_vk(key)
    if vk is None:
        raise ValueError(f"不支持的键: {key}")

    win32gui.SendMessage(hwnd, win32con.WM_KEYUP, vk, 0)