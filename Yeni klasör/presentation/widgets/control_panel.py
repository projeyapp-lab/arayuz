from typing import Dict

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QPushButton,
    QLineEdit,
    QGridLayout,
    QCheckBox,
    QFileDialog,
    QSizePolicy
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt


class ControlPanel(QWidget):
    """
    Temiz, kurumsal, optimized Control Panel:
    - Üstte TEST KARTI: Start / Stop / Reset + Test Name + Output Folder
    - Altta grafik gösterim checkbox'ları
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # ======================================================
        # ANA LAYOUT
        # ======================================================
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(8)

        # ======================================================
        # TEST CONTROL  (Start/Stop/Reset + Test/Folder)
        # ======================================================
    
        #  COMPACT TEST CONTROL CARD
        # ==========================================================

        test_frame = QFrame()
        test_frame.setObjectName("TestFrame")
        test_frame.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)


        test_layout = QVBoxLayout(test_frame)
        test_layout.setContentsMargins(8, 6, 8, 6)   
        test_layout.setSpacing(6)

        #Tek satır control bar (en alt kısma)

        bar = QHBoxLayout()
        bar.setSpacing(8)

        #Start / stop / reset

        self.btn_start_test = QPushButton("Start")
        self.btn_start_test.setFixedSize(60, 24)

        self.btn_stop_test = QPushButton("Stop")
        self.btn_start_test.setFixedSize(60, 24)
        self.btn_stop_test.setEnabled(False)

        self.btn_reset = QPushButton("Reset")
        self.btn_reset.setFixedSize(60, 24)

        bar.addWidget(self.btn_start_test)
        bar.addWidget(self.btn_stop_test)
        bar.addWidget(self.btn_reset)

        #-- Test Name -- 

        bar.addSpacing(10)
        bar.addWidget(QLabel("Test:"))

        self.test_name_edit = QLineEdit()
        self.test_name_edit.setPlaceholderText("Name")
        self.test_name_edit.setFixedSize(90, 22)
        bar.addWidget(self.test_name_edit)

        # --- Folder + Browse ---


        bar.addSpacing(10)
        bar.addWidget(QLabel("Folder:"))

        self.output_edit = QLineEdit()
        self.output_edit.setPlaceholderText("Select...")
        self.output_edit.setFixedSize(90, 22)
        bar.addWidget(self.output_edit)

        self.btn_browse = QPushButton("Browse")
        self.btn_browse.setFixedSize(70, 22)
        bar.addWidget(self.btn_browse)

        bar.addStretch()

        
        test_layout.addLayout(bar)

        # ince uzun ayar kısmı
        test_frame.setFixedHeight(50)



        card_row = QHBoxLayout()
        card_row.setContentsMargins(0, 0, 0, 0)
        card_row.setSpacing(0)

        card_row.addWidget(test_frame)
        card_row.addStretch()

        main_layout.addLayout(card_row)



        # ======================================================
        # BROWSE SIGNAL
        # ======================================================
        self.btn_browse.clicked.connect(self._choose_folder)

    # ==================================================================
    # FOLDER SEÇME
    # ==================================================================
    def _choose_folder(self):
        path = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if path:
            self.output_edit.setText(path)

    # ==================================================================
    # TEST DURUMU (main_window tarafından çağrılıyor)
    # ==================================================================
    def set_test_status(self, active: bool):
        self.btn_start_test.setEnabled(not active)
        self.btn_stop_test.setEnabled(active)
