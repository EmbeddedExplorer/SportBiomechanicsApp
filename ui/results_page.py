from pathlib import Path
import html

import pandas as pd

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QComboBox,
    QListWidget,
    QScrollArea,
    QMessageBox,
    QHeaderView
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QPixmap, QDesktopServices


class ResultsPage(QWidget):
    def __init__(self, on_back_home):
        super().__init__()

        self.on_back_home = on_back_home
        self.current_session_path = None
        self.plot_files = []
        self.last_summary_data = {}

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(12, 8, 12, 8)
        main_layout.setSpacing(8)

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
        csv_layout.setSpacing(8)

        self.csv_selector = QComboBox()
        self.csv_selector.currentIndexChanged.connect(self.load_selected_csv)

        self.csv_table = QTableWidget()
        self.csv_table.setAlternatingRowColors(True)
        self.csv_table.horizontalHeader().setStretchLastSection(False)
        self.csv_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Interactive
        )

        csv_layout.addWidget(QLabel("Select CSV File:"))
        csv_layout.addWidget(self.csv_selector)
        csv_layout.addWidget(self.csv_table)

        csv_tab.setLayout(csv_layout)

        # ================= PLOTS TAB =================
        plots_tab = QWidget()
        plots_layout = QHBoxLayout()
        plots_layout.setSpacing(10)

        self.plot_list = QListWidget()
        self.plot_list.currentRowChanged.connect(self.display_selected_plot)

        self.plot_label = QLabel("Select a plot to view")
        self.plot_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.plot_label.setMinimumSize(800, 520)

        self.plot_scroll = QScrollArea()
        self.plot_scroll.setWidgetResizable(True)
        self.plot_scroll.setWidget(self.plot_label)

        plots_layout.addWidget(self.plot_list, 1)
        plots_layout.addWidget(self.plot_scroll, 4)

        plots_tab.setLayout(plots_layout)

        self.tabs.addTab(self.summary_box, "Summary")
        self.tabs.addTab(csv_tab, "CSV Viewer")
        self.tabs.addTab(plots_tab, "Plots")

        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        btn_open_folder = QPushButton("Open Results Folder")
        btn_open_folder.clicked.connect(self.open_results_folder)

        btn_back = QPushButton("Back to Home")
        btn_back.clicked.connect(self.on_back_home)

        button_layout.addWidget(btn_open_folder)
        button_layout.addWidget(btn_back)

        main_layout.addWidget(title)
        main_layout.addWidget(self.tabs, 1)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

        self.apply_styles()

    # ==========================================================
    # CSV SAFE HELPERS
    # ==========================================================
    def safe_csv_value(self, value):
        try:
            if pd.isna(value):
                return ""
        except Exception:
            pass

        try:
            if hasattr(value, "item"):
                return value.item()
        except Exception:
            pass

        return value

    def read_first_row_csv(self, csv_path):
        csv_path = Path(csv_path)

        if not csv_path.exists():
            return {}

        try:
            df = pd.read_csv(csv_path)

            if df.empty:
                return {}

            row = df.iloc[0].to_dict()
            clean_row = {}

            for key, value in row.items():
                clean_row[key] = self.safe_csv_value(value)

            return clean_row

        except Exception:
            return {}

    # ==========================================================
    # SUMMARY
    # ==========================================================
    def set_summary(self, data):
        """
        Receive session_info and build dashboard summary.

        Fallback:
        If enhanced values are not passed through session_info,
        read them directly from CSV/lift_summary.csv.
        """

        self.last_summary_data = data or {}

        results_folder = self.get_data_value(
            self.last_summary_data,
            ["results_folder", "Results Folder", "session_path", "Session Path"],
            default=""
        )

        if results_folder and results_folder != "No folder created yet":
            self.current_session_path = Path(results_folder)
        else:
            self.current_session_path = None

        if self.current_session_path and self.current_session_path.exists():
            lift_summary_path = self.current_session_path / "CSV" / "lift_summary.csv"

            lift_summary = self.read_first_row_csv(lift_summary_path)

            if lift_summary:
                self.last_summary_data["lift_summary"] = lift_summary

                for key, value in lift_summary.items():
                    if (
                        key not in self.last_summary_data
                        or self.last_summary_data.get(key) in [None, "", "N/A"]
                    ):
                        self.last_summary_data[key] = value

        self.summary_box.setHtml(
            self.build_summary_html(self.last_summary_data)
        )

        if self.current_session_path and self.current_session_path.exists():
            self.load_session_outputs()
        else:
            self.csv_selector.clear()
            self.csv_table.clear()
            self.plot_list.clear()
            self.plot_files = []
            self.plot_label.setText("No plots available yet.")

    def build_summary_html(self, data):
        lift_summary = data.get("lift_summary", {})

        if not isinstance(lift_summary, dict):
            lift_summary = {}

        def get_value(keys, default="N/A"):
            for key in keys:
                if key in data and data.get(key) not in [None, "", "nan", "N/A"]:
                    return data.get(key)

                if key in lift_summary and lift_summary.get(key) not in [None, "", "nan", "N/A"]:
                    return lift_summary.get(key)

            return default

        sport = get_value(["sport", "Sport"])
        exercise = get_value(["exercise", "Exercise"])
        camera_view = get_value(["camera_view", "Camera View"])
        input_mode = get_value(["input_mode", "Input Mode"])
        source_file = get_value(["source_file", "Source File"], "")

        results_folder = self.get_data_value(
            data,
            ["results_folder", "Results Folder", "session_path", "Session Path"],
            "N/A"
        )

        record_count = get_value(["record_count", "Record Count", "Recorded Samples"])
        duration = get_value(["total_duration_s"])
        detected_phase_count = get_value(["detected_phase_count"])
        detected_phases = get_value(["detected_phases"])
        barbell_detected_samples = get_value(["barbell_detected_samples"])

        max_height = self.best_unit_value(
            value_m=get_value(["max_barbell_height_m"], ""),
            value_px=get_value(["max_barbell_height_px"], ""),
            label_m="m",
            label_px="px"
        )

        max_vertical_velocity = self.best_unit_value(
            value_m=get_value(["max_vertical_velocity_m_s"], ""),
            value_px=get_value(["max_vertical_velocity_px_s"], ""),
            label_m="m/s",
            label_px="px/s"
        )

        max_horizontal_velocity = self.best_unit_value(
            value_m=get_value(["max_horizontal_velocity_m_s"], ""),
            value_px=get_value(["max_horizontal_velocity_px_s"], ""),
            label_m="m/s",
            label_px="px/s"
        )

        csv_status_html = self.build_output_status_html(
            title="Generated CSV Files",
            output_dict=self.get_data_value(data, ["csv_files"], {}),
            fallback_folder=self.current_session_path / "CSV" if self.current_session_path else None,
            extension="*.csv"
        )

        plot_status_html = self.build_output_status_html(
            title="Generated Plot Files",
            output_dict=self.get_data_value(data, ["plot_files"], {}),
            fallback_folder=self.current_session_path / "Plots" if self.current_session_path else None,
            extension="*.png"
        )

        source_file_html = ""

        if source_file and source_file != "N/A":
            source_file_html = f"""
                <tr>
                    <td class="key">Source File</td>
                    <td class="value">{self.html_escape(source_file)}</td>
                </tr>
            """

        duration_html = self.format_optional_metric(duration, "s")
        phase_count_html = self.format_optional_metric(detected_phase_count, "")
        barbell_samples_html = self.format_optional_metric(barbell_detected_samples, "")

        if not detected_phases:
            detected_phases = "N/A"

        html_text = f"""
        <html>
        <head>
        <style>
            body {{
                font-family: Segoe UI;
                color: #FFFFFF;
                background-color: #1E2A35;
            }}

            h1 {{
                color: #00D4FF;
                font-size: 24px;
                margin-bottom: 8px;
            }}

            h2 {{
                color: #00D4FF;
                font-size: 18px;
                margin-top: 18px;
                margin-bottom: 8px;
            }}

            .section {{
                background-color: #16232E;
                border: 1px solid #0078D7;
                border-radius: 8px;
                padding: 12px;
                margin-bottom: 12px;
            }}

            table {{
                width: 100%;
                border-collapse: collapse;
            }}

            td {{
                padding: 7px;
                border-bottom: 1px solid #2E3D49;
                vertical-align: top;
            }}

            .key {{
                width: 32%;
                color: #C9D6DF;
                font-weight: bold;
            }}

            .value {{
                color: #FFFFFF;
            }}

            .good {{
                color: #66FF99;
                font-weight: bold;
            }}

            .warn {{
                color: #FFCC66;
                font-weight: bold;
            }}

            .path {{
                color: #CFCFCF;
                font-size: 12px;
            }}

            .phasebox {{
                background-color: #101820;
                border-radius: 6px;
                padding: 8px;
                color: #FFFFFF;
            }}
        </style>
        </head>

        <body>
            <h1>Analysis Session Summary</h1>

            <div class="section">
                <h2>Session Information</h2>
                <table>
                    <tr>
                        <td class="key">Sport</td>
                        <td class="value">{self.html_escape(sport)}</td>
                    </tr>
                    <tr>
                        <td class="key">Exercise</td>
                        <td class="value">{self.html_escape(exercise)}</td>
                    </tr>
                    <tr>
                        <td class="key">Camera View</td>
                        <td class="value">{self.html_escape(camera_view)}</td>
                    </tr>
                    <tr>
                        <td class="key">Input Mode</td>
                        <td class="value">{self.html_escape(input_mode)}</td>
                    </tr>
                    {source_file_html}
                    <tr>
                        <td class="key">Results Folder</td>
                        <td class="value path">{self.html_escape(results_folder)}</td>
                    </tr>
                </table>
            </div>

            <div class="section">
                <h2>Key Results</h2>
                <table>
                    <tr>
                        <td class="key">Total Samples</td>
                        <td class="value">{self.html_escape(record_count)}</td>
                    </tr>
                    <tr>
                        <td class="key">Total Duration</td>
                        <td class="value">{duration_html}</td>
                    </tr>
                    <tr>
                        <td class="key">Detected Phase Count</td>
                        <td class="value">{phase_count_html}</td>
                    </tr>
                    <tr>
                        <td class="key">Barbell Detected Samples</td>
                        <td class="value">{barbell_samples_html}</td>
                    </tr>
                    <tr>
                        <td class="key">Max Barbell Height</td>
                        <td class="value">{self.html_escape(max_height)}</td>
                    </tr>
                    <tr>
                        <td class="key">Max Vertical Velocity</td>
                        <td class="value">{self.html_escape(max_vertical_velocity)}</td>
                    </tr>
                    <tr>
                        <td class="key">Max Horizontal Velocity</td>
                        <td class="value">{self.html_escape(max_horizontal_velocity)}</td>
                    </tr>
                </table>
            </div>

            <div class="section">
                <h2>Detected Phases</h2>
                <div class="phasebox">{self.html_escape(detected_phases)}</div>
            </div>

            <div class="section">
                {csv_status_html}
            </div>

            <div class="section">
                {plot_status_html}
            </div>

        </body>
        </html>
        """

        return html_text

    def build_output_status_html(self, title, output_dict, fallback_folder=None, extension="*"):
        rows = []

        if isinstance(output_dict, dict) and output_dict:
            for name, path in output_dict.items():
                label = self.pretty_name(name)
                exists = bool(path) and Path(path).exists()

                status = "<span class='good'>Available</span>" if exists else "<span class='warn'>Missing</span>"
                path_text = path if path else "Not generated"

                rows.append(f"""
                    <tr>
                        <td class="key">{self.html_escape(label)}</td>
                        <td class="value">{status}<br><span class="path">{self.html_escape(path_text)}</span></td>
                    </tr>
                """)

        elif fallback_folder and fallback_folder.exists():
            files = sorted(fallback_folder.glob(extension))

            for file_path in files:
                rows.append(f"""
                    <tr>
                        <td class="key">{self.html_escape(file_path.name)}</td>
                        <td class="value"><span class='good'>Available</span><br><span class="path">{self.html_escape(str(file_path))}</span></td>
                    </tr>
                """)

        if not rows:
            rows.append("""
                <tr>
                    <td class="key">No files found</td>
                    <td class="value"><span class='warn'>Missing</span></td>
                </tr>
            """)

        return f"""
            <h2>{self.html_escape(title)}</h2>
            <table>
                {''.join(rows)}
            </table>
        """

    def get_data_value(self, data, keys, default=""):
        if not isinstance(data, dict):
            return default

        for key in keys:
            if key in data:
                value = data.get(key)

                if value is None:
                    continue

                return value

        return default

    def html_escape(self, value):
        if value is None:
            return ""

        return html.escape(str(value))

    def pretty_name(self, value):
        if value is None:
            return ""

        text = str(value).replace("_", " ").strip()
        return text.title()

    def format_optional_metric(self, value, unit=""):
        if value is None or value == "":
            return "N/A"

        try:
            numeric_value = float(value)

            if unit:
                return f"{numeric_value:.3f} {unit}"

            if numeric_value.is_integer():
                return str(int(numeric_value))

            return f"{numeric_value:.3f}"

        except Exception:
            return self.html_escape(value)

    def best_unit_value(self, value_m, value_px, label_m="m", label_px="px"):
        if value_m not in [None, ""]:
            try:
                return f"{float(value_m):.4f} {label_m}"
            except Exception:
                return f"{value_m} {label_m}"

        if value_px not in [None, ""]:
            try:
                return f"{float(value_px):.2f} {label_px}"
            except Exception:
                return f"{value_px} {label_px}"

        return "N/A"

    # ==========================================================
    # SESSION OUTPUT LOADING
    # ==========================================================
    def load_session_outputs(self):
        if not self.current_session_path:
            return

        csv_folder = self.current_session_path / "CSV"
        plots_folder = self.current_session_path / "Plots"

        self.load_csv_files(csv_folder)
        self.load_plot_files(plots_folder)

    def load_csv_files(self, csv_folder):
        self.csv_selector.blockSignals(True)
        self.csv_selector.clear()

        preferred_order = [
            "lift_summary.csv",
            "phase_biomechanics_summary.csv",
            "phase_summary.csv",
            "analysis_summary.csv",
            "barbell_trajectory.csv",
            "depth_data.csv",
            "joint_angles_2d.csv"
        ]

        csv_files = []

        if csv_folder.exists():
            all_files = list(csv_folder.glob("*.csv"))

            for preferred_name in preferred_order:
                for file_path in all_files:
                    if file_path.name == preferred_name and file_path not in csv_files:
                        csv_files.append(file_path)

            for file_path in sorted(all_files):
                if file_path not in csv_files:
                    csv_files.append(file_path)

        for csv_file in csv_files:
            self.csv_selector.addItem(csv_file.name, str(csv_file))

        self.csv_selector.blockSignals(False)

        if csv_files:
            self.csv_selector.setCurrentIndex(0)
            self.load_csv_to_table(csv_files[0])
        else:
            self.csv_table.clear()
            self.csv_table.setRowCount(0)
            self.csv_table.setColumnCount(0)

    def load_plot_files(self, plots_folder):
        self.plot_list.clear()
        self.plot_files = []

        preferred_order = [
            "barbell_trajectory_phase_highlighted.png",
            "barbell_trajectory_annotated.png",
            "barbell_trajectory_powerpoint_style.png",
            "barbell_velocity_phase_highlighted.png",
            "hip_knee_angles_phase_highlighted.png",
            "upper_limb_angles_phase_highlighted.png",
            "trunk_lean_phase_highlighted.png"
        ]

        if plots_folder.exists():
            all_files = list(plots_folder.glob("*.png"))

            for preferred_name in preferred_order:
                for file_path in all_files:
                    if file_path.name == preferred_name and file_path not in self.plot_files:
                        self.plot_files.append(file_path)

            for file_path in sorted(all_files):
                if file_path not in self.plot_files:
                    self.plot_files.append(file_path)

        for plot_file in self.plot_files:
            self.plot_list.addItem(plot_file.name)

        if self.plot_files:
            self.plot_list.setCurrentRow(0)
            self.display_plot(self.plot_files[0])
        else:
            self.plot_label.setText("No plot images found.")

    # ==========================================================
    # CSV VIEWER
    # ==========================================================
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

    # ==========================================================
    # PLOT VIEWER
    # ==========================================================
    def display_selected_plot(self, index):
        if 0 <= index < len(self.plot_files):
            self.display_plot(self.plot_files[index])

    def display_plot(self, plot_path):
        pixmap = QPixmap(str(plot_path))

        if pixmap.isNull():
            self.plot_label.setText("Could not load plot image.")
            return

        viewport = self.plot_scroll.viewport()
        target_width = max(850, viewport.width() - 40)
        target_height = max(520, viewport.height() - 40)

        scaled_pixmap = pixmap.scaled(
            target_width,
            target_height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        self.plot_label.setPixmap(scaled_pixmap)

    def resizeEvent(self, event):
        super().resizeEvent(event)

        current_row = self.plot_list.currentRow()

        if 0 <= current_row < len(self.plot_files):
            self.display_plot(self.plot_files[current_row])

    # ==========================================================
    # FOLDER OPENING
    # ==========================================================
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

            QTabWidget::pane {
                border: 2px solid #0078D7;
                border-radius: 8px;
            }

            QTabBar::tab {
                background-color: #1E2A35;
                color: white;
                padding: 10px;
                min-width: 140px;
            }

            QTabBar::tab:selected {
                background-color: #0078D7;
            }

            QTextEdit {
                background-color: #1E2A35;
                color: white;
                border-radius: 8px;
                padding: 10px;
                border: 1px solid #0078D7;
            }

            QTableWidget {
                background-color: #1E2A35;
                alternate-background-color: #17232E;
                color: white;
                gridline-color: #0078D7;
                border: 1px solid #0078D7;
                border-radius: 6px;
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
                padding: 4px;
            }

            QListWidget::item {
                padding: 6px;
            }

            QListWidget::item:selected {
                background-color: #0078D7;
                color: white;
            }

            QLabel {
                color: white;
            }

            QScrollArea {
                background-color: #101820;
                border: 1px solid #1E2A35;
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

            QPushButton:disabled {
                background-color: #555555;
                color: #AAAAAA;
            }
        """)