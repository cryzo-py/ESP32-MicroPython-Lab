from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QCheckBox, 
    QPushButton, QLabel, QFrame
)
from PySide6.QtCore import Qt
from ....core.models.project import ProjectModel
from ....application.education.interaction_policy import InteractionPolicy

class LockPropertiesDialog(QDialog):
    def __init__(self, comp_id: str, project: ProjectModel, interaction_policy: InteractionPolicy, parent=None):
        super().__init__(parent)
        self.comp_id = comp_id
        self.project = project
        self.interaction_policy = interaction_policy
        self.setWindowTitle(f"🔒 Verrouillage: {comp_id}")
        self.setFixedSize(300, 250)
        
        self._setup_ui()
        self._load_current_state()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        lbl = QLabel(f"Interdire l'action pour les élèves sur <b>{self.comp_id}</b> :")
        lbl.setWordWrap(True)
        layout.addWidget(lbl)
        
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame { background-color: #1e293b; border-radius: 6px; padding: 5px; }
            QCheckBox { color: #f8fafc; font-weight: bold; }
        """)
        flayout = QVBoxLayout(frame)
        
        self.chk_move = QCheckBox("Interdire le déplacement")
        self.chk_delete = QCheckBox("Interdire la suppression")
        self.chk_rotate = QCheckBox("Interdire la rotation")
        self.chk_interact = QCheckBox("Interdire l'interaction (ex: bouton)")
        self.chk_props = QCheckBox("Interdire l'édition de propriétés")
        
        flayout.addWidget(self.chk_move)
        flayout.addWidget(self.chk_delete)
        flayout.addWidget(self.chk_rotate)
        flayout.addWidget(self.chk_interact)
        flayout.addWidget(self.chk_props)
        layout.addWidget(frame)
        
        btn_layout = QHBoxLayout()
        btn_apply = QPushButton("Appliquer")
        btn_apply.setStyleSheet("background-color: #3b82f6; color: white;")
        btn_apply.clicked.connect(self.accept)
        
        btn_cancel = QPushButton("Annuler")
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_apply)
        layout.addLayout(btn_layout)
        
    def _load_current_state(self):
        locks = {}
        if self.project.pedagogy_profile:
            comps = self.project.pedagogy_profile.get("locked_elements", {}).get("components", [])
            for c in comps:
                if c.get("id") == self.comp_id:
                    locks = c.get("locks", {})
                    break
                    
        self.chk_move.setChecked(locks.get("move", False))
        self.chk_delete.setChecked(locks.get("delete", False))
        self.chk_rotate.setChecked(locks.get("rotate", False))
        self.chk_interact.setChecked(locks.get("interact", False))
        self.chk_props.setChecked(locks.get("properties", False))
        
    def get_locks(self) -> dict:
        return {
            "move": self.chk_move.isChecked(),
            "delete": self.chk_delete.isChecked(),
            "rotate": self.chk_rotate.isChecked(),
            "interact": self.chk_interact.isChecked(),
            "properties": self.chk_props.isChecked()
        }
