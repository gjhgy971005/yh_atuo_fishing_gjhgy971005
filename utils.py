import sys
import os

def resource_path(relative_path):
    if getattr(sys, 'frozen', False):
        # Nuitka standalone 打包后，exe 与 res 文件夹同级
        base = os.path.dirname(sys.executable)
        return os.path.join(base, "_internal", relative_path)
    else:
        # 开发环境
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)