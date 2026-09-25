from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QScrollArea, QFrame, QHBoxLayout
)
from PySide6.QtCore import Qt, Signal

class FeedbackPanel(QWidget):
    request_hint = Signal()
    request_retry = Signal()
    request_next = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.setVisible(False)
        
    def _setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(8, 8, 8, 8)
        self.layout.setSpacing(10)
        
        self.setStyleSheet("background-color: #1e293b; border-radius: 4px; border: 1px solid #334155;")
        
        self.title_lbl = QLabel("")
        self.title_lbl.setStyleSheet("font-weight: bold; font-size: 16px; border: none;")
        self.layout.addWidget(self.title_lbl)
        
        self.msg_lbl = QLabel("")
        self.msg_lbl.setWordWrap(True)
        self.msg_lbl.setStyleSheet("font-size: 13px; border: none;")
        self.layout.addWidget(self.msg_lbl)
        
        self.hints_layout = QVBoxLayout()
        self.layout.addLayout(self.hints_layout)
        
        btn_layout = QHBoxLayout()
        self.btn_hint = QPushButton("💡 Indice")
        self.btn_hint.setStyleSheet("background-color: #3b82f6; color: white; padding: 6px; border: none; border-radius: 3px;")
        self.btn_hint.clicked.connect(self.request_hint.emit)
        
        self.btn_retry = QPushButton("↻ Réessayer")
        self.btn_retry.setStyleSheet("background-color: #475569; color: white; padding: 6px; border: none; border-radius: 3px;")
        self.btn_retry.clicked.connect(self.request_retry.emit)
        
        self.btn_next = QPushButton("Continuer ➔")
        self.btn_next.setStyleSheet("background-color: #10b981; color: white; padding: 6px; border: none; border-radius: 3px;")
        self.btn_next.clicked.connect(self.request_next.emit)
        self.btn_next.setVisible(False)
        
        btn_layout.addWidget(self.btn_hint)
        btn_layout.addWidget(self.btn_retry)
        btn_layout.addWidget(self.btn_next)
        
        self.layout.addLayout(btn_layout)
        
    def show_failure(self, feedbacks):
        self.setVisible(True)
        self.title_lbl.setText("❌ Évaluation échouée")
        self.title_lbl.setStyleSheet("font-weight: bold; font-size: 16px; color: #ef4444; border: none;")
        
        if feedbacks:
            fb = feedbacks[0]
            self.msg_lbl.setText(f"<b>{fb.title}</b><br><br>{fb.message}<br><br><i>{fb.pedagogical_explanation}</i>")
        else:
            self.msg_lbl.setText("Une erreur inattendue est survenue.")
            
        self._clear_hints()
        self.btn_hint.setVisible(True)
        self.btn_retry.setVisible(True)
        self.btn_next.setVisible(False)
        
    def show_success(self):
        self.setVisible(True)
        self.title_lbl.setText("🎉 Objectif Atteint !")
        self.title_lbl.setStyleSheet("font-weight: bold; font-size: 16px; color: #10b981; border: none;")
        self.msg_lbl.setText("Bravo ! Tous les critères ont été validés avec succès.")
        
        self._clear_hints()
        self.btn_hint.setVisible(False)
        self.btn_retry.setVisible(False)
        self.btn_next.setVisible(True)
        
    def add_hint(self, text: str, level: int):
        lbl = QLabel(f"💡 Indice {level} : {text}")
        lbl.setWordWrap(True)
        lbl.setStyleSheet("color: #fbbf24; background-color: #334155; padding: 6px; border-radius: 3px; border: none;")
        self.hints_layout.addWidget(lbl)
        
    def _clear_hints(self):
        while self.hints_layout.count():
            item = self.hints_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
