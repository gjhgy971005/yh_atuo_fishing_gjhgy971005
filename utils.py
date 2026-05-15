import sys
import os

def resource_path(relative_path):
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
        return os.path.join(base, "_internal", relative_path)
    else:
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)
