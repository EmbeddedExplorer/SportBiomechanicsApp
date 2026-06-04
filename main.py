import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QStackedWidget

from ui.home_page import HomePage
from ui.weightlifting_page import WeightliftingPage
from ui.sprinting_page import SprintingPage
from ui.results_page import ResultsPage
from ui.history_page import HistoryPage

from modules.result_manager import create_session_folder, generate_dummy_outputs


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Sports Biomechanics Analysis Platform")
        self.resize(1280, 720)

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.home_page = HomePage(
            on_weightlifting=self.show_weightlifting_page,
            on_sprinting=self.show_sprinting_page,
            on_results=self.show_results_page,
            on_history=self.show_history_page,
            on_exit=self.close
        )

        self.weightlifting_page = WeightliftingPage(
            on_back=self.show_home_page,
            on_start_analysis=self.start_weightlifting_analysis
        )

        self.sprinting_page = SprintingPage(
            on_back=self.show_home_page,
            on_start_analysis=self.start_sprinting_analysis
        )

        self.results_page = ResultsPage(
            on_back_home=self.show_home_page
        )

        self.history_page = HistoryPage(
            on_back=self.show_home_page
        )

        self.stack.addWidget(self.home_page)
        self.stack.addWidget(self.weightlifting_page)
        self.stack.addWidget(self.sprinting_page)
        self.stack.addWidget(self.results_page)
        self.stack.addWidget(self.history_page)

        self.show_home_page()

    def show_home_page(self):
        self.stack.setCurrentWidget(self.home_page)

    def show_weightlifting_page(self):
        self.stack.setCurrentWidget(self.weightlifting_page)

    def show_sprinting_page(self):
        self.stack.setCurrentWidget(self.sprinting_page)

    def show_results_page(self):
        self.results_page.set_summary({
            "Sport": "Previous Analysis",
            "Exercise": "Not selected",
            "Input Mode": "Not selected",
            "File": "No file selected",
            "Results Folder": "No folder created yet"
        })

        self.stack.setCurrentWidget(self.results_page)

    def show_history_page(self):
        self.history_page.load_sessions()
        self.stack.setCurrentWidget(self.history_page)

    def start_weightlifting_analysis(self, exercise, input_mode, file_path):
        session_path = create_session_folder(
            sport="Weightlifting",
            exercise=exercise,
            input_mode=input_mode,
            source_file=file_path
        )

        generate_dummy_outputs(
            session_path=session_path,
            sport="Weightlifting",
            exercise=exercise
        )

        self.results_page.set_summary({
            "Sport": "Weightlifting",
            "Exercise": exercise,
            "Input Mode": input_mode,
            "File": file_path if file_path else "Live RealSense Camera",
            "Results Folder": str(session_path)
        })

        self.stack.setCurrentWidget(self.results_page)

    def start_sprinting_analysis(self, input_mode, file_path):
        session_path = create_session_folder(
            sport="Sprinting",
            exercise="Sprinting",
            input_mode=input_mode,
            source_file=file_path
        )

        generate_dummy_outputs(
            session_path=session_path,
            sport="Sprinting",
            exercise="Sprinting"
        )

        self.results_page.set_summary({
            "Sport": "Sprinting Biomechanics",
            "Exercise": "Sprinting",
            "Input Mode": input_mode,
            "File": file_path if file_path else "Live Camera",
            "Results Folder": str(session_path)
        })

        self.stack.setCurrentWidget(self.results_page)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())