from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QGridLayout, QFrame
)
from PyQt6.QtCore import Qt


class SensorStatusPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._request_cb = None  # callback tutulur

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(6)

        card = QFrame()
        card.setObjectName("sensorStatusCard")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        title = QLabel("Sensor Status")
        layout.addWidget(title)

        self.btn_check = QPushButton("Check Sensor Status")
        layout.addWidget(self.btn_check)

        grid = QGridLayout()
        grid.setVerticalSpacing(6)

        self.labels = {}
        sensors = ["Voltage", "Loadcell", "Temperature", "Current", "RPM"]

        for row, name in enumerate(sensors):
            lbl_name = QLabel(name)
            lbl_state = QLabel("--")
            lbl_state.setAlignment(Qt.AlignmentFlag.AlignRight)

            grid.addWidget(lbl_name, row, 0)
            grid.addWidget(lbl_state, row, 1)

            self.labels[name.lower()] = lbl_state

        layout.addLayout(grid)
        outer.addWidget(card)

        self.setFixedWidth(180)

        # 🔴 BUTON → CALLBACK
        self.btn_check.clicked.connect(self._on_check_clicked)

    def set_status_request_callback(self, cb):
        self._request_cb = cb

    def _on_check_clicked(self):
        if self._request_cb:
            self._request_cb()

    def update_status(self, **kwargs):
        for k, v in kwargs.items():
            if k in self.labels:
                self.labels[k].setText(v)
