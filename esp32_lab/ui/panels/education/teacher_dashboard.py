# -*- coding: utf-8 -*-
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QFrame, QSpacerItem, QSizePolicy)
from PySide6.QtCore import Qt, Signal
from .grading_panel import GradingPanelWidget

class TeacherDashboardWidget(QWidget):
    create_activity_requested = Signal()
    open_submission_requested = Signal(str)
    back_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("TeacherDashboardWidget")
        self._setup_ui()
        self.grading_panel.open_submission_requested.connect(self.open_submission_requested.emit)

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(20)

        # Header
        header_layout = QHBoxLayout()
        title_lbl = QLabel("🎓 Espace Enseignant")
        title_lbl.setStyleSheet("font-size: 28px; font-weight: bold; color: #f8fafc;")
        
        self.btn_back = QPushButton("🔙 Retour à l'accueil")
        self.btn_back.setStyleSheet("padding: 8px 16px; background-color: #334155; color: white; border-radius: 4px;")
        self.btn_back.setCursor(Qt.PointingHandCursor)
        self.btn_back.clicked.connect(self.back_requested.emit)
        self.btn_back.setVisible(False)
        
        header_layout.addWidget(title_lbl)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_back)
        
        main_layout.addLayout(header_layout)
        
        # Line separator
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #334155;")
        main_layout.addWidget(line)

        # Content Layout
        content_layout = QHBoxLayout()
        
        # Left side: Authoring Tools
        author_layout = QVBoxLayout()
        author_layout.setAlignment(Qt.AlignTop)
        
        create_box = QFrame()
        create_box.setStyleSheet("background-color: #1e293b; border-radius: 8px; padding: 20px;")
        create_box_layout = QVBoxLayout(create_box)
        
        lbl_create_title = QLabel("Création d'Activité")
        lbl_create_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #38bdf8;")
        lbl_create_desc = QLabel("Créez un nouveau TP ou Examen avec correction automatique (v4.0).")
        lbl_create_desc.setStyleSheet("color: #94a3b8; margin-bottom: 10px;")
        
        self.btn_create = QPushButton("➕ Créer une Nouvelle Activité")
        self.btn_create.setCursor(Qt.PointingHandCursor)
        self.btn_create.setStyleSheet("""
            QPushButton {
                background-color: #0284c7; color: white; font-weight: bold;
                padding: 12px 20px; border-radius: 6px; font-size: 14px;
            }
            QPushButton:hover { background-color: #0369a1; }
        """)
        self.btn_create.clicked.connect(self.create_activity_requested.emit)
        
        create_box_layout.addWidget(lbl_create_title)
        create_box_layout.addWidget(lbl_create_desc)
        create_box_layout.addWidget(self.btn_create)
        
        author_layout.addWidget(create_box)
        
                # Right side: Mass grading Panel
        self.grading_panel = GradingPanelWidget()
        self.grading_panel.setStyleSheet("background-color: #1e293b; border-radius: 8px; padding: 10px;")
        
        content_layout.addLayout(author_layout, 1)
        content_layout.addSpacing(20)
        content_layout.addWidget(self.grading_panel, 2)
        
        main_layout.addLayout(content_layout)
        main_layout.addStretch(1)
