from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt


class SummaryDialog(QDialog):
    """
    Test bitiminde özet bilgiyi gösteren açılan diyalog penceresi (SUMMARY)
    """

    def __init__(self, summary_text: str, parent=None):
        super().__init__(parent)
        self.setObjectName("SummaryDialog")
        self.setWindowTitle("Test Summary")
        self.setMinimumWidth(520)

        layout = QVBoxLayout(self)

        title = QLabel("Test Summary")
        title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setObjectName("SummaryTitle")
        layout.addWidget(title)

        label = QLabel(summary_text)
        label.setAlignment(Qt.AlignmentFlag.AlignTop)
        label.setWordWrap(True)
        label.setFont(QFont("Segoe UI", 11))
        layout.addWidget(label)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)
        layout.addLayout(btn_layout)

        self.setModal(True)
