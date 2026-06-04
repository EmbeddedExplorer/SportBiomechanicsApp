from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QFrame
)
from PyQt6.QtCore import Qt


class HomePage(QWidget):
    def __init__(self, on_weightlifting, on_sprinting, on_results, on_exit):
        super().__init__()

        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.setSpacing(20)

        title = QLabel("SPORTS BIOMECHANICS ANALYSIS PLATFORM")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setObjectName("TitleLabel")

        subtitle = QLabel("Weightlifting and Sprinting Motion Analysis System")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setObjectName("SubtitleLabel")

        card = QFrame()
        card.setObjectName("HomeCard")
        card_layout = QVBoxLayout()
        card_layout.setSpacing(15)

        btn_weightlifting = QPushButton("Weightlifting Analysis")
        btn_sprinting = QPushButton("Sprinting Biomechanics Analysis")
        btn_results = QPushButton("Analysis History / Results")
        btn_exit = QPushButton("Exit")

        for btn in [btn_weightlifting, btn_sprinting, btn_results, btn_exit]:
            btn.setMinimumHeight(50)
            btn.setObjectName("MainButton")

        btn_weightlifting.clicked.connect(on_weightlifting)
        btn_sprinting.clicked.connect(on_sprinting)
        btn_results.clicked.connect(on_results)
        btn_exit.clicked.connect(on_exit)

        card_layout.addWidget(btn_weightlifting)
        card_layout.addWidget(btn_sprinting)
        card_layout.addWidget(btn_results)
        card_layout.addWidget(btn_exit)

        card.setLayout(card_layout)

        main_layout.addWidget(title)
        main_layout.addWidget(subtitle)
        main_layout.addWidget(card)

        self.setLayout(main_layout)

        self.setStyleSheet("""
            QWidget {
                background-color: #101820;
                color: white;
                font-family: Segoe UI;
            }

            QLabel#TitleLabel {
                font-size: 32px;
                font-weight: bold;
                color: #00D4FF;
            }

            QLabel#SubtitleLabel {
                font-size: 18px;
                color: #D0D0D0;
            }

            QFrame#HomeCard {
                background-color: #1E2A35;
                border-radius: 18px;
                padding: 30px;
                min-width: 450px;
            }

            QPushButton#MainButton {
                background-color: #0078D7;
                color: white;
                border-radius: 10px;
                font-size: 17px;
                font-weight: bold;
                padding: 10px;
            }

            QPushButton#MainButton:hover {
                background-color: #0099FF;
            }
        """)