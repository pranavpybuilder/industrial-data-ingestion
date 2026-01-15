"""
Main desktop application entry point.

Responsibilities:
- Create and manage the application window
- Load the frontend renderer
- Register the Qt WebChannel bridge

No business logic is allowed here.
"""

import sys
from pathlib import Path

# --- Ensure project root is on sys.path ---
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import QUrl
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebChannel import QWebChannel

from frontend.electron_app.main.preload import frontend_api


class FrontendMainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("Offline Industrial Data Intelligence System")
        self.setMinimumSize(1200, 800)

        self._init_web_view()

    def _init_web_view(self) -> None:
        web_view = QWebEngineView(self)

        channel = QWebChannel(web_view.page())
        channel.registerObject("frontendAPI", frontend_api)
        web_view.page().setWebChannel(channel)

        frontend_index_path = (
            PROJECT_ROOT
            / "frontend"
            / "electron_app"
            / "renderer"
            / "build"
            / "index.html"
        )

        if frontend_index_path.exists():
            web_view.setUrl(QUrl.fromLocalFile(str(frontend_index_path)))
        else:
            web_view.setHtml(
                """
                <html>
                  <head>
                    <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
                    <script>
                      document.addEventListener("DOMContentLoaded", function () {
                        new QWebChannel(qt.webChannelTransport, function (channel) {
                          window.frontendAPI = channel.objects.frontendAPI;
                          console.log(
                            "Runs:",
                            window.frontendAPI.get_runs()
                          );
                        });
                      });
                    </script>
                  </head>
                  <body>
                    <h2 style="text-align:center;margin-top:20%;">
                      Desktop shell & bridge are operational.<br/>
                      Frontend API is live.
                    </h2>
                  </body>
                </html>
                """
            )

        self.setCentralWidget(web_view)


def main() -> None:
    app = QApplication(sys.argv)

    window = FrontendMainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()