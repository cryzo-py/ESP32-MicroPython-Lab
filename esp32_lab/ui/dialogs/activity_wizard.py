# -*- coding: utf-8 -*-
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QTextEdit, QComboBox, QSpinBox, 
                               QPushButton, QFrame)
from PySide6.QtCore import Qt

class ActivityWizardDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Assistant de Création d'Activité")
        self.resize(600, 500)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Header
        header = QLabel("Étape 1 : Informations de l'Activité")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #38bdf8;")
        layout.addWidget(header)
        
        # Title
        layout.addWidget(QLabel("Titre de l'activité :"))
        self.txt_title = QLineEdit()
        self.txt_title.setPlaceholderText("Ex: TP 1 - Clignotement de LED")
        layout.addWidget(self.txt_title)
        
        # Type and Duration
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Type :"))
        self.cb_type = QComboBox()
        self.cb_type.addItems(["TP (Libre avec indices)", "EXAM (Chronométré, strict)"])
        row1.addWidget(self.cb_type)
        
        row1.addSpacing(20)
        row1.addWidget(QLabel("Durée (minutes) :"))
        self.spin_duration = QSpinBox()
        self.spin_duration.setRange(0, 300)
        self.spin_duration.setValue(0)
        self.spin_duration.setToolTip("0 = Illimité")
        row1.addWidget(self.spin_duration)
        row1.addSpacing(20)
        row1.addWidget(QLabel("Barème (sur) :"))
        self.spin_score = QSpinBox()
        self.spin_score.setRange(0, 100)
        self.spin_score.setValue(20)
        row1.addWidget(self.spin_score)
        row1.addStretch()
        layout.addLayout(row1)

        # Board and Language Selection
        row_board = QHBoxLayout()
        row_board.addWidget(QLabel("Carte & Langage :"))
        self.cb_board = QComboBox()
        self.cb_board.addItem("ESP32 DevKit V1 — MicroPython", "esp32_wroom_32")
        self.cb_board.addItem("Arduino Uno R3 — C++ (sketch.ino)", "arduino_uno")
        row_board.addWidget(self.cb_board)
        row_board.addStretch()
        layout.addLayout(row_board)
        
        # Description
        layout.addWidget(QLabel("Énoncé / Instructions pour l'élève :"))
        self.txt_desc = QTextEdit()
        self.txt_desc.setPlaceholderText("Rédigez le contexte et la mission de l'élève ici...")
        layout.addWidget(self.txt_desc)
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_cancel = QPushButton("Annuler")
        self.btn_cancel.clicked.connect(self.reject)
        
        self.btn_next = QPushButton("Suivant : Préparer le Montage ➡️")
        self.btn_next.setStyleSheet("background-color: #0284c7; color: white; font-weight: bold;")
        self.btn_next.clicked.connect(self.accept)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_next)
        
        layout.addLayout(btn_layout)


    def load_data(self, data: dict):
        self.txt_title.setText(data.get("title", ""))
        self.txt_desc.setPlainText(data.get("description", ""))
        self.spin_duration.setValue(data.get("duration", 30))
        if hasattr(self, "spin_score"):
            self.spin_score.setValue(data.get("max_score", 20))
        act_type = data.get("type", "TP").upper()
        if hasattr(self, "cb_type"):
            self.cb_type.setCurrentIndex(1 if act_type == "EXAM" else 0)
        if hasattr(self, "cb_board"):
            board_id = data.get("board_id", "esp32_wroom_32")
            idx = self.cb_board.findData(board_id)
            if idx >= 0:
                self.cb_board.setCurrentIndex(idx)

    def get_activity_data(self):
        act_type = "EXAM" if "EXAM" in self.cb_type.currentText() else "TP"
        board_id = self.cb_board.currentData() if hasattr(self, "cb_board") else "esp32_wroom_32"
        language = "arduino" if board_id == "arduino_uno" else "micropython"
        return {
            "title": self.txt_title.text().strip() or "Nouvelle Activité",
            "type": act_type,
            "duration": self.spin_duration.value(),
            "max_score": getattr(self, "spin_score", None) and self.spin_score.value() or 20,
            "board_id": board_id,
            "language": language,
            "description": self.txt_desc.toPlainText()
        }
