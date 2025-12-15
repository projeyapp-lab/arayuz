from typing import Dict, List, Tuple

from PyQt6.QtWidgets import (
    QWidget,
    QGridLayout,
    QLabel,
    QCheckBox,
    QVBoxLayout,
    QHBoxLayout,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPen
import pyqtgraph as pg


class GraphPanel(QWidget):
    """8 ayrı grafiği rolling-window ve smooth autoscale ile çizer."""

    WINDOW_SECONDS = 30.0
    SMOOTH_FACTOR = 0.15
    MIN_MARGIN_RATIO = 0.10

    def __init__(self, parent=None):
        super().__init__(parent)

        pg.setConfigOptions(antialias=True)

        self.layout = QGridLayout(self)
        self.layout.setContentsMargins(4, 4, 4, 4)
        self.layout.setSpacing(6)

        self.plot_widgets: Dict[str, pg.PlotWidget] = {}
        self.curves: Dict[str, pg.PlotDataItem] = {}
        self.data: Dict[str, List[Tuple[float, float]]] = {}
        self.title_checkboxes: Dict[str, QCheckBox] = {}

        titles = {
            "thrust_kgf": "Thrust (kgf)",
            "voltage": "Voltage (V)",
            "current": "Current (A)",
            "rpm": "Motor Speed (RPM)",
            "temperature": "Temperature (°C)",
            "power": "Electrical Power (W)",
            "pt_eff": "PT Efficiency (kgf/W)",
            "tpa": "Thrust per Amp (kgf/A)",
        }

        units = {
            "thrust_kgf": "kgf",
            "voltage": "V",
            "current": "A",
            "rpm": "RPM",
            "temperature": "°C",
            "power": "W",
            "pt_eff": "kgf/W",
            "tpa": "kgf/A",
        }

        keys = list(titles.keys())

        # -------------------------------------------------------
        #             ANA GRAFİK OLUŞTURMA DÖNGÜSÜ
        # -------------------------------------------------------
        for i, key in enumerate(keys):
            row = i // 4
            col = i % 4

            # ————— Plot widget —————
            pw = pg.PlotWidget()

            left_axis = pw.getAxis("left")
            bottom_axis = pw.getAxis("bottom")

            black_pen = QPen(Qt.GlobalColor.black)
            left_axis.setTickFont(QFont("Segoe UI", 10))
            bottom_axis.setTickFont(QFont("Segoe UI", 10))
            left_axis.setPen(black_pen)
            bottom_axis.setPen(black_pen)
            left_axis.setTextPen(black_pen)
            bottom_axis.setTextPen(black_pen)

            pw.setBackground("#ffffff")
            pw.showGrid(x=True, y=True, alpha=0.25)

            pw.setLabel("left", units[key], color="black")
            pw.setLabel("bottom", "Time (s)", color="black")

            axis = pw.getAxis("bottom")
            axis.setTickSpacing(major=5, minor=1)
            axis.enableAutoSIPrefix(False)

            pw.setXRange(0, self.WINDOW_SECONDS, padding=0)

            curve = pw.plot([], [], pen=pg.mkPen("#0078ff", width=2))

            self.plot_widgets[key] = pw
            self.curves[key] = curve
            self.data[key] = []

            # ——————————————————————————————————————————————
            #             BAŞLIK + TİK KONTEYNERİ
            # ——————————————————————————————————————————————
            container = QWidget()
            vbox = QVBoxLayout(container)
            vbox.setContentsMargins(0, 0, 0, 0)
            vbox.setSpacing(2)

            title_widget = QWidget()
            title_row = QHBoxLayout(title_widget)
            title_row.setContentsMargins(0, 0, 0, 0)
            title_row.setSpacing(6)

            title_label = QLabel(titles[key])
            title_label.setObjectName("graphTitleLabel")

            checkbox = QCheckBox()
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(
                lambda state, k=key: self.set_curve_visible(
                    k, state == Qt.CheckState.Checked
                )
            )

            # Başlık + checkbox yan yana
            title_row.addWidget(title_label)
            title_row.addWidget(checkbox)

            # Ortalanmış başlık
            vbox.addWidget(title_widget, alignment=Qt.AlignmentFlag.AlignHCenter)
            vbox.addWidget(pw)

            self.title_checkboxes[key] = checkbox

            # Grid'e ekle
            self.layout.addWidget(container, row, col)

    # ============================================================
    #                       VERİ EKLEME
    # ============================================================
    def add_sample(self, key: str, t: float, value: float, visible: bool = True):
        if key not in self.data:
            return

        arr = self.data[key]
        arr.append((t, value))

        min_t = max(0.0, t - self.WINDOW_SECONDS)
        self.data[key] = [(tx, vy) for (tx, vy) in arr if tx >= min_t]

        xs = [tx for (tx, vy) in self.data[key]]
        ys = [vy for (tx, vy) in self.data[key]]

        pw = self.plot_widgets[key]
        curve = self.curves[key]

        if not visible:
            curve.setData([], [])
            return

        curve.setData(xs, ys)
        
        
        

        # ————— Y ekseni smooth autoscale —————
        if ys:
            y_min = min(ys)
            y_max = max(ys)

            if y_min == y_max:
                y_min -= 0.5
                y_max += 0.5

            span = y_max - y_min
            if span <= 0:
                span = abs(y_max) if y_max != 0 else 1.0

            margin = span * self.MIN_MARGIN_RATIO
            target_min = y_min - margin
            target_max = y_max + margin

            vb = pw.getPlotItem().vb
            current_min, current_max = vb.viewRange()[1]

            smooth_min = current_min + (target_min - current_min) * self.SMOOTH_FACTOR
            smooth_max = current_max + (target_max - current_max) * self.SMOOTH_FACTOR

            pw.setYRange(smooth_min, smooth_max, padding=0)

        if t < self.WINDOW_SECONDS:
            pw.setXRange(0, self.WINDOW_SECONDS, padding=0)
        else:
            pw.setXRange(min_t, t, padding=0)

    # ============================================================
    #                       GRAFİK TEMİZLEME
    # ============================================================
    def clear_all(self):
        for key in self.data:
            self.data[key] = []
            self.curves[key].setData([], [])
            self.plot_widgets[key].setXRange(0, self.WINDOW_SECONDS, padding=0)

    # ============================================================
    #                       SHOW / HIDE (tik)
    # ============================================================
    def set_curve_visible(self, key: str, visible: bool):
        curve = self.curves.get(key)
        if not curve:
            return

        if not visible:
            curve.setData([], [])
            return

        arr = self.data.get(key, [])
        if not arr:
            curve.setData([], [])
            return

        xs = [tx for (tx, vy) in arr]
        ys = [vy for (tx, vy) in arr]
        curve.setData(xs, ys)

    def export_png(self, file_path: str, width: int = 1920, height: int = 1080) -> None:
        """
        Export all 8 graphs as a single dashboard PNG 
        2x4 grid, her plot kendi hücresine yerleştirilir.
        """
        from PyQt6.QtGui import QImage, QPainter
        from PyQt6.QtCore import QRect

        # 1920x1080 beyaz arka planlı hedef görüntü
        image = QImage(width, height, QImage.Format.Format_ARGB32)
        image.fill(0xFFFFFFFF)  # beyaz

        painter = QPainter(image)

        try:
            # 2 satır x 4 sütun layout
            rows = 2
            cols = 4
            cell_w = width // cols
            cell_h = height // rows

            # self.plot_widgets: dict[str, PlotWidget]
            
            for index, pw in enumerate(self.plot_widgets.values()):
                row = index // cols
                col = index % cols

                x = col * cell_w
                y = row * cell_h
                target_rect = QRect(x, y, cell_w, cell_h)

                # Her plot widget'in snapshot'ını al (QPixmap)
                pixmap = pw.grab()

                # QPixmap → QImage ve hedef dikdörtgene çiz
                painter.drawImage(target_rect, pixmap.toImage())

        finally:
            # Her durumda painter düzgün kapansın (hata olsa bile)
            painter.end()

        # Son olarak image'i dosyaya kaydet
        image.save(file_path)
