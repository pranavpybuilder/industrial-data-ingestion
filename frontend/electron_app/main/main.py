"""
Main desktop application entry point.
Fully offline.
Production ready.
Bridge injected at document creation.
"""

import sys
from pathlib import Path

# -----------------------------------------------------
# Ensure project root is on sys.path
# -----------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from storage.connection import initialize_database
from frontend.electron_app.main.preload import frontend_api

from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import QUrl
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineScript
from PySide6.QtWebChannel import QWebChannel


class FrontendMainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("Offline Industrial Data Intelligence System")
        self.setMinimumSize(1200, 800)

        self._init_web_view()

    def _init_web_view(self) -> None:
        self.web_view = QWebEngineView(self)

        # -------------------------------------------------
        # Create WebChannel
        # -------------------------------------------------
        self.channel = QWebChannel(self.web_view.page())
        self.channel.registerObject("frontendAPI", frontend_api)
        self.web_view.page().setWebChannel(self.channel)

        # -------------------------------------------------
        # Inject qwebchannel.js and bridge BEFORE React loads
        # -------------------------------------------------
        script = QWebEngineScript()
        script.setName("qt_bridge")
        script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentCreation)
        script.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
        script.setRunsOnSubFrames(False)

        # Load qwebchannel.js from PySide6 resources
        try:
            from PySide6.QtCore import QFile, QIODevice
            qwc_file = QFile(":/qtwebchannel/qwebchannel.js")
            if qwc_file.open(QIODevice.ReadOnly):
                qwc_code = bytes(qwc_file.readAll()).decode("utf-8")
                qwc_file.close()
            else:
                # Fallback: minimal QWebChannel init
                qwc_code = ""
        except Exception:
            qwc_code = ""

        bridge_code = f"""
        {qwc_code}
        (function() {{
            if (typeof qt !== "undefined" && typeof QWebChannel !== "undefined") {{
                new QWebChannel(qt.webChannelTransport, function(channel) {{
                    window.frontendAPI = channel.objects.frontendAPI;
                    console.log("✓ Qt bridge ready (offline mode).");
                    window.dispatchEvent(new Event("qt-ready"));
                }});
            }} else {{
                console.warn("⚠ Qt bridge unavailable - running in reduced mode");
            }}
        }})();
        """

        script.setSourceCode(bridge_code)
        self.web_view.page().scripts().insert(script)

        # -------------------------------------------------
        # Load frontend
        # -------------------------------------------------
        frontend_index_path = (
            PROJECT_ROOT
            / "frontend"
            / "electron_app"
            / "renderer"
            / "dist"
            / "index.html"
        )

        if frontend_index_path.exists():
            print(f"Loading frontend from: {frontend_index_path}")
            self.web_view.setUrl(QUrl.fromLocalFile(str(frontend_index_path)))
        else:
            self.web_view.setHtml("<h1>Frontend build not found</h1>")

        self.setCentralWidget(self.web_view)


def main() -> None:
    initialize_database()

    app = QApplication(sys.argv)
    window = FrontendMainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()