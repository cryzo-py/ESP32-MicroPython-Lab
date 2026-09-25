# -*- coding: utf-8 -*-
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox

class StudentIdentityDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Identité de l'élève")
        self.setModal(True)
        self.setFixedSize(300, 200)
        
        layout = QVBoxLayout(self)
        
        # Prénom
        lay_prenom = QHBoxLayout()
        lay_prenom.addWidget(QLabel("Prénom : "))
        self.le_prenom = QLineEdit()
        lay_prenom.addWidget(self.le_prenom)
        layout.addLayout(lay_prenom)
        
        # Nom
        lay_nom = QHBoxLayout()
        lay_nom.addWidget(QLabel("Nom : "))
        self.le_nom = QLineEdit()
        lay_nom.addWidget(self.le_nom)
        layout.addLayout(lay_nom)
        
        # Classe
        lay_classe = QHBoxLayout()
        lay_classe.addWidget(QLabel("Classe : "))
        self.le_classe = QLineEdit()
        lay_classe.addWidget(self.le_classe)
        layout.addLayout(lay_classe)
        
        layout.addStretch()
        
        # Bouton
        self.btn_valider = QPushButton("Valider et Commencer")
        self.btn_valider.setStyleSheet("background-color: #3498db; color: white; font-weight: bold; padding: 6px;")
        self.btn_valider.clicked.connect(self.validate)
        layout.addWidget(self.btn_valider)
        
    def validate(self):
        if not self.le_prenom.text().strip() or not self.le_nom.text().strip() or not self.le_classe.text().strip():
            QMessageBox.warning(self, "Attention", "Veuillez remplir tous les champs pour commencer l'activité.")
            return
        self.accept()
        
    def get_data(self):
        return {
            "prenom": self.le_prenom.text().strip(),
            "nom": self.le_nom.text().strip(),
            "classe": self.le_classe.text().strip()
        }
