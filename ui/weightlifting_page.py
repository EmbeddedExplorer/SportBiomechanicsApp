from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QRadioButton, QGroupBox, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt


class WeightliftingPage(QWidget):
    def __init__(self, on_back, on_start_analysis):
        super().__init__()

        self.on_back = on_back
        self.on_start_analysis = on_start_analysis
        self.selected_file = ""

        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)

        title = QLabel("WEIGHTLIFTING BIOMECHANICS ANALYSIS")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setObjectName("PageTitle")

        exercise_group = QGroupBox("Select Exercise")
        exercise_layout = QVBoxLayout()

        self.radio_snatch = QRadioButton("Snatch")
        self.radio_clean_jerk = QRadioButton("Clean & Jerk")
        self.radio_snatch.setChecked(True)

        exercise_layout.addWidget(self.radio_snatch)
        exercise_layout.addWidget(self.radio_clean_jerk)
        exercise_group.setLayout(exercise_layout)

        input_group = QGroupBox("Select Input Source")
        input_layout = QVBoxLayout()

        self.radio_live = QRadioButton("Live RealSense Camera")
        self.radio_bag = QRadioButton("Pre-recorded RealSense .bag File")
        self.radio_live.setChecked(True)

        self.file_label = QLabel("No file selected")
        self.file_label.setObjectName("FileLabel")

        btn_select_file = QPushButton("Select .bag File")
        btn_select_file.clicked.connect(self.select_bag_file)

        input_layout.addWidget(self.radio_live)
        input_layout.addWidget(self.radio_bag)
        input_layout.addWidget(btn_select_file)
        input_layout.addWidget(self.file_label)

        input_group.setLayout(input_layout)

        button_layout = QHBoxLayout()

        btn_back = QPushButton("Back")
        btn_start = QPushButton("Start Analysis")

        btn_back.clicked.connect(self.on_back)
        btn_start.clicked.connect(self.start_analysis)

        button_layout.addWidget(btn_back)
        button_layout.addWidget(btn_start)

        main_layout.addWidget(title)
        main_layout.addWidget(exercise_group)
        main_layout.addWidget(input_group)
        main_layout.addStretch()
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

        self.setStyleSheet("""
            QWidget {
                background-color: #101820;
                color: white;
                font-family: Segoe UI;
                font-size: 16px;
            }

            QLabel#PageTitle {
                font-size: 28px;
                font-weight: bold;
                color: #00D4FF;
                margin: 20px;
            }

            QGroupBox {
                border: 2px solid #0078D7;
                border-radius: 10px;
                margin: 15px;
                padding: 20px;
                font-size: 18px;
                font-weight: bold;
            }

            QRadioButton {
                font-size: 16px;
                padding: 8px;
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

            QLabel#FileLabel {
                color: #CFCFCF;
                font-size: 14px;
            }
        """)

    def select_bag_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select RealSense Bag File",
            "",
            "RealSense Bag Files (*.bag);;All Files (*)"
        )

        if file_path:
            self.selected_file = file_path
            self.file_label.setText(file_path)
            self.radio_bag.setChecked(True)

    def start_analysis(self):
        exercise = "Snatch" if self.radio_snatch.isChecked() else "Clean & Jerk"
        input_mode = "Live RealSense Camera" if self.radio_live.isChecked() else "RealSense Bag File"

        if self.radio_bag.isChecked() and not self.selected_file:
            QMessageBox.warning(
                self,
                "File Required",
                "Please select a RealSense .bag file before starting analysis."
            )
            return

        self.on_start_analysis(exercise, input_mode, self.selected_file)