import sys

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QStackedWidget,
    QScrollArea,
    QFrame
)
from PyQt6.QtCore import Qt

from ui.home_page import HomePage
from ui.weightlifting_page import WeightliftingPage
from ui.sprinting_page import SprintingPage
from ui.results_page import ResultsPage
from ui.history_page import HistoryPage
from ui.about_page import AboutPage

from modules.database_manager import (
    init_database,
    add_session,
    get_recent_sessions,
    get_session_count
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        init_database()

        self.setWindowTitle("BioMotion Studio")

        # Minimum size keeps layout usable, but scroll area helps if screen is smaller.
        self.setMinimumSize(1100, 650)

        # Main page stack
        self.stack = QStackedWidget()

        # Scroll area prevents bottom controls from being hidden on smaller screens.
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
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
            on_back=self.show_home_page
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
            "Sport": "Previous Analysis",
            "Exercise": "Not selected",
            "Input Mode": "Not selected",
            "File": "No file selected",
            "Results Folder": "No folder created yet"
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

    def complete_analysis_session(self, session_info):
        add_session({
            "sport": session_info.get("sport", ""),
            "exercise": session_info.get("exercise", ""),
            "input_mode": session_info.get("input_mode", ""),
            "source_file": session_info.get("source_file", ""),
            "results_folder": session_info.get("results_folder", "")
        })

        self.results_page.set_summary({
            "Sport": session_info.get("sport", ""),
            "Exercise": session_info.get("exercise", ""),
            "Input Mode": session_info.get("input_mode", ""),
            "File": session_info.get("source_file", "") if session_info.get("source_file", "") else "Live / Webcam Source",
            "Results Folder": session_info.get("results_folder", ""),
            "Recorded Samples": str(session_info.get("record_count", 0))
        })

        self.refresh_status_bar()
        self.stack.setCurrentWidget(self.results_page)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()

    # Important:
    # showMaximized() respects the Windows taskbar.
    # Do not use showFullScreen(), because that can cover the taskbar.
    window.showMaximized()

    sys.exit(app.exec())