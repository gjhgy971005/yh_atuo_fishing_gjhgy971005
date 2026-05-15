import time
import threading
import win32gui
import win32con

def keep_focus(hwnd: int, stop_event: threading.Event, interval: float = 0.05):
    while stop_event.is_set():
        try:
            win32gui.SendMessage(hwnd, win32con.WM_ACTIVATE, 1, 0)
        except Exception as e:
            print(f"Focus keep error: {e}")
            continue
        for _ in range(int(interval / 0.05)):
            if not stop_event.is_set():
                break
            time.sleep(0.05)