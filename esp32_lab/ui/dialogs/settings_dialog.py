# -*- coding: utf-8 -*-
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QTabWidget, QWidget, QComboBox, 
                               QFileDialog, QLineEdit, QCheckBox)
from PySide6.QtCore import Qt, QSettings
from esp32_lab.app.i18n import get_current_language

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Paramètres - ESP32 MicroPython Lab")
        self.resize(500, 350)
        self.settings = QSettings("ESP32Lab", "ESP32MicroPythonLab")
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # --- Onglet Général ---
        tab_general = QWidget()
        gen_layout = QVBoxLayout(tab_general)
        gen_layout.setSpacing(15)
        
        # Langue
        row_lang = QHBoxLayout()
        row_lang.addWidget(QLabel("Langue de l'interface :"))
        self.cb_lang = QComboBox()
        self.cb_lang.addItems(["Français", "English"])
        row_lang.addWidget(self.cb_lang)
        row_lang.addStretch()
        gen_layout.addLayout(row_lang)
        
        # Dossier par défaut
        gen_layout.addWidget(QLabel("Dossier de sauvegarde par défaut :"))
        row_dir = QHBoxLayout()
        self.txt_default_dir = QLineEdit()
        self.txt_default_dir.setPlaceholderText("Laissez vide pour utiliser Mes Documents")
        btn_browse = QPushButton("Parcourir...")
        btn_browse.clicked.connect(self._browse_default_dir)
        row_dir.addWidget(self.txt_default_dir)
        row_dir.addWidget(btn_browse)
        gen_layout.addLayout(row_dir)
        
        gen_layout.addStretch()
        self.tabs.addTab(tab_general, "Général")
        
        # --- Onglet Apparence ---
        tab_apparence = QWidget()
        app_layout = QVBoxLayout(tab_apparence)
        
        row_theme = QHBoxLayout()
        row_theme.addWidget(QLabel("Thème Visuel :"))
        self.cb_theme = QComboBox()
        self.cb_theme.addItems(["Sombre (Dark)", "Clair (Light)"])
        row_theme.addWidget(self.cb_theme)
        row_theme.addStretch()
        app_layout.addLayout(row_theme)
        
        app_layout.addStretch()
        self.tabs.addTab(tab_apparence, "Apparence")
        
        # --- Onglet Simulation ---
        tab_sim = QWidget()
        sim_layout = QVBoxLayout(tab_sim)
        
        self.chk_bridge = QCheckBox("Activer la Passerelle Réseau (Host Network Bridge)")

        self.chk_bridge.setToolTip("Permet à l'ESP32 simulé d'accéder à Internet via votre connexion PC.")
        sim_layout.addWidget(self.chk_bridge)
        
        sim_layout.addStretch()
        self.tabs.addTab(tab_sim, "Simulation")
        
        # Boutons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_cancel = QPushButton("Annuler")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Enregistrer")
        btn_save.setStyleSheet("background-color: #0284c7; color: white; font-weight: bold;")
        btn_save.clicked.connect(self._save_settings)
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        
        layout.addLayout(btn_layout)

    def _load_settings(self):
        # Lang
        curr_lang = get_current_language()
        self.cb_lang.setCurrentIndex(0 if curr_lang == "fr" else 1)
        
        # Theme
        curr_theme = self.settings.value("theme", "dark")
        self.cb_theme.setCurrentIndex(0 if curr_theme == "dark" else 1)
        
        # Dir
        self.txt_default_dir.setText(self.settings.value("default_save_dir", ""))
        
        # Bridge
        self.chk_bridge.setChecked(self.settings.value("use_host_network_bridge", True, type=bool))

    def _browse_default_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Choisir un dossier", self.txt_default_dir.text())
        if dir_path:
            self.txt_default_dir.setText(dir_path)

    def _save_settings(self):
        new_lang = "fr" if self.cb_lang.currentIndex() == 0 else "en"
        self.settings.setValue("language", new_lang)
        
        new_theme = "dark" if self.cb_theme.currentIndex() == 0 else "light"
        self.settings.setValue("theme", new_theme)
        
        self.settings.setValue("default_save_dir", self.txt_default_dir.text().strip())
        
        bridge_val = self.chk_bridge.isChecked()
        self.settings.setValue("use_host_network_bridge", bridge_val)
        from esp32_lab.simulator.modules.network import set_host_bridge_enabled
        set_host_bridge_enabled(bridge_val)
        
        self.accept()
