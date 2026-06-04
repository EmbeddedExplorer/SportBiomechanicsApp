from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QTabWidget,
    QTableWidget, QTableWidgetItem, QTextEdit
)
from PyQt6.QtCore import Qt


class ResultsPage(QWidget):
    def __init__(self, on_back_home):
        super().__init__()

        self.on_back_home = on_back_home

        main_layout = QVBoxLayout()

        title = QLabel("ANALYSIS RESULTS DASHBOARD")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setObjectName("PageTitle")

        self.tabs = QTabWidget()

        self.summary_box = QTextEdit()
        self.summary_box.setReadOnly(True)

        self.csv_table = QTableWidget()
        self.csv_table.setColumnCount(5)
        self.csv_table.setHorizontalHeaderLabels([
            "Time", "Hip Angle", "Knee Angle", "Velocity", "Phase"
        ])

        self.plot_placeholder = QLabel("Plots will be displayed here after analysis.")
        self.plot_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.tabs.addTab(self.summary_box, "Summary")
        self.tabs.addTab(self.csv_table, "CSV Viewer")
        self.tabs.addTab(self.plot_placeholder, "Plots")

        btn_back = QPushButton("Back to Home")
        btn_back.clicked.connect(self.on_back_home)

        main_layout.addWidget(title)
        main_layout.addWidget(self.tabs)
        main_layout.addWidget(btn_back)

        self.setLayout(main_layout)

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

            QTabWidget::pane {
                border: 2px solid #0078D7;
                border-radius: 8px;
            }

            QTabBar::tab {
                background-color: #1E2A35;
                color: white;
                padding: 10px;
                min-width: 120px;
            }

            QTabBar::tab:selected {
                background-color: #0078D7;
            }

            QTextEdit {
                background-color: #1E2A35;
                color: white;
                border-radius: 8px;
                padding: 10px;
            }

            QTableWidget {
                background-color: #1E2A35;
                color: white;
                gridline-color: #0078D7;
            }

            QPushButton {
                background-color: #0078D7;
                color: white;
                border-radius: 8px;
                padding: 12px;
                font-size: 16px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #0099FF;
            }
        """)

    def set_summary(self, data):
        text = "Analysis Session Summary\n\n"

        for key, value in data.items():
            text += f"{key}: {value}\n"

        text += """

Generated Outputs:

- CSV data files
- Biomechanical plots
- Joint angle analysis
- Velocity analysis
- Phase-wise analysis

Note:
Actual analysis modules will be connected in the next development stage.
"""

        self.summary_box.setText(text)

        self.load_dummy_csv_data()

    def load_dummy_csv_data(self):
        dummy_data = [
            ["0.00", "145.2", "132.4", "0.00", "Setup"],
            ["0.03", "148.1", "136.2", "0.35", "First Pull"],
            ["0.06", "152.8", "140.7", "0.72", "Second Pull"],
            ["0.09", "160.3", "148.9", "1.15", "Catch"],
        ]

        self.csv_table.setRowCount(len(dummy_data))

        for row, row_data in enumerate(dummy_data):
            for col, value in enumerate(row_data):
                self.csv_table.setItem(row, col, QTableWidgetItem(value))