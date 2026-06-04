from pathlib import Path

import pandas as pd

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QTableWidget, QTableWidgetItem, QTextEdit,
    QComboBox, QListWidget, QScrollArea, QMessageBox
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QPixmap, QDesktopServices


class ResultsPage(QWidget):
    def __init__(self, on_back_home):
        super().__init__()

        self.on_back_home = on_back_home
        self.current_session_path = None
        self.plot_files = []

        main_layout = QVBoxLayout()

        title = QLabel("ANALYSIS RESULTS DASHBOARD")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setObjectName("PageTitle")

        self.tabs = QTabWidget()

        # ================= SUMMARY TAB =================
        self.summary_box = QTextEdit()
        self.summary_box.setReadOnly(True)

        # ================= CSV TAB =================
        csv_tab = QWidget()
        csv_layout = QVBoxLayout()

        self.csv_selector = QComboBox()
        self.csv_selector.currentIndexChanged.connect(self.load_selected_csv)

        self.csv_table = QTableWidget()

        csv_layout.addWidget(QLabel("Select CSV File:"))
        csv_layout.addWidget(self.csv_selector)
        csv_layout.addWidget(self.csv_table)

        csv_tab.setLayout(csv_layout)

        # ================= PLOTS TAB =================
        plots_tab = QWidget()
        plots_layout = QHBoxLayout()

        self.plot_list = QListWidget()
        self.plot_list.currentRowChanged.connect(self.display_selected_plot)

        self.plot_label = QLabel("Select a plot to view")
        self.plot_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.plot_scroll = QScrollArea()
        self.plot_scroll.setWidgetResizable(True)
        self.plot_scroll.setWidget(self.plot_label)

        plots_layout.addWidget(self.plot_list, 1)
        plots_layout.addWidget(self.plot_scroll, 4)

        plots_tab.setLayout(plots_layout)

        # ================= TABS =================
        self.tabs.addTab(self.summary_box, "Summary")
        self.tabs.addTab(csv_tab, "CSV Viewer")
        self.tabs.addTab(plots_tab, "Plots")

        # ================= BUTTONS =================
        button_layout = QHBoxLayout()

        btn_open_folder = QPushButton("Open Results Folder")
        btn_open_folder.clicked.connect(self.open_results_folder)

        btn_back = QPushButton("Back to Home")
        btn_back.clicked.connect(self.on_back_home)

        button_layout.addWidget(btn_open_folder)
        button_layout.addWidget(btn_back)

        main_layout.addWidget(title)
        main_layout.addWidget(self.tabs)
        main_layout.addLayout(button_layout)

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

            QHeaderView::section {
                background-color: #0078D7;
                color: white;
                padding: 5px;
                border: 1px solid #101820;
            }

            QComboBox {
                background-color: #1E2A35;
                color: white;
                padding: 8px;
                border: 1px solid #0078D7;
                border-radius: 6px;
            }

            QListWidget {
                background-color: #1E2A35;
                color: white;
                border: 1px solid #0078D7;
                border-radius: 6px;
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

"""

        self.summary_box.setText(text)

        results_folder = data.get("Results Folder", "")

        if results_folder and results_folder != "No folder created yet":
            self.current_session_path = Path(results_folder)
            self.load_session_outputs()
        else:
            self.current_session_path = None
            self.csv_selector.clear()
            self.csv_table.clear()
            self.plot_list.clear()
            self.plot_label.setText("No plots available yet.")

    def load_session_outputs(self):
        if not self.current_session_path:
            return

        csv_folder = self.current_session_path / "CSV"
        plots_folder = self.current_session_path / "Plots"

        # Load CSV file list
        self.csv_selector.clear()

        if csv_folder.exists():
            csv_files = list(csv_folder.glob("*.csv"))

            for csv_file in csv_files:
                self.csv_selector.addItem(csv_file.name, str(csv_file))

            if csv_files:
                self.load_csv_to_table(csv_files[0])

        # Load plot file list
        self.plot_list.clear()
        self.plot_files = []

        if plots_folder.exists():
            self.plot_files = list(plots_folder.glob("*.png"))

            for plot_file in self.plot_files:
                self.plot_list.addItem(plot_file.name)

            if self.plot_files:
                self.plot_list.setCurrentRow(0)
                self.display_plot(self.plot_files[0])
            else:
                self.plot_label.setText("No plot images found.")

    def load_selected_csv(self):
        csv_path = self.csv_selector.currentData()

        if csv_path:
            self.load_csv_to_table(Path(csv_path))

    def load_csv_to_table(self, csv_path):
        try:
            df = pd.read_csv(csv_path)

            self.csv_table.clear()
            self.csv_table.setRowCount(len(df))
            self.csv_table.setColumnCount(len(df.columns))
            self.csv_table.setHorizontalHeaderLabels(df.columns.astype(str).tolist())

            for row in range(len(df)):
                for col in range(len(df.columns)):
                    value = str(df.iloc[row, col])
                    self.csv_table.setItem(row, col, QTableWidgetItem(value))

            self.csv_table.resizeColumnsToContents()

        except Exception as e:
            QMessageBox.critical(
                self,
                "CSV Loading Error",
                f"Could not load CSV file:\n{csv_path}\n\nError:\n{e}"
            )

    def display_selected_plot(self, index):
        if 0 <= index < len(self.plot_files):
            self.display_plot(self.plot_files[index])

    def display_plot(self, plot_path):
        pixmap = QPixmap(str(plot_path))

        if pixmap.isNull():
            self.plot_label.setText("Could not load plot image.")
            return

        scaled_pixmap = pixmap.scaled(
            950,
            550,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        self.plot_label.setPixmap(scaled_pixmap)

    def open_results_folder(self):
        if self.current_session_path and self.current_session_path.exists():
            QDesktopServices.openUrl(
                QUrl.fromLocalFile(str(self.current_session_path.resolve()))
            )
        else:
            QMessageBox.warning(
                self,
                "No Results Folder",
                "No valid results folder is available for this session."
            )