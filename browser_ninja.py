import sys
import os
import ctypes
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QToolBar,
    QLineEdit,
)
from PyQt6.QtGui import QAction, QKeySequence, QShowEvent
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import (
    QWebEnginePage,
    QWebEngineProfile,
    QWebEngineSettings,
    qWebEngineChromiumVersion,
)
from PyQt6.QtCore import QUrl, QTimer, Qt, qVersion

# Qt WebEngine shares one GPU process; without shared GL contexts, Windows often
# hits renderer/GPU crashes on heavy sites. Must be set before QApplication exists.
# Optional Chromium flags (merged with any existing QTWEBENGINE_CHROMIUM_FLAGS).

_CHROMIUM_FLAGS = "--disable-breakpad --js-flags=--max-old-space-size=4096"
if os.environ.get("QTWEBENGINE_CHROMIUM_FLAGS"):
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] += " " + _CHROMIUM_FLAGS
else:
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = _CHROMIUM_FLAGS.strip()

WDA_EXCLUDEFROMCAPTURE = 0x00000011

user32 = ctypes.WinDLL("user32", use_last_error=True)


def _print_webengine_version_hint() -> None:
    print("Embedded engine: Qt %s, Chromium %s" % (qVersion(), qWebEngineChromiumVersion()))


def set_display_affinity(hwnd: int) -> None:
    result = user32.SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)
    if result == 0:
        error_code = ctypes.get_last_error()
        print(f"Failed to set display affinity. Error code: {error_code}")
    else:
        print("Display affinity set successfully.")


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Enhanced Browser Window Example")
        self.resize(1280, 800)

        self._home_url = QUrl("https://www.google.com/")

        self.browser = QWebEngineView(self)
        self.setCentralWidget(self.browser)

        self.browser.page().renderProcessTerminated.connect(
            self._on_render_process_terminated
        )

        settings = self.browser.settings()
        wa = QWebEngineSettings.WebAttribute
        settings.setAttribute(wa.JavascriptEnabled, True)
        settings.setAttribute(wa.JavascriptCanOpenWindows, True)
        settings.setAttribute(wa.PluginsEnabled, False)
        settings.setAttribute(wa.AutoLoadImages, True)
        settings.setAttribute(wa.LocalStorageEnabled, True)
        settings.setAttribute(wa.WebGLEnabled, True)

        self._build_toolbar()

        self.browser.load(self._home_url)
        self.browser.loadFinished.connect(self._on_load_finished)
        self.browser.urlChanged.connect(self._sync_url_bar)
        self.browser.urlChanged.connect(self._update_nav_actions)
        self._update_nav_actions()

    def _build_toolbar(self) -> None:
        toolbar = QToolBar()
        toolbar.setMovable(False)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)

        self._act_back = QAction("Back", self)
        self._act_back.setShortcut(QKeySequence.StandardKey.Back)
        self._act_back.triggered.connect(self.browser.back)
        toolbar.addAction(self._act_back)

        self._act_forward = QAction("Forward", self)
        self._act_forward.setShortcut(QKeySequence.StandardKey.Forward)
        self._act_forward.triggered.connect(self.browser.forward)
        toolbar.addAction(self._act_forward)

        act_reload = QAction("Reload", self)
        act_reload.setShortcut(QKeySequence.StandardKey.Refresh)
        act_reload.triggered.connect(self.browser.reload)
        toolbar.addAction(act_reload)

        act_home = QAction("Home", self)
        act_home.triggered.connect(lambda: self.browser.load(self._home_url))
        toolbar.addAction(act_home)

        self._url_bar = QLineEdit()
        self._url_bar.returnPressed.connect(self._load_from_url_bar)
        toolbar.addWidget(self._url_bar)

        self.browser.loadProgress.connect(self._on_load_progress)

    def _on_load_progress(self, progress: int) -> None:
        self._url_bar.setPlaceholderText(f"Loading… {progress}%" if progress < 100 else "")

    def _sync_url_bar(self, url: QUrl) -> None:
        if self._url_bar.hasFocus():
            return
        self._url_bar.setText(url.toString())

    def _update_nav_actions(self, _url: QUrl | None = None) -> None:
        h = self.browser.history()
        self._act_back.setEnabled(h.canGoBack())
        self._act_forward.setEnabled(h.canGoForward())

    def _load_from_url_bar(self) -> None:
        text = self._url_bar.text().strip()
        if not text:
            return
        self.browser.load(QUrl.fromUserInput(text))

    def _on_render_process_terminated(
        self, status: QWebEnginePage.RenderProcessTerminationStatus, exit_code: int
    ) -> None:
        if status == QWebEnginePage.RenderProcessTerminationStatus.NormalTerminationStatus:
            return
        print(f"Render process ended ({status}, exit {exit_code}); reloading…")
        QTimer.singleShot(300, self.browser.reload)

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        QTimer.singleShot(0, self.apply_affinity)
        QTimer.singleShot(500, self.apply_affinity)

    def _on_load_finished(self, ok: bool) -> None:
        if ok:
            QTimer.singleShot(0, self.apply_affinity)

    def apply_affinity(self) -> None:
        hwnd = int(self.winId())
        print(f"main window handle: {hwnd}")
        set_display_affinity(hwnd)


def main() -> None:
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts, True)

    app = QApplication(sys.argv)
    _print_webengine_version_hint()

    QWebEngineProfile.defaultProfile().setHttpCacheMaximumSize(256 * 1024 * 1024)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
