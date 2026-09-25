# -*- coding: utf-8 -*-
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QScrollArea, QFrame, QHBoxLayout
from PySide6.QtCore import Qt, QTimer
from ....core.models.project import ProjectModel
from ....core.models.pedagogical_activity import ActivityType, ActivityContext
from ....core.models.activity_session import SessionState
from ....core.activity_session_service import ActivitySessionService

class ActivityPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ActivityPanel")
        self.setMinimumWidth(220)
        
        self.session_service = None
        self.is_teacher = False
        self.project = None
        
        self._setup_ui()
        
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self._on_timer_tick)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        self.lbl_header = QLabel("🎓 ACTIVITÉ")
        self.lbl_header.setAlignment(Qt.AlignCenter)
        self.lbl_header.setStyleSheet("font-size: 14pt; font-weight: bold; background-color: #2c3e50; color: white; padding: 10px;")
        layout.addWidget(self.lbl_header)
        
        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        content = QWidget()
        self.vbox = QVBoxLayout(content)
        self.vbox.setContentsMargins(10, 10, 10, 10)
        self.vbox.setSpacing(15)
        
        self.lbl_title = QLabel()
        self.lbl_title.setStyleSheet("font-size: 12pt; font-weight: bold;")
        self.lbl_title.setWordWrap(True)
        self.vbox.addWidget(self.lbl_title)
        
        self.lbl_mission_title = QLabel("<b>Mission</b><hr>")
        self.vbox.addWidget(self.lbl_mission_title)
        
        self.lbl_desc = QLabel()
        self.lbl_desc.setWordWrap(True)
        self.vbox.addWidget(self.lbl_desc)
        
        self.lbl_constraints_title = QLabel("<b>Contraintes</b><hr>")
        self.vbox.addWidget(self.lbl_constraints_title)
        
        self.lbl_constraints = QLabel()
        self.lbl_constraints.setWordWrap(True)
        self.vbox.addWidget(self.lbl_constraints)
        
        self.lbl_hints_title = QLabel("<b>Indices</b><hr>")
        self.vbox.addWidget(self.lbl_hints_title)
        
        self.lbl_hints = QLabel()
        self.lbl_hints.setWordWrap(True)
        self.vbox.addWidget(self.lbl_hints)
        
        # Results area
        self.lbl_result = QLabel()
        self.lbl_result.setWordWrap(True)
        self.vbox.addWidget(self.lbl_result)
        self.lbl_result.hide()
        
        # Correction section
        self.w_correction = QWidget()
        self.lay_correction = QVBoxLayout(self.w_correction)
        self.lay_correction.setContentsMargins(0, 0, 0, 0)
        
        lbl_corr_title = QLabel("<b>Évaluation de l'Enseignant</b><hr>")
        self.lay_correction.addWidget(lbl_corr_title)
        
        lay_grade = QHBoxLayout()
        lay_grade.addWidget(QLabel("Note (/20) :"))
        from PySide6.QtWidgets import QDoubleSpinBox, QTextEdit
        self.spin_grade = QDoubleSpinBox()
        self.spin_grade.setRange(0, 20)
        self.spin_grade.setDecimals(1)
        lay_grade.addWidget(self.spin_grade)
        self.lay_correction.addLayout(lay_grade)
        
        self.txt_comment = QTextEdit()
        self.txt_comment.setPlaceholderText("Commentaire de correction...")
        self.txt_comment.setMaximumHeight(80)
        self.lay_correction.addWidget(self.txt_comment)
        
        self.btn_save_eval = QPushButton("Enregistrer la note")
        self.btn_save_eval.setStyleSheet("background-color: #2980b9; color: white; padding: 5px;")
        self.btn_save_eval.clicked.connect(self._save_evaluation)
        self.lay_correction.addWidget(self.btn_save_eval)
        
        self.w_correction.hide()
        self.vbox.addWidget(self.w_correction)

        # Status & Time
        time_layout = QHBoxLayout()
        self.lbl_status = QLabel("")
        self.lbl_status.setStyleSheet("font-weight: bold;")
        time_layout.addWidget(self.lbl_status)
        time_layout.addStretch()
        
        self.lbl_duration = QLabel()
        self.lbl_duration.setStyleSheet("color: #e67e22; font-weight: bold; font-size: 11pt;")
        time_layout.addWidget(self.lbl_duration)
        self.vbox.addLayout(time_layout)
        
        self.btn_action = QPushButton("Commencer")
        self.btn_action.setStyleSheet("background-color: #3498db; color: white; font-weight: bold; padding: 8px;")
        self.btn_action.clicked.connect(self._on_action_clicked)
        self.vbox.addWidget(self.btn_action)
        
        self.btn_reset_local = QPushButton("Réinitialiser ma tentative (Test)")
        self.btn_reset_local.setStyleSheet("background-color: #e74c3c; color: white; font-weight: bold; padding: 5px;")
        self.btn_reset_local.clicked.connect(self._reset_local_session)
        self.btn_reset_local.hide()
        self.vbox.addWidget(self.btn_reset_local)

        self.vbox.addStretch()
        
        scroll.setWidget(content)
        layout.addWidget(scroll)

    def attach_service(self, service: ActivitySessionService, is_teacher: bool = False):
        self.session_service = service
        self.is_teacher = is_teacher

    def _reset_local_session(self):
        from PySide6.QtWidgets import QMessageBox
        if not self.project: return
        act = self.project.pedagogy_profile.get("activity", {})
        if not act: return
        activity_id = act.get("id", "")
        if not activity_id: return
        
        reply = QMessageBox.question(self, "Réinitialiser", 
            "Voulez-vous vraiment effacer votre tentative locale de test ?\nCela effacera vos réponses de test.", 
            QMessageBox.Yes | QMessageBox.No)
            
        if reply == QMessageBox.Yes:
            from ....core.session_repository import SQLiteSessionRepository
            repo = SQLiteSessionRepository()
            sess = repo.find_active_session(activity_id, "student_local")
            if sess:
                repo.delete(sess.session_id)
                from ....core.submission_repository import SQLiteSubmissionRepository
                sub_repo = SQLiteSubmissionRepository()
                sub = sub_repo.find_by_session(sess.session_id)
                if sub:
                    sub_repo.delete(sub.submission_id)
                QMessageBox.information(self, "Succès", "Tentative locale réinitialisée avec succès.")
            else:
                QMessageBox.information(self, "Info", "Aucune tentative locale trouvée en base.")


    def load_project(self, project: ProjectModel):
        self.project = project
        if not self.is_teacher and self.session_service and project and project.pedagogy_profile:
            from esp32_lab.core.models.activity_session import StudentIdentity
            self.session_service.load_or_create_session(project, StudentIdentity("student_local"))
        self._refresh()

    def _refresh(self):
        if not self.project:
            self.setVisible(False)
            self.timer.stop()
            return
            
        ctx = ActivityContext(self.project.pedagogy_profile)
        if not ctx.has_activity:
            self.setVisible(False)
            self.timer.stop()
            return
            
        self.setVisible(True)
        
        act = ctx.activity
        act_type = ctx.activity_type
        settings = act.get("settings", {})
        
        # Header translation
        header_text = "🎓 TP"
        if act_type == ActivityType.EXERCISE:
            header_text = "🎓 EXERCICE"
        elif act_type == ActivityType.EXAM:
            header_text = "🎓 EXAMEN"
            
        if settings.get("strict_mode", False):
            header_text += " (Strict)"
        self.lbl_header.setText(header_text)
        
        mission = self.project.pedagogy_profile.get("mission", {})
        self.lbl_title.setText(mission.get("title", act.get("title", "Nouvelle Activité")))
        self.lbl_desc.setText(mission.get("description", act.get("description", "")))

        # Correction Mode
        if self.is_teacher and "student_submission" in self.project.pedagogy_profile:
            self.w_correction.show()
            student = self.project.pedagogy_profile["student_submission"]
            self.lbl_header.setText(f"Copie : {student.get('nom', '')} {student.get('prenom', '')}")
            
            # Load existing evaluation
            evaluation = self.project.pedagogy_profile.get("evaluation", {})
            self.spin_grade.setValue(evaluation.get("grade", 0.0))
            self.txt_comment.setText(evaluation.get("comment", ""))
        else:
            self.w_correction.hide()
            self.btn_reset_local.show()

        
        # Constraints summary
        criteria = self.project.pedagogy_profile.get("criteria", [])
        constraints = [c.get("description", "") for c in criteria if c.get("category") == "constraints" and c.get("enabled", True)]
        if constraints:
            self.lbl_constraints_title.show()
            self.lbl_constraints.setText("\n".join(f"• {c}" for c in constraints))
            self.lbl_constraints.show()
        else:
            self.lbl_constraints_title.hide()
            self.lbl_constraints.hide()
            
        # Hints
        if settings.get("allow_hints", False):
            hints = mission.get("hints", act.get("hints", []))
            if hints:
                self.lbl_hints_title.show()
                self.lbl_hints.setText("\n".join(f"• {h}" for h in hints))
                self.lbl_hints.show()
            else:
                self.lbl_hints_title.hide()
                self.lbl_hints.hide()
        else:
            self.lbl_hints_title.hide()
            self.lbl_hints.hide()
            
        self.lbl_result.hide()
        self._update_session_ui()
        
    def _save_evaluation(self):
        if not self.project or not self.project.pedagogy_profile: return
        eval_data = {
            "grade": self.spin_grade.value(),
            "comment": self.txt_comment.toPlainText()
        }
        self.project.pedagogy_profile["evaluation"] = eval_data
        
        from esp32_lab.app.event_bus import get_event_bus
        bus = get_event_bus()
        if hasattr(bus, "project_modified"):
            bus.project_modified.emit()
            
        csv_msg = ""
        main_win = self.window()
        if hasattr(main_win, "current_file_path") and main_win.current_file_path:
            try:
                import csv
                from pathlib import Path
                
                file_path = main_win.current_file_path
                csv_path = file_path.parent / "recap_notes.csv"
                
                student = self.project.pedagogy_profile.get("student_submission", {})
                nom = student.get("nom", "")
                prenom = student.get("prenom", "")
                classe = student.get("classe", "")
                
                fields = ["Fichier", "Nom", "Prenom", "Classe", "Note", "Commentaire"]
                rows = []
                found = False
                
                # Lire les lignes existantes s'il y en a
                if csv_path.exists():
                    with open(csv_path, mode="r", encoding="utf-8", newline="") as f:
                        reader = csv.DictReader(f, delimiter=";")
                        if reader.fieldnames:
                            fields = list(reader.fieldnames)
                            for req_col in ["Fichier", "Nom", "Prenom", "Classe", "Note", "Commentaire"]:
                                if req_col not in fields:
                                    fields.append(req_col)
                        for row in reader:
                            if row.get("Fichier") == file_path.name:
                                row["Nom"] = nom
                                row["Prenom"] = prenom
                                row["Classe"] = classe
                                row["Note"] = str(eval_data["grade"])
                                row["Commentaire"] = eval_data["comment"].replace("\n", " ")
                                found = True
                            rows.append(row)
                            
                # Ajouter si non trouvé
                if not found:
                    rows.append({
                        "Fichier": file_path.name,
                        "Nom": nom,
                        "Prenom": prenom,
                        "Classe": classe,
                        "Note": str(eval_data["grade"]),
                        "Commentaire": eval_data["comment"].replace("\n", " ")
                    })
                    
                # Réécrire le fichier
                with open(csv_path, mode="w", encoding="utf-8", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=fields, delimiter=";")
                    writer.writeheader()
                    writer.writerows(rows)
                    
                csv_msg = f"\n\n✔ Le fichier CSV récapitulatif a été mis à jour :\n{csv_path.name}"
            except PermissionError:
                csv_msg = "\n\n⚠️ IMPOSSIBLE de mettre à jour le CSV.\nIl est probablement ouvert dans Excel. Veuillez le fermer et réessayer."
            except Exception as e:
                csv_msg = f"\n\n⚠️ Erreur lors de la mise à jour du CSV : {e}"
                
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Évaluation enregistrée", f"La note a été appliquée.\nN'oubliez pas d'enregistrer le projet (Ctrl+S).{csv_msg}")

    def _update_session_ui(self):
        if self.is_teacher or not self.session_service:
            if self.project and self.project.pedagogy_profile and "student_submission" in self.project.pedagogy_profile:
                self.lbl_status.setText("Mode Correction")
            else:
                self.lbl_status.setText("Mode Auteur")
            self.btn_action.hide()
            self.timer.stop()
            
            ctx = ActivityContext(self.project.pedagogy_profile)
            dur = ctx.activity.get("duration_minutes", 0) if ctx.has_activity else 0
            if dur > 0:
                self.lbl_duration.setText(f"⏱ {dur} min")
                self.lbl_duration.show()
            else:
                self.lbl_duration.setText("⏱ Illimité")
                self.lbl_duration.show()
            return
            
        sess = self.session_service.get_session()
        if not sess:
            self.lbl_status.setText("")
            self.btn_action.hide()
            self.timer.stop()
            return
            
        self.btn_action.show()
        self.btn_reset_local.hide()
        
        if sess.status == SessionState.NOT_STARTED:
            from ....app.event_bus import get_event_bus
            get_event_bus().session_locked.emit({"locked": False})
            self.lbl_status.setText("Prêt")
            self.lbl_duration.setText(self._get_duration_text(sess))
            self.btn_action.setText("Commencer")
            self.btn_action.setStyleSheet("background-color: #3498db; color: white; font-weight: bold; padding: 8px;")
            self.btn_action.setEnabled(True)
            self.timer.stop()
            
        elif sess.status == SessionState.IN_PROGRESS:
            from ....app.event_bus import get_event_bus
            get_event_bus().session_locked.emit({"locked": False})
            self.lbl_status.setText("En cours...")
            self.btn_action.setText("✓ Valider mon travail")
            self.btn_action.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; padding: 8px;")
            self.btn_action.setEnabled(True)
            self.timer.start()
            self._on_timer_tick()
            
        elif sess.status in (SessionState.EXPIRED, SessionState.FROZEN):
            from ....app.event_bus import get_event_bus
            get_event_bus().session_locked.emit({"locked": True})
            self.lbl_status.setText("Terminé" if sess.status == SessionState.FROZEN else "Expiré")
            self.lbl_status.setStyleSheet("color: #c0392b; font-weight: bold;")
            self.lbl_duration.setText("00:00")
            
            # Plus de bouton recommencer pour l'élève ! Verrouillage complet.
            self.btn_action.hide()
            self.timer.stop()
            
            # Show Submission result
            if self.session_service.submission_repo:
                sub = self.session_service.submission_repo.find_by_session(sess.session_id)
                if sub:
                    result_text = "<b>État :</b><br/>✓ Travail remis<br/><br/>"
                    if sub.status.value in ("WAITING_TEACHER", "AUTO_EVALUATED"):
                        result_text += "<b>Correction :</b><br/>✓ Correction automatique terminée<br/><br/>"
                        result_text += "<i>🕐 En attente de validation de l'enseignant</i>"
                    
                    self.lbl_result.setText(result_text)
                    pass # Handled by set_theme
                    self.lbl_result.show()

    def _get_duration_text(self, sess):
        ctx = ActivityContext(self.project.pedagogy_profile)
        dur = ctx.activity.get("duration_minutes", 0)
        return f"⏱ {dur} min" if dur > 0 else "⏱ Illimité"

    def _auto_save_student_work(self):
        if not self.project or not self.project.pedagogy_profile: return
        student_data = self.project.pedagogy_profile.get("student_submission")
        if not student_data: return
        
        main_win = self.window()
        
        nom = student_data.get("nom", "").strip()
        prenom = student_data.get("prenom", "").strip()
        classe = student_data.get("classe", "").strip()
        if not nom: return
        
        from pathlib import Path
        from PySide6.QtWidgets import QMessageBox, QFileDialog
        
        act_title = self.project.pedagogy_profile.get("activity", {}).get("title", "TP")
        act_title = act_title.replace(" ", "_").replace("/", "-")
        default_name = f"{act_title}_{nom}_{prenom}_{classe}.lab32"
        
        current_path = getattr(main_win, "current_file_path", None)
        if current_path:
            p = Path(current_path)
            if p.name == default_name or p.name.startswith(f"{act_title}_{nom}_{prenom}"):
                if hasattr(main_win, "_save_project"):
                    main_win._save_project()
                return

        path, _ = QFileDialog.getSaveFileName(
            self, 
            "Enregistrer mon travail", 
            default_name, 
            "ESP32 Lab Project (*.lab32);;Fichier JSON (*.json)"
        )
        
        if path:
            if not any(path.lower().endswith(ext) for ext in [".lab32", ".json"]):
                path += ".lab32"
                
            main_win.current_project.name = Path(path).stem
            from ....core.project_service import ProjectService
            ProjectService.save_project(self.project, path)
            main_win.current_file_path = Path(path)
            if hasattr(main_win, "_update_title"):
                main_win._update_title()
                QMessageBox.information(self, "Succès", "Tentative locale réinitialisée avec succès.")


    def _on_timer_tick(self):
        if not self.session_service:
            return
            
        rem = self.session_service.update_and_get_remaining_time()
        if rem is not None:
            mins, secs = divmod(rem, 60)
            self.lbl_duration.setText(f"⏱ {mins:02d}:{secs:02d}")
            if rem <= 0:
                self._auto_save_student_work()
                self._update_session_ui()
        else:
            self.lbl_duration.setText("⏱ Illimité")
            
    def _on_action_clicked(self):
        if not self.session_service:
            return
            
        sess = self.session_service.get_session()
        if not sess:
            return
            
        if sess.status == SessionState.NOT_STARTED:
            from ....app.event_bus import get_event_bus
            get_event_bus().session_locked.emit({"locked": False})
            from .student_identity_dialog import StudentIdentityDialog
            from PySide6.QtWidgets import QDialog
            dlg = StudentIdentityDialog(self)
            if dlg.exec_() == QDialog.Accepted:
                data = dlg.get_data()
                if self.project.pedagogy_profile is None:
                    self.project.pedagogy_profile = {}
                self.project.pedagogy_profile["student_submission"] = data
                
                from ....core.models.activity_session import StudentIdentity
                sess.student = StudentIdentity(student_id=f"{data['nom']}_{data['prenom']}")
                
                self.session_service.start_session()
                self._update_session_ui()
                
        elif sess.status == SessionState.IN_PROGRESS:
            from ....app.event_bus import get_event_bus
            get_event_bus().session_locked.emit({"locked": True})
            if hasattr(self.session_service, "request_freeze"):
                self.session_service.request_freeze()
            else:
                self.session_service.freeze_session()
            self._auto_save_student_work()
            self._update_session_ui()

    def set_theme(self, theme_name: str):
        is_light = (theme_name == "light")
        bg_col = "#f8fafc" if is_light else "#0f172a"
        text_col = "#0f172a" if is_light else "#f8fafc"
        result_bg = "#e2e8f0" if is_light else "#1e293b"
        
        self.setStyleSheet(f"QWidget {{ background-color: {bg_col}; color: {text_col}; }}")
        if hasattr(self, 'lbl_result'):
            self.lbl_result.setStyleSheet(f"background-color: {result_bg}; padding: 10px; border-radius: 5px;")
