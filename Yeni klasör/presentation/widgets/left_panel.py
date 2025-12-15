from typing import Dict

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGroupBox,
    QGridLayout,
    QLabel,
    QFrame,
)
from PyQt6.QtCore import Qt


class LeftDataPanel(QWidget):
    """
    Sol panel: anlık sensör değerleri (voltage, current, thrust, rpm, vb.).
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(6)

        # ===========================
        # CARD (QFrame) + TITLE
        # ===========================
        card = QFrame()
        card.setObjectName("liveSensorCard")

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(10, 10, 10, 10)
        card_layout.setSpacing(8)

        title = QLabel("Live Sensor Data")
        title.setObjectName("liveSensorTitle")
        card_layout.addWidget(title)

        # Grid is inside the card
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(6)
        card_layout.addLayout(grid)

        # ===========================
        # FIELDS (same as before)
        # ===========================
        fields = [
            ("Voltage (V)", "voltage"),
            ("Current (A)", "current"),
            ("Thrust (kgf)", "thrust_kgf"),
            ("Motor Speed (RPM)", "rpm"),
            ("Temperature (°C)", "temperature"),
            ("Electrical Power (W)", "power"),
            ("PT Efficiency (kgf/W)", "pt_eff"),
            ("Thrust per Amp (kgf/A)", "tpa"),
        ]

        self.value_labels: Dict[str, QLabel] = {}

        for row, (title_text, key) in enumerate(fields):
            title_label = QLabel(title_text)
            title_label.setAlignment(
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            )

                #Live sensor data içindeki parametrelerin değerlerinin yazdığı kutucuklar
            value_label = QLabel("--")
            value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            value_label.setObjectName("liveSensorValue")


            grid.addWidget(title_label, row, 0)
            grid.addWidget(value_label, row, 1)

            self.value_labels[key] = value_label

        # Live sensor panel ayarları
        outer_layout.addWidget(card)

        # live sensor kısmı genişlik ayarı burdan
        self.setFixedWidth(180)
        outer_layout.addStretch()


    def update_values(self, **kwargs):
        """
        Örnek:
        update_values(voltage="39.7", current="3.5", ...)
        """
        for key, value in kwargs.items():
            label = self.value_labels.get(key)
            if label is not None:
                label.setText(str(value))

