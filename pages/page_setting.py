import json
import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QFileDialog
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt, pyqtSignal
from qfluentwidgets import (
    ColorPickerButton, setThemeColor, ScrollArea, SettingCard,
    FluentIcon as FIF, PushButton, InfoBar
)
from utils import resource_path

CONFIG_FILE = resource_path("./config.json")

class SettingPage(QWidget):
    backgroundChanged = pyqtSignal(str)  # 通知主窗口背景改变
    themeColorChanged = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background: transparent;")
        self._setup_ui()
        self.load_config()

    def _setup_ui(self):
        # 滚动区域
        self.scrollArea = ScrollArea(self)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setStyleSheet("QScrollArea{background:transparent;border:none}")

        self.container = QWidget()
        self.container.setObjectName("SettingContainer")
        self.container.setStyleSheet("#SettingContainer{background:transparent;}")

        self.main_layout = QVBoxLayout(self.container)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)

        # 主题色卡片
        self.color_picker = ColorPickerButton("#0065d5", "选择颜色")
        self.color_picker.setMaximumWidth(150)
        self.color_picker.colorChanged.connect(self.on_color_changed)
        self.theme_card = SettingCard(
            icon=FIF.PALETTE, title="主题色", content="选择应用的全局主题颜色", parent=self
        )
        self.theme_card.hBoxLayout.addWidget(self.color_picker)
        self.theme_card.hBoxLayout.addSpacing(16)

        # 背景图片卡片
        self.bg_card = SettingCard(
            icon=FIF.PHOTO, title="背景图片", content="设置应用背景图片", parent=self
        )
        self.bg_button = PushButton("选择图片")
        self.bg_button.clicked.connect(self.choose_background)
        self.clear_bg_button = PushButton("清除背景")
        self.clear_bg_button.clicked.connect(self.clear_background)

        self.bg_card.hBoxLayout.addStretch(1)
        self.bg_card.hBoxLayout.addWidget(self.bg_button)
        self.bg_card.hBoxLayout.addSpacing(10)
        self.bg_card.hBoxLayout.addWidget(self.clear_bg_button)
        self.bg_card.hBoxLayout.addSpacing(16)

        self.main_layout.addWidget(self.theme_card)
        self.main_layout.addWidget(self.bg_card)
        self.main_layout.addStretch()

        self.scrollArea.setWidget(self.container)
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.addWidget(self.scrollArea)

    def on_color_changed(self, color: QColor):
        setThemeColor(color)
        self.themeColorChanged.emit(color.name())  # 向外发送信号
        self.save_config()

    def choose_background(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择背景图片", "", "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        if not path:
            return
        abs_path = os.path.abspath(path)
        self.backgroundChanged.emit(abs_path)
        InfoBar.success(
            title="背景已设置",
            content="背景图片已应用",
            parent=self,
            duration=2000
        )

    def clear_background(self):
        self.backgroundChanged.emit("")
        InfoBar.success(
            title="背景已清除",
            content="已恢复默认背景",
            parent=self,
            duration=2000
        )

    def load_config(self):
        if not os.path.exists(CONFIG_FILE):
            self.save_config()
            return
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                theme_color = config.get("theme_color", "#0065d5")
                setThemeColor(theme_color)
                self.color_picker.setColor(QColor(theme_color))
        except Exception as e:
            print(f"加载配置失败: {e}")

    def save_config(self):
        try:
            config = {
                "theme_color": self.color_picker.color.name(),
            }
            os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"保存配置失败: {e}")

    def on_color_changed(self, color: QColor):
        setThemeColor(color)
        self.save_config()