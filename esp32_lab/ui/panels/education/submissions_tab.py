# -*- coding: utf-8 -*-
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, 
    QLabel, QPushButton, QTextEdit, QSpinBox, QMessageBox, QSplitter
)
from PySide6.QtCore import Qt
import time

class SubmissionsTab(QWidget):
    def __init__(self, review_service=None, project=None):
        super().__init__()
        self.review_service = review_service
        self.project = project
        self.submissions = []
        self.current_sub = None
        
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QHBoxLayout(self)
        
        splitter = QSplitter(Qt.Horizontal)
        
        # Left side: List of submissions
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        btn_refresh = QPushButton("🔄 Actualiser")
        btn_refresh.clicked.connect(self.refresh_list)
        left_layout.addWidget(btn_refresh)
        
        self.list_subs = QListWidget()
        self.list_subs.itemSelectionChanged.connect(self._on_selection_changed)
        left_layout.addWidget(self.list_subs)
        
        splitter.addWidget(left_widget)
        
        # Right side: Details
        right_widget = QWidget()
        self.right_layout = QVBoxLayout(right_widget)
        
        self.lbl_details = QLabel("Sélectionnez une soumission à corriger.")
        self.lbl_details.setWordWrap(True)
        self.right_layout.addWidget(self.lbl_details)
        
        # Grading controls (hidden initially)
        self.grade_widget = QWidget()
        grade_layout = QVBoxLayout(self.grade_widget)
        
        grade_layout.addWidget(QLabel("<b>Note Finale :</b>"))
        self.spin_score = QSpinBox()
        self.spin_score.setRange(0, 100)
        grade_layout.addWidget(self.spin_score)
        
        grade_layout.addWidget(QLabel("<b>Commentaire :</b>"))
        self.txt_comment = QTextEdit()
        self.txt_comment.setMaximumHeight(100)
        grade_layout.addWidget(self.txt_comment)
        
        self.btn_validate = QPushButton("Enregistrer la correction")
        self.btn_validate.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; padding: 5px;")
        self.btn_validate.clicked.connect(self._on_validate_clicked)
        grade_layout.addWidget(self.btn_validate)
        
        self.right_layout.addWidget(self.grade_widget)
        self.grade_widget.hide()
        
        splitter.addWidget(right_widget)
        splitter.setSizes([200, 400])
        main_layout.addWidget(splitter)

    def attach_service(self, review_service):
        self.review_service = review_service

    def refresh_list(self):
        self.list_subs.clear()
        self.submissions = []
        if not self.review_service or not self.project:
            return
            
        activity = self.project.pedagogy_profile.get("activity", {}) if self.project.pedagogy_profile else {}
        act_id = activity.get("id")
        if not act_id:
            return
            
        try:
            self.submissions = self.review_service.get_activity_submissions(act_id)
            for sub in self.submissions:
                stu = sub.student_identity.student_id if sub.student_identity else "Inconnu"
                date_str = time.strftime("%Y-%m-%d %H:%M", time.localtime(sub.submitted_at)) if sub.submitted_at else ""
                label = f"{stu} - {date_str} ({sub.status.value})"
                item = QListWidgetItem(label)
                item.setData(Qt.UserRole, sub.submission_id)
                self.list_subs.addItem(item)
        except PermissionError:
            self.lbl_details.setText("Mode enseignant inactif. Accès refusé.")

    def _on_selection_changed(self):
        items = self.list_subs.selectedItems()
        if not items:
            self.grade_widget.hide()
            return
            
        sub_id = items[0].data(Qt.UserRole)
        self.current_sub = next((s for s in self.submissions if s.submission_id == sub_id), None)
        
        if not self.current_sub:
            return
            
        details = f"<h3>Soumission : {self.current_sub.submission_id}</h3>"
        details += f"<b>Élève :</b> {self.current_sub.student_identity.student_id if self.current_sub.student_identity else 'N/A'}<br/>"
        details += f"<b>Raison :</b> {self.current_sub.submission_reason.value}<br/>"
        details += f"<b>Statut :</b> {self.current_sub.status.value}<br/><hr/>"
        
        # Results
        res = self.current_sub.evaluation_result
        if res:
            details += f"<b>Résultat Automatique :</b> {res.get('status', '')}<br/>"
            for cid, crit in res.get("criteria", {}).items():
                result = crit.get("result", "UNKNOWN")
                details += f"• {cid} : {result}<br/>"
        
        if self.current_sub.proposed_grade:
            details += f"<br/><b>Note Proposée :</b> {self.current_sub.proposed_grade.score} / {self.current_sub.proposed_grade.max_score}<br/>"
            self.spin_score.setMaximum(int(self.current_sub.proposed_grade.max_score))
            
            # Populate form
            if self.current_sub.teacher_review:
                self.spin_score.setValue(int(self.current_sub.teacher_review.final_grade.score))
                self.txt_comment.setText(self.current_sub.teacher_review.comment)
            else:
                self.spin_score.setValue(int(self.current_sub.proposed_grade.score))
                self.txt_comment.clear()
                
            self.grade_widget.show()
        else:
            self.grade_widget.hide()
            
        self.lbl_details.setText(details)

    def _on_validate_clicked(self):
        if not self.current_sub or not self.review_service:
            return
            
        score = self.spin_score.value()
        comment = self.txt_comment.toPlainText()
        
        try:
            self.review_service.submit_review(self.current_sub.submission_id, float(score), comment)
            QMessageBox.information(self, "Succès", "Correction enregistrée avec succès.")
            self.refresh_list()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))
