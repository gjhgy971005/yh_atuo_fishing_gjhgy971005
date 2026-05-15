import time
import ctypes
import traceback
import numpy as np
import psutil
import pyautogui
import threading
import win32process
import win32con
import win32gui
from ctypes import wintypes


import BackgroundInput as bi
from ImageProcessing import TemplateMatcher, CheckFishLevel, CheckSlider
from KeepsFocused import keep_focus

WIN32_LOCK = threading.Lock()

# ==============================================
# DPI初始化
# ==============================================
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except:
        pass

# ==============================================
# 初始化全局变量
# ==============================================
BAIT_DICT = {
    "万能鱼饵": 0, "杂谷饵": 1, "果渍饵": 2, "虾籽饵": 3,
    "鲜腴饵": 4, "蠕须饵": 5, "酒糟饵": 6, "甜麦饵": 7,
    "螺腥饵": 8, "连竿饵": 9, "诱食饵": 10, "八珍饵": 11,
    "密酿饵": 12, "丰藻饵": 13, "骨渣饵": 14, "未知": 15,
    "芳泽饵": 16, "金髓饵": 17, "沉香饵": 18, "玉引饵": 19
}

BUYABLE_BAIT = [
    "万能鱼饵", "杂谷饵", "果渍饵", "虾籽饵", "鲜腴饵",
    "蠕须饵", "酒糟饵", "甜麦饵", "螺腥饵", "连竿饵",
    "诱食饵"
]

# ==============================================
# 窗口句柄查找
# ==============================================
def find_hwnd_by_process(process_name: str):
    # 获取进程 PID
    pid = None
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'].lower() == process_name.lower():
            pid = proc.info['pid']
            break
    if not pid:
        return None

    # 查找属于该 PID 的可见窗口
    def callback(hwnd, hwnds):
        if win32gui.IsWindowVisible(hwnd):
            _, found_pid = win32process.GetWindowThreadProcessId(hwnd)
            if found_pid == pid:
                hwnds.append(hwnd)
        return True

    hwnds = []
    win32gui.EnumWindows(callback, hwnds)
    # 如果存在多个窗口，返回第一个（通常为主窗口）
    return hwnds[0] if hwnds else None

# ==============================================
# 打印去重类
# ==============================================
class PrintControl:
    def __init__(self):
        self.printed_set = set()
        self.limit_mode = True
    def log(self, msg):
        if not self.limit_mode:
            print(msg)
            return
        if msg not in self.printed_set:
            print(msg)
            self.printed_set.add(msg)
    def reset(self):
        self.printed_set.clear()
    def enable_limit(self):
        self.limit_mode = True
    def disable_limit(self):
        self.limit_mode = False

# ==============================================
# 独立钓鱼线程
# ==============================================
class FishingBot(threading.Thread):
    def __init__(self, capture_worker=None, on_finished=None, template_callback=None):
        super().__init__()

        self.game_hwnd = find_hwnd_by_process("HTGame.exe")
        self.on_finished = on_finished
        self.template_callback = template_callback

        # 数值变量
        self.retry_count = 0
        self.remaining_bait_count = 0
        self.fishing_times = 0
        self.esc_times = 0
        self.max_times = 10
        self.sell_times = 50
        self.sell_remaining = 0
        self.check_times_slider = 0
        self.check_times = 0

        # 状态变量
        self.now_work = "fishing"
        self.selected_bait = None
        self.current_key = None
        self.now_window = None

        # 布尔值变量
        self.stop_flag = True
        self.auto_buy_check = True
        self.auto_sell_check = True
        self.check_first_while = True

        # 黑名单标志
        self.black_fish5 = False
        self.black_fish6 = False
        self.black_fish9 = False

        # 依赖组件
        self.capture_worker = capture_worker
        self.template_matcher = TemplateMatcher(self.capture_worker)
        self.fish_level = CheckFishLevel(self.capture_worker, self)
        self.check_slider = CheckSlider(self.capture_worker)
        self.pc = PrintControl()

        # 焦点保持线程相关
        self.focus_stop_event = None
        self.focus_thread = None

    # 工具函数
    def click_pos(self, x, y, duration=0.1, interval=0.1, clicks=0):
        rect = wintypes.RECT()
        ctypes.windll.user32.GetClientRect(self.game_hwnd, ctypes.byref(rect))
        point = wintypes.POINT(0, 0)
        ctypes.windll.user32.ClientToScreen(self.game_hwnd, ctypes.byref(point))
        screen_x = point.x + x
        screen_y = point.y + y
        pyautogui.moveTo(screen_x, screen_y, duration=duration)
        if clicks > 0:
            pyautogui.click(clicks=clicks, interval=interval)

    # 调用匹配模板
    def _check_template_with_callback(self, template_name, threshold=0.7):
        if self.template_callback:
            self.template_callback(template_name)
        return self.template_matcher.check_template(template_name, threshold)


    # 检查开始按钮
    def _check_homepage(self):

        start_try_times = 0

        if self.sell_remaining >= self.sell_times and self.auto_sell_check:
            self.now_work = "sell_fish"
            return


        while self.stop_flag:

            check_results, _ = self._check_template_with_callback("抛钩按钮")

            if check_results:
                self.pc.log("✅  已定位开始界面")
                return

            else:
                start_try_times += 1

                self.pc.log("⌛  未找到按钮，等待开始位置...")

                self.now_window = win32gui.GetForegroundWindow()

                if self.stop_flag and start_try_times > 2:

                    self.pc.log("🛠️  尝试修复位置...")

                    check_results_f1, _ = self._check_template_with_callback("开始钓鱼按钮")
                    check_results_f0, _ = self._check_template_with_callback("进入钓鱼")

                    if self.now_window != self.game_hwnd:
                        win32gui.SetForegroundWindow(self.game_hwnd)

                    if check_results_f0:
                        bi.press("f",self.game_hwnd)
                        time.sleep(1)
                        self.click_pos(1070, 630, clicks=1)
                        time.sleep(0.2)
                        win32gui.SetWindowPos(self.game_hwnd, win32con.HWND_BOTTOM, 0, 0, 0, 0,
                                              win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
                        win32gui.SetForegroundWindow(self.now_window)
                        time.sleep(1)
                        bi.press("f",self.game_hwnd)
                        break

                    elif check_results_f1:
                        self.click_pos(1070, 630, clicks=1)
                        time.sleep(0.2)
                        win32gui.SetWindowPos(self.game_hwnd, win32con.HWND_BOTTOM, 0, 0, 0, 0,
                                              win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
                        win32gui.SetForegroundWindow(self.now_window)
                        time.sleep(1)
                        bi.press("f", self.game_hwnd)
                        break

                    else:
                        win32gui.SetForegroundWindow(self.now_window)
                        break
            time.sleep(1)
        return


    # 检查缺鱼饵
    def _check_bait_count(self):

        if not self.stop_flag: return False
        time.sleep(1)

        check_results, _ = self._check_template_with_callback("缺鱼饵提示")

        if check_results:
            self.now_work = "buy_bait"
            time.sleep(0.5)
            return False  # 无鱼饵
        else:
            return True  # 有鱼饵



    # 检测滑块
    def _waiting_bite(self):

        while self.stop_flag:

            slider_result = self.check_slider.find_slider()

            check_result, _ = self._check_template_with_callback("上钩")

            if not slider_result:
                continue

            if (len(slider_result[0][1]) > 0 and len(slider_result[1][1]) > 0) or check_result:
                bi.press("f", self.game_hwnd,3,0.2)
                self.pc.log("✨ 鱼上钩了！！！")
                return

            else:
                self.pc.log("🐌 等待鱼上钩中...")
                bi.press("f",self.game_hwnd)
                time.sleep(0.5)
                continue



    # 移动滑块
    def _move_slider(self,interval:float = 0.05):

        try_times = 0

        start_time = time.time()

        while self.stop_flag:

            if time.time() - start_time > 40:
                check_results, _ = self._check_template_with_callback("抛钩按钮")
                if check_results:
                    self.check_first_while = True
                    self.pc.reset()
                    self.pc.log("🤔 好像卡住了...")
                    self.now_work = "fishing"
                    return

            slider_result = self.check_slider.find_slider()
            if slider_result is None:
                self.pc.log("⚠️ slider_result 是空的")
                time.sleep(interval)
                continue

            yellow_exists = len(slider_result[0][1]) > 0
            blue_exists = len(slider_result[1][1]) > 0

            if yellow_exists and blue_exists:
                try:
                    y_l = np.min(slider_result[0][1])
                    y_r = np.max(slider_result[0][1])
                    b_l = np.min(slider_result[1][1])
                    b_r = np.max(slider_result[1][1])
                    ym_point = (y_l + y_r) // 2
                    bm_point = (b_l + b_r) // 2
                    diff = ym_point - bm_point

                except Exception as e:
                    if "zero-size array" in str(e):
                        return
                    else:
                        self.pc.log(f"⚠️ 滑块计算出错: {e}")
                        time.sleep(0.1)
                        return

                if diff > 15:
                    if self.current_key != 'a':
                        if self.current_key:
                            bi.keyup(self.current_key, self.game_hwnd)
                        bi.keydown('a', self.game_hwnd)
                        self.current_key = 'a'
                elif diff < -15:
                    if self.current_key != 'd':
                        if self.current_key:
                            bi.keyup(self.current_key, self.game_hwnd)
                        bi.keydown('d', self.game_hwnd)
                        self.current_key = 'd'
                else:
                    if self.current_key:
                        bi.keyup(self.current_key, self.game_hwnd)
                        self.current_key = None

                try_times = 0

            else:
                try_times += 1

                while self.stop_flag and try_times > 2:

                    check_result_end, _ = self._check_template_with_callback("结算继续")
                    check_result_end2, _ = self._check_template_with_callback("结算继续2")
                    check_result_lost, _ = self._check_template_with_callback("脱钩")

                    if check_result_lost:
                        self.check_first_while = True
                        self.pc.reset()
                        self.pc.log("✈️ 完蛋！鱼跑了，空军了...")
                        self.now_work = "fishing"
                        return

                    if check_result_end or check_result_end2:
                        self.check_first_while = True
                        self.sell_remaining += 1
                        self.fishing_times += 1
                        self.pc.reset()
                        self.pc.log(f"🎏 芜湖！钓到了！这是钓到的第 {self.fishing_times} 条")
                        print("-------------------------------------------------")
                        bi.press("esc", self.game_hwnd)
                        self.now_work = "fishing"
                        return

                    else:
                        try_times = 0
                        break

            time.sleep(interval)





    # 打开鱼饵菜单
    def _open_bait_menu(self):

        self.pc.log("🔁 开始更换/购买鱼饵...")

        try_times = 0

        while self.stop_flag:

            bi.press("e", self.game_hwnd)

            check_result, _ = self._check_template_with_callback("更换鱼饵")

            if check_result:
                return

            else:
                if try_times > 2:
                    bi.press("e", self.game_hwnd)
                    try_times = 0

                continue



    def _change_bait(self):

        if not self.stop_flag:
            return

        if self.auto_buy_check or self.fishing_times == 0:

            self.now_window = win32gui.GetForegroundWindow()

            win32gui.SetForegroundWindow(self.game_hwnd)

            bait_index = BAIT_DICT.get(self.selected_bait, 0)

            self.click_pos(470,360)

            if bait_index == 0:
                pass

            elif 0 < bait_index < 16:
                pyautogui.scroll(bait_index * -450)

            elif bait_index >= 16:
                pyautogui.scroll(bait_index * -450)
                time.sleep(0.2)
                pyautogui.moveRel((bait_index - 15) * 82, 0, duration=0.1)
            else:
                return

            time.sleep(0.5)
            pyautogui.click()
            time.sleep(0.5)

            check_result, _ = self._check_template_with_callback("选饵点重")
            if check_result:
                bi.press("esc", self.game_hwnd)
                time.sleep(1)



    def _click_button(self):

        check_result_change, _ = self._check_template_with_callback("更换")

        check_result_buy, _ = self._check_template_with_callback("购买")

        if check_result_change:
            self.click_pos(780, 470, clicks=1)
            self.pc.log("✅ 已完成装备该鱼饵")
            time.sleep(1)
            return True

        elif check_result_buy:
            self.click_pos(780, 470, clicks=1)
            self.pc.log("🏬 有问题，重新购买")
            time.sleep(1)
            return False



    def _search_products(self):
        page_two = True

        time.sleep(1)
        self.pc.log("🔍️ 搜索对应鱼饵中...")

        while self.stop_flag:

            now_window = win32gui.GetForegroundWindow()
            if now_window != self.game_hwnd:
                win32gui.SetForegroundWindow(self.game_hwnd)
                continue

            check_result, pos = self._check_template_with_callback(self.selected_bait)

            if check_result:
                self.pc.log("✅️ 找到商品了")
                self.click_pos(pos[0], pos[1], clicks=2)
                time.sleep(0.5)

                self.pc.log("🔍️ 检查能否购买")
                times = 0
                while self.stop_flag:
                    check_result, _ = self._check_template_with_callback("商店购买")
                    if check_result:
                        self.pc.log("✅️ 可以购买")
                        return True

                    else:
                        times += 1
                        if times > 2:
                            self.pc.log("❌️ 无法购买")
                            self.now_work = "no_bait"
                            return False

            else:
                if page_two:
                    self.click_pos(100, 600)
                    time.sleep(0.2)
                    pyautogui.scroll(-2700)
                    page_two = False
                    continue
                self.pc.log("❌️ 没找到这鱼饵...请自行配置后重开")
                self.now_work = "no_bait"
                return False


    def _set_bait_count(self):

        if not self.stop_flag:
            return

        buy_now = self.remaining_bait_count

        if self.remaining_bait_count == 0:
            self.click_pos(1180, 635, clicks=49, interval=0)
            self.click_pos(1070, 680, clicks=1)
            time.sleep(0.5)
            self.click_pos(770, 470, clicks=1)
            time.sleep(1)

        else:
            while self.stop_flag and buy_now > 0:
                buy_now = min(buy_now, 99)
                self.click_pos(1180, 635, clicks=buy_now-1, interval=0)
                self.click_pos(1070, 680, clicks=1)
                if buy_now >= 50:
                    time.sleep(0.5)
                    self.click_pos(770, 470, clicks=1)
                    time.sleep(1)
                buy_now -= buy_now
        self.check_times = 0

        while True:
            win32gui.SetForegroundWindow(self.game_hwnd)
            check_result, _ = self._check_template_with_callback("结算继续")
            if check_result:
                self.check_times = 0
                bi.press("esc", self.game_hwnd)
                continue
            else:
                if self.check_times > 2:
                    self.pc.log("💸 完成购物，开始钓鱼！")
                    time.sleep(1)
                    return
                self.check_times += 1
            time.sleep(1)


    def _close_store(self):
        if not self.stop_flag:
            return
        self.check_times = 0
        while True:
            win32gui.SetForegroundWindow(self.game_hwnd)
            check_result, _ = self._check_template_with_callback("渔具商店")
            if check_result:
                self.check_times = 0
                bi.press("esc", self.game_hwnd)
                time.sleep(1)
                continue
            else:
                if self.check_times > 2:
                    self.pc.log("🏃 离开商店界面")
                    time.sleep(1)
                    return
                self.check_times += 1


    def _check_unsuitable_bait(self):
        if not self.stop_flag:
            return
        time.sleep(1.5)
        check_result, _ = self._check_template_with_callback("异饵确认")
        if check_result:
            self.click_pos(770, 470, clicks=2, interval=0.5)
            time.sleep(1)
            pyautogui.press("f", self.game_hwnd)
        else:
            self.now_work = "fishing"


    def _sell_fish_menu(self):
        if not self.stop_flag:
            return

        self.pc.log("💲💲 钓的差不多了，清仓大甩卖！")
        print("-------------------------------------------------")

        self.now_window = win32gui.GetForegroundWindow()
        win32gui.SetForegroundWindow(self.game_hwnd)

        time.sleep(1)

        while self.stop_flag:

            check_result, _ = self._check_template_with_callback("鱼库")

            if check_result:

                try:
                    now_window = win32gui.GetForegroundWindow()  # 记录当前窗口
                    if now_window != self.game_hwnd:
                        win32gui.SetForegroundWindow(self.game_hwnd)
                        continue
                except Exception as e:
                    self.pc.log(f"ℹ️ 可忽略报错:{e}")
                    continue

                time.sleep(1)

                self.click_pos(110, 275, clicks=2, interval=0.2)
                self.click_pos(710, 645, clicks=2, interval=0.2)
                self.click_pos(780, 470, clicks=2, interval=1)

                while self.stop_flag:
                    try:
                        win32gui.SetWindowPos(self.game_hwnd, win32con.HWND_BOTTOM, 0, 0, 0, 0,
                                              win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
                        win32gui.SetForegroundWindow(self.now_window)
                        break
                    except Exception as e:
                        self.pc.log(f"ℹ️ 可忽略报错:{e}")
                        continue
                break
            else:
                bi.press("q", self.game_hwnd)
                continue

        while self.stop_flag:

            bi.press("esc", self.game_hwnd)

            check_result, _ = self._check_template_with_callback("鱼库")
            if check_result:
                continue
            else:
                self.sell_remaining = 0
                self.now_work = "fishing"
                time.sleep(1)
                return




    # 钓鱼循环
    def _fishing_operation_module(self):

        bi.press("f", self.game_hwnd,2)
        if self._check_bait_count():        # 检查鱼饵
            self._check_unsuitable_bait()   # 检测非优势饵
            self._waiting_bite()            # 等待上钩
            self._move_slider()             # 溜鱼

    # 买鱼饵循环
    def _buy_bait_module(self):

        self.now_window = win32gui.GetForegroundWindow()  # 记录当前窗口

        try:
            while self.stop_flag:

                check_result, _ = self._check_template_with_callback("渔具商店")

                if check_result:
                    try:
                        now_window = win32gui.GetForegroundWindow()
                        if now_window != self.game_hwnd:
                            win32gui.SetForegroundWindow(self.game_hwnd)    # 激活异环窗口
                    except Exception as e:
                        self.pc.log(f"ℹ️ 可忽略报错:{e}")
                        continue

                    time.sleep(1)

                    if self._search_products():             # 搜索商品
                        self._set_bait_count()              # 设置数量
                        self._close_store()                 # 关闭界面
                        self._open_bait_menu()              # 打开装配
                        self._change_bait()                 # 选择鱼饵
                        if self._click_button():            # 选择装备
                            self._check_unsuitable_bait()   # 检查不合适弹窗

                        while self.stop_flag:
                            try:
                                win32gui.SetWindowPos(self.game_hwnd, win32con.HWND_BOTTOM, 0, 0, 0, 0,
                                                      win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
                                win32gui.SetForegroundWindow(self.now_window)

                                print("-------------------------------------------------")
                                return
                            except Exception as e:
                                self.pc.log(f"ℹ️ 可忽略报错:{e}")
                                continue
                        else:
                            continue
                    else:
                        return
                else:
                    bi.press("r", self.game_hwnd)
                    continue
        except Exception as e:
            self.pc.log(e)
            return



    # 主线程入口
    def run(self):
        self.pc.log(self.game_hwnd)
        self.pc.log("⚙️ 截图线程已由外部启动，直接开始钓鱼流程")
        self.pc.log("⚙️ 等待焦点保持启动")
        self.focus_stop_event = threading.Event()
        self.focus_stop_event.set()
        self.focus_thread = threading.Thread(target=keep_focus,
                                             args=(self.game_hwnd, self.focus_stop_event, 0.05))
        self.focus_thread.daemon = True
        self.focus_thread.start()

        self.pc.log("✅ 线程已启动，开始钓鱼")
        print("-------------------------------------------------")
        try:
            win32gui.SetWindowPos(self.game_hwnd, win32con.HWND_BOTTOM, 0, 0, 0, 0,
                                  win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
            while self.stop_flag and self.fishing_times < self.max_times:
                self._check_homepage()
                if self.now_work == "fishing":
                    bi.press("f", self.game_hwnd)
                    self._fishing_operation_module()

                elif self.now_work == "buy_bait":
                    if self.auto_buy_check:
                        self.pc.log("🛒 鱼饵用尽，开始自动采购！")
                        bi.press("r", self.game_hwnd)
                        self._buy_bait_module()
                    else:
                        self.pc.log("❌️ 鱼饵用尽，停止钓鱼")
                        break

                elif self.now_work == "sell_fish":
                    bi.press("q", self.game_hwnd)
                    self._sell_fish_menu()

                elif self.now_work == "no_bait":
                    break

        except Exception as e:
            self.pc.log(f"💥 脚本异常崩溃: {e}")
            traceback.print_exc()
            return

        finally:
            if self.stop_flag:
                print("🛑 钓鱼已停止")
            pyautogui.keyUp('a')
            pyautogui.keyUp('d')
            pyautogui.keyUp('f')
            self.pc.log("🧹 已清理所有按键状态")
            print("-------------------------------------------------")
            self.pc.log(f"🎉🎉🎉  全部完成！总计钓鱼：{self.fishing_times:>2} 次  🎉🎉🎉")
            self.pc.log(f"🛑🛑🛑       跳过黑名单鱼：{self.esc_times:>2} 次       🛑🛑🛑")
            self.fishing_times = 0
            self.esc_times = 0
            if self.on_finished:
                self.on_finished()

    def stop(self):
        print("🛑 正在停止所有流程...")
        self.stop_flag = False
        if self.focus_stop_event:
            self.focus_stop_event.clear()
        if self.focus_thread and self.focus_thread.is_alive():
            self.focus_thread.join(timeout=1.0)