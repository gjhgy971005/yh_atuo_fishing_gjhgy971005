import traceback
import cv2
import pytesseract
import numpy as np

import BackgroundInput as bi
from utils import resource_path


# ==============================================
# OCR 配置
# ==============================================

pytesseract.pytesseract.tesseract_cmd = resource_path("tesseract/tesseract.exe")

OCR_CONFIG = r'--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789/'

# ==============================================
# 初始化图片路径
# ==============================================
# 图片模板路径
TEMPLATE_PATH = {
    "进入钓鱼": resource_path("image/进入钓鱼.png"),
    "开始钓鱼按钮": resource_path("image/开始钓鱼按钮.png"),
    "缺鱼饵提示": resource_path("image/需要装备钓饵才可以钓鱼.png"),
    "上钩": resource_path("image/上钩.png"),
    "结算继续": resource_path("image/点击空白区域关闭.png"),
    "结算继续2": resource_path("image/钓鱼等级.png"),
    "更换鱼饵": resource_path("image/更换鱼饵.png"),
    "更换": resource_path("image/更换.png"),
    "购买": resource_path("image/购买.png"),
    "商店购买": resource_path("image/商店购买.png"),
    "鱼库": resource_path("image/鱼库.png"),
    "异饵确认": resource_path("image/异饵确认.png"),
    "选饵点重": resource_path("image/选饵点重.png"),
    "渔具商店": resource_path("image/渔具商店.png"),
    "脱钩":resource_path("image/脱钩.png"),
    "抛钩按钮": resource_path("image/抛钩按钮.png"),

    "万能鱼饵": resource_path("image/shop/万能鱼饵.png"),
    "杂谷饵": resource_path("image/shop/杂谷饵.png"),
    "果渍饵": resource_path("image/shop/果渍饵.png"),
    "虾籽饵": resource_path("image/shop/虾籽饵.png"),
    "鲜腴饵": resource_path("image/shop/鲜腴饵.png"),
    "蠕须饵": resource_path("image/shop/蠕须饵.png"),
    "酒糟饵": resource_path("image/shop/酒糟饵.png"),
    "甜麦饵": resource_path("image/shop/甜麦饵.png"),
    "螺腥饵": resource_path("image/shop/螺腥饵.png"),
    "连竿饵": resource_path("image/shop/连竿饵.png"),
    "诱食饵": resource_path("image/shop/诱食饵.png"),
}



# 截图范围
Screenshot_Area = {
    "进入钓鱼": {"left": 760, "top": 370, "width": 100, "height": 40},
    "开始钓鱼按钮": {"left": 900,"top": 590, "width": 350, "height": 70},
    "缺鱼饵提示": {"left": 400,"top": 330, "width": 560, "height": 60},
    "结算继续": {"left": 400,"top": 580, "width": 450, "height": 100},
    "结算继续2": {"left": 450,"top": 60, "width": 130, "height": 50},
    "更换鱼饵": {"left": 540,"top": 220, "width": 220, "height": 60},
    "更换": {"left": 670,"top": 450, "width": 220, "height": 45},
    "购买": {"left": 670,"top": 450, "width": 220, "height": 45},
    "商店购买": {"left": 900,"top": 665, "width": 350, "height": 45},
    "钓鱼体力": {"left": 331,"top": 105, "width": 45, "height": 20},
    "滑块": {"left": 410,"top": 45, "width": 465, "height": 10},
    "上钩": {"left": 460,"top": 155, "width": 390, "height": 40},
    "鱼库": {"left": 160,"top": 160, "width": 140, "height": 40},
    "异饵确认": {"left": 780,"top": 300, "width": 185, "height": 80},
    "选饵点重": {"left": 540,"top": 120, "width": 50, "height": 40},
    "渔具商店": {"left": 30,"top": 15, "width": 160, "height": 45},
    "脱钩": {"left": 0,"top": 0, "width": 1280, "height": 720},
    "抛钩按钮": {"left": 830, "top": 580, "width": 450, "height": 140},
}

# Screenshot_Area = {
#     "进入钓鱼": {"left": 760, "top": 370, "width": 100, "height": 40},
#     "开始钓鱼按钮": {"left": 0,"top": 0, "width": 1280, "height": 720},
#     "缺鱼饵提示": {"left": 0,"top": 0, "width": 1280, "height": 720},
#     "结算继续": {"left": 0,"top": 0, "width": 1280, "height": 720},
#     "选择鱼饵": {"left": 0,"top": 0, "width": 1280, "height": 720},
#     "更换": {"left": 0,"top": 0, "width": 1280, "height": 720},
#     "购买": {"left": 0,"top": 0, "width": 1280, "height": 720},
#     "商店购买": {"left": 0,"top": 0, "width": 1280, "height": 720},
#     "钓鱼体力": {"left": 0,"top": 0, "width": 1280, "height": 720},
#     "滑块": {"left": 410,"top": 45, "width": 465, "height": 10},  #重要
#     "上钩": {"left": 0,"top": 0, "width": 1280, "height": 720},
#     "鱼库": {"left": 0,"top": 0, "width": 1280, "height": 720},
#     "异饵确认": {"left": 0,"top": 0, "width": 1280, "height": 720},
#     "选饵点重": {"left": 0,"top": 0, "width": 1280, "height": 720},
#     "渔具商店": {"left": 0,"top": 0, "width": 1280, "height": 720},
#     "脱钩": {"left": 0,"top": 0, "width": 1280, "height": 720},
#     "卡位检测": {"left": 830, "top": 580, "width": 450, "height": 140},
# }

# ==============================================
# 图片加载函数
# ==============================================
def image_color(img_path):
    try:
        img = cv2.imdecode(np.fromfile(img_path, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
        if img is None: return None
        if len(img.shape) == 3 and img.shape[2] == 4:
            img = img[..., :3]
        return img
    except:
        return None

# ==============================================
# 类- 图像处理模块
# ==============================================
class TemplateMatcher:
    # 初始化函数
    def __init__(self,screenshots_sent):
        # 群组/字典类
        self.TEMPLATE_CACHE = {}
        # 预加载函数
        self._preload_all_templates()
        # 定义锚点
        self.screenshot = screenshots_sent


    # 预加载模板图片函数
    def _preload_all_templates(self):
        for name, path in TEMPLATE_PATH.items():
            try:
                gray = image_color(path)
                if gray is not None:
                    self.TEMPLATE_CACHE[name] = gray
            except:
                pass

    # 模板匹配函数
    def check_template(self, template_name, threshold=0.7):

        # 字典中提取模板
        template_gray = self.TEMPLATE_CACHE.get(template_name)

        if template_gray is None:
            print(f"❌ 模板{template_name}不存在")
            return False, None

        frame = self.screenshot.get_latest_frame()
        if frame is None:
            return False, None

        # 判断是否有截图限位
        if template_name in Screenshot_Area:
            area = Screenshot_Area.get(template_name)

            crop = frame[
                area["top"]:area["top"] + area["height"],
                area["left"]:area["left"] + area["width"]
            ]
        else:
            crop = frame

        # 4. 匹配逻辑
        try:
            results = cv2.matchTemplate(crop, template_gray, cv2.TM_CCOEFF_NORMED)
            locations = np.where(results >= threshold)

            h, w = template_gray.shape[:2]

            # 坐标计算，返回 状态，坐标
            if len(locations[0]) > 0:
                y_pos = locations[0][0]
                x_pos = locations[1][0]
                center_x = x_pos + w // 2
                center_y = y_pos + h // 2
                return True, (center_x, center_y)

            return False, None

        except Exception as e:
            print(f"❌ {template_name}匹配失败：{str(e)}")
            traceback.print_exc()
            return False, None

# ==============================================
# 类 - OCR处理模块（检查鱼体力等级）
# ==============================================
class CheckFishLevel:
    def __init__(self,screenshots_sent,fishing_bot_ref):
        self.screenshot = screenshots_sent
        self.fishing_bot = fishing_bot_ref

    def _get_frame(self):

        frame = self.screenshot.get_latest_frame()

        if frame is None:
            return None
        area = Screenshot_Area["钓鱼体力"]
        return frame[
            area["top"]:area["top"] + area["height"],
            area["left"]:area["left"] + area["width"]
        ]

    def _color_template(self):
        try:
            fish_ocr_text = pytesseract.image_to_string(self.fish_ocr_frame, config=OCR_CONFIG).strip()
            if not fish_ocr_text:
                print("⚠️ OCR 彩图未识别到鱼的体力,重新尝试")
                return None
            else:
                print(f"🎯 OCR彩色识别到鱼的体力：{fish_ocr_text}")
                results = self._judgment_result(fish_ocr_text)
                return results
        except Exception as e:
            print(f"⚠️ OCR彩色识别出错: {e}")
            return False

    def _gray_template(self):
        try:
            fish_ocr_gray = cv2.cvtColor(self.fish_ocr_frame, cv2.COLOR_BGR2GRAY)
            fish_ocr_gray = cv2.GaussianBlur(fish_ocr_gray, (3, 3), 0)
            fish_ocr_gray = cv2.resize(fish_ocr_gray, None, 1.5, 1.5, cv2.INTER_CUBIC)
            fish_ocr_binary = cv2.adaptiveThreshold(fish_ocr_gray, 255,
                                                        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                                        cv2.THRESH_BINARY_INV, 11, 2)
            fish_ocr_text = pytesseract.image_to_string(fish_ocr_binary, config=OCR_CONFIG).strip()
            if not fish_ocr_text:
                print("⚠️ OCR 黑白图未识别到鱼的体力，正常钓鱼")
                return False
            else:
                print(f"🎯 OCR黑白识别到鱼的体力：{fish_ocr_text}")
                results = self._judgment_result(fish_ocr_text)
                return results
        except Exception as e:
            print(f"⚠️ OCR黑白识别出错: {e}")
            return False

    def _judgment_result(self,results):
        if self.fishing_bot.black_fish5 and "15" not in results and "5" in results:
            return True
        if self.fishing_bot.black_fish6 and "6" in results:
            return True
        if self.fishing_bot.black_fish9 and "9" in results:
            return True
        return False

    def check_fish_level(self,stop_flag):
        if not stop_flag:
            return False

        if self.fishing_bot.black_fish5 or self.fishing_bot.black_fish6 or self.fishing_bot.black_fish9:
            results_gray = None
            print("🧐 我要验鱼！(f♂a国口音)")
            self.fish_ocr_frame = self._get_frame()

            results_color = self._color_template()
            results_gray = self._gray_template()

            if results_gray or results_color:
                bi.press("esc",self.fishing_bot.game_hwnd)
                print("💢 鱼有大问题，撤退！！！")
                print("-------------------------------------------------")
                return True
            else:
                print("✅ 鱼没有问题，开钓~~~")
                return False
        print("🧐 今天不验鱼，给我擦皮鞋！(f♂a国口音)")
        return False


class CheckSlider:
    def __init__(self,screenshots_sent):
        self.area = {"left": 400, "top": 45, "width": 480, "height": 10}
        # 滑条颜色范围
        self.yellow_low = np.array([15, 80, 150], dtype=np.uint8)
        self.yellow_high = np.array([35, 255, 255], dtype=np.uint8)
        self.blue_low = np.array([75, 170, 120], dtype=np.uint8)
        self.blue_high = np.array([110, 255, 255], dtype=np.uint8)
        self.red_low1 = np.array([0, 50, 100], dtype=np.uint8)
        self.red_high1 = np.array([10, 255, 255], dtype=np.uint8)
        self.red_low2 = np.array([160, 50, 100], dtype=np.uint8)
        self.red_high2 = np.array([180, 255, 255], dtype=np.uint8)

        self.screenshot = screenshots_sent

    def find_slider(self):
        frame = self.screenshot.get_latest_frame()
        if frame is None:
            return None

        crop = frame[
            self.area["top"]:self.area["top"] + self.area["height"],
            self.area["left"]:self.area["left"] + self.area["width"]
        ]

        # 抑制随机噪点
        # crop = cv2.GaussianBlur(crop, (3, 3), 0)

        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)

        # 红色掩码
        mask_red1 = cv2.inRange(hsv, self.red_low1, self.red_high1)
        mask_red2 = cv2.inRange(hsv, self.red_low2, self.red_high2)
        mask_red = cv2.bitwise_or(mask_red1, mask_red2)

        # 掩码排除红色
        mask_yellow = cv2.inRange(hsv, self.yellow_low, self.yellow_high)
        mask_blue = cv2.inRange(hsv, self.blue_low, self.blue_high)
        mask_yellow = cv2.bitwise_and(mask_yellow, cv2.bitwise_not(mask_red))
        mask_blue = cv2.bitwise_and(mask_blue, cv2.bitwise_not(mask_red))

        # 去噪优化
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))

        # 开运算去掉小噪点
        mask_yellow = cv2.morphologyEx(mask_yellow, cv2.MORPH_CLOSE, kernel_close)
        mask_blue = cv2.morphologyEx(mask_blue, cv2.MORPH_OPEN, kernel, iterations=1)

        # 连通域面积过滤
        mask_yellow = self.filter_small_blobs(mask_yellow, min_area=20)
        mask_blue = self.filter_small_blobs(mask_blue, min_area=100)

        y_points = np.where(mask_yellow > 0)
        b_points = np.where(mask_blue > 0)
        return y_points, b_points

    # 可把这个辅助方法加到类里
    @staticmethod
    def filter_small_blobs(mask, min_area=100):
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
        filtered = np.zeros_like(mask)
        for i in range(1, num_labels):
            if stats[i, cv2.CC_STAT_AREA] >= min_area:
                filtered[labels == i] = 255
        return filtered