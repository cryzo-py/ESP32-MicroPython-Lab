# -*- coding: utf-8 -*-
from PySide6.QtWidgets import QWidget, QVBoxLayout, QSplitter, QTabWidget
from PySide6.QtCore import Qt

class EducationOrchestrator:
    """Manages the UI injection and wiring of the Educational features into MainWindow."""
    
    def __init__(self, main_window):
        self.mw = main_window
        self._init_engines()
        self._inject_ui()
        self._connect_signals()
        
    def _init_engines(self):
        # We keep the engines initialization just in case, but we don't inject the old UI
        pass
        
    def _inject_ui(self):
        # Remove all old legacy injection. The new UI (ActivityPanel) is already created and injected in main_window.py!
        pass

    def _connect_signals(self):
        pass

def inject(main_window):
    main_window.edu_orchestrator = EducationOrchestrator(main_window)
