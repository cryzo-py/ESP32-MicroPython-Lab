# -*- coding: utf-8 -*-
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLineEdit, QTextEdit, QFormLayout, QGroupBox, QSpinBox, QCheckBox, QComboBox,
    QListWidget, QHBoxLayout, QPushButton, QLabel, QInputDialog
)
from ....core.models.project import ProjectModel
from ....core.models.pedagogical_activity import ActivityType, get_default_settings, create_default_activity

class MissionTab(QWidget):
    def __init__(self, project: ProjectModel, parent=None):
        super().__init__(parent)
        self.project = project
        self._setup_ui()
        self.load_from_project()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # --- Section Configuration de l'Activité ---
        grp_activity = QGroupBox("Configuration de l'Activité")
        form_act = QFormLayout(grp_activity)
        
        self.cb_type = QComboBox()
        self.cb_type.addItems(["tp", "exercise", "exam"])
        self.cb_type.currentTextChanged.connect(self._on_type_changed)
        form_act.addRow("Type d'activité :", self.cb_type)
        
        self.spin_duration = QSpinBox()
        self.spin_duration.setRange(0, 600)
        self.spin_duration.setSuffix(" min (0 = illimité)")
        self.spin_duration.valueChanged.connect(self._on_changed)
        form_act.addRow("Durée :", self.spin_duration)
        
        self.chk_strict = QCheckBox("Mode strict (examen)")
        self.chk_strict.stateChanged.connect(self._on_changed)
        form_act.addRow("", self.chk_strict)
        
        self.chk_hints = QCheckBox("Autoriser les indices")
        self.chk_hints.stateChanged.connect(self._on_changed)
        form_act.addRow("", self.chk_hints)
        
        layout.addWidget(grp_activity)
        
        # --- Section Mission ---
        grp_mission = QGroupBox("Mission")
        layout_mission = QVBoxLayout(grp_mission)
        
        layout_mission.addWidget(QLabel("Titre :"))
        self.edit_title = QLineEdit()
        self.edit_title.textChanged.connect(self._on_changed)
        layout_mission.addWidget(self.edit_title)
        
        layout_mission.addWidget(QLabel("Énoncé :"))
        self.edit_desc = QTextEdit()
        self.edit_desc.textChanged.connect(self._on_changed)
        layout_mission.addWidget(self.edit_desc)
        
        layout_mission.addWidget(QLabel("Hints :"))
        self.list_hints = QListWidget()
        layout_mission.addWidget(self.list_hints)
        
        btn_layout = QHBoxLayout()
        btn_add_hint = QPushButton("+ Ajouter un indice")
        btn_add_hint.clicked.connect(self._add_hint)
        btn_rem_hint = QPushButton("- Supprimer")
        btn_rem_hint.clicked.connect(self._remove_hint)
        btn_layout.addWidget(btn_add_hint)
        btn_layout.addWidget(btn_rem_hint)
        layout_mission.addLayout(btn_layout)
        
        self.btn_preview = QPushButton("Aperçu élève")
        self.btn_preview.clicked.connect(self._show_preview)
        layout_mission.addWidget(self.btn_preview)
        
        self.btn_reset_local = QPushButton("Réinitialiser la tentative locale (Test)")
        self.btn_reset_local.setStyleSheet("background-color: #e74c3c; color: white;")
        self.btn_reset_local.clicked.connect(self._reset_local_session)
        layout_mission.addWidget(self.btn_reset_local)
        
        layout.addWidget(grp_mission)

    def load_from_project(self):
        if not self.project:
            return
        if not self.project.pedagogy_profile:
            return
            
        # Charger activity
        act = self.project.pedagogy_profile.get("activity")
        if act:
            self.cb_type.blockSignals(True)
            self.cb_type.setCurrentText(act.get("type", "tp"))
            self.cb_type.blockSignals(False)
            
            self.spin_duration.blockSignals(True)
            self.spin_duration.setValue(act.get("duration_minutes", 0))
            self.spin_duration.blockSignals(False)
            
            settings = act.get("settings", {})
            self.chk_strict.blockSignals(True)
            self.chk_strict.setChecked(settings.get("strict_mode", False))
            self.chk_strict.blockSignals(False)
            
            self.chk_hints.blockSignals(True)
            self.chk_hints.setChecked(settings.get("allow_hints", True))
            self.chk_hints.blockSignals(False)
        else:
            self.cb_type.blockSignals(True)
            self.cb_type.setCurrentText("tp")
            self.cb_type.blockSignals(False)

        # Charger mission
        mission = self.project.pedagogy_profile.get("mission", {})
        self.edit_title.blockSignals(True)
        self.edit_title.setText(mission.get("title", ""))
        self.edit_title.blockSignals(False)
        
        self.edit_desc.blockSignals(True)
        self.edit_desc.setPlainText(mission.get("description", ""))
        self.edit_desc.blockSignals(False)
        
        self.list_hints.clear()
        for h in mission.get("hints", []):
            self.list_hints.addItem(h)

    def _on_type_changed(self, new_type):
        if self.project.pedagogy_profile is None:
            self.project.pedagogy_profile = {}
            
        act = self.project.pedagogy_profile.get("activity")
        if not act:
            act = create_default_activity(new_type)
            self.project.pedagogy_profile["activity"] = act
        else:
            act["type"] = new_type
            act["settings"] = get_default_settings(new_type)
            
        self.load_from_project()
        self._on_changed()

    def _on_changed(self):
        self._save_to_project()

    def _save_to_project(self):
        if self.project.pedagogy_profile is None:
            self.project.pedagogy_profile = {}
            
        if "activity" not in self.project.pedagogy_profile:
            self.project.pedagogy_profile["activity"] = create_default_activity(self.cb_type.currentText())
            
        act = self.project.pedagogy_profile["activity"]
        act["type"] = self.cb_type.currentText()
        act["duration_minutes"] = self.spin_duration.value()
        
        if "settings" not in act:
            act["settings"] = {}
        act["settings"]["strict_mode"] = self.chk_strict.isChecked()
        act["settings"]["allow_hints"] = self.chk_hints.isChecked()

        if "mission" not in self.project.pedagogy_profile:
            self.project.pedagogy_profile["mission"] = {}
            
        self.project.pedagogy_profile["mission"]["title"] = self.edit_title.text()
        self.project.pedagogy_profile["mission"]["description"] = self.edit_desc.toPlainText()
        
        hints = []
        for i in range(self.list_hints.count()):
            hints.append(self.list_hints.item(i).text())
        self.project.pedagogy_profile["mission"]["hints"] = hints

    def _add_hint(self):
        text, ok = QInputDialog.getText(self, "Nouvel indice", "Texte de l'indice :")
        if ok and text:
            self.list_hints.addItem(text)
            self._save_to_project()

    def _remove_hint(self):
        row = self.list_hints.currentRow()
        if row >= 0:
            self.list_hints.takeItem(row)
            self._save_to_project()

    def _reset_local_session(self):
        from PySide6.QtWidgets import QMessageBox
        if not self.project: return
        act = self.project.pedagogy_profile.get("activity", {})
        if not act: return
        activity_id = act.get("id", "")
        if not activity_id: return
        
        reply = QMessageBox.question(self, "Réinitialiser", 
            "Voulez-vous vraiment effacer votre tentative locale de test pour cette activité ?\nCela effacera vos réponses de test.", 
            QMessageBox.Yes | QMessageBox.No)
            
        if reply == QMessageBox.Yes:
            from ....core.session_repository import SQLiteSessionRepository
            repo = SQLiteSessionRepository()
            sess = repo.find_active_session(activity_id, "student_local")
            if sess:
                repo.delete(sess.session_id)
                QMessageBox.information(self, "Succès", "Tentative locale réinitialisée.")
            else:
                QMessageBox.information(self, "Info", "Aucune tentative locale trouvée.")

    def _show_preview(self):
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel
        dlg = QDialog(self)
        dlg.setWindowTitle("Aperçu élève")
        dlg.resize(400, 300)
        
        layout = QVBoxLayout(dlg)
        
        lbl_title = QLabel(f"<h1>{self.edit_title.text()}</h1>")
        lbl_title.setWordWrap(True)
        layout.addWidget(lbl_title)
        
        lbl_desc = QLabel(self.edit_desc.toPlainText())
        lbl_desc.setWordWrap(True)
        layout.addWidget(lbl_desc)
        
        hints = [self.list_hints.item(i).text() for i in range(self.list_hints.count())]
        if hints:
            layout.addWidget(QLabel("<b>Indices disponibles :</b>"))
            for h in hints:
                layout.addWidget(QLabel(f"- {h}"))
                
        layout.addStretch()
        dlg.exec()
