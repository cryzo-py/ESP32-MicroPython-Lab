# -*- coding: utf-8 -*-
import uuid
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QPushButton, 
    QDialog, QHBoxLayout, QLabel, QComboBox, QLineEdit
)
from ....core.models.project import ProjectModel

class TeacherTestDialog(QDialog):
    def __init__(self, parent=None, test_data=None):
        super().__init__(parent)
        self.test_data = test_data or {}
        self.setWindowTitle("Éditer Test TP")
        self.setFixedSize(300, 150)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel("Nom du test :"))
        self.edit_name = QLineEdit()
        self.edit_name.setText(self.test_data.get("name", "Nouveau test"))
        layout.addWidget(self.edit_name)
        
        layout.addWidget(QLabel("Résultat attendu :"))
        self.cb_outcome = QComboBox()
        self.cb_outcome.addItems(["SUCCESS", "FAILURE"])
        if "expected_outcome" in self.test_data:
            self.cb_outcome.setCurrentText(self.test_data["expected_outcome"])
        layout.addWidget(self.cb_outcome)
        
        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("Enregistrer")
        btn_ok.clicked.connect(self.accept)
        btn_cancel = QPushButton("Annuler")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_ok)
        layout.addLayout(btn_layout)

    def get_test_data(self):
        return {
            "id": self.test_data.get("id", f"test_{str(uuid.uuid4())[:8]}"),
            "name": self.edit_name.text(),
            "description": self.test_data.get("description", ""),
            "expected_outcome": self.cb_outcome.currentText(),
            "patches": self.test_data.get("patches", [])
        }

class TestsTab(QWidget):
    def __init__(self, project: ProjectModel, parent=None):
        super().__init__(parent)
        self.project = project
        self._setup_ui()
        self.load_from_project()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        self.list_tests = QListWidget()
        layout.addWidget(self.list_tests)
        
        btn_layout = QHBoxLayout()
        btn_add = QPushButton("+ Nouveau test")
        btn_add.clicked.connect(self._add_test)
        btn_rem = QPushButton("- Supprimer")
        btn_rem.clicked.connect(self._remove_test)
        btn_layout.addWidget(btn_add)
        btn_layout.addWidget(btn_rem)
        layout.addLayout(btn_layout)

    def load_from_project(self):
        if not self.project:
            return
        self.list_tests.clear()
        if not self.project.pedagogy_profile:
            return
            
        tests = self.project.pedagogy_profile.get("teacher_tests", [])
        for t in tests:
            icon = "✓" if t.get("expected_outcome") == "SUCCESS" else "✗"
            item = f"{icon} {t.get('name', 'Unnamed')}"
            self.list_tests.addItem(item)
            self.list_tests.item(self.list_tests.count() - 1).setData(32, t)

    def _save_to_project(self):
        if self.project.pedagogy_profile is None:
            self.project.pedagogy_profile = {}
            
        tests = []
        for i in range(self.list_tests.count()):
            tests.append(self.list_tests.item(i).data(32))
            
        self.project.pedagogy_profile["teacher_tests"] = tests

    def _add_test(self):
        dlg = TeacherTestDialog(self)
        if dlg.exec() == 1:
            t = dlg.get_test_data()
            if self.project.pedagogy_profile is None:
                self.project.pedagogy_profile = {}
            if "teacher_tests" not in self.project.pedagogy_profile:
                self.project.pedagogy_profile["teacher_tests"] = []
            self.project.pedagogy_profile["teacher_tests"].append(t)
            self.load_from_project()

    def _remove_test(self):
        row = self.list_tests.currentRow()
        if row >= 0:
            self.list_tests.takeItem(row)
            self._save_to_project()
