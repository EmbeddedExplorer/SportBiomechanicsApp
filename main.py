import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QStackedWidget

from ui.home_page import HomePage
from ui.weightlifting_page import WeightliftingPage
from ui.sprinting_page import SprintingPage
from ui.results_page import ResultsPage


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

        self.stack.addWidget(self.home_page)
        self.stack.addWidget(self.weightlifting_page)
        self.stack.addWidget(self.sprinting_page)
        self.stack.addWidget(self.results_page)

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
            "File": "No file selected"
        })
        self.stack.setCurrentWidget(self.results_page)

    def start_weightlifting_analysis(self, exercise, input_mode, file_path):
        self.results_page.set_summary({
            "Sport": "Weightlifting",
            "Exercise": exercise,
            "Input Mode": input_mode,
            "File": file_path if file_path else "Live RealSense Camera"
        })
        self.stack.setCurrentWidget(self.results_page)

    def start_sprinting_analysis(self, input_mode, file_path):
        self.results_page.set_summary({
            "Sport": "Sprinting Biomechanics",
            "Exercise": "Sprinting",
            "Input Mode": input_mode,
            "File": file_path if file_path else "Live Camera"
        })
        self.stack.setCurrentWidget(self.results_page)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())