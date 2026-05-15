import threading
import time
import numpy as np
import cv2
import win32gui
import win32ui
import win32con
import ctypes
from typing import Optional, Callable

class BackgroundCaptureThread(threading.Thread):

    def __init__(self, hwnd: int, capture_client: bool = True, interval: float = 0.05,
                 frame_callback: Optional[Callable[[np.ndarray], None]] = None):

        super().__init__(daemon=True)
        self.hwnd = hwnd
        self.capture_client = capture_client
        self.interval = interval
        self.frame_callback = frame_callback

        self.running = False
        self.latest_frame = None
        self._lock = threading.Lock()
        self._stop_event = threading.Event()

    def get_latest_frame(self) -> Optional[np.ndarray]:
        """线程安全获取最新帧"""
        with self._lock:
            return self.latest_frame.copy() if self.latest_frame is not None else None

    def stop(self):
        self.running = False
        self._stop_event.set()

    def run(self):
        self.running = True
        fail_count = 0
        max_fail = 5

        while self.running:
            try:
                # 检查窗口是否有效
                if not win32gui.IsWindow(self.hwnd):
                    time.sleep(0.5)
                    continue

                # 确定截图区域大小
                if self.capture_client:
                    rect = win32gui.GetClientRect(self.hwnd)
                    width = rect[2] - rect[0]
                    height = rect[3] - rect[1]
                else:
                    rect = win32gui.GetWindowRect(self.hwnd)
                    width = rect[2] - rect[0]
                    height = rect[3] - rect[1]

                if width <= 0 or height <= 0:
                    if self._stop_event.wait(timeout=0.1):
                        break
                    continue

                # 执行 PrintWindow 截图
                frame = self._print_window(self.hwnd, width, height)

                if frame is not None:
                    fail_count = 0
                    with self._lock:
                        self.latest_frame = frame
                    if self.frame_callback:
                        self.frame_callback(frame)
                else:
                    fail_count += 1
                    if fail_count >= max_fail:
                        time.sleep(0.5)
                        fail_count = 0
            except Exception as e:
                print(f"[CaptureThread] 异常: {e}")
                time.sleep(0.5)

            if self._stop_event.wait(timeout=self.interval):
                break

    def _print_window(self, hwnd, width, height):
        """使用 PrintWindow API 捕获窗口内容并返回 BGR numpy 数组"""
        hdc = None
        mfc_dc = None
        save_dc = None
        bitmap = None
        try:
            hdc = win32gui.GetWindowDC(hwnd)
            mfc_dc = win32ui.CreateDCFromHandle(hdc)
            save_dc = mfc_dc.CreateCompatibleDC()
            bitmap = win32ui.CreateBitmap()
            bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
            save_dc.SelectObject(bitmap)

            # 调用 PrintWindow
            result = ctypes.windll.user32.PrintWindow(hwnd, save_dc.GetSafeHdc(), 3)
            if result == 0:
                return None

            buf = bitmap.GetBitmapBits(True)
            img = np.frombuffer(buf, dtype=np.uint8).reshape((height, width, 4))
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            return img
        except Exception as e:
            print(f"[PrintWindow] 失败: {e}")
            return None
        finally:
            # 释放资源
            if bitmap:
                try:
                    win32gui.DeleteObject(bitmap.GetHandle())
                except:
                    pass
            if save_dc:
                try:
                    save_dc.DeleteDC()
                except:
                    pass
            if mfc_dc:
                try:
                    mfc_dc.DeleteDC()
                except:
                    pass
            if hdc:
                try:
                    win32gui.ReleaseDC(hwnd, hdc)
                except:
                    pass
