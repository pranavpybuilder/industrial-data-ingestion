"""
Main desktop application entry point.
Fully offline.
Production ready.
Bridge injected at document creation.

Renderer path resolution:
  - Development:   PROJECT_ROOT / frontend / electron_app / renderer / dist / index.html
  - Frozen (NSIS): sys._MEIPASS / renderer / dist / index.html
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


def get_renderer_path() -> Path:
    """
    Resolves renderer index.html for both dev and PyInstaller frozen modes.

    Development mode:
        Uses PROJECT_ROOT to find the renderer dist directory.

    Frozen mode (PyInstaller / NSIS install):
        Files are bundled inside sys._MEIPASS by PyInstaller.
        The .spec file must include renderer/dist/ as data files:
          datas=[('frontend/electron_app/renderer/dist', 'renderer/dist')]
    """
    if getattr(sys, "frozen", False):
        # Frozen by PyInstaller — files are in sys._MEIPASS
        base = Path(sys._MEIPASS)
    else:
        # Development mode — navigate from main.py up to electron_app
        base = Path(__file__).resolve().parent.parent

    path = base / "renderer" / "dist" / "index.html"
    if not path.exists():
        raise FileNotFoundError(
            f"Renderer not built. Expected: {path}\n"
            f"Run: cd frontend/electron_app/renderer && npm run build"
        )
    return path


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
        # Load frontend — supports both dev and frozen modes
        # -------------------------------------------------
        try:
            frontend_index_path = get_renderer_path()
            print(f"Loading frontend from: {frontend_index_path}")
            self.web_view.setUrl(QUrl.fromLocalFile(str(frontend_index_path)))
        except FileNotFoundError as e:
            error_html = f"""
            <html>
            <head><style>
                body {{ font-family: 'Segoe UI', sans-serif; background: #0f172a; color: #e2e8f0;
                       display: flex; align-items: center; justify-content: center; height: 100vh;
                       margin: 0; }}
                .card {{ background: #1e293b; border-radius: 16px; padding: 40px; max-width: 600px;
                         border: 1px solid #334155; box-shadow: 0 8px 32px rgba(0,0,0,0.4); }}
                h1 {{ color: #f87171; margin-top: 0; font-size: 22px; }}
                p {{ line-height: 1.6; color: #94a3b8; }}
                code {{ background: #334155; padding: 4px 8px; border-radius: 6px; font-size: 13px;
                        color: #a5b4fc; display: block; margin: 12px 0; padding: 12px; }}
            </style></head>
            <body>
                <div class="card">
                    <h1>⚠ Frontend Not Built</h1>
                    <p>{str(e).replace(chr(10), '<br>')}</p>
                    <p>To fix this, run the following commands:</p>
                    <code>cd frontend/electron_app/renderer<br>npm install<br>npm run build</code>
                    <p>Then restart the application.</p>
                </div>
            </body>
            </html>
            """
            self.web_view.setHtml(error_html)

        self.setCentralWidget(self.web_view)


def main() -> None:
    try:
        initialize_database()
    except ModuleNotFoundError as exc:
        print(str(exc))
        raise SystemExit(1) from exc

    app = QApplication(sys.argv)
    window = FrontendMainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
