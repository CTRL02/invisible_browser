import sys
import os
import ctypes
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile
from PyQt5.QtCore import QUrl, QTimer, Qt

os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu"

WDA_EXCLUDEFROMCAPTURE = 0x00000011

user32 = ctypes.WinDLL('user32', use_last_error=True)

def set_display_affinity(hwnd):
    result = user32.SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)
    if result == 0:
        error_code = ctypes.get_last_error()
        print(f"Failed to set display affinity. Error code: {error_code}")
    else:
        print("Display affinity set successfully.")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Enhanced Browser Window Example")
        self.resize(1280, 800)
        
        self.browser = QWebEngineView(self)
        self.setCentralWidget(self.browser)
        
        settings = self.browser.settings()
        settings.setAttribute(settings.JavascriptEnabled, True)
        settings.setAttribute(settings.PluginsEnabled, True)
        settings.setAttribute(settings.AutoLoadImages, True)
        
        self.browser.load(QUrl("https://google.com/"))
        # comment this if you want window to appear
        # QTimer.singleShot(2000, self.apply_affinity)
    
    def apply_affinity(self):
        hwnd = int(self.winId())
        print(f"Main window handle: {hwnd}")
        set_display_affinity(hwnd)

def main():
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
