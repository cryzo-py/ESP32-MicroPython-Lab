import os
from pathlib import Path
import json

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QFrame, QTableWidget, QTableWidgetItem,
                               QHeaderView, QFileDialog, QMessageBox, QInputDialog, QLineEdit)
from PySide6.QtCore import Qt, Signal

class GradingPanelWidget(QWidget):
    open_submission_requested = Signal(str) # Path to the lab32 file
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.submissions = [] # List of dicts
        self.current_folder = ""
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header = QHBoxLayout()
        title = QLabel("📥 Centre de Correction")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #38bdf8;")
        
        self.btn_import = QPushButton("Importer des copies (Fichiers .lab32)")
        self.btn_import.setStyleSheet("background-color: #0284c7; color: white; font-weight: bold; padding: 6px 12px; border-radius: 4px;")
        self.btn_import.clicked.connect(self._import_folder)
        
        self.btn_export = QPushButton("Exporter vers Excel (CSV)")
        self.btn_export.setStyleSheet("background-color: #22c55e; color: white; font-weight: bold; padding: 6px 12px; border-radius: 4px;")
        self.btn_export.clicked.connect(self._export_csv)
        self.btn_export.setEnabled(False)
        
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.btn_import)
        header.addWidget(self.btn_export)
        layout.addLayout(header)
        
        # Table
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Nom", "Prénom", "Classe", "Fichier", "Note", "Commentaire"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.cellDoubleClicked.connect(self._on_row_double_clicked)
        self.table.setStyleSheet("QTableWidget { background-color: #0f172a; color: #f8fafc; gridline-color: #334155; } QHeaderView::section { background-color: #1e293b; color: #f8fafc; padding: 4px; border: 1px solid #334155; min-height: 35px; font-weight: bold; }")

        
        layout.addWidget(self.table)
        
        # Actions for selected copy
        action_layout = QHBoxLayout()
        self.btn_open = QPushButton("Ouvrir la copie sélectionnée")
        self.btn_open.clicked.connect(self._open_selected)
        
        self.btn_open.setStyleSheet("background-color: #334155; color: white; padding: 6px 12px; border-radius: 4px; font-weight: bold;")
        
        self.btn_grade = QPushButton("Saisir la note")
        self.btn_grade.setStyleSheet("background-color: #0ea5e9; color: white; padding: 6px 12px; border-radius: 4px; font-weight: bold;")
        self.btn_grade.clicked.connect(self._grade_selected)
        
        action_layout.addWidget(self.btn_open)
        action_layout.addWidget(self.btn_grade)
        action_layout.addStretch()
        layout.addLayout(action_layout)
        
    def _import_folder(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Sélectionner les copies (.lab32)", "", "ESP32 Lab Projects (*.lab32)")
        if not files:
            return
            
        self.table.setRowCount(0)
        self.submissions.clear()
        
        from esp32_lab.core.project_service import ProjectService
        
        for file_path in files:
            p = Path(file_path)
            try:
                project = ProjectService.load_project(file_path)
                data = project.to_dict()
                if not isinstance(data, dict): data = {}
                    
                pedagogy = data.get("pedagogy_profile") or {}
                sub_info = pedagogy.get("student_submission") or {}
                
                nom = sub_info.get("nom", "Inconnu")
                prenom = sub_info.get("prenom", "Inconnu")
                classe = sub_info.get("classe", "Inconnu")
                
                act_info = pedagogy.get("activity") or {}
                max_score = act_info.get("max_score", 20)
                
                grade = pedagogy.get("teacher_grade", "")
                comment = pedagogy.get("teacher_comment", "")
                # Compatibilité : l'ActivityPanel écrit dans evaluation.grade
                if not grade:
                    eval_data = pedagogy.get("evaluation", {})
                    grade = str(eval_data.get("grade", "")) if eval_data.get("grade") else ""
                    comment = comment or eval_data.get("comment", "")
                
                self.submissions.append({
                    "nom": nom,
                    "prenom": prenom,
                    "classe": classe,
                    "file": p.name,
                    "path": str(p),
                    "grade": grade,
                    "max_score": max_score,
                    "comment": comment,
                    "raw_data": data
                })
            except Exception as e:
                print(f"Failed to read {p}: {e}")
                import traceback
                traceback.print_exc()
                
        self._refresh_table()
        
        if self.submissions:
            self.btn_export.setEnabled(True)
            QMessageBox.information(self, "Import réussi", f"{len(self.submissions)} copies importées avec succès !")
        else:
            QMessageBox.warning(self, "Aucune copie", "Aucun fichier .lab32 valide n'a été trouvé dans ce dossier.")

    def _refresh_table(self):
        self.table.setRowCount(len(self.submissions))
        for i, sub in enumerate(self.submissions):
            self.table.setItem(i, 0, QTableWidgetItem(sub["nom"]))
            self.table.setItem(i, 1, QTableWidgetItem(sub["prenom"]))
            self.table.setItem(i, 2, QTableWidgetItem(sub["classe"]))
            self.table.setItem(i, 3, QTableWidgetItem(sub["file"]))
            
            grade_str = f"{sub['grade']} / {sub['max_score']}" if sub['grade'] else "-"
            self.table.setItem(i, 4, QTableWidgetItem(grade_str))
            self.table.setItem(i, 5, QTableWidgetItem(sub["comment"]))
            
    def _on_row_double_clicked(self, row, col):
        self._open_selected()

    def _open_selected(self):
        row = self.table.currentRow()
        if row >= 0:
            sub = self.submissions[row]
            self.open_submission_requested.emit(sub["path"])
            
    def _grade_selected(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Erreur", "Veuillez sélectionner une copie.")
            return
            
        sub = self.submissions[row]
        
        # Simple dialog for grade
        grade, ok = QInputDialog.getDouble(
            self, "Note", f"Note pour {sub['nom']} {sub['prenom']} (sur {sub['max_score']}) :",
            value=float(sub['grade']) if sub['grade'] else 0.0,
            minValue=0, maxValue=float(sub['max_score']), decimals=2
        )
        if ok:
            comment, ok2 = QInputDialog.getText(
                self, "Commentaire", "Commentaire pour l'élève :",
                QLineEdit.Normal, sub['comment']
            )
            if ok2:
                sub['grade'] = str(grade)
                sub['comment'] = comment
                
                # Save back to file
                from esp32_lab.core.project_service import ProjectService
                from esp32_lab.core.models.project import ProjectModel
                
                try:
                    project = ProjectService.load_project(sub["path"])
                    if not project.pedagogy_profile:
                        project.pedagogy_profile = {}
                    project.pedagogy_profile["teacher_grade"] = sub['grade']
                    project.pedagogy_profile["teacher_comment"] = sub['comment']
                    # Compatibilité : écrire aussi dans evaluation
                    project.pedagogy_profile["evaluation"] = {
                        "grade": float(sub['grade']) if sub['grade'] else 0.0,
                        "comment": sub['comment']
                    }
                    
                    ProjectService.save_project(project, sub["path"])
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    
                self._refresh_table()

    def _export_csv(self):
        if not self.submissions:
            return
            
        path, _ = QFileDialog.getSaveFileName(self, "Exporter les notes", "Notes_Classe.csv", "CSV Files (*.csv)")
        if path:
            import csv
            with open(path, "w", newline='', encoding="utf-8-sig") as f:
                writer = csv.writer(f, delimiter=';')
                writer.writerow(["Nom", "Prénom", "Classe", "Fichier", "Note", "Barème", "Commentaire"])
                for sub in self.submissions:
                    writer.writerow([
                        sub["nom"], sub["prenom"], sub["classe"], sub["file"],
                        sub["grade"], sub["max_score"], sub["comment"]
                    ])
            QMessageBox.information(self, "Export réussi", f"Les notes ont été exportées vers :\n{path}")

