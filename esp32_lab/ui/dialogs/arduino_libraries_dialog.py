"""
Boîte de dialogue : Gestionnaire de Bibliothèques et Outils Arduino (ArduinoLibrariesDialog)
Recherche, installation et gestion des bibliothèques C++ et du cœur AVR via arduino-cli.
"""

import webbrowser
from PySide6.QtCore import QSettings, Qt, QThread, Signal
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ...hardware.arduino_cli import ArduinoLibraryService


class ArduinoWorker(QThread):
    """Worker d'arrière-plan pour exécuter les opérations arduino-cli sans bloquer l'UI."""
    log_message = Signal(str)
    task_finished = Signal(bool, str, str)  # success, task_type, message
    search_results_ready = Signal(list)     # list of dicts

    def __init__(self, task_type: str, payload=None, parent=None):
        super().__init__(parent)
        self.task_type = task_type
        self.payload = payload

    def run(self):
        try:
            if self.task_type == "install_lib":
                success, msg = ArduinoLibraryService.install_library(
                    self.payload, log_callback=self.log_message.emit
                )
                self.task_finished.emit(success, self.task_type, self.payload)

            elif self.task_type == "uninstall_lib":
                success, msg = ArduinoLibraryService.uninstall_library(
                    self.payload, log_callback=self.log_message.emit
                )
                self.task_finished.emit(success, self.task_type, self.payload)

            elif self.task_type == "install_avr_core":
                success, msg = ArduinoLibraryService.install_avr_core(
                    log_callback=self.log_message.emit
                )
                self.task_finished.emit(success, self.task_type, msg)

            elif self.task_type in ("install_cli_direct", "install_cli_auto"):
                success, msg = ArduinoLibraryService.install_cli_direct(
                    log_callback=self.log_message.emit
                )
                self.task_finished.emit(success, self.task_type, msg)

            elif self.task_type == "install_cli_winget":
                success, msg = ArduinoLibraryService.install_cli_via_winget(
                    log_callback=self.log_message.emit
                )
                self.task_finished.emit(success, self.task_type, msg)

            elif self.task_type == "search_libs":
                results = ArduinoLibraryService.search_libraries(self.payload)
                self.search_results_ready.emit(results)
                self.task_finished.emit(True, self.task_type, "Recherche terminée")

        except Exception as ex:
            self.log_message.emit(f"❌ Erreur worker : {ex}")
            self.task_finished.emit(False, self.task_type, str(ex))


class LibraryItemWidget(QWidget):
    """Widget de carte pour afficher une bibliothèque dans la liste."""
    install_clicked = Signal(str)
    uninstall_clicked = Signal(str)

    def __init__(self, lib_data: dict, is_light: bool = False, parent=None):
        super().__init__(parent)
        self.lib_data = lib_data
        self.is_light = is_light
        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(12)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)

        # En-tête : Titre + Catégorie + Version
        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        lbl_name = QLabel(self.lib_data.get("name", "Sans nom"))
        name_col = "#0f172a" if self.is_light else "#f8fafc"
        lbl_name.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {name_col};")
        top_row.addWidget(lbl_name)

        cat = self.lib_data.get("category", "")
        if cat:
            lbl_cat = QLabel(cat)
            lbl_cat.setStyleSheet("""
                background-color: rgba(14, 165, 233, 0.15);
                color: #0284c7;
                font-size: 11px;
                font-weight: 600;
                padding: 2px 6px;
                border-radius: 4px;
            """)
            top_row.addWidget(lbl_cat)

        version = self.lib_data.get("version", "")
        if version:
            lbl_ver = QLabel(f"v{version}")
            lbl_ver.setStyleSheet("font-size: 11px; color: #64748b; font-weight: 600;")
            top_row.addWidget(lbl_ver)

        top_row.addStretch()
        info_layout.addLayout(top_row)

        # Description
        desc_text = self.lib_data.get("sentence", "Aucune description fournie.")
        lbl_desc = QLabel(desc_text)
        lbl_desc.setWordWrap(True)
        desc_col = "#475569" if self.is_light else "#94a3b8"
        lbl_desc.setStyleSheet(f"font-size: 12px; color: {desc_col};")
        info_layout.addWidget(lbl_desc)

        # Inclusion C++ conseillée
        header = self.lib_data.get("header", "")
        author = self.lib_data.get("author", "")
        sub_info = []
        if header:
            sub_info.append(f"Inclusion : <code>#include {header}</code>")
        if author:
            sub_info.append(f"Auteur : {author}")
        if sub_info:
            lbl_sub = QLabel("  •  ".join(sub_info))
            lbl_sub.setTextFormat(Qt.RichText)
            sub_col = "#64748b" if self.is_light else "#64748b"
            lbl_sub.setStyleSheet(f"font-size: 11px; color: {sub_col};")
            info_layout.addWidget(lbl_sub)

        layout.addLayout(info_layout, 1)

        # Boutons d'action
        is_builtin = self.lib_data.get("is_builtin", False)
        is_installed = self.lib_data.get("installed", False)

        if is_builtin:
            badge_builtin = QLabel("✔ Intégrée au cœur")
            badge_builtin.setStyleSheet("""
                background-color: rgba(16, 185, 129, 0.15);
                color: #059669;
                font-size: 11px;
                font-weight: bold;
                padding: 6px 12px;
                border-radius: 6px;
            """)
            layout.addWidget(badge_builtin)
        elif is_installed:
            badge_inst = QLabel("✔ Installée")
            badge_inst.setStyleSheet("""
                background-color: rgba(16, 185, 129, 0.15);
                color: #059669;
                font-size: 11px;
                font-weight: bold;
                padding: 6px 10px;
                border-radius: 6px;
            """)
            layout.addWidget(badge_inst)

            btn_del = QPushButton("Désinstaller")
            btn_del.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #ef4444;
                    border: 1px solid #ef4444;
                    padding: 4px 10px;
                    border-radius: 4px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #ef4444;
                    color: white;
                }
            """)
            btn_del.clicked.connect(lambda: self.uninstall_clicked.emit(self.lib_data["name"]))
            layout.addWidget(btn_del)
        else:
            btn_install = QPushButton("📥 Installer")
            btn_install.setStyleSheet("""
                QPushButton {
                    background-color: #0284c7;
                    color: white;
                    font-weight: 700;
                    padding: 6px 14px;
                    border-radius: 6px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #0369a1;
                }
            """)
            btn_install.clicked.connect(lambda: self.install_clicked.emit(self.lib_data["name"]))
            layout.addWidget(btn_install)


class ArduinoLibrariesDialog(QDialog):
    """Dialogue complet de gestion des bibliothèques C++ et outils Arduino."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📦 Gestionnaire de Bibliothèques Arduino — ESP32 MicroPython Lab")
        self.resize(850, 620)
        self.setMinimumSize(750, 520)

        settings = QSettings("ESP32Lab", "ESP32MicroPythonLab")
        self.is_light = (settings.value("theme", "dark") == "light")

        self.worker = None
        self._init_styles()
        self._setup_ui()
        self._refresh_status()

    def _init_styles(self):
        bg_dlg = "#ffffff" if self.is_light else "#0f172a"
        fg_dlg = "#0f172a" if self.is_light else "#f8fafc"
        tab_bg = "#f1f5f9" if self.is_light else "#1e293b"
        tab_active_bg = "#ffffff" if self.is_light else "#0f172a"
        tab_border = "#cbd5e1" if self.is_light else "#334155"
        header_fg = "#0284c7" if self.is_light else "#38bdf8"
        muted_fg = "#475569" if self.is_light else "#94a3b8"

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {bg_dlg};
                color: {fg_dlg};
                font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            }}
            QLabel {{
                background: transparent;
                color: {fg_dlg};
            }}
            QTabWidget::pane {{
                border: 1px solid {tab_border};
                border-radius: 8px;
                background-color: {bg_dlg};
                top: -1px;
            }}
            QTabBar::tab {{
                background-color: {tab_bg};
                color: {muted_fg};
                padding: 9px 18px;
                border: 1px solid {tab_border};
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 4px;
                font-size: 12px;
                font-weight: 700;
            }}
            QTabBar::tab:selected {{
                background-color: {tab_active_bg};
                color: {header_fg};
                border-bottom: 2px solid {header_fg};
            }}
        """)

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # En-tête
        header_row = QHBoxLayout()
        header_text = QVBoxLayout()
        header_text.setSpacing(2)

        lbl_title = QLabel("📦 Gestionnaire de Bibliothèques & Cœur Arduino")
        lbl_title.setStyleSheet("font-size: 17px; font-weight: 800; color: #0284c7; background: transparent;")
        lbl_sub = QLabel("Téléchargez et installez les bibliothèques C++ indispensables pour vos montages physiques réels.")
        lbl_sub.setStyleSheet("font-size: 12px; color: #64748b; background: transparent;")
        header_text.addWidget(lbl_title)
        header_text.addWidget(lbl_sub)
        header_row.addLayout(header_text)
        header_row.addStretch()

        self.btn_refresh = QPushButton("🔄 Actualiser")
        self.btn_refresh.setStyleSheet("""
            QPushButton {
                background-color: rgba(2, 132, 199, 0.1);
                color: #0284c7;
                border: 1px solid rgba(2, 132, 199, 0.3);
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: rgba(2, 132, 199, 0.2);
            }
        """)
        self.btn_refresh.clicked.connect(self._refresh_status)
        header_row.addWidget(self.btn_refresh)
        main_layout.addLayout(header_row)

        # Bannière d'état (arduino-cli & Cœur AVR)
        self.status_banner = QFrame()
        self.status_banner.setFrameShape(QFrame.StyledPanel)
        self.status_layout = QHBoxLayout(self.status_banner)
        self.status_layout.setContentsMargins(14, 10, 14, 10)
        self.status_layout.setSpacing(12)
        main_layout.addWidget(self.status_banner)

        # Onglets
        self.tabs = QTabWidget()

        # Onglet 1 : Bibliothèques Recommandées / Éducatives
        self.tab_curated = QWidget()
        self._setup_curated_tab(self.tab_curated)
        self.tabs.addTab(self.tab_curated, "⭐ Bibliothèques Recommandées")

        # Onglet 2 : Bibliothèques Installées
        self.tab_installed = QWidget()
        self._setup_installed_tab(self.tab_installed)
        self.tabs.addTab(self.tab_installed, "📥 Installées sur ce PC")

        # Onglet 3 : Recherche en ligne
        self.tab_search = QWidget()
        self._setup_search_tab(self.tab_search)
        self.tabs.addTab(self.tab_search, "🔍 Recherche dans le Catalogue")

        main_layout.addWidget(self.tabs, 1)

        # Zone d'exécution / Console
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Mode indéterminé
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        self.console_frame = QFrame()
        console_layout = QVBoxLayout(self.console_frame)
        console_layout.setContentsMargins(0, 0, 0, 0)
        console_layout.setSpacing(4)

        console_header = QHBoxLayout()
        self.lbl_console_title = QLabel("📄 Journal d'installation / Console")
        self.lbl_console_title.setStyleSheet("font-size: 11px; font-weight: 700; color: #64748b;")
        console_header.addWidget(self.lbl_console_title)
        console_header.addStretch()

        self.btn_toggle_console = QPushButton("Afficher le journal")
        self.btn_toggle_console.setCheckable(True)
        self.btn_toggle_console.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #0284c7;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover { text-decoration: underline; }
        """)
        self.btn_toggle_console.toggled.connect(self._toggle_console)
        console_header.addWidget(self.btn_toggle_console)
        console_layout.addLayout(console_header)

        self.console_log = QPlainTextEdit()
        self.console_log.setReadOnly(True)
        self.console_log.setMaximumHeight(110)
        self.console_log.setVisible(False)
        code_bg = "#f8fafc" if self.is_light else "#090d16"
        code_fg = "#0f172a" if self.is_light else "#38bdf8"
        self.console_log.setStyleSheet(f"""
            background-color: {code_bg};
            color: {code_fg};
            border: 1px solid #cbd5e1;
            border-radius: 6px;
            font-family: Consolas, monospace;
            font-size: 11px;
        """)
        console_layout.addWidget(self.console_log)
        main_layout.addWidget(self.console_frame)

        # Boutons du bas
        bottom_bar = QHBoxLayout()
        lbl_hint = QLabel("💡 En simulation virtuelle, ces bibliothèques sont déjà simulées sans installation requise.")
        lbl_hint.setStyleSheet("font-size: 11px; color: #64748b; font-style: italic;")
        bottom_bar.addWidget(lbl_hint)
        bottom_bar.addStretch()

        btn_close = QPushButton("Fermer")
        btn_close_bg = "#e2e8f0" if self.is_light else "#334155"
        btn_close_fg = "#0f172a" if self.is_light else "#f1f5f9"
        btn_close.setStyleSheet(f"""
            QPushButton {{
                background-color: {btn_close_bg};
                color: {btn_close_fg};
                padding: 8px 18px;
                border-radius: 6px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: #cbd5e1;
            }}
        """)
        btn_close.clicked.connect(self.accept)
        bottom_bar.addWidget(btn_close)
        main_layout.addLayout(bottom_bar)

    def _setup_curated_tab(self, parent_widget):
        layout = QVBoxLayout(parent_widget)
        layout.setContentsMargins(8, 12, 8, 8)
        layout.setSpacing(10)

        # Filtre rapide
        filter_row = QHBoxLayout()
        self.txt_curated_filter = QLineEdit()
        self.txt_curated_filter.setPlaceholderText("🔍 Filtrer parmi les bibliothèques recommandées (ex: servo, lcd, dht)...")
        self.txt_curated_filter.setStyleSheet("""
            QLineEdit {
                padding: 6px 12px;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                font-size: 12px;
            }
        """)
        self.txt_curated_filter.textChanged.connect(self._filter_curated_list)
        filter_row.addWidget(self.txt_curated_filter)
        layout.addLayout(filter_row)

        self.list_curated = QListWidget()
        self._style_list(self.list_curated)
        layout.addWidget(self.list_curated)

    def _setup_installed_tab(self, parent_widget):
        layout = QVBoxLayout(parent_widget)
        layout.setContentsMargins(8, 12, 8, 8)
        layout.setSpacing(10)

        lbl_desc = QLabel("Bibliothèques actuellement téléchargées et prêtes pour la compilation avec avr-gcc :")
        lbl_desc.setStyleSheet("font-size: 12px; color: #64748b;")
        layout.addWidget(lbl_desc)

        self.list_installed = QListWidget()
        self._style_list(self.list_installed)
        layout.addWidget(self.list_installed)

    def _setup_search_tab(self, parent_widget):
        layout = QVBoxLayout(parent_widget)
        layout.setContentsMargins(8, 12, 8, 8)
        layout.setSpacing(10)

        search_row = QHBoxLayout()
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Entrez un nom de bibliothèque ou capteur (ex: ultrasonic, mpu6050, rtc)...")
        self.txt_search.setStyleSheet("""
            QLineEdit {
                padding: 7px 12px;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                font-size: 12px;
            }
        """)
        self.txt_search.returnPressed.connect(self._start_search)
        search_row.addWidget(self.txt_search)

        btn_search = QPushButton("🔍 Rechercher")
        btn_search.setStyleSheet("""
            QPushButton {
                background-color: #0284c7;
                color: white;
                font-weight: 700;
                padding: 7px 16px;
                border-radius: 6px;
                font-size: 12px;
            }
            QPushButton:hover { background-color: #0369a1; }
        """)
        btn_search.clicked.connect(self._start_search)
        search_row.addWidget(btn_search)
        layout.addLayout(search_row)

        self.list_search = QListWidget()
        self._style_list(self.list_search)
        layout.addWidget(self.list_search)

    def _style_list(self, list_widget: QListWidget):
        list_bg = "#f8fafc" if self.is_light else "#131b2e"
        border_col = "#cbd5e1" if self.is_light else "#1e293b"
        list_widget.setStyleSheet(f"""
            QListWidget {{
                background-color: {list_bg};
                border: 1px solid {border_col};
                border-radius: 8px;
            }}
            QListWidget::item {{
                border-bottom: 1px solid {border_col};
            }}
            QListWidget::item:hover {{
                background-color: rgba(2, 132, 199, 0.05);
            }}
        """)

    def _toggle_console(self, checked: bool):
        self.console_log.setVisible(checked)
        self.btn_toggle_console.setText("Masquer le journal" if checked else "Afficher le journal")

    # -------------------------------------------------------------------------
    # GESTION DU STATUT DE L'ENVIRONNEMENT ARDUINO
    # -------------------------------------------------------------------------
    def _refresh_status(self):
        # Vider la bannière
        while self.status_layout.count() > 0:
            item = self.status_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        cli_installed = ArduinoLibraryService.is_cli_installed()
        version = ArduinoLibraryService.get_cli_version() if cli_installed else None
        avr_installed = ArduinoLibraryService.is_avr_core_installed() if cli_installed else False

        if not cli_installed:
            self.status_banner.setStyleSheet("""
                QFrame {
                    background-color: rgba(245, 158, 11, 0.12);
                    border: 1px solid #f59e0b;
                    border-radius: 8px;
                }
            """)
            lbl_warn = QLabel("⚠️ <b>arduino-cli</b> n'est pas encore détecté sur votre ordinateur. Pour compiler vers une carte physique, installez-le :")
            lbl_warn.setStyleSheet("color: #b45309; font-size: 12px;")
            self.status_layout.addWidget(lbl_warn, 1)

            btn_direct = QPushButton("⚡ Installer en 1 clic (recommandé)")
            btn_direct.setToolTip("Télécharge directement et configure arduino-cli de façon autonome sans droits administrateur")
            btn_direct.setStyleSheet("""
                QPushButton {
                    background-color: #059669;
                    color: white;
                    font-weight: bold;
                    padding: 6px 14px;
                    border-radius: 6px;
                    font-size: 12px;
                }
                QPushButton:hover { background-color: #047857; }
            """)
            btn_direct.clicked.connect(self._install_cli_direct)
            self.status_layout.addWidget(btn_direct)

            btn_winget = QPushButton("Installer via winget")
            btn_winget.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #475569;
                    border: 1px solid #cbd5e1;
                    padding: 6px 10px;
                    border-radius: 6px;
                    font-size: 11px;
                }
                QPushButton:hover { background-color: rgba(0,0,0,0.05); }
            """)
            btn_winget.clicked.connect(self._install_cli_winget)
            self.status_layout.addWidget(btn_winget)

            btn_manual = QPushButton("🌐 Site officiel")
            btn_manual.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #0284c7;
                    border: 1px solid #0284c7;
                    padding: 6px 10px;
                    border-radius: 6px;
                    font-size: 11px;
                }
            """)
            btn_manual.clicked.connect(lambda: webbrowser.open("https://arduino.github.io/arduino-cli/"))
            self.status_layout.addWidget(btn_manual)

        elif not avr_installed:
            self.status_banner.setStyleSheet("""
                QFrame {
                    background-color: rgba(2, 132, 199, 0.1);
                    border: 1px solid #0284c7;
                    border-radius: 8px;
                }
            """)
            ver_text = f" ({version})" if version else ""
            lbl_info = QLabel(f"✔ <b>arduino-cli</b> est prêt{ver_text}, mais le cœur <b>arduino:avr</b> (compilateur Uno) n'est pas installé.")
            lbl_info.setStyleSheet("color: #0284c7; font-size: 12px;")
            self.status_layout.addWidget(lbl_info, 1)

            btn_avr = QPushButton("⚡ Installer le Cœur Arduino AVR")
            btn_avr.setStyleSheet("""
                QPushButton {
                    background-color: #0284c7;
                    color: white;
                    font-weight: bold;
                    padding: 6px 14px;
                    border-radius: 6px;
                    font-size: 12px;
                }
                QPushButton:hover { background-color: #0369a1; }
            """)
            btn_avr.clicked.connect(self._install_avr_core)
            self.status_layout.addWidget(btn_avr)

        else:
            self.status_banner.setStyleSheet("""
                QFrame {
                    background-color: rgba(16, 185, 129, 0.1);
                    border: 1px solid #10b981;
                    border-radius: 8px;
                }
            """)
            ver_text = f" ({version})" if version else ""
            lbl_ok = QLabel(f"✔ <b>Environnement Arduino opérationnel :</b> arduino-cli{ver_text} actif & Cœur <b>arduino:avr</b> prêt pour le téléversement.")
            lbl_ok.setStyleSheet("color: #059669; font-size: 12px;")
            self.status_layout.addWidget(lbl_ok, 1)

        self._populate_curated_list()
        self._populate_installed_list()

    # -------------------------------------------------------------------------
    # POPULATION DES LISTES
    # -------------------------------------------------------------------------
    def _populate_curated_list(self):
        self.list_curated.clear()
        installed_names = {l["name"].lower() for l in ArduinoLibraryService.list_installed_libraries()}
        filter_text = self.txt_curated_filter.text().lower().strip()

        for lib in ArduinoLibraryService.CURATED_LIBRARIES:
            name = lib["name"]
            cat = lib.get("category", "")
            desc = lib.get("sentence", "")
            if filter_text and (filter_text not in name.lower() and filter_text not in cat.lower() and filter_text not in desc.lower()):
                continue

            lib_copy = dict(lib)
            if not lib_copy.get("is_builtin"):
                lib_copy["installed"] = (name.lower() in installed_names)

            item = QListWidgetItem(self.list_curated)
            widget = LibraryItemWidget(lib_copy, is_light=self.is_light)
            widget.install_clicked.connect(self._install_lib)
            widget.uninstall_clicked.connect(self._uninstall_lib)
            item.setSizeHint(widget.sizeHint())
            self.list_curated.addItem(item)
            self.list_curated.setItemWidget(item, widget)

    def _filter_curated_list(self):
        self._populate_curated_list()

    def _populate_installed_list(self):
        self.list_installed.clear()
        installed_libs = ArduinoLibraryService.list_installed_libraries()

        if not installed_libs:
            item = QListWidgetItem("Aucune bibliothèque externe installée pour le moment.")
            item.setTextAlignment(Qt.AlignCenter)
            item.setFlags(Qt.NoItemFlags)
            self.list_installed.addItem(item)
            return

        for lib in installed_libs:
            item = QListWidgetItem(self.list_installed)
            widget = LibraryItemWidget(lib, is_light=self.is_light)
            widget.uninstall_clicked.connect(self._uninstall_lib)
            item.setSizeHint(widget.sizeHint())
            self.list_installed.addItem(item)
            self.list_installed.setItemWidget(item, widget)

    # -------------------------------------------------------------------------
    # ACTIONS ASYNCHRONES VIA WORKER
    # -------------------------------------------------------------------------
    def _install_lib(self, lib_name: str):
        self._start_task("install_lib", lib_name, f"Installation de la bibliothèque '{lib_name}'...")

    def _uninstall_lib(self, lib_name: str):
        reply = QMessageBox.question(
            self,
            "Confirmer la désinstallation",
            f"Voulez-vous vraiment désinstaller la bibliothèque '{lib_name}' ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self._start_task("uninstall_lib", lib_name, f"Désinstallation de '{lib_name}'...")

    def _install_avr_core(self):
        self._start_task("install_avr_core", None, "Installation du cœur Arduino AVR...")

    def _install_cli_direct(self):
        self._start_task("install_cli_direct", None, "Installation directe de arduino-cli...")

    def _install_cli_winget(self):
        self._start_task("install_cli_winget", None, "Installation de arduino-cli via winget...")

    def _start_search(self):
        q = self.txt_search.text().strip()
        if not q:
            return
        self._start_task("search_libs", q, f"Recherche de '{q}' dans le catalogue Arduino...")

    def _start_task(self, task_type: str, payload, desc: str):
        if self.worker and self.worker.isRunning():
            QMessageBox.warning(self, "Opération en cours", "Veuillez patienter qu'une opération se termine.")
            return

        self.progress_bar.setVisible(True)
        self.btn_toggle_console.setChecked(True)
        self.console_log.appendPlainText(f"\n--- {desc} ---")

        self.worker = ArduinoWorker(task_type, payload, self)
        self.worker.log_message.connect(self._on_worker_log)
        self.worker.task_finished.connect(self._on_worker_finished)
        if task_type == "search_libs":
            self.worker.search_results_ready.connect(self._on_search_results)
        self.worker.start()

    def _on_worker_log(self, text: str):
        self.console_log.appendPlainText(text)

    def _on_worker_finished(self, success: bool, task_type: str, payload: str):
        self.progress_bar.setVisible(False)
        if success:
            self.console_log.appendPlainText("✔ Opération terminée avec succès !")
        else:
            self.console_log.appendPlainText(f"❌ Échec de l'opération : {payload}")

        self._refresh_status()

    def _on_search_results(self, results: list):
        self.list_search.clear()
        if not results:
            item = QListWidgetItem("Aucun résultat correspondant dans le catalogue officiel.")
            item.setTextAlignment(Qt.AlignCenter)
            item.setFlags(Qt.NoItemFlags)
            self.list_search.addItem(item)
            return

        for lib in results:
            item = QListWidgetItem(self.list_search)
            widget = LibraryItemWidget(lib, is_light=self.is_light)
            widget.install_clicked.connect(self._install_lib)
            widget.uninstall_clicked.connect(self._uninstall_lib)
            item.setSizeHint(widget.sizeHint())
            self.list_search.addItem(item)
            self.list_search.setItemWidget(item, widget)
