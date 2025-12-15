import os
import csv
import time
import ctypes
from pathlib import Path

import serial
from serial.tools import list_ports

from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QMessageBox,
    QLabel,
    QFrame,
    QComboBox,
    QPushButton,
)

from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtCore import Qt, QTimer

from presentation.widgets.summary_dialog import SummaryDialog
from presentation.widgets.left_panel import LeftDataPanel
from presentation.widgets.graph_panel import GraphPanel
from presentation.widgets.control_panel import ControlPanel
from data.serial_repository import SerialRepository
from domain.ports import SerialPortReader
from presentation.widgets.sensor_status_panel import SensorStatusPanel



class MainWindow(QMainWindow):
    """
    GMK AIR – Motor Test Unit ana penceresi.


    """

    def _check_sensor_status(self):
        if not self.ser or not self.ser.is_open:
            return

        try:
            self.ser.write(b"STATUS?\n")
            line = self.ser.readline().decode("utf-8", errors="ignore").strip()
        except Exception:
            return

        if not line.startswith("STATUS"):
            return

        parts = line.split(",")[1:]
        status = {}

        for p in parts:
            if ":" in p:
                k, v = p.split(":", 1)
                status[k] = v

        self.sensor_status_panel.update_status(status)

    def _fix_messagebox_theme(self, box: QMessageBox):
        """Tüm uyarı pencerelerinde beyaz arka plan ve okunaklı butonlar kullan."""
        box.setStyleSheet(
            """
        QMessageBox {
            background-color: #ffffff;
        }
        QLabel {
            color: #000000;
            font-size: 11pt;
        }
        QPushButton {
            background-color: #00b4aa;
            color: #ffffff;
            padding: 6px 14px;
            border-radius: 6px;
            font-size: 10pt;
        }
        QPushButton:hover {
            background-color: #009a92;
        }
        """
        )

    def __init__(self):
        super().__init__()

        # DPI fix (Windows)
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass

        self.setWindowTitle("GMK AIR Motor Test Unit v1.0")

        self.setWindowFlags(Qt.WindowType.Window)
        self.setMinimumSize(1280, 720)
        self.resize(1280, 760)
        self.setGeometry(100, 100, 1280, 760)
        self.showNormal()

        central = QWidget(self)
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(6)

        header = self._build_header()
        main_layout.addWidget(header)

        center_layout = QHBoxLayout()
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(8)

        self.sensor_status_panel = SensorStatusPanel(self)
        self.sensor_status_panel.set_status_request_callback(
            self._check_sensor_status
        )

        self.left_panel = LeftDataPanel(self)
        self.graph_panel = GraphPanel(self)



        left_column = QVBoxLayout()
        left_column.setSpacing(8)
        left_column.addWidget(self.sensor_status_panel)
        left_column.addWidget(self.left_panel)
        left_column.addStretch()

        center_layout.addLayout(left_column, stretch=1)
        center_layout.addWidget(self.graph_panel, stretch=5)

        main_layout.addLayout(center_layout, stretch=4)
        main_layout.addSpacing(4)

        self.control_panel = ControlPanel(self)
        #main_layout.addWidget(self.control_panel, stretch=1)

        main_layout.addStretch()
        main_layout.addWidget(self.control_panel)


        # Serial / zaman / logging / segment state
        self.ser: serial.Serial | None = None
        self.serial_repo: SerialPortReader | None = None
        self.read_timer = QTimer(self)
        self.read_timer.setInterval(100)  # 10 Hz
        self.read_timer.timeout.connect(self._poll_serial)

        self.stream_start_time: float | None = None
        self.segment_start_time: float | None = None
        self.segment_active: bool = False
        self.segment_index: int = 0

        self.logging_enabled = False
        self.log_file = None
        self.log_writer: csv.writer | None = None
        self.current_log_path: str | None = None

        self.segment_stats = None

        self._connect_control_signals()
        self._refresh_ports()
        self._update_status_label("idle")

    def _build_header(self) -> QWidget:
        frame = QFrame(self)
        frame.setObjectName("HeaderFrame")

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(16)

        # -------------------------------------------------------
        # LOGO
        # -------------------------------------------------------
        logo_label = QLabel()
        root_dir = Path(__file__).resolve().parent.parent
        logo_06 = root_dir / "gmkair-logo-06.png"
        logo_05 = root_dir / "gmkair-logo-05.png"

        pix = QPixmap()
        if logo_06.exists():
            pix.load(str(logo_06))
        elif logo_05.exists():
            pix.load(str(logo_05))

        if not pix.isNull():
            pix = pix.scaled(
                42,
                42,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            logo_label.setPixmap(pix)
        logo_label.setFixedSize(50, 50)

        # -------------------------------------------------------
        # BAŞLIK METİNLERİ
        # -------------------------------------------------------
        text_container = QWidget()
        text_layout = QVBoxLayout(text_container)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(0)

        title = QLabel("GMK AIR Motor Test Unit")
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))

        subtitle = QLabel("Drone Motor / ESC / Propeller Thrust & Efficiency Bench")
        subtitle.setFont(QFont("Segoe UI", 9))

        text_layout.addWidget(title)
        text_layout.addWidget(subtitle)

        # -------------------------------------------------------
        # CONNECTION PANEL (Strong Corporate Card)
        # -------------------------------------------------------
        conn_frame = QFrame()
        conn_frame.setObjectName("ConnFrame")
        conn_layout = QHBoxLayout(conn_frame)
        conn_layout.setContentsMargins(10, 6, 10, 6)
        conn_layout.setSpacing(8)

        lbl_com = QLabel("COM Port:")
        self.port_combo = QComboBox()
        self.port_combo.setFixedWidth(120)

        self.btn_refresh_ports = QPushButton("Refresh")
        self.btn_refresh_ports.setFixedWidth(80)

        self.btn_connect = QPushButton("Connect")
        self.btn_connect.setFixedWidth(80)

        self.btn_disconnect = QPushButton("Disconnect")
        self.btn_disconnect.setFixedWidth(90)
        self.btn_disconnect.setEnabled(False)

        conn_layout.addWidget(lbl_com)
        conn_layout.addWidget(self.port_combo)
        conn_layout.addWidget(self.btn_refresh_ports)
        conn_layout.addWidget(self.btn_connect)
        conn_layout.addWidget(self.btn_disconnect)

        # -------------------------------------------------------
        # STATUS LABEL (stilini _update_status_label zaten değiştirecek)
        # -------------------------------------------------------
        self.status_label = QLabel("STATUS: IDLE")
        self.status_label.setObjectName("StatusLabel")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setMinimumWidth(150)
        self.status_label.setFixedHeight(40)

        # -------------------------------------------------------
        # HEADER LAYOUT
        # -------------------------------------------------------
        layout.addWidget(logo_label)
        layout.addWidget(text_container, stretch=1)
        layout.addWidget(conn_frame)        # Connection kartı
        layout.addWidget(self.status_label) # Sağda status kutusu

        return frame



    def _update_status_label(self, mode: str):
        """
        mode:
          - "idle"
          - "connected"
          - "active"
          - "error"
        """
        if mode == "connected":
            text = "STATUS: CONNECTED"
        elif mode == "active":
            text = "STATUS: TEST ACTIVE"
        elif mode == "error":
            text = "STATUS: ERROR"
        else:
            text = "STATUS: IDLE"
            mode = "idle"

        self.status_label.setText(text)
        self.status_label.setProperty("status", mode)
        # Re-polish to apply QSS for the updated dynamic property.
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)

    # Kontrol paneli sinyalleri
    def _connect_control_signals(self):
        cp = self.control_panel

        # Connection bar (header'daki)
        self.btn_refresh_ports.clicked.connect(self._refresh_ports)
        self.btn_connect.clicked.connect(self._connect_serial)
        self.btn_disconnect.clicked.connect(self._disconnect_serial)

        # Aşağıdaki kontrol paneli
        cp.btn_start_test.clicked.connect(self._start_test_segment)
        cp.btn_reset.clicked.connect(self._reset_test)
        cp.btn_stop_test.clicked.connect(
            lambda _checked=False: self._stop_test_segment(show_summary=True)
        )


        
    # Serial port yönetimi
    def _refresh_ports(self):
        self.port_combo.clear()
        ports = list_ports.comports()
        if not ports:
            self.port_combo.addItem("No ports")
            return
        for p in ports:
            self.port_combo.addItem(p.device)


    def _connect_serial(self):
        if self.ser and self.ser.is_open:
            box = QMessageBox(
                QMessageBox.Icon.Information, "Serial", "Already connected."
            )
            self._fix_messagebox_theme(box)
            box.exec()
            return

        port_text = self.port_combo.currentText()
        if not port_text or port_text == "No ports":
            box = QMessageBox(
                QMessageBox.Icon.Warning, "Serial", "Select a valid COM port."
            )
            self._fix_messagebox_theme(box)
            box.exec()

            return

        try:
            self.ser = serial.Serial(port_text, baudrate=115200, timeout=0.1)
        except serial.SerialException as e:
            box = QMessageBox(
                QMessageBox.Icon.Critical, "Serial", f"Port could not be opened:\n{e}"
            )
            self._fix_messagebox_theme(box)
            box.exec()

            self.ser = None
            self._update_status_label("error")
            return

        self.stream_start_time = time.monotonic()
        self.read_timer.start()

        self.btn_connect.setEnabled(False)
        self.btn_disconnect.setEnabled(True)
        self.serial_repo = SerialRepository(self.ser)


        self._update_status_label("connected")
        box = QMessageBox(
            QMessageBox.Icon.Information, "Serial", f"{port_text} connected."
        )
        self._fix_messagebox_theme(box)
        box.exec()

    def _disconnect_serial(self):
        self.read_timer.stop()
        if self.ser:
            try:
                self.ser.close()
            except serial.SerialException:
                pass
            self.ser = None
            self.serial_repo = None


        if self.segment_active:
            self._stop_test_segment(show_summary=False)

        self._update_status_label("idle")
        self.control_panel.set_test_status(active=False)
        self.btn_connect.setEnabled(True)
        self.btn_disconnect.setEnabled(False)


        box = QMessageBox(QMessageBox.Icon.Information, "Serial", "Connection closed.")
        self._fix_messagebox_theme(box)
        box.exec()

    def _reset_test(self):
        """Test duruyken grafikleri ve canlı verileri sıfırlar."""
        if self.segment_active:
            box = QMessageBox(
                QMessageBox.Icon.Warning,
                "Reset",
                "Reset için önce testi durdur (Stop Test).",
            )
            self._fix_messagebox_theme(box)
            box.exec()
            return

        # Grafikleri temizle
        self.graph_panel.clear_all()

        # Segment istatistiklerini ve indexi sıfırla
        self.segment_stats = None
        self.segment_index = 0

        # Sol paneldeki canlı verileri sıfırla
        self.left_panel.update_values(
            voltage="0.000",
            current="0.000",
            thrust_kgf="0.0000",
            temperature="0.00",
            rpm="0",
            power="0.00",
            pt_eff="0.000000",
            tpa="0.000000",
        )

    # Test / logging yönetimi
    def _start_test_segment(self):
        if not self.ser or not self.ser.is_open:
            box = QMessageBox(
                QMessageBox.Icon.Warning, "Test", "Connect to a COM port first."
            )
            self._fix_messagebox_theme(box)
            box.exec()
            return

        if self.segment_active:
            self._stop_test_segment(show_summary=True)

        self.segment_index += 1
        self.segment_active = True
        self.segment_start_time = time.monotonic()
        self.stream_start_time = self.segment_start_time

        self.graph_panel.clear_all()
        self._reset_segment_stats()

        if not self._start_logging_segment():
            # logging başlatılamadı ama test yine de çalışabilir
            pass

        self.control_panel.set_test_status(active=True)
        self._update_status_label("active")

    def _stop_test_segment(self, show_summary: bool = True):
        if not self.segment_active:
            return

        self.segment_active = False
        if self.segment_stats is not None:
            self.segment_stats["end_time"] = time.monotonic()

        self._stop_logging()
        self.control_panel.set_test_status(active=False)

        # Bağlantı duruyorsa CONNECTED'e, yoksa IDLE'a dön
        if self.ser and self.ser.is_open:
            self._update_status_label("connected")
        else:
            self._update_status_label("idle")

        if show_summary and self.segment_stats is not None:
            self._show_segment_summary()

        self.segment_stats = None

    def _reset_segment_stats(self):
        keys = [
            "thrust_kgf",
            "current",
            "voltage",
            "temperature",
            "rpm",
            "pt_eff",
            "tpa",
        ]
        self.segment_stats = {
            "start_time": self.segment_start_time,
            "end_time": None,
            "count": 0,
            "sum": {k: 0.0 for k in keys},
            "max": {k: None for k in keys},
            "min": {k: None for k in keys},
        }

    # Logging
    def _resolve_output_folder_and_name(self):
        folder = self.control_panel.output_edit.text().strip()
        if not folder or not os.path.isdir(folder):
            return None, None

        base_name = self.control_panel.test_name_edit.text().strip()
        if not base_name:
            base_name = "test"

        return folder, base_name

    def _start_logging_segment(self) -> bool:
        if self.logging_enabled:
            return True

        folder, base_name = self._resolve_output_folder_and_name()
        if folder is None:
            # klasör seçilmemişse logging devre dışı, test akmaya devam eder
            return False

        filename = f"{base_name}_segment{self.segment_index}.csv"
        path = os.path.join(folder, filename)

        try:
            self.log_file = open(path, "w", newline="", encoding="utf-8")
        except OSError as e:
            QMessageBox.critical(self, "Logging", f"File could not be opened:\n{e}")
            self.log_file = None
            return False

        self.log_writer = csv.writer(self.log_file, delimiter=";")
        header = [
            "time_s",
            "voltage_V",
            "current_A",
            "thrust_kgf",
            "temperature_C",
            "rpm",
            "power_W",
            "pt_eff_kgf_per_W",
            "tpa_kgf_per_A",
        ]
        self.log_writer.writerow(header)
        self.logging_enabled = True
        self.current_log_path = path
        return True

    def _stop_logging(self):
        if not self.logging_enabled:
            return
        self.logging_enabled = False
        if self.log_file:
            try:
                self.log_file.flush()
                self.log_file.close()
            except OSError:
                pass
        self.log_file = None
        self.log_writer = None
        self.current_log_path = None

    def _format_csv_value(self, key, value):
            if value is None:
                return ""

            try:
                num = float(value)
            except:
                return str(value)

            # Alanlara göre gösterilecek hassasiyet
            precision = {
                "time_s": 3,
                "voltage": 3,
                "current": 3,
                "thrust_kgf": 3,
                "temperature": 2,
                "rpm": 0,
                "power": 3,
                "pt_eff": 4,
                "tpa": 4,
            }

            p = precision.get(key, 3)

            # Excel’in TARİH saçmalığını engellemek için başa '=' koyuyoruz
            return f"={num:.{p}f}"





    # Serial'den veri okuma
    def _poll_serial(self):
        if not self.serial_repo:
            return

        try:
            for values in self.serial_repo.read_available():
                self._update_ui_with_values(values)
        except serial.SerialException:
            self._update_status_label("error")
            self._disconnect_serial()

    # UI güncelleme + grafik + logging + istatistik
    def _update_ui_with_values(self, values: dict):
        now = time.monotonic()
        if self.stream_start_time is None:
            self.stream_start_time = now

        if self.segment_active and self.segment_start_time is not None:
            t = now - self.segment_start_time
        else:
            t = now - self.stream_start_time

            # --- SENSOR STATUS UI UPDATE ---
            if "sensor_status" in values:
                s = values["sensor_status"]  # örn: {"V":"READY","LC":"READY","T":"READY","I":"READY","RPM":"READY"}
                self.sensor_status_panel.update_status(
                    voltage=s.get("V", "--"),
                    loadcell=s.get("LC", "--"),
                    temperature=s.get("T", "--"),
                    current=s.get("I", "--"),
                    rpm=s.get("RPM", "--"),
                )

        left_updates = {}
        if "voltage" in values:
            left_updates["voltage"] = f"{values['voltage']:.3f}"
        if "current" in values:
            left_updates["current"] = f"{values['current']:.3f}"
        if "thrust_kgf" in values:
            left_updates["thrust_kgf"] = f"{values['thrust_kgf']:.4f}"
        if "temperature" in values:
            left_updates["temperature"] = f"{values['temperature']:.2f}"
        if "rpm" in values:
            left_updates["rpm"] = f"{values['rpm']:.0f}"
        if "power" in values:
            left_updates["power"] = f"{values['power']:.2f}"
        if "pt_eff" in values:
            left_updates["pt_eff"] = f"{values['pt_eff']:.6f}"
        if "tpa" in values:
            left_updates["tpa"] = f"{values['tpa']:.6f}"

        if left_updates:
            self.left_panel.update_values(**left_updates)

        if self.segment_active:
            for key in (
                "thrust_kgf",
                "voltage",
                "current",
                "rpm",
                "temperature",
                "power",
                "pt_eff",
                "tpa",
            ):
                if key in values:
                    visible = self.graph_panel.title_checkboxes[key].isChecked()

                    self.graph_panel.add_sample(key, t, values[key], visible=visible)

            if self.logging_enabled and self.log_writer is not None:
                row = [
                    self._format_csv_value("time_s", t),
                    self._format_csv_value("voltage", values.get("voltage")),
                    self._format_csv_value("current", values.get("current")),
                    self._format_csv_value("thrust_kgf", values.get("thrust_kgf")),
                    self._format_csv_value("temperature", values.get("temperature")),
                    self._format_csv_value("rpm", values.get("rpm")),
                    self._format_csv_value("power", values.get("power")),
                    self._format_csv_value("pt_eff", values.get("pt_eff")),
                    self._format_csv_value("tpa", values.get("tpa")),
                ]

                self.log_writer.writerow(row)


            self._update_segment_stats(values)

    def _update_segment_stats(self, values: dict):
        if self.segment_stats is None:
            return

        keys = self.segment_stats["sum"].keys()
        self.segment_stats["count"] += 1

        for k in keys:
            v = values.get(k)
            if v is None:
                continue
            self.segment_stats["sum"][k] += v

            cur_max = self.segment_stats["max"][k]
            cur_min = self.segment_stats["min"][k]

            if cur_max is None or v > cur_max:
                self.segment_stats["max"][k] = v
            if cur_min is None or v < cur_min:
                self.segment_stats["min"][k] = v

    # Summary
    def _show_segment_summary(self):
        stats = self.segment_stats
        if not stats or stats["count"] == 0:
            box = QMessageBox(
                QMessageBox.Icon.Information, "Summary", "No data in this segment."
            )
            self._fix_messagebox_theme(box)
            box.exec()
            return

        duration = (
            stats["end_time"] - stats["start_time"] if stats["end_time"] else 0.0
        )
        n = stats["count"]

        def avg(key):
            s = stats["sum"].get(key)
            return (s / n) if (s is not None and n > 0) else None

        def fmt(val, fmt_str):
            if val is None:
                return "--"
            return fmt_str.format(val)

        lines = []
        lines.append(f"Segment #{self.segment_index}")
        lines.append(f"Duration: {duration:.2f} s")
        lines.append(f"Sample count: {n}")
        lines.append("")
        lines.append(
            f"Average Thrust: {fmt(avg('thrust_kgf'), '{:.4f}')} kgf"
        )
        lines.append(
            f"Max Thrust: {fmt(stats['max']['thrust_kgf'], '{:.4f}')} kgf"
        )

        lines.append("")
        lines.append(f"Average Current: {fmt(avg('current'), '{:.3f}')} A")
        lines.append(f"Max Current: {fmt(stats['max']['current'], '{:.3f}')} A")
        lines.append("")
        lines.append(f"Average Voltage: {fmt(avg('voltage'), '{:.3f}')} V")
        lines.append(f"Min Voltage: {fmt(stats['min']['voltage'], '{:.3f}')} V")
        lines.append("")
        lines.append(f"Average Temperature: {fmt(avg('temperature'), '{:.2f}')} °C")
        lines.append(
            f"Max Temperature: {fmt(stats['max']['temperature'], '{:.2f}')} °C"
        )
        lines.append("")
        lines.append(f"Average RPM: {fmt(avg('rpm'), '{:.0f}')}")
        lines.append(f"Max RPM: {fmt(stats['max']['rpm'], '{:.0f}')}")
        lines.append("")
        lines.append(
            f"Average PT Efficiency: {fmt(avg('pt_eff'), '{:.6f}')} kgf/W"
        )
        lines.append(
            f"Average Thrust per Amp: {fmt(avg('tpa'), '{:.6f}')} kgf/A"
        )
        lines.append("")

        if self.current_log_path:
            lines.append(f"CSV file: {self.current_log_path}")

        folder, base_name = self._resolve_output_folder_and_name()
        if folder is not None:
            png_path = os.path.join(
                folder, f"{base_name}_segment{self.segment_index}.png"
            )
            try:
                self.graph_panel.export_png(png_path)
                lines.append(f"Graph PNG: {png_path}")
            except Exception:
                pass

        text = "\n".join(lines)
        dlg = SummaryDialog(text, self)
        dlg.exec()



    def _check_sensor_status(self):
        if not self.ser or not self.ser.is_open:
            return
        try:
            self.ser.write(b"STATUS?\n")
        except Exception:
            pass
