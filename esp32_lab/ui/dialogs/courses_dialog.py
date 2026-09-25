"""
Boîte de dialogue pédagogique : Cours & TPs MicroPython ESP32
Affichage des cours théoriques officiels, des leçons, théories, défis et moteur d'évaluation automatique interactif.
"""

from PySide6.QtCore import QSettings, Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from ...core.courses import Lesson, get_course_curriculum
from ...core.course_theory import TheoryChapter, TheorySection, get_official_course_curriculum
from ...core.database import get_progress_db
from ...core.evaluator import EvaluationResult, ExerciseEvaluator
from ...core.models.project import ProjectModel
from ...core.report_generator import LabReportGenerator


class CoursesDialog(QDialog):
    """Dialogue affichant le cursus d'apprentissage officiel (Cours) et les TPs auto-évalués."""

    lesson_loaded = Signal(object)  # ProjectModel

    def __init__(self, current_project: ProjectModel, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🎓 Parcours Pédagogique Officiel & TPs — ESP32 MicroPython Lab")
        self.resize(980, 680)
        self.setMinimumSize(850, 560)
        settings = QSettings("ESP32Lab", "ESP32MicroPythonLab")
        self.is_light = (settings.value("theme", "dark") == "light")

        bg_dlg = "#ffffff" if self.is_light else "#0f172a"
        fg_dlg = "#0f172a" if self.is_light else "#f8fafc"
        card_bg = "#f8fafc" if self.is_light else "#1e293b"
        card_border = "#cbd5e1" if self.is_light else "#334155"
        muted_fg = "#475569" if self.is_light else "#94a3b8"
        header_fg = "#0284c7" if self.is_light else "#38bdf8"
        sub_fg = "#475569" if self.is_light else "#94a3b8"
        sec_title_fg = "#1e293b" if self.is_light else "#e2e8f0"
        challenge_bg = "#fffbeb" if self.is_light else "#1c1917"
        challenge_border = "#f59e0b" if self.is_light else "#78350f"
        challenge_fg = "#78350f" if self.is_light else "#fef3c7"
        eval_bg = "#f8fafc" if self.is_light else "#0b1329"
        eval_border = "#cbd5e1" if self.is_light else "#1e3a8a"
        eval_header = "#1d4ed8" if self.is_light else "#60a5fa"
        list_bg = "#f8fafc" if self.is_light else "#0f172a"
        list_border = "#cbd5e1" if self.is_light else "#1e293b"
        list_item_border = "#e2e8f0" if self.is_light else "#1e293b"
        list_item_hover = "#e2e8f0" if self.is_light else "#1e293b"

        tab_bg = "#f1f5f9" if self.is_light else "#1e293b"
        tab_active_bg = "#ffffff" if self.is_light else "#0f172a"
        tab_border = "#cbd5e1" if self.is_light else "#334155"

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
                padding: 10px 20px;
                border: 1px solid {tab_border};
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 4px;
                font-size: 13px;
                font-weight: 700;
            }}
            QTabBar::tab:selected {{
                background-color: {tab_active_bg};
                color: {header_fg};
                border-bottom: 2px solid {header_fg};
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {list_item_hover};
            }}
        """)

        self.current_project = current_project
        self.lessons = get_course_curriculum()
        self.theory_chapters = get_official_course_curriculum()
        self.evaluator = ExerciseEvaluator()
        self.last_eval_result = None

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # En-tête général
        header_box = QHBoxLayout()
        header_text_box = QVBoxLayout()
        header_text_box.setSpacing(2)

        header_title = QLabel("🎓 Cursus Pédagogique Officiel : Robotique & ESP32 MicroPython")
        header_title.setStyleSheet(f"font-size: 16px; font-weight: 800; color: {header_fg}; background: transparent;")
        header_sub = QLabel("Formation théorique complète conforme aux directives officielles et travaux pratiques interactifs.")
        header_sub.setStyleSheet(f"font-size: 12px; color: {sub_fg}; background: transparent;")
        header_text_box.addWidget(header_title)
        header_text_box.addWidget(header_sub)
        header_box.addLayout(header_text_box)
        header_box.addStretch()
        main_layout.addLayout(header_box)

        # Onglets principaux
        self.tabs = QTabWidget()
        
        # 1. Onglet Cours Théorique Officiel
        self.tab_theory = QWidget()
        self._setup_theory_tab(self.tab_theory, list_bg, list_border, list_item_border, list_item_hover, fg_dlg, sec_title_fg)
        self.tabs.addTab(self.tab_theory, "📖 Cours Théorique Officiel")

        # 2. Onglet Travaux Pratiques & Évaluation
        self.tab_tps = QWidget()
        self._setup_tps_tab(self.tab_tps, list_bg, list_border, list_item_border, list_item_hover, fg_dlg, sec_title_fg, challenge_bg, challenge_border, challenge_fg, eval_bg, eval_border, eval_header)
        self.tabs.addTab(self.tab_tps, "🛠️ Travaux Pratiques & Évaluation (11 TPs)")

        main_layout.addWidget(self.tabs, 1)

    # -------------------------------------------------------------------------
    # CONFIGURATION ONGLET 1 : COURS THÉORIQUE OFFICIEL
    # -------------------------------------------------------------------------
    def _setup_theory_tab(self, parent_widget, list_bg, list_border, list_item_border, list_item_hover, fg_dlg, sec_title_fg):
        layout = QHBoxLayout(parent_widget)
        layout.setContentsMargins(8, 12, 8, 8)
        layout.setSpacing(12)

        splitter = QSplitter(Qt.Horizontal)

        # Volet Gauche : Sommaire des Chapitres et Sections
        left_box = QWidget()
        left_layout = QVBoxLayout(left_box)
        left_layout.setContentsMargins(0, 0, 4, 0)
        left_layout.setSpacing(6)

        lbl_sommaire = QLabel("📚 Sommaire du Programme Officiel")
        lbl_sommaire.setStyleSheet(f"font-weight: 700; color: {sec_title_fg}; font-size: 13px; background: transparent;")
        left_layout.addWidget(lbl_sommaire)

        self.theory_list = QListWidget()
        self.theory_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {list_bg};
                border: 1px solid {list_border};
                border-radius: 8px;
                color: {fg_dlg};
                font-size: 12px;
            }}
            QListWidget::item {{
                padding: 10px 8px;
                border-bottom: 1px solid {list_item_border};
                border-radius: 4px;
                color: {fg_dlg};
            }}
            QListWidget::item:hover {{
                background-color: {list_item_hover};
            }}
            QListWidget::item:selected {{
                background-color: #0284c7;
                color: #ffffff;
                font-weight: bold;
            }}
        """)
        left_layout.addWidget(self.theory_list)
        splitter.addWidget(left_box)

        # Volet Droit : Lecteur de Cours & Projets Pratiques
        right_box = QWidget()
        right_layout = QVBoxLayout(right_box)
        right_layout.setContentsMargins(8, 0, 0, 0)
        right_layout.setSpacing(10)

        # En-tête de la section
        self.theory_header_widget = QWidget()
        header_vbox = QVBoxLayout(self.theory_header_widget)
        header_vbox.setContentsMargins(0, 0, 0, 6)
        header_vbox.setSpacing(4)

        self.lbl_theory_chap = QLabel("Chapitre")
        self.lbl_theory_chap.setStyleSheet("font-size: 11px; font-weight: 700; color: #0284c7; text-transform: uppercase;")
        header_vbox.addWidget(self.lbl_theory_chap)

        self.lbl_theory_sec_title = QLabel("Titre de la section")
        self.lbl_theory_sec_title.setStyleSheet(f"font-size: 18px; font-weight: 800; color: {sec_title_fg};")
        header_vbox.addWidget(self.lbl_theory_sec_title)

        self.lbl_theory_sec_summary = QLabel("Résumé")
        self.lbl_theory_sec_summary.setStyleSheet("font-size: 12px; color: #64748b; font-style: italic;")
        self.lbl_theory_sec_summary.setWordWrap(True)
        header_vbox.addWidget(self.lbl_theory_sec_summary)

        right_layout.addWidget(self.theory_header_widget)

        # Lecteur HTML riche
        self.theory_browser = QTextBrowser()
        self.theory_browser.setOpenExternalLinks(True)
        browser_bg = "#ffffff" if self.is_light else "#090d16"
        browser_border = "#cbd5e1" if self.is_light else "#1e293b"
        self.theory_browser.setStyleSheet(f"""
            QTextBrowser {{
                background-color: {browser_bg};
                border: 1px solid {browser_border};
                border-radius: 8px;
                padding: 14px;
                color: {fg_dlg};
                font-size: 13px;
                line-height: 1.6;
            }}
        """)
        right_layout.addWidget(self.theory_browser, 1)

        # Barre d'actions du cours
        theory_action_bar = QHBoxLayout()
        theory_action_bar.setSpacing(10)

        self.btn_load_theory_project = QPushButton("🚀 Charger ce projet officiel dans le simulateur")
        self.btn_load_theory_project.setStyleSheet("""
            QPushButton {
                background-color: #0284c7;
                color: white;
                font-weight: 700;
                padding: 10px 18px;
                border-radius: 6px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #0369a1;
            }
        """)
        self.btn_load_theory_project.clicked.connect(self._load_theory_starter_project)
        theory_action_bar.addWidget(self.btn_load_theory_project)
        theory_action_bar.addStretch()

        btn_theory_close = QPushButton("Fermer")
        btn_close_bg = "#e2e8f0" if self.is_light else "#334155"
        btn_close_fg = "#0f172a" if self.is_light else "#f1f5f9"
        btn_close_hover = "#cbd5e1" if self.is_light else "#475569"
        btn_theory_close.setStyleSheet(f"""
            QPushButton {{
                background-color: {btn_close_bg};
                color: {btn_close_fg};
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {btn_close_hover};
            }}
        """)
        btn_theory_close.clicked.connect(self.accept)
        theory_action_bar.addWidget(btn_theory_close)

        right_layout.addLayout(theory_action_bar)
        splitter.addWidget(right_box)
        splitter.setSizes([280, 660])

        layout.addWidget(splitter)

        # Mapping des sections à plat pour la navigation
        self.flat_theory_sections: list[tuple[TheoryChapter, TheorySection]] = []
        self._populate_theory_list()
        self.theory_list.currentRowChanged.connect(self._select_theory_section)
        if self.flat_theory_sections:
            self.theory_list.setCurrentRow(0)

    def _populate_theory_list(self):
        self.theory_list.clear()
        self.flat_theory_sections = []
        for chap in self.theory_chapters:
            for sec in chap.sections:
                self.flat_theory_sections.append((chap, sec))
                item = QListWidgetItem(f"{chap.icon} Ch.{chap.number} - {sec.title}")
                item.setToolTip(sec.summary)
                self.theory_list.addItem(item)

    def _select_theory_section(self, row: int):
        if row < 0 or row >= len(self.flat_theory_sections):
            return
        chap, sec = self.flat_theory_sections[row]
        self.lbl_theory_chap.setText(f"Chapitre {chap.number} : {chap.title}")
        self.lbl_theory_sec_title.setText(f"{sec.icon} {sec.title}")
        self.lbl_theory_sec_summary.setText(sec.summary)
        
        # Rendu HTML avec styles adaptés
        font_col = "#0f172a" if self.is_light else "#f1f5f9"
        wrapped_html = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: 'Segoe UI', system-ui, sans-serif;
                    color: {font_col};
                    font-size: 13px;
                }}
                h2 {{ color: #0284c7; margin-top: 4px; font-size: 16px; }}
                h3 {{ color: #0284c7; margin-top: 10px; font-size: 14px; }}
                p {{ margin-bottom: 8px; line-height: 1.5; }}
                ul {{ margin-left: 15px; padding-left: 10px; }}
                li {{ margin-bottom: 6px; }}
                table {{ border-color: #cbd5e1; }}
                code {{ background-color: rgba(14, 165, 233, 0.1); padding: 2px 4px; border-radius: 4px; font-family: Consolas, monospace; }}
            </style>
        </head>
        <body>
            {sec.content_html}
        </body>
        </html>
        """
        self.theory_browser.setHtml(wrapped_html)

        # Afficher le bouton si un circuit pré-câblé est disponible
        if sec.starter_project is not None:
            self.btn_load_theory_project.setVisible(True)
            self.btn_load_theory_project.setText(f"🚀 Charger le circuit : {sec.title}")
        else:
            self.btn_load_theory_project.setVisible(False)

    def _load_theory_starter_project(self):
        row = self.theory_list.currentRow()
        if 0 <= row < len(self.flat_theory_sections):
            _, sec = self.flat_theory_sections[row]
            if sec.starter_project is not None:
                self.lesson_loaded.emit(sec.starter_project)
                self.accept()

    # -------------------------------------------------------------------------
    # CONFIGURATION ONGLET 2 : TRAVAUX PRATIQUES & ÉVALUATION
    # -------------------------------------------------------------------------
    def _setup_tps_tab(self, parent_widget, list_bg, list_border, list_item_border, list_item_hover, fg_dlg, sec_title_fg, challenge_bg, challenge_border, challenge_fg, eval_bg, eval_border, eval_header):
        layout = QHBoxLayout(parent_widget)
        layout.setContentsMargins(8, 12, 8, 8)
        layout.setSpacing(12)

        splitter = QSplitter(Qt.Horizontal)

        # Colonne de gauche : Liste des 11 TPs
        left_box = QWidget()
        left_layout = QVBoxLayout(left_box)
        left_layout.setContentsMargins(0, 0, 4, 0)
        left_layout.setSpacing(6)

        lbl_catalog = QLabel("📚 Liste des 11 Travaux Pratiques")
        lbl_catalog.setStyleSheet(f"font-weight: 700; color: {sec_title_fg}; font-size: 13px; background: transparent;")
        left_layout.addWidget(lbl_catalog)

        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet(f"""
            QListWidget {{
                background-color: {list_bg};
                border: 1px solid {list_border};
                border-radius: 8px;
                color: {fg_dlg};
                font-size: 12px;
            }}
            QListWidget::item {{
                padding: 10px 8px;
                border-bottom: 1px solid {list_item_border};
                border-radius: 4px;
                color: {fg_dlg};
            }}
            QListWidget::item:hover {{
                background-color: {list_item_hover};
            }}
            QListWidget::item:selected {{
                background-color: #0284c7;
                color: #ffffff;
                font-weight: bold;
            }}
        """)
        left_layout.addWidget(self.list_widget)
        splitter.addWidget(left_box)

        # Colonne de droite : Détails de la leçon & Évaluation
        right_box = QWidget()
        right_layout = QVBoxLayout(right_box)
        right_layout.setContentsMargins(8, 0, 0, 0)
        right_layout.setSpacing(10)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background-color: transparent;")

        scroll_content = QWidget()
        self.content_layout = QVBoxLayout(scroll_content)
        self.content_layout.setContentsMargins(4, 4, 12, 4)
        self.content_layout.setSpacing(12)

        # En-tête leçon
        self.lbl_chapter = QLabel("Chapitre")
        self.lbl_chapter.setStyleSheet("font-size: 11px; font-weight: 700; color: #0284c7; text-transform: uppercase; background: transparent;")
        self.content_layout.addWidget(self.lbl_chapter)

        self.lbl_title = QLabel("Titre du TP")
        self.lbl_title.setStyleSheet(f"font-size: 18px; font-weight: 800; color: {sec_title_fg}; background: transparent;")
        self.content_layout.addWidget(self.lbl_title)

        self.lbl_summary = QLabel("Résumé")
        self.lbl_summary.setStyleSheet("font-size: 12px; color: #64748b; font-style: italic; background: transparent;")
        self.lbl_summary.setWordWrap(True)
        self.content_layout.addWidget(self.lbl_summary)

        # Badges composants requis
        self.comp_badges_layout = QHBoxLayout()
        self.comp_badges_layout.setSpacing(6)
        comp_title = QLabel("Composants requis :")
        comp_title.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {sec_title_fg}; background: transparent;")
        self.comp_badges_layout.addWidget(comp_title)
        self.comp_badges_container = QWidget()
        self.comp_badges_container.setLayout(self.comp_badges_layout)
        self.content_layout.addWidget(self.comp_badges_container)

        # Section Théorie du TP
        lbl_sec_theory = QLabel("📖 Rappel Pédagogique & Notions Clés")
        lbl_sec_theory.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {sec_title_fg}; margin-top: 6px; background: transparent;")
        self.content_layout.addWidget(lbl_sec_theory)

        self.tp_theory_browser = QTextBrowser()
        self.tp_theory_browser.setOpenExternalLinks(True)
        self.tp_theory_browser.setStyleSheet(f"""
            QTextBrowser {{
                background-color: {list_bg};
                border: 1px solid {list_border};
                border-radius: 8px;
                padding: 10px;
                color: {fg_dlg};
                font-size: 12px;
            }}
        """)
        self.tp_theory_browser.setMinimumHeight(140)
        self.content_layout.addWidget(self.tp_theory_browser)

        # Section Défi / Consignes
        lbl_sec_challenge = QLabel("🎯 Consignes Pratiques du TP")
        challenge_title_fg = "#b45309" if self.is_light else "#f59e0b"
        lbl_sec_challenge.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {challenge_title_fg}; margin-top: 6px; background: transparent;")
        self.content_layout.addWidget(lbl_sec_challenge)

        self.challenge_browser = QTextBrowser()
        self.challenge_browser.setStyleSheet(f"""
            QTextBrowser {{
                background-color: {challenge_bg};
                border: 1px solid {challenge_border};
                border-left: 4px solid #f59e0b;
                border-radius: 8px;
                padding: 10px;
                color: {challenge_fg};
                font-size: 12px;
            }}
        """)
        self.challenge_browser.setMinimumHeight(100)
        self.content_layout.addWidget(self.challenge_browser)

        # Section Rapport d'évaluation
        self.eval_frame = QFrame()
        self.eval_frame.setObjectName("EvalFrame")
        self.eval_frame.setStyleSheet(f"""
            QFrame#EvalFrame {{
                background-color: {eval_bg};
                border: 1px solid {eval_border};
                border-radius: 8px;
                padding: 12px;
            }}
        """)
        self.eval_layout = QVBoxLayout(self.eval_frame)
        self.eval_layout.setContentsMargins(12, 12, 12, 12)
        self.eval_layout.setSpacing(8)

        self.lbl_eval_header = QLabel("📊 Résultat de l'Évaluation")
        self.lbl_eval_header.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {eval_header}; background: transparent;")
        self.eval_layout.addWidget(self.lbl_eval_header)

        self.progress_score = QProgressBar()
        self.progress_score.setRange(0, 100)
        self.progress_score.setValue(0)
        self.progress_score.setTextVisible(True)
        prog_bg = "#e2e8f0" if self.is_light else "#1e293b"
        prog_fg = "#0f172a" if self.is_light else "white"
        self.progress_score.setStyleSheet(f"""
            QProgressBar {{
                background-color: {prog_bg};
                border-radius: 6px;
                text-align: center;
                height: 22px;
                color: {prog_fg};
                font-weight: bold;
            }}
            QProgressBar::chunk {{
                background-color: #0284c7;
                border-radius: 6px;
            }}
        """)
        self.eval_layout.addWidget(self.progress_score)

        self.lbl_eval_feedback = QLabel("Cliquez sur « ✅ Évaluer mon travail » pour tester votre code et votre montage actuel.")
        feedback_fg = "#475569" if self.is_light else "#94a3b8"
        self.lbl_eval_feedback.setStyleSheet(f"font-size: 12px; color: {feedback_fg}; background: transparent;")
        self.lbl_eval_feedback.setWordWrap(True)
        self.eval_layout.addWidget(self.lbl_eval_feedback)

        self.eval_details_browser = QTextBrowser()
        code_preview_bg = "#ffffff" if self.is_light else "#030712"
        code_preview_border = "#cbd5e1" if self.is_light else "#1f2937"
        self.eval_details_browser.setStyleSheet(f"""
            QTextBrowser {{
                background-color: {code_preview_bg};
                border: 1px solid {code_preview_border};
                border-radius: 6px;
                padding: 8px;
                font-size: 12px;
            }}
        """)
        self.eval_details_browser.setMinimumHeight(100)
        self.eval_details_browser.setVisible(False)
        self.eval_layout.addWidget(self.eval_details_browser)

        self.content_layout.addWidget(self.eval_frame)
        scroll.setWidget(scroll_content)
        right_layout.addWidget(scroll, 1)

        # Barre d'actions des TPs
        btn_bar = QHBoxLayout()
        btn_bar.setSpacing(10)

        self.btn_load_starter = QPushButton("🚀 Charger le circuit de départ")
        self.btn_load_starter.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                font-weight: 700;
                padding: 9px 16px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #3b82f6;
            }
        """)
        self.btn_load_starter.clicked.connect(self._load_current_tp)
        btn_bar.addWidget(self.btn_load_starter)

        self.btn_evaluate = QPushButton("✅ Évaluer mon travail")
        self.btn_evaluate.setStyleSheet("""
            QPushButton {
                background-color: #059669;
                color: white;
                font-weight: 700;
                padding: 9px 18px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #10b981;
            }
        """)
        self.btn_evaluate.clicked.connect(self._run_evaluation)
        btn_bar.addWidget(self.btn_evaluate)

        self.btn_export = QPushButton("📄 Exporter le compte-rendu")
        self.btn_export.setStyleSheet("""
            QPushButton {
                background-color: #0284c7;
                color: white;
                font-weight: 700;
                padding: 9px 16px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #0369a1;
            }
        """)
        self.btn_export.clicked.connect(self._export_report)
        btn_bar.addWidget(self.btn_export)

        btn_bar.addStretch()

        btn_close_bg = "#e2e8f0" if self.is_light else "#334155"
        btn_close_fg = "#0f172a" if self.is_light else "#f1f5f9"
        btn_close_hover = "#cbd5e1" if self.is_light else "#475569"
        btn_close = QPushButton("Fermer")
        btn_close.setStyleSheet(f"""
            QPushButton {{
                background-color: {btn_close_bg};
                color: {btn_close_fg};
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {btn_close_hover};
            }}
        """)
        btn_close.clicked.connect(self.accept)
        btn_bar.addWidget(btn_close)

        right_layout.addLayout(btn_bar)
        splitter.addWidget(right_box)
        splitter.setSizes([260, 640])

        layout.addWidget(splitter)

        self.list_widget.currentRowChanged.connect(self._select_lesson)
        self._populate_lesson_list()

    def _select_lesson(self, row: int):
        if row < 0 or row >= len(self.lessons):
            return

        lesson = self.lessons[row]
        self.lbl_chapter.setText(lesson.chapter_title)
        self.lbl_title.setText(lesson.title)
        self.lbl_summary.setText(lesson.summary)

        self.tp_theory_browser.setMarkdown(lesson.theory)
        self.challenge_browser.setMarkdown(lesson.challenge)

        while self.comp_badges_layout.count() > 1:
            item = self.comp_badges_layout.takeAt(1)
            if item.widget():
                item.widget().deleteLater()

        badge_bg = "#e0f2fe" if self.is_light else "#1e293b"
        badge_fg = "#0369a1" if self.is_light else "#38bdf8"
        badge_border = "#bae6fd" if self.is_light else "#334155"
        for c in lesson.required_components:
            badge = QLabel(c.upper())
            badge.setStyleSheet(f"""
                background-color: {badge_bg};
                color: {badge_fg};
                font-size: 11px;
                font-weight: bold;
                padding: 3px 8px;
                border: 1px solid {badge_border};
                border-radius: 4px;
            """)
            self.comp_badges_layout.addWidget(badge)
        self.comp_badges_layout.addStretch()

        self.progress_score.setValue(0)
        self.lbl_eval_feedback.setText("Cliquez sur « ✅ Évaluer mon travail » pour tester votre code et votre montage actuel.")
        feedback_init_fg = "#475569" if self.is_light else "#94a3b8"
        self.lbl_eval_feedback.setStyleSheet(f"font-size: 12px; color: {feedback_init_fg}; background: transparent;")
        self.eval_details_browser.setVisible(False)

    def _load_current_tp(self):
        row = self.list_widget.currentRow()
        if 0 <= row < len(self.lessons):
            lesson = self.lessons[row]
            if lesson.starter_project:
                self.lesson_loaded.emit(lesson.starter_project)
                self.accept()

    def _run_evaluation(self):
        row = self.list_widget.currentRow()
        if row < 0 or row >= len(self.lessons):
            return

        lesson = self.lessons[row]
        result: EvaluationResult = self.evaluator.evaluate(lesson, self.current_project)

        prog_bg = "#e2e8f0" if self.is_light else "#1e293b"
        prog_fg = "#0f172a" if self.is_light else "white"

        self.progress_score.setValue(result.percentage)
        if result.passed:
            self.progress_score.setStyleSheet(f"""
                QProgressBar {{
                    background-color: {prog_bg};
                    border-radius: 6px;
                    text-align: center;
                    height: 22px;
                    color: {prog_fg};
                    font-weight: bold;
                }}
                QProgressBar::chunk {{
                    background-color: #10b981;
                    border-radius: 6px;
                }}
            """)
            feedback_pass_fg = "#059669" if self.is_light else "#34d399"
            self.lbl_eval_feedback.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {feedback_pass_fg}; background: transparent;")
        else:
            self.progress_score.setStyleSheet(f"""
                QProgressBar {{
                    background-color: {prog_bg};
                    border-radius: 6px;
                    text-align: center;
                    height: 22px;
                    color: {prog_fg};
                    font-weight: bold;
                }}
                QProgressBar::chunk {{
                    background-color: #f59e0b;
                    border-radius: 6px;
                }}
            """)
            feedback_fail_fg = "#b45309" if self.is_light else "#f59e0b"
            self.lbl_eval_feedback.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {feedback_fail_fg}; background: transparent;")

        self.lbl_eval_feedback.setText(f"{result.general_feedback} (Score : {result.score}/{result.max_score} pts)")

        crit_detail_col = "#334155" if self.is_light else "#cbd5e1"
        html = "<ul style='margin-left: 0; padding-left: 15px;'>"
        for crit in result.criteria:
            icon = "✅" if crit.passed else "❌"
            color = ("#059669" if self.is_light else "#34d399") if crit.passed else ("#dc2626" if self.is_light else "#f87171")
            html += (
                f"<li style='margin-bottom: 6px;'>"
                f"<b>{icon} <span style='color: {color};'>{crit.title}</span> ({crit.points}/{crit.max_points} pts)</b><br/>"
                f"<span style='color: {crit_detail_col};'>{crit.feedback}</span>"
                f"</li>"
            )
        html += "</ul>"
        self.eval_details_browser.setHtml(html)
        self.eval_details_browser.setVisible(True)
        self.last_eval_result = result
        self._populate_lesson_list()

    def _export_report(self):
        row = self.list_widget.currentRow()
        if row < 0 or row >= len(self.lessons):
            return

        lesson = self.lessons[row]
        if self.last_eval_result is None or self.last_eval_result.lesson_id != lesson.id:
            self._run_evaluation()

        if self.last_eval_result is None:
            return

        default_filename = f"Compte_Rendu_{lesson.id}.html"
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Enregistrer le compte-rendu du TP",
            default_filename,
            "Fichiers HTML (*.html);;Tous les fichiers (*)"
        )
        if not filepath:
            return

        try:
            generator = LabReportGenerator()
            generator.save_report(
                filepath=filepath,
                lesson=lesson,
                project=self.current_project,
                eval_result=self.last_eval_result,
                student_name="Apprenant ESP32 MicroPython Lab"
            )
            QMessageBox.information(
                self,
                "Rapport Généré",
                f"Le compte-rendu du {lesson.title} a été enregistré avec succès !\n\nFichier : {filepath}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erreur d'exportation",
                f"Impossible d'enregistrer le rapport : {e}"
            )

    def _populate_lesson_list(self):
        try:
            completed_ids = set(get_progress_db().get_completed_lessons())
        except Exception:
            completed_ids = set()

        if self.list_widget.count() == len(self.lessons):
            for i, lesson in enumerate(self.lessons):
                status_icon = "✅ " if lesson.id in completed_ids else "⭕ "
                item = self.list_widget.item(i)
                if item:
                    item.setText(f"{status_icon}Ch.{lesson.chapter_num} : {lesson.title}")
                    if lesson.id in completed_ids:
                        item.setForeground(Qt.green)
        else:
            self.list_widget.blockSignals(True)
            self.list_widget.clear()
            for lesson in self.lessons:
                status_icon = "✅ " if lesson.id in completed_ids else "⭕ "
                item = QListWidgetItem(f"{status_icon}Ch.{lesson.chapter_num} : {lesson.title}")
                item.setToolTip(lesson.summary)
                if lesson.id in completed_ids:
                    item.setForeground(Qt.green)
                self.list_widget.addItem(item)
            self.list_widget.blockSignals(False)
            self.list_widget.setCurrentRow(0)
