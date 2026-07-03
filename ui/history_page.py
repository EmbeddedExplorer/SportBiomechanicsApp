import shutil
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QListWidget,
    QMessageBox,
    QHBoxLayout,
    QTextEdit
)

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices

from modules.history_manager import get_analysis_sessions


class HistoryPage(QWidget):

    def __init__(self, on_back, on_open_results):
        super().__init__()

        self.on_back = on_back
        self.on_open_results = on_open_results

        self.sessions = []

        layout = QVBoxLayout()
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

        title = QLabel("ANALYSIS HISTORY")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setObjectName("PageTitle")

        self.session_list = QListWidget()
        self.session_list.currentRowChanged.connect(self.update_session_details)
        self.session_list.itemDoubleClicked.connect(self.open_selected_in_dashboard)

        self.details_box = QTextEdit()
        self.details_box.setReadOnly(True)
        self.details_box.setMinimumHeight(145)
        self.details_box.setObjectName("DetailsBox")

        btn_refresh = QPushButton("Refresh")
        btn_open_dashboard = QPushButton("Open in Results Dashboard")
        btn_open_folder = QPushButton("Open Folder")
        btn_delete = QPushButton("Delete Session")
        btn_back = QPushButton("Back")

        btn_refresh.clicked.connect(self.load_sessions)
        btn_open_dashboard.clicked.connect(self.open_selected_in_dashboard)
        btn_open_folder.clicked.connect(self.open_selected_folder)
        btn_delete.clicked.connect(self.delete_selected_session)
        btn_back.clicked.connect(self.on_back)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        button_layout.addWidget(btn_refresh)
        button_layout.addWidget(btn_open_dashboard)
        button_layout.addWidget(btn_open_folder)
        button_layout.addWidget(btn_delete)
        button_layout.addWidget(btn_back)

        layout.addWidget(title)
        layout.addWidget(self.session_list, 1)
        layout.addWidget(QLabel("Selected Session Details:"))
        layout.addWidget(self.details_box)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        self.apply_styles()
        self.load_sessions()

    # ==========================================================
    # SESSION LOADING
    # ==========================================================
    def load_sessions(self):
        self.session_list.clear()
        self.details_box.clear()

        self.sessions = get_analysis_sessions()

        if not self.sessions:
            self.session_list.addItem("No analysis sessions found.")
            self.details_box.setText("No previous analysis sessions were found in the results folder.")
            return

        for session in self.sessions:
            sport = session.get("sport", "N/A")
            exercise = session.get("exercise", "N/A")
            camera_view = session.get("camera_view", "N/A")
            input_mode = session.get("input_mode", "N/A")
            record_count = session.get("record_count", "")
            created_at = session.get("created_at", "")
            session_name = session.get("session", "Unknown Session")

            if record_count:
                samples_text = f"{record_count} samples"
            else:
                samples_text = "samples N/A"

            if created_at:
                date_text = created_at
            else:
                date_text = session_name

            text = (
                f"{sport} | "
                f"{exercise} | "
                f"{camera_view} | "
                f"{input_mode} | "
                f"{samples_text} | "
                f"{date_text}"
            )

            self.session_list.addItem(text)

        self.session_list.setCurrentRow(0)

    def get_selected_session(self):
        row = self.session_list.currentRow()

        if row < 0 or row >= len(self.sessions):
            return None

        return self.sessions[row]

    def update_session_details(self):
        session = self.get_selected_session()

        if not session:
            self.details_box.setText("No valid session selected.")
            return

        sport = session.get("sport", "N/A")
        exercise = session.get("exercise", "N/A")
        camera_view = session.get("camera_view", "N/A")
        input_mode = session.get("input_mode", "N/A")
        source_file = session.get("source_file", "")
        record_count = session.get("record_count", "N/A")
        created_at = session.get("created_at", "N/A")
        session_name = session.get("session", "N/A")
        path = session.get("path", "")

        source_text = source_file if source_file else "Live Source / Not recorded"

        details = (
            f"Sport: {sport}\n"
            f"Exercise: {exercise}\n"
            f"Camera View: {camera_view}\n"
            f"Input Mode: {input_mode}\n"
            f"Recorded Samples: {record_count}\n"
            f"Created At: {created_at}\n"
            f"Session Folder: {session_name}\n"
            f"Source File: {source_text}\n"
            f"Results Path: {path}"
        )

        self.details_box.setText(details)

    # ==========================================================
    # ACTIONS
    # ==========================================================
    def open_selected_in_dashboard(self):
        session = self.get_selected_session()

        if not session:
            QMessageBox.warning(
                self,
                "No Session Selected",
                "Please select a valid analysis session first."
            )
            return

        path = session.get("path", "")

        if not path or not Path(path).exists():
            QMessageBox.warning(
                self,
                "Missing Results Folder",
                "The selected session folder does not exist."
            )
            return

        session_info = {
            "sport": session.get("sport", ""),
            "exercise": session.get("exercise", ""),
            "camera_view": session.get("camera_view", "N/A"),
            "input_mode": session.get("input_mode", "N/A"),
            "source_file": session.get("source_file", ""),
            "record_count": session.get("record_count", 0),

            "results_folder": path,
            "session_path": path,

            # Legacy compatibility keys
            "Sport": session.get("sport", ""),
            "Exercise": session.get("exercise", ""),
            "Camera View": session.get("camera_view", "N/A"),
            "Input Mode": session.get("input_mode", "N/A"),
            "File": session.get("source_file", "") or "Live Source",
            "Results Folder": path,
            "Recorded Samples": str(session.get("record_count", 0))
        }

        self.on_open_results(session_info)

    def open_selected_folder(self):
        session = self.get_selected_session()

        if not session:
            QMessageBox.warning(
                self,
                "No Session Selected",
                "Please select a valid analysis session first."
            )
            return

        path = session.get("path", "")

        if not path or not Path(path).exists():
            QMessageBox.warning(
                self,
                "Missing Results Folder",
                "The selected session folder does not exist."
            )
            return

        QDesktopServices.openUrl(
            QUrl.fromLocalFile(str(Path(path).resolve()))
        )

    def delete_selected_session(self):
        session = self.get_selected_session()

        if not session:
            QMessageBox.warning(
                self,
                "No Session Selected",
                "Please select a valid analysis session first."
            )
            return

        path = session.get("path", "")
        session_name = session.get("session", "Unknown Session")

        if not path or not Path(path).exists():
            QMessageBox.warning(
                self,
                "Missing Results Folder",
                "The selected session folder does not exist."
            )
            self.load_sessions()
            return

        reply = QMessageBox.question(
            self,
            "Delete Session",
            (
                "Are you sure you want to delete this session?\n\n"
                f"{session_name}\n\n"
                "This will delete the CSV files, plots, reports, and metadata for this session."
            )
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                shutil.rmtree(path)
                self.load_sessions()

                QMessageBox.information(
                    self,
                    "Session Deleted",
                    "The selected analysis session was deleted."
                )

            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Delete Failed",
                    f"Could not delete the selected session.\n\nError:\n{e}"
                )

    # ==========================================================
    # STYLES
    # ==========================================================
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
                margin: 12px;
            }

            QListWidget {
                background-color: #1E2A35;
                color: white;
                border: 1px solid #0078D7;
                border-radius: 8px;
                padding: 8px;
            }

            QListWidget::item {
                padding: 8px;
            }

            QListWidget::item:selected {
                background-color: #0078D7;
                color: white;
            }

            QTextEdit#DetailsBox {
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
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #0099FF;
            }

            QPushButton:disabled {
                background-color: #555555;
                color: #AAAAAA;
            }
        """)