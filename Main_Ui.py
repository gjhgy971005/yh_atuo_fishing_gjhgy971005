import sys
import json
import os
from PyQt6.QtWidgets import QApplication, QStackedWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QColor
from qfluentwidgets import (
    NavigationItemPosition, MSFluentWindow, setTheme, Theme, FluentIcon as FIF,
    toggleTheme, FluentIconBase, getIconColor, setFontFamilies, FluentTitleBarButton, setThemeColor
)
from enum import Enum

from pages.page_fishing import FishingWindow
from pages.page_setting import SettingPage
from pages.page_wait import WaitingPage
from pages.page_about import HelpPage
from utils import resource_path

CONFIG_FILE = resource_path("./config.json")

class MyFluentIcon(FluentIconBase, Enum):
    FISHING = "Fishing"
    def path(self, theme=Theme.AUTO):
        icon_file = f"{self.value}_{getIconColor(theme)}.svg"
        return resource_path(f"icons/{icon_file}")

class Window(MSFluentWindow):
    def __init__(self):
        super().__init__()
        setTheme(Theme.DARK)
        self.init_theme_button()
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowMaximizeButtonHint)


        # 获取内容区域控件
        self.content_widget = self._get_content_widget()

        # 创建设置页面并连接信号
        self.settingInterface = SettingPage()
        self.settingInterface.backgroundChanged.connect(self.set_global_background)
        self.settingInterface.themeColorChanged.connect(self.on_theme_color_changed)

        # 创建其他页面
        self.homeInterface = FishingWindow()
        self.waitingInterface = WaitingPage()
        self.aboutInterface = HelpPage()

        self.homeInterface.setObjectName("Home")
        self.waitingInterface.setObjectName("Waiting")
        self.settingInterface.setObjectName("Setting")
        self.aboutInterface.setObjectName("About")

        self.initNavigation()
        self.initWindow()

        # 加载已保存的背景图片
        self._load_background_image()

    def on_theme_color_changed(self, color_hex: str):
        # 重新设置全局主题色
        setThemeColor(QColor(color_hex))

        # 强制刷新主窗口的样式表
        self.style().unpolish(self)
        self.style().polish(self)

        # 刷新内容区域
        if self.content_widget:
            self.content_widget.style().unpolish(self.content_widget)
            self.content_widget.style().polish(self.content_widget)

        # 让当前页面也重新应用
        current_page = self.content_widget.currentWidget()
        if current_page:
            current_page.style().unpolish(current_page)
            current_page.style().polish(current_page)

    def _get_content_widget(self):
        if hasattr(self, 'stackedWidget'):
            return self.stackedWidget
        for child in self.findChildren(QStackedWidget):
            return child
        return None

    def set_global_background(self, image_path: str):
        if not self.content_widget:
            return
        if image_path and os.path.exists(image_path):
            path = image_path.replace("\\", "/")
            style = f"""
            QStackedWidget {{
                background-image: url("{path}");
                background-position: center;
                background-repeat: no-repeat;
                background-size: cover;
            }}
            """
            self.content_widget.setStyleSheet(style)
            self._save_background_path(image_path)
        else:
            self.content_widget.setStyleSheet("")
            self._save_background_path("")

    def _save_background_path(self, path: str):
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            else:
                config = {}
            config["background_image"] = path
            os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"保存背景配置失败: {e}")

    def _load_background_image(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    bg_path = config.get("background_image", "")
                    if bg_path and os.path.exists(bg_path):
                        self.set_global_background(bg_path)
            except Exception as e:
                print(f"加载背景配置失败: {e}")

    def initNavigation(self):
        self.addSubInterface(self.homeInterface, MyFluentIcon.FISHING, '自动钓鱼', selectedIcon=MyFluentIcon.FISHING)
        self.addSubInterface(self.waitingInterface, FIF.ADD_TO, '保留页')
        self.addSubInterface(self.settingInterface, FIF.SETTING, '设置',
                             selectedIcon=FIF.SETTING, position=NavigationItemPosition.BOTTOM)
        self.addSubInterface(self.aboutInterface, FIF.HELP, '关于/帮助',
                             selectedIcon=FIF.HELP, position=NavigationItemPosition.BOTTOM)

    def init_theme_button(self):
        self.themeBtn = FluentTitleBarButton(FIF.CONSTRACT)
        self.themeBtn.clicked.connect(toggleTheme)
        self.titleBar.buttonLayout.insertWidget(0, self.themeBtn)

    def initWindow(self):
        self.setFixedSize(1100, 619)
        self.setWindowIcon(QIcon(resource_path('icons/logo.ico')))
        self.setWindowTitle('v-5.13 有问题加群：531673719 猛戳丢人群主')
        self.titleBar.maxBtn.hide()
        self.titleBar.mouseDoubleClickEvent = lambda e: None


if __name__ == '__main__':
    app = QApplication(sys.argv)
    setFontFamilies([
        "Microsoft YaHei",
        "DengXian Light",
        "SimHei",
        "Arial"
    ])
    w = Window()
    w.show()
    sys.exit(app.exec())
