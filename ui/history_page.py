import shutil

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QListWidget,
    QMessageBox,
    QHBoxLayout
)

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices

from modules.history_manager import get_analysis_sessions


class HistoryPage(QWidget):

    def __init__(self, on_back):
        super().__init__()

        self.on_back = on_back

        layout = QVBoxLayout()

        title = QLabel("ANALYSIS HISTORY")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setObjectName("PageTitle")

        self.session_list = QListWidget()

        btn_refresh = QPushButton("Refresh")
        btn_open = QPushButton("Open Folder")
        btn_delete = QPushButton("Delete Session")
        btn_back = QPushButton("Back")

        btn_refresh.clicked.connect(self.load_sessions)
        btn_open.clicked.connect(self.open_selected_folder)
        btn_delete.clicked.connect(self.delete_selected_session)
        btn_back.clicked.connect(self.on_back)

        button_layout = QHBoxLayout()

        button_layout.addWidget(btn_refresh)
        button_layout.addWidget(btn_open)
        button_layout.addWidget(btn_delete)
        button_layout.addWidget(btn_back)

        layout.addWidget(title)
        layout.addWidget(self.session_list)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        self.sessions = []

        self.apply_styles()
        self.load_sessions()

    def load_sessions(self):
        self.session_list.clear()

        self.sessions = get_analysis_sessions()

        if not self.sessions:
            self.session_list.addItem("No analysis sessions found.")
            return

        for session in self.sessions:
            text = (
                f"{session['sport']} | "
                f"{session['exercise']} | "
                f"{session.get('camera_view', 'N/A')} | "
                f"{session['session']}"
            )

            self.session_list.addItem(text)

    def open_selected_folder(self):
        row = self.session_list.currentRow()

        if row < 0 or row >= len(self.sessions):
            return

        session = self.sessions[row]

        QDesktopServices.openUrl(
            QUrl.fromLocalFile(session["path"])
        )

    def delete_selected_session(self):
        row = self.session_list.currentRow()

        if row < 0 or row >= len(self.sessions):
            return

        session = self.sessions[row]

        reply = QMessageBox.question(
            self,
            "Delete Session",
            f"Delete session?\n\n{session['session']}"
        )

        if reply == QMessageBox.StandardButton.Yes:
            shutil.rmtree(session["path"])
            self.load_sessions()

    def apply_styles(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #101820;
                color: white;
                font-family: Segoe UI;
                font-size: 15px;
            }

            QLabel#PageTitle {
                font-size: 28px;
                font-weight: bold;
                color: #00D4FF;
                margin: 20px;
            }

            QListWidget {
                background-color: #1E2A35;
                color: white;
                border: 1px solid #0078D7;
                border-radius: 8px;
                padding: 8px;
            }

            QPushButton {
                background-color: #0078D7;
                color: white;
                border-radius: 8px;
                padding: 12px;
                font-size: 15px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #0099FF;
            }
        """)