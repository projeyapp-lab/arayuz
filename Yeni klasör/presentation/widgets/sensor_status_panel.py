from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QGridLayout,
    QFrame,
)
from PyQt6.QtCore import Qt, QTimer


class SensorStatusPanel(QWidget):
    """
    Sensor Status Card

    - Pasif UI + sınırlı kontrol
    - Serial detaylarını BİLMEZ
    - Sadece callback tetikler
    """

    TIMEOUT_MS = 3000

    def __init__(self, parent=None):
        super().__init__(parent)

        self._request_cb = None

        # ===========================
        # TIMEOUT TIMER
        # ===========================
        self._timeout_timer = QTimer(self)
        self._timeout_timer.setSingleShot(True)
        self._timeout_timer.timeout.connect(self._on_timeout)

        # ===========================
        # OUTER LAYOUT (panel)
        # ===========================
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(8)

        # ===========================
        # CARD
        # ===========================
        card = QFrame()
        card.setObjectName("sensorStatusCard")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # ===========================
        # TITLE
        # ===========================
        title = QLabel("Sensor Status")
        title.setObjectName("liveSensorTitle")  # QSS ile hizalı
        title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(title)

        # ===========================
        # ACTION BUTTON
        # ===========================
        self.btn_check = QPushButton("Check Sensor Status")
        self.btn_check.setMinimumHeight(36)
        self.btn_check.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_check.clicked.connect(self._on_check_clicked)
        layout.addWidget(self.btn_check)

        # ===========================
        # SENSOR GRID
        # ===========================
        grid = QGridLayout()
        grid.setContentsMargins(0, 8, 0, 8)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)

        self.labels = {}

        sensors = [
            ("Voltage", "V"),
            ("Loadcell", "LC"),
            ("Temperature", "T"),
            ("Current", "I"),
            ("RPM", "RPM"),
        ]

        for row, (name, key) in enumerate(sensors):
            lbl_name = QLabel(f"{name}:")
            lbl_name.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

            lbl_state = QLabel("--")
            lbl_state.setObjectName("sensorStatusLabel")
            lbl_state.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            lbl_state.setMinimumWidth(80)

            grid.addWidget(lbl_name, row, 0)
            grid.addWidget(lbl_state, row, 1)

            self.labels[key] = lbl_state

        layout.addLayout(grid)

        # ===========================
        # INFO LABEL
        # ===========================
        self.info_label = QLabel("")
        self.info_label.setObjectName("info_label")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_label.setMinimumHeight(28)
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)

        outer.addWidget(card)
        self.setFixedWidth(220)

    # ======================================================
    # PUBLIC API (MainWindow kullanır)
    # ======================================================

    def set_status_request_callback(self, cb):
        self._request_cb = cb

    def reset_status(self):
        self._timeout_timer.stop()
        self.btn_check.setEnabled(True)
        self.btn_check.setText("Check Sensor Status")
        self.info_label.clear()
        self.info_label.setStyleSheet("")

        for lbl in self.labels.values():
            lbl.setText("--")
            lbl.setStyleSheet("")

    def update_status(self, status_dict: dict):
        self._timeout_timer.stop()

        self.btn_check.setEnabled(True)
        self.btn_check.setText("Check Sensor Status")

        all_ready = True
        errors = 0

        for key, label in self.labels.items():
            status = status_dict.get(key, "UNKNOWN")
            label.setText(status)

            if status == "READY":
                label.setStyleSheet(
                    "color:#107c10;background:#dff6dd;padding:4px 8px;border-radius:4px;"
                )
            elif status in ("ERROR", "FAIL", "TIMEOUT", "NO_RESPONSE"):
                label.setStyleSheet(
                    "color:#d13438;background:#fde7e9;padding:4px 8px;border-radius:4px;"
                )
                all_ready = False
                errors += 1
            else:
                label.setStyleSheet(
                    "color:#f7630c;background:#fff4ce;padding:4px 8px;border-radius:4px;"
                )
                all_ready = False

        if all_ready:
            self.info_label.setText("✓ All sensors ready")
            self.info_label.setStyleSheet(
                "color:#107c10;background:#dff6dd;padding:4px;border-radius:4px;"
            )
        elif errors > 0:
            self.info_label.setText(f"⚠ {errors} sensor(s) failed")
            self.info_label.setStyleSheet(
                "color:#d13438;background:#fde7e9;padding:4px;border-radius:4px;"
            )
        else:
            self.info_label.setText("⚠ Some sensors need attention")
            self.info_label.setStyleSheet(
                "color:#f7630c;background:#fff4ce;padding:4px;border-radius:4px;"
            )

    # ======================================================
    # INTERNALS
    # ======================================================

    def _on_check_clicked(self):
        if not self._request_cb:
            return

        self.btn_check.setEnabled(False)
        self.btn_check.setText("Checking...")
        self.info_label.setText("⏳ Requesting status...")
        self.info_label.setStyleSheet(
            "color:#0078d4;background:#e7f3ff;padding:4px;border-radius:4px;"
        )

        for lbl in self.labels.values():
            lbl.setText("...")
            lbl.setStyleSheet("color:#666;background:#f5f5f5;")

        self._timeout_timer.start(self.TIMEOUT_MS)
        self._request_cb()

    def _on_timeout(self):
        self.btn_check.setEnabled(True)
        self.btn_check.setText("Check Sensor Status")

        self.info_label.setText("⚠ No response from device")
        self.info_label.setStyleSheet(
            "color:#d13438;background:#fde7e9;padding:4px;border-radius:4px;"
        )

        for lbl in self.labels.values():
            if lbl.text() == "...":
                lbl.setText("TIMEOUT")
                lbl.setStyleSheet(
                    "color:#d13438;background:#fde7e9;padding:4px 8px;border-radius:4px;"
                )
