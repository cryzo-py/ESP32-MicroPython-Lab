from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QScrollArea, QFrame, QHBoxLayout
)
from PySide6.QtCore import Qt

class MissionPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header = QLabel("🎯 Mission")
        header.setStyleSheet("font-weight: bold; font-size: 14px; padding: 6px; background-color: #1e293b; color: #f8fafc;")
        layout.addWidget(header)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background-color: transparent; }")
        
        content_widget = QWidget()
        content_widget.setStyleSheet("background-color: transparent;")
        self.content_layout = QVBoxLayout(content_widget)
        self.content_layout.setAlignment(Qt.AlignTop)
        
        self.title_lbl = QLabel("Sélectionnez un exercice à gauche")
        self.title_lbl.setStyleSheet("font-weight: bold; font-size: 16px; color: #38bdf8;")
        self.title_lbl.setWordWrap(True)
        self.content_layout.addWidget(self.title_lbl)
        
        self.context_lbl = QLabel("")
        self.context_lbl.setWordWrap(True)
        self.context_lbl.setStyleSheet("color: #94a3b8; font-style: italic; margin-bottom: 10px;")
        self.content_layout.addWidget(self.context_lbl)
        
        self.mission_lbl = QLabel("")
        self.mission_lbl.setWordWrap(True)
        self.mission_lbl.setStyleSheet("font-size: 13px;")
        self.content_layout.addWidget(self.mission_lbl)
        
        self.constraints_lbl = QLabel("")
        self.constraints_lbl.setWordWrap(True)
        self.constraints_lbl.setStyleSheet("color: #fbbf24; margin-top: 10px;")
        self.content_layout.addWidget(self.constraints_lbl)
        
        # Section Objectifs Techniques
        obj_title = QLabel("Objectifs Techniques")
        obj_title.setStyleSheet("font-weight: bold; margin-top: 15px; border-bottom: 1px solid #334155;")
        self.content_layout.addWidget(obj_title)
        
        self.objectives_container = QVBoxLayout()
        self.content_layout.addLayout(self.objectives_container)
        
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)
        
    def load_exercise(self, exercise):
        self.title_lbl.setText(exercise.title)
        if exercise.mission:
            self.context_lbl.setText(exercise.mission.context)
            self.mission_lbl.setText(f"<b>Consigne :</b> {exercise.mission.mission}")
            
            if exercise.mission.constraints:
                c_text = "<b>Contraintes :</b><ul>"
                for c in exercise.mission.constraints:
                    c_text += f"<li>{c}</li>"
                c_text += "</ul>"
                self.constraints_lbl.setText(c_text)
                self.constraints_lbl.setVisible(True)
            else:
                self.constraints_lbl.setVisible(False)
                
        # Afficher les règles sous forme de checklist d'objectifs
        self.clear_objectives()
        for rule in exercise.evaluation_rules:
            lbl = QLabel(f"☐ {self._translate_rule(rule)}")
            lbl.setStyleSheet("color: #94a3b8;")
            self.objectives_container.addWidget(lbl)
            
    def _translate_rule(self, rule: dict) -> str:
        rule_type = rule.get("type", "")
        if rule_type == "code_pin":
            return f"Configurer le GPIO {rule.get('gpio')} en mode {rule.get('mode')}"
        elif rule_type == "topology":
            comp = rule.get("component_type", "Composant").upper()
            return f"Connecter un {comp} au GPIO {rule.get('gpio')}"
        return f"Objectif : {rule.get('id', 'inconnu')}"
        
    def clear_objectives(self):
        while self.objectives_container.count():
            item = self.objectives_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
    def set_objective_status(self, rule_id: str, success: bool):
        # A simple visual feedback, can be expanded if Engine tracks individual rule status dynamically
        pass
