import sys
import time
import cv2
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import QFont, QTextCursor, QImage, QPixmap
from qfluentwidgets import *
import pyautogui
import numpy as np

import Fishing_Core
from MSSScreenshot import BackgroundCaptureThread
from ImageProcessing import Screenshot_Area
from utils import resource_path

# ======================
# 线程安全日志重定向
# ======================
class LogSignal(QObject):
    new_log = pyqtSignal(str)


class PrintRedirect:
    MAX_LINES = 100

    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.signal = LogSignal()
        self.signal.new_log.connect(self._append_log_safe)

    def write(self, msg):
        msg = msg.rstrip()
        if msg:
            self.signal.new_log.emit(msg)

    def _append_log_safe(self, msg):
        now_time = time.strftime("%H:%M:%S")
        new_line = f'<font color="#666666">[{now_time}]</font> {msg}<br>'

        self.text_widget.moveCursor(QTextCursor.MoveOperation.Start)
        self.text_widget.insertHtml(new_line)

        sb = self.text_widget.verticalScrollBar()
        sb.setValue(sb.minimum())

        if self.text_widget.document().blockCount() > self.MAX_LINES:
            doc = self.text_widget.document()
            cursor = QTextCursor(doc.lastBlock())
            cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
            cursor.removeSelectedText()
            cursor.deletePreviousChar()

    def flush(self):
        pass

class FishingWindow(QWidget):

    preview_signal = pyqtSignal(np.ndarray)
    current_template_signal = pyqtSignal(str)
    log_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        # 初始化变量
        self.thread_state = "IDLE"

        # 信号绑定
        self.log_signal.connect(self._append_log)
        self.preview_signal.connect(self.update_preview)
        self.current_template_signal.connect(self.on_current_template_changed)

        # 加载UI
        self.init_ui()

        # 日志重定向
        sys.stdout = PrintRedirect(self.log)

        self.current_template = None
        self.capture_worker = None
        self.retry_find_window = True

        self._start_background_capture()
        print("✅ 异环自动钓鱼界面加载完成，等待启动...")

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(16, 16, 16, 16)
        self.main_layout.setSpacing(12)

        # 顶部布局
        top_layout = QHBoxLayout()
        top_layout.setSpacing(12)

        # 设置卡片
        setting_card = CardWidget()
        setting_card.setClickEnabled(False)
        setting_layout = QHBoxLayout(setting_card)
        setting_layout.setContentsMargins(16, 16, 8, 16)
        setting_layout.setSpacing(32)

        # 鱼饵设置列
        bait_col = QVBoxLayout()
        bait_col.setSpacing(6)

        # 开关组件生成函数
        def make_switch_card(text):
            card = CardWidget()
            layout = QHBoxLayout(card)
            layout.addWidget(BodyLabel(text))
            sw = SwitchButton()
            layout.addWidget(sw)
            return card, sw

        # 自动购买开关
        self.auto_buy_layout, self.auto_fish_switch = make_switch_card("自动买饵")
        self.auto_sell_layout, self.sell_fish_switch = make_switch_card("自动卖鱼")

        # 鱼饵选择
        bait_label = BodyLabel("选择鱼饵：")
        self.bait_combobox = ComboBox()
        self.bait_combobox.setMaximumWidth(180)
        self.bait_list = [
            "万能鱼饵", "杂谷饵", "果渍饵", "虾籽饵", "鲜腴饵",
            "蠕须饵", "酒糟饵", "甜麦饵", "螺腥饵", "连竿饵",
            "诱食饵", "八珍饵", "密酿饵", "丰藻饵", "骨渣饵",
            "芳泽饵", "金髓饵", "沉香饵", "玉引饵"
        ]
        self.bait_combobox.addItems(self.bait_list)
        self.bait_combobox.currentIndexChanged.connect(self._on_bait_changed)

        # 购买数量
        buy_label = BodyLabel("购买上限：")
        self.buy_count_input = LineEdit()
        self.buy_count_input.setMaximumWidth(180)
        self.buy_count_input.setPlaceholderText("默认50个")

        # 购买数量
        sell_label = BodyLabel("卖鱼阈值：")
        self.sell_count_input = LineEdit()
        self.sell_count_input.setMaximumWidth(180)
        self.sell_count_input.setPlaceholderText("默认50条")

        # 左侧鱼饵列
        bait_col.addWidget(bait_label)
        bait_col.addWidget(self.bait_combobox)
        bait_col.addWidget(buy_label)
        bait_col.addWidget(self.buy_count_input)
        bait_col.addWidget(sell_label)
        bait_col.addWidget(self.sell_count_input)

        # 鱼饵预览图
        self.bait_preview = ImageLabel()
        self.bait_preview.setFixedSize(110, 110)
        self.bait_preview.setBorderRadius(18, 18, 18, 18)

        # 分割线
        separator = VerticalSeparator()

        # 黑名单设置
        black_col = QVBoxLayout()
        black_col.setSpacing(8)
        black_title = SubtitleLabel("钓鱼黑名单")

        row5, self.black_fish5 = make_switch_card("5体鱼（绿）")
        row6, self.black_fish6 = make_switch_card("6体鱼（蓝）")
        row9, self.black_fish9 = make_switch_card("9体鱼（紫）")

        warn_label = CaptionLabel("⚠️ 识别模型限制，有概率钓错...")
        warn_label.setStyleSheet("color:#e74c3c;font-size:8px;")

        black_col.addWidget(black_title)
        black_col.addWidget(row5)
        black_col.addWidget(row6)
        black_col.addWidget(row9)
        black_col.addWidget(warn_label)
        black_col.addStretch()

        # 拼接左侧设置区
        setting_layout.addLayout(bait_col)
        setting_layout.addWidget(self.bait_preview)
        setting_layout.addWidget(separator)
        setting_layout.addLayout(black_col)

        # 右侧控制按钮
        control_col = QVBoxLayout()
        control_col.setSpacing(12)
        control_col.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.btn_start = PrimaryPushButton("开始钓鱼")
        self.btn_stop = PushButton("停止钓鱼")
        self.btn_stop.setEnabled(False)

        self.btn_start.clicked.connect(self.start_fishing)
        self.btn_stop.clicked.connect(self.stop_fishing)

        # 钓鱼次数
        count_row = QHBoxLayout()
        count_row.addWidget(BodyLabel("钓鱼次数："))
        self.input_count = LineEdit()
        self.input_count.setText("10")
        self.input_count.setFixedWidth(120)
        count_row.addWidget(self.input_count)
        count_row.addStretch()

        # 右侧布局组装
        control_col.addWidget(self.btn_start)
        control_col.addWidget(self.btn_stop)
        control_col.addLayout(count_row)
        control_col.addWidget(self.auto_buy_layout)
        control_col.addWidget(self.auto_sell_layout)
        control_col.addStretch()

        # 拼接顶部
        top_layout.addWidget(setting_card, stretch=3)
        top_layout.addLayout(control_col, stretch=1)
        self.main_layout.addLayout(top_layout)

        # 底部日志
        bottom_layout = QHBoxLayout()
        self.log = TextBrowser()
        self.log.setFrameShape(QFrame.Shape.NoFrame)
        self.log.setMinimumHeight(220)
        self.log.setFont(QFont("Microsoft YaHei Light", 10))
        self.log.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse |
            Qt.TextInteractionFlag.TextSelectableByKeyboard
        )
        bottom_layout.addWidget(self.log, stretch=1)

        # 预览标签
        self.preview_label = ImageLabel()
        self.preview_label.setMinimumHeight(220)
        self.preview_label.setStyleSheet("background-color: black; border-radius: 6px;")
        self.preview_label.setScaledContents(True)  # 图片自动适应控件大小
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bottom_layout.addWidget(self.preview_label, stretch=1)

        self.main_layout.addLayout(bottom_layout)



        # 初始化预览图
        self._on_bait_changed(0)


    def _start_background_capture(self):
        # 异步启动
        self._try_start_capture()

    def _try_start_capture(self):
        """尝试获取窗口并启动截图线程，如果失败则延迟重试"""
        hwnd = Fishing_Core.find_hwnd_by_process("HTGame.exe")
        if hwnd is None:
            # 未找到窗口，1秒后重试
            QTimer.singleShot(1000, self._try_start_capture)
            return

        # 找到窗口，创建截图线程
        if self.capture_worker is not None:
            # 如果已存在先停止
            self.capture_worker.stop()
            self.capture_worker.join(0.5)

        def on_frame_received(frame):
            self.preview_signal.emit(frame.copy())

        self.capture_worker = BackgroundCaptureThread(
            hwnd, capture_client=True, interval=0.05,
            frame_callback=on_frame_received
        )
        self.capture_worker.start()
        print("✅ 游戏画面预览已启动")

    # ======================
    # 开始钓鱼
    # ======================
    def start_fishing(self):
        if self.thread_state == "RUNNING":
            # 🔥 用 InfoBar 提示
            InfoBar.warning(
                title="提示",
                content="钓鱼已在运行中",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return
        self.thread_state = "RUNNING"

        # 获取 UI 参数
        selected_bait = self.bait_combobox.currentText()
        auto_buy = self.auto_fish_switch.isChecked()
        auto_sell = self.sell_fish_switch.isChecked()
        buy_count_text = self.buy_count_input.text().strip()
        sell_count_text = self.sell_count_input.text().strip()
        max_times_text = self.input_count.text().strip()

        # 参数校验
        if not max_times_text.isdigit() or int(max_times_text) < 1:
            # 🔥 用 InfoBar 显示错误
            InfoBar.error(
                title="输入错误",
                content="钓鱼次数必须为大于0的整数！",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            self.thread_state = "IDLE"
            return

        if buy_count_text and (not buy_count_text.isdigit() or int(buy_count_text) < 1):
            # 🔥 用 InfoBar 显示错误
            InfoBar.error(
                title="输入错误",
                content="购买数量上限必须为大于0的整数！",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            self.thread_state = "IDLE"
            return

        if sell_count_text and (not sell_count_text.isdigit() or int(sell_count_text) < 1):
            # 🔥 用 InfoBar 显示错误
            InfoBar.error(
                title="输入错误",
                content="卖鱼阈值上限必须为大于0的整数！",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            self.thread_state = "IDLE"
            return


        buy_bait_count = int(buy_count_text) if buy_count_text else 0
        sell_fish_count = int(sell_count_text) if sell_count_text  else 50
        times = int(max_times_text)

        # 更新按钮状态
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.input_count.setReadOnly(True)
        self.buy_count_input.setReadOnly(True)
        self.sell_count_input.setReadOnly(True)
        self.log.clear()

        # 打印启动信息
        b5 = self.black_fish5.isChecked()
        b6 = self.black_fish6.isChecked()
        b9 = self.black_fish9.isChecked()
        print(f"🎯 启动钓鱼，次数：{times}")
        print(f"🚫 绿鱼:{b5} | 蓝鱼:{b6} | 紫鱼:{b9}")
        print(f"🎣 鱼饵：{selected_bait} | 每次{buy_bait_count}个 | 自动购买：{auto_buy}")

        def on_frame_received(frame):
            self.preview_signal.emit(frame.copy())

        # 建立截图线程实例
        hwnd = Fishing_Core.find_hwnd_by_process("HTGame.exe")

        if self.capture_worker is None or not self.capture_worker.is_alive():
            self._try_start_capture()
            for _ in range(5):
                if self.capture_worker and self.capture_worker.is_alive():
                    break
                time.sleep(0.1)
            else:
                InfoBar.error(title="错误", content="无法启动画面预览，请确认游戏已运行", parent=self)
                return

        def on_template_check(template_name):
            self.current_template_signal.emit(template_name)


        # 初始化核心逻辑
        self.fishing_bot = Fishing_Core.FishingBot(
            capture_worker=self.capture_worker,
            on_finished=self.on_fishing_finished,
            template_callback=on_template_check
        )
        self.fishing_bot.daemon = True
        self.fishing_bot.fishing_times = 0
        self.fishing_bot.sell_times = sell_fish_count
        self.fishing_bot.remaining_bait_count = buy_bait_count
        self.fishing_bot.selected_bait = selected_bait
        self.fishing_bot.max_times = times
        self.fishing_bot.black_fish5 = b5
        self.fishing_bot.black_fish6 = b6
        self.fishing_bot.black_fish9 = b9
        self.fishing_bot.auto_buy_check = auto_buy
        self.fishing_bot.auto_sell_check = auto_sell
        self.fishing_bot.stop_flag = True




        # 直接启动 FishingBot 线程
        self.fishing_bot.start()

    # ======================
    # 停止钓鱼
    # ======================
    def stop_fishing(self):
        pyautogui.keyUp("a")
        pyautogui.keyUp("d")
        if hasattr(self, "fishing_bot") and self.fishing_bot:
            self.fishing_bot.stop()
        self.thread_state = "IDLE"
        self.input_count.setReadOnly(False)
        self.buy_count_input.setReadOnly(False)
        self.sell_count_input.setReadOnly(False)
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)

    def closeEvent(self, event):
        if hasattr(self, "fishing_bot") and self.fishing_bot:
            self.fishing_bot.stop()
            self.fishing_bot.join(2.0)
        if hasattr(self, "capture_worker") and self.capture_worker:
            self.capture_worker.stop()
            self.capture_worker.join(1.0)
        sys.stdout = sys.__stdout__
        super().closeEvent(event)

    # ======================
    # 回传同步信号
    # ======================
    def on_fishing_finished(self):
        QMetaObject.invokeMethod(self, "reset_ui_after_fishing", Qt.ConnectionType.QueuedConnection)

    @pyqtSlot()
    def reset_ui_after_fishing(self):
        if self.thread_state == "RUNNING":
            self.stop_fishing()

    @pyqtSlot(str)
    def on_current_template_changed(self, template_name):
        self.current_template = template_name

    @pyqtSlot(np.ndarray)
    def update_preview(self, frame):
        if frame is None:
            return

        # 只绘制当前正在匹配的模板区域
        if hasattr(self, 'current_template') and self.current_template:
            name = self.current_template
            area = Screenshot_Area.get(name)
            if area and not (area["width"] == 1280 and area["height"] == 720):
                x, y, w, h = area["left"], area["top"], area["width"], area["height"]
                if w > 0 and h > 0:
                    # 黄色粗框高亮
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 255), 3)
                    cv2.putText(frame, name, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

        # 转换格式并显示
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qt_img = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_img)
        self.preview_label.setPixmap(pixmap.scaled(self.preview_label.size(), Qt.AspectRatioMode.KeepAspectRatio))

    # ======================
    # 日志输出
    # ======================
    def _append_log(self, msg):
        pass

    # ======================
    # 鱼饵预览图更新
    # ======================
    def _on_bait_changed(self, index):
        bait_name = self.bait_list[index]
        img_path = resource_path(f"image/bait/{bait_name}.png")
        self.bait_preview.setImage(img_path)

