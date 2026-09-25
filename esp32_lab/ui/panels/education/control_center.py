# -*- coding: utf-8 -*-
from PySide6.QtWidgets import QDockWidget, QTabWidget, QVBoxLayout, QWidget
from ....core.models.project import ProjectModel
from .mission_tab import MissionTab
from .criteria_tab import CriteriaTab
from .tests_tab import TestsTab
from .submissions_tab import SubmissionsTab

class TeacherControlCenter(QDockWidget):
    def __init__(self, parent=None, project: ProjectModel = None):
        super().__init__("Centre de Contrôle TP", parent)
        self.setObjectName("TeacherControlCenter")
        self.project = project
        from PySide6.QtCore import Qt
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.tabs = QTabWidget()
        self.mission_tab = MissionTab(self.project)
        self.criteria_tab = CriteriaTab(self.project)
        self.tests_tab = TestsTab(self.project)
        self.submissions_tab = SubmissionsTab(project=self.project)
        
        self.tabs.addTab(self.mission_tab, "Mission")
        self.tabs.addTab(self.criteria_tab, "Critères")
        self.tabs.addTab(self.tests_tab, "Tests")
        self.tabs.addTab(self.submissions_tab, "Corrections")
        
        layout.addWidget(self.tabs)
        self.setWidget(container)
        self.setVisible(False)

    def attach_review_service(self, review_service):
        self.submissions_tab.attach_service(review_service)

    def load_project(self, project: ProjectModel):
        self.project = project
        self.mission_tab.project = project
        self.mission_tab.load_from_project()
        
        self.criteria_tab.project = project
        self.criteria_tab.load_from_project()
        
        self.tests_tab.project = project
        self.tests_tab.load_from_project()
        
        self.submissions_tab.project = project
        self.submissions_tab.refresh_list()
