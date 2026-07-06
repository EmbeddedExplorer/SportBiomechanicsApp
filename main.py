import sys

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QStackedWidget,
    QScrollArea,
    QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

from ui.home_page import HomePage
from ui.weightlifting_page import WeightliftingPage
from ui.sprinting_page import SprintingPage
from ui.results_page import ResultsPage
from ui.history_page import HistoryPage
from ui.about_page import AboutPage

from pathlib import Path

from modules.database_manager import (
    init_database,
    add_session,
    get_recent_sessions,
    get_session_count
)



def resource_path(relative_path):
    """
    Return a resource path that works in both source mode and PyInstaller mode.
    """

    try:
        base_path = Path(sys._MEIPASS)
    except Exception:
        base_path = Path(__file__).resolve().parent

    return base_path / relative_path


def get_app_icon():
    icon_path = resource_path("assets/app_icon.ico")

    if icon_path.exists():
        return QIcon(str(icon_path))

    return QIcon()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        init_database()

        self.setWindowTitle("BioMotion Studio")
        self.setWindowIcon(get_app_icon())
        self.setMinimumSize(1100, 650)

        self.stack = QStackedWidget()

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.scroll_area.setWidget(self.stack)

        self.setCentralWidget(self.scroll_area)

        self.home_page = HomePage(
            on_weightlifting=self.show_weightlifting_page,
            on_sprinting=self.show_sprinting_page,
            on_results=self.show_results_page,
            on_history=self.show_history_page,
            on_about=self.show_about_page,
            on_exit=self.close
        )

        self.weightlifting_page = WeightliftingPage(
            on_back=self.show_home_page,
            on_start_analysis=self.complete_analysis_session
        )

        self.sprinting_page = SprintingPage(
            on_back=self.show_home_page,
            on_start_analysis=self.complete_analysis_session
        )

        self.results_page = ResultsPage(
            on_back_home=self.show_home_page
        )

        self.history_page = HistoryPage(
            on_back=self.show_home_page,
            on_open_results=self.open_history_session_results
        )

        self.about_page = AboutPage(
            on_back=self.show_home_page
        )

        self.stack.addWidget(self.home_page)
        self.stack.addWidget(self.weightlifting_page)
        self.stack.addWidget(self.sprinting_page)
        self.stack.addWidget(self.results_page)
        self.stack.addWidget(self.history_page)
        self.stack.addWidget(self.about_page)

        self.refresh_status_bar()
        self.show_home_page()

    # ==========================================================
    # SYSTEM STATUS
    # ==========================================================
    def get_system_status(self):
        status_parts = []

        try:
            import pyrealsense2 as rs

            devices = rs.context().query_devices()

            try:
                device_count = len(devices)
            except TypeError:
                device_count = devices.size()

            if device_count > 0:
                status_parts.append(f"RealSense: Connected ({device_count} device)")
            else:
                status_parts.append("RealSense: SDK Ready / No Device Connected")

        except Exception:
            status_parts.append("RealSense: Not Ready")

        try:
            import mediapipe
            status_parts.append("MediaPipe: Ready")
        except Exception:
            status_parts.append("MediaPipe: Not Ready")

        try:
            session_count = get_session_count()
            status_parts.append(f"Database: Ready ({session_count} sessions)")
        except Exception:
            status_parts.append("Database: Not Ready")

        return "   |   ".join(status_parts)

    def refresh_status_bar(self):
        self.statusBar().showMessage(self.get_system_status())

    # ==========================================================
    # PAGE NAVIGATION
    # ==========================================================
    def show_home_page(self):
        self.home_page.set_recent_sessions(
            get_recent_sessions(limit=5)
        )

        self.home_page.set_system_status(
            self.get_system_status()
        )

        self.refresh_status_bar()
        self.stack.setCurrentWidget(self.home_page)

    def show_weightlifting_page(self):
        self.refresh_status_bar()
        self.stack.setCurrentWidget(self.weightlifting_page)

    def show_sprinting_page(self):
        self.refresh_status_bar()
        self.stack.setCurrentWidget(self.sprinting_page)

    def show_results_page(self):
        self.results_page.set_summary({
            "sport": "Previous Analysis",
            "exercise": "Not selected",
            "camera_view": "N/A",
            "input_mode": "Not selected",
            "source_file": "",
            "results_folder": "",
            "record_count": 0,

            # Legacy display keys
            "Sport": "Previous Analysis",
            "Exercise": "Not selected",
            "Camera View": "N/A",
            "Input Mode": "Not selected",
            "File": "No file selected",
            "Results Folder": "No folder created yet",
            "Recorded Samples": "0"
        })

        self.refresh_status_bar()
        self.stack.setCurrentWidget(self.results_page)

    def show_history_page(self):
        self.history_page.load_sessions()
        self.refresh_status_bar()
        self.stack.setCurrentWidget(self.history_page)

    def show_about_page(self):
        self.refresh_status_bar()
        self.stack.setCurrentWidget(self.about_page)

    # ==========================================================
    # ANALYSIS COMPLETE
    # ==========================================================
    def complete_analysis_session(self, session_info):
        """
        Called after weightlifting or sprinting analysis is completed.

        Important:
        - Keep enhanced session_info from weightlifting_page.py / sprinting_page.py.
        - Do not shrink it into only old display keys.
        - Add old display keys only for compatibility.
        """

        if session_info is None:
            session_info = {}

        sport = session_info.get("sport", session_info.get("Sport", ""))
        exercise = session_info.get("exercise", session_info.get("Exercise", ""))
        camera_view = session_info.get("camera_view", session_info.get("Camera View", "N/A"))
        input_mode = session_info.get("input_mode", session_info.get("Input Mode", ""))
        source_file = session_info.get("source_file", session_info.get("File", ""))

        results_folder = (
            session_info.get("results_folder")
            or session_info.get("session_path")
            or session_info.get("Results Folder")
            or ""
        )

        record_count = (
            session_info.get("record_count")
            or session_info.get("Recorded Samples")
            or 0
        )

        add_session({
            "sport": sport,
            "exercise": exercise,
            "camera_view": camera_view,
            "input_mode": input_mode,
            "source_file": source_file,
            "results_folder": results_folder
        })

        dashboard_info = dict(session_info)

        # Normalized keys
        dashboard_info["sport"] = sport
        dashboard_info["exercise"] = exercise
        dashboard_info["camera_view"] = camera_view
        dashboard_info["input_mode"] = input_mode
        dashboard_info["source_file"] = source_file
        dashboard_info["results_folder"] = results_folder
        dashboard_info["record_count"] = record_count
        dashboard_info["session_path"] = dashboard_info.get("session_path", results_folder)

        # Legacy compatibility keys
        dashboard_info["Sport"] = sport
        dashboard_info["Exercise"] = exercise
        dashboard_info["Camera View"] = camera_view
        dashboard_info["Input Mode"] = input_mode
        dashboard_info["File"] = source_file if source_file else "Live Source"
        dashboard_info["Results Folder"] = results_folder
        dashboard_info["Recorded Samples"] = str(record_count)

        self.results_page.set_summary(dashboard_info)

        self.refresh_status_bar()
        self.stack.setCurrentWidget(self.results_page)

    # ==========================================================
    # OPEN PREVIOUS HISTORY SESSION
    # ==========================================================
    def open_history_session_results(self, session_info):
        """
        Called from HistoryPage when the user wants to reopen
        a previous analysis session in the Results Dashboard.
        """

        if session_info is None:
            return

        results_folder = (
            session_info.get("results_folder")
            or session_info.get("session_path")
            or session_info.get("path")
            or session_info.get("Results Folder")
            or ""
        )

        sport = session_info.get("sport", session_info.get("Sport", "Previous Analysis"))
        exercise = session_info.get("exercise", session_info.get("Exercise", "N/A"))
        camera_view = session_info.get("camera_view", session_info.get("Camera View", "N/A"))
        input_mode = session_info.get("input_mode", session_info.get("Input Mode", "N/A"))
        source_file = session_info.get("source_file", session_info.get("File", ""))
        record_count = session_info.get("record_count", session_info.get("Recorded Samples", 0))

        dashboard_info = dict(session_info)

        dashboard_info["sport"] = sport
        dashboard_info["exercise"] = exercise
        dashboard_info["camera_view"] = camera_view
        dashboard_info["input_mode"] = input_mode
        dashboard_info["source_file"] = source_file
        dashboard_info["results_folder"] = results_folder
        dashboard_info["session_path"] = results_folder
        dashboard_info["record_count"] = record_count

        dashboard_info["Sport"] = sport
        dashboard_info["Exercise"] = exercise
        dashboard_info["Camera View"] = camera_view
        dashboard_info["Input Mode"] = input_mode
        dashboard_info["File"] = source_file if source_file else "Live Source"
        dashboard_info["Results Folder"] = results_folder
        dashboard_info["Recorded Samples"] = str(record_count)

        self.results_page.set_summary(dashboard_info)

        self.refresh_status_bar()
        self.stack.setCurrentWidget(self.results_page)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(get_app_icon())

    window = MainWindow()
    window.showMaximized()

    sys.exit(app.exec())