# -*- coding: utf-8 -*-
import uuid
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem, QPushButton, 
    QDialog, QHBoxLayout, QLabel, QComboBox, QLineEdit, QCheckBox
)
from ....core.models.project import ProjectModel
from ....core.models.success_profile import VALID_CATEGORIES, VALID_TYPES

class CriterionDialog(QDialog):
    def __init__(self, parent=None, criterion=None):
        super().__init__(parent)
        self.criterion = criterion or {}
        self.setWindowTitle("Éditer Critère")
        self.setFixedSize(350, 250)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel("Catégorie :"))
        self.cb_category = QComboBox()
        self.cb_category.addItems(list(VALID_CATEGORIES))
        self.cb_category.currentTextChanged.connect(self._update_types)
        layout.addWidget(self.cb_category)
        
        layout.addWidget(QLabel("Type :"))
        self.cb_type = QComboBox()
        layout.addWidget(self.cb_type)
        
        if "category" in self.criterion and self.criterion["category"] in VALID_CATEGORIES:
            self.cb_category.setCurrentText(self.criterion["category"])
        self._update_types(self.cb_category.currentText())
        if "type" in self.criterion:
            self.cb_type.setCurrentText(self.criterion["type"])
        
        layout.addWidget(QLabel("Description :"))
        self.edit_desc = QLineEdit()
        self.edit_desc.setText(self.criterion.get("description", ""))
        layout.addWidget(self.edit_desc)
        
        self.chk_blocking = QCheckBox("Condition obligatoire (Bloquante)")
        self.chk_blocking.setChecked(self.criterion.get("blocking", False))
        layout.addWidget(self.chk_blocking)
        
        self.chk_enabled = QCheckBox("Activé")
        self.chk_enabled.setChecked(self.criterion.get("enabled", True))
        layout.addWidget(self.chk_enabled)
        
        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("Enregistrer")
        btn_ok.clicked.connect(self.accept)
        btn_cancel = QPushButton("Annuler")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_ok)
        layout.addLayout(btn_layout)

    def _update_types(self, category):
        self.cb_type.clear()
        if category in VALID_TYPES:
            self.cb_type.addItems(sorted(list(VALID_TYPES[category])))

    def get_criterion(self):
        c_type = self.cb_type.currentText()
        crit = {
            "id": self.criterion.get("id", f"{self.cb_category.currentText()}_{str(uuid.uuid4())[:8]}"),
            "category": self.cb_category.currentText(),
            "type": c_type,
            "description": self.edit_desc.text(),
            "blocking": self.chk_blocking.isChecked(),
            "enabled": self.chk_enabled.isChecked(),
            "severity": "error" if self.chk_blocking.isChecked() else "warning"
        }
        
        # Conserver les anciens champs étendus s'ils existent
        for key in ["target", "trigger", "expect", "sampling", "min", "max", "depends_on", "subject"]:
            if key in self.criterion:
                crit[key] = self.criterion[key]
                
        # Assurer la validité basique du type
        if c_type == "required_connection" and "target" not in crit:
            crit["target"] = {}
        if c_type == "causality_mapping" and ("trigger" not in crit or "expect" not in crit):
            crit["trigger"] = {}
            crit["expect"] = {}
        if c_type == "allowed_range" and "min" not in crit and "max" not in crit:
            crit["min"] = 0
            
        return crit

class CriteriaTab(QWidget):
    def __init__(self, project: ProjectModel, parent=None):
        super().__init__(parent)
        self.project = project
        self._setup_ui()
        self.load_from_project()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Critères de réussite"])
        layout.addWidget(self.tree)
        
        self.roots = {
            "topology": QTreeWidgetItem(self.tree, ["🔌 Topologie"]),
            "code": QTreeWidgetItem(self.tree, ["💻 Code"]),
            "behavior": QTreeWidgetItem(self.tree, ["⚙️ Comportement"]),
            "constraints": QTreeWidgetItem(self.tree, ["🚧 Contraintes"]),
        }
        for root in self.roots.values():
            root.setExpanded(True)
            
        btn_layout = QHBoxLayout()
        btn_add = QPushButton("+ Ajouter un critère")
        btn_add.clicked.connect(self._add_criterion)
        btn_edit = QPushButton("Modifier")
        btn_edit.clicked.connect(self._edit_criterion)
        btn_rem = QPushButton("-")
        btn_rem.clicked.connect(self._remove_criterion)
        btn_layout.addWidget(btn_add)
        btn_layout.addWidget(btn_edit)
        btn_layout.addWidget(btn_rem)
        layout.addLayout(btn_layout)

    def load_from_project(self):
        if not self.project:
            return
        for root in self.roots.values():
            root.takeChildren()
            
        if not self.project.pedagogy_profile:
            return
            
        criteria = self.project.pedagogy_profile.get("criteria", [])
        for c in criteria:
            cat = c.get("category", "topology")
            if cat not in self.roots:
                cat = "topology"
            root = self.roots[cat]
            status = "☑" if c.get("enabled", True) else "☐"
            block = "[OBLIG]" if c.get("blocking", False) else "[REC]"
            desc = c.get("description", "")
            item = QTreeWidgetItem(root, [f"{status} {block} {desc}"])
            item.setData(0, 32, c)

    def _save_to_project(self):
        if self.project.pedagogy_profile is None:
            self.project.pedagogy_profile = {}
            
        criteria = []
        for root in self.roots.values():
            for i in range(root.childCount()):
                criteria.append(root.child(i).data(0, 32))
                
        self.project.pedagogy_profile["criteria"] = criteria

    def _add_criterion(self):
        dlg = CriterionDialog(self)
        if dlg.exec() == 1:
            crit = dlg.get_criterion()
            if self.project.pedagogy_profile is None:
                self.project.pedagogy_profile = {}
            if "criteria" not in self.project.pedagogy_profile:
                self.project.pedagogy_profile["criteria"] = []
            self.project.pedagogy_profile["criteria"].append(crit)
            self.load_from_project()

    def _edit_criterion(self):
        item = self.tree.currentItem()
        if not item or item.parent() is None:
            return
            
        crit = item.data(0, 32)
        dlg = CriterionDialog(self, crit)
        if dlg.exec() == 1:
            new_crit = dlg.get_criterion()
            item.setData(0, 32, new_crit)
            self._save_to_project()
            self.load_from_project()

    def _remove_criterion(self):
        item = self.tree.currentItem()
        if not item or item.parent() is None:
            return
        item.parent().takeChild(item.parent().indexOfChild(item))
        self._save_to_project()
