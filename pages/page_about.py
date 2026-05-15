from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget

from qfluentwidgets import (
    ListWidget,
    SmoothScrollArea,
    CardWidget,
    TitleLabel,
    SubtitleLabel,
    BodyLabel, ImageLabel
)

from utils import resource_path

# =========================
# 主帮助页面
# =========================
class HelpPage(QWidget):
    def __init__(self):
        super().__init__()

        self.setObjectName("Help")

        mainLayout = QHBoxLayout(self)
        mainLayout.setContentsMargins(0, 0, 0, 0)

        # =========================
        # 左侧列表
        # =========================
        self.listWidget = ListWidget()
        self.listWidget.setFixedWidth(220)

        # 帮助项
        self.items = [
            ("自动钓鱼", self.page_use),
            ("常见问题", self.page_faq),
            ("功能说明", self.page_feature),
            ("关于软件", self.page_about),
        ]

        for name, _ in self.items:
            self.listWidget.addItem(name)

        # =========================
        # 右侧堆叠
        # =========================
        self.stack = QStackedWidget()

        for _, func in self.items:
            page = func()

            scroll = SmoothScrollArea()
            scroll.setWidget(page)
            scroll.setWidgetResizable(True)
            scroll.setStyleSheet("background: transparent; border: none;")
            scroll.viewport().setStyleSheet("background: transparent;")

            self.stack.addWidget(scroll)

        # =========================
        # 绑定切换
        # =========================
        self.listWidget.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.listWidget.setCurrentRow(0)

        # =========================
        # 布局
        # =========================
        mainLayout.addWidget(self.listWidget)
        mainLayout.addWidget(self.stack)
        mainLayout.setStretch(1, 1)

    # =========================================================
    # 工具函数
    # =========================================================
    def create_base_page(self, title):
        w = QWidget()
        w.setStyleSheet("background: transparent;")

        layout = QVBoxLayout(w)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(15)

        titleLabel = TitleLabel(title)
        layout.addWidget(titleLabel)

        return w, layout

    def add_card(self, layout, subtitle, text=None, image=None):
        card = CardWidget()
        cardLayout = QVBoxLayout(card)

        sub = SubtitleLabel(subtitle)
        cardLayout.addWidget(sub)

        if text:
            body = BodyLabel(text)
            body.setWordWrap(True)
            cardLayout.addWidget(body)

        if image:
            img = ImageLabel(image)
            img.scaledToWidth(500)
            cardLayout.addWidget(img)

        layout.addWidget(card)

    # =========================================================
    # 帮助项
    # =========================================================

    def page_use(self):
        w, layout = self.create_base_page("自动钓鱼")

        self.add_card(
            layout,
            "重要的设置",
            " — 将游戏分辨率改为“1280*720窗口\n — 以管理员权限运行（右键EXE可见）",
            image=resource_path("image/help/setting.png")
        )

        self.add_card(
            layout,
            "后台模式/半后台模式",
            " — 在未开启自动买饵、卖鱼的情况下可纯后台工作\n — 如开启任意一项功能，窗口会在需要时自动呼出，用后隐藏",
            image = resource_path("image/help/setting2.png")
        )

        self.add_card(
            layout,
            "脚本起始点说明",
            " — 这是开始脚本的位置，检测点为“开始钓鱼”按钮",
            image= resource_path("image/help/startpoint.png")
        )

        self.add_card(
            layout,
            "自动切换/购买鱼饵说明",
            " — 按如下图数字顺序修改即可",
            image = resource_path("image/help/buy_bait.png")
        )

        self.add_card(
            layout,
            "自动卖鱼说明",
            " — 按如下图数字顺序修改即可",
            image = resource_path("image/help/sell_fish.png")
        )

        layout.addStretch()
        return w

    def page_faq(self):
        w, layout = self.create_base_page("常见问题")

        self.add_card(
            layout,
            "识别失败",
            "1. 检查分辨率是否正确\n2. 猛戳丢人作者反馈问题"
        )

        self.add_card(
            layout,
            "程序无响应",
            "1. 确认游戏窗口在前台\n2. 尝试管理员运行"
        )

        self.add_card(
            layout,
            "钓鱼结果显示和体力等级不匹配",
            "这是个游戏BUG，在起杆动画中，如果继续按F进入下一杆钓鱼，\n结算界面会显示下一个杆钓起的鱼，而两条鱼都鱼会直接进入仓库",
            image = resource_path("image/help/double_fish.png")
        )

        layout.addStretch()
        return w

    def page_feature(self):
        w, layout = self.create_base_page("功能说明")

        self.add_card(
            layout,
            "核心功能",
            "自动钓鱼 + 自动换饵 + 自动卖鱼"
        )

        layout.addStretch()
        return w

    def page_about(self):
        w, layout = self.create_base_page("关于软件")

        self.add_card(
            layout,
            "信息",
            "作者：想了一个小时取得名字\n版本：1.0"
        )

        layout.addStretch()
        return w