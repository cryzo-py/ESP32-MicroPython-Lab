"""
Boîte de dialogue À propos (AboutDialog) — ESP32 MicroPython Lab
Présente le résumé de l'application, l'auteur Fares Bel Haj Ali, les contacts et les droits d'auteur.
"""

from pathlib import Path
from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QFont, QIcon, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("À propos — ESP32 MicroPython Lab")
        self.setFixedSize(540, 580)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        self._setup_ui()

    def _setup_ui(self):
        settings = QSettings("ESP32Lab", "ESP32MicroPythonLab")
        is_light = (settings.value("theme", "dark") == "light")

        bg_dlg = "#ffffff" if is_light else "#0f172a"
        fg_dlg = "#0f172a" if is_light else "#f8fafc"
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
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 20)
        layout.setSpacing(14)

        # 1. En-tête : Logo, Titre, Version
        header_layout = QHBoxLayout()
        header_layout.setSpacing(16)

        # Icône officielle
        icon_path = Path(__file__).resolve().parent.parent.parent / "resources" / "icons" / "app_icon.png"
        logo_lbl = QLabel()
        if icon_path.exists():
            pix = QPixmap(str(icon_path)).scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_lbl.setPixmap(pix)
            self.setWindowIcon(QIcon(str(icon_path)))
        else:
            logo_lbl.setText("⚡")
            logo_lbl.setStyleSheet("font-size: 44px; color: #38bdf8;")
        header_layout.addWidget(logo_lbl, 0, Qt.AlignTop)

        title_vbox = QVBoxLayout()
        title_vbox.setSpacing(4)

        app_title = QLabel("ESP32 MicroPython Lab")
        title_col = "#0f172a" if is_light else "#ffffff"
        app_title.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {title_col}; letter-spacing: -0.5px; background: transparent;")
        title_vbox.addWidget(app_title)

        subtitle = QLabel("Laboratoire virtuel d'électronique & programmation ESP32")
        sub_col = "#0284c7" if is_light else "#38bdf8"
        subtitle.setStyleSheet(f"font-size: 12px; color: {sub_col}; font-weight: 600; background: transparent;")
        title_vbox.addWidget(subtitle)

        version_badge = QLabel("Version 3.0 • Édition Simulateur Réaliste MB-102")
        ver_col = "#64748b" if is_light else "#94a3b8"
        version_badge.setStyleSheet(f"font-size: 11px; color: {ver_col}; font-style: italic; background: transparent;")
        title_vbox.addWidget(version_badge)

        header_layout.addLayout(title_vbox, 1)
        layout.addLayout(header_layout)

        # Séparateur subtil
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.HLine)
        sep_col = "#cbd5e1" if is_light else "#1e293b"
        sep1.setStyleSheet(f"color: {sep_col}; background-color: {sep_col}; max-height: 1px;")
        layout.addWidget(sep1)

        # 2. Résumé de l'application
        card_bg = "#f8fafc" if is_light else "#1e293b"
        card_border = "#cbd5e1" if is_light else "#334155"
        summary_frame = QFrame()
        summary_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {card_bg};
                border: 1px solid {card_border};
                border-radius: 8px;
                padding: 10px;
            }}
        """)
        summary_layout = QVBoxLayout(summary_frame)
        summary_layout.setContentsMargins(12, 10, 12, 10)
        summary_layout.setSpacing(6)

        summary_title = QLabel("📋 Résumé de l'application")
        hdr_col = "#0f172a" if is_light else "#e2e8f0"
        summary_title.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {hdr_col}; border: none; background: transparent;")
        summary_layout.addWidget(summary_title)

        summary_text = QLabel(
            "Environnement complet d'apprentissage et de prototypage dédié à l'électronique "
            "et au développement MicroPython sur microcontrôleur ESP32 :<br>"
            "• <b>Platine MB-102 physique</b> avec modélisation électrique et détection de contacts réels.<br>"
            "• <b>Câblage interactif Dupont</b> : déplacement libre des broches et couleurs personnalisables.<br>"
            "• <b>Bibliothèque de composants</b> : LEDs, résistances, capteurs (DHT22, HC-SR04), écrans (OLED, LCD), relais, NeoPixel.<br>"
            "• <b>Moteur de simulation temps réel</b> avec interpréteur MicroPython et console REPL.<br>"
            "• <b>Cursus pédagogique</b> complet composé de 10 TPs avec auto-évaluation automatique."
        )
        summary_text.setWordWrap(True)
        summary_text.setTextFormat(Qt.RichText)
        text_col = "#334155" if is_light else "#cbd5e1"
        summary_text.setStyleSheet(f"font-size: 11px; color: {text_col}; line-height: 140%; border: none; background: transparent;")
        summary_layout.addWidget(summary_text)
        layout.addWidget(summary_frame)

        # 3. Informations Auteur & Contact
        author_frame = QFrame()
        author_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {card_bg};
                border: 1px solid {card_border};
                border-radius: 8px;
                padding: 10px;
            }}
        """)
        author_layout = QVBoxLayout(author_frame)
        author_layout.setContentsMargins(12, 10, 12, 10)
        author_layout.setSpacing(6)

        author_title = QLabel("👨‍💻 Conception & Développement")
        author_title.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {hdr_col}; border: none; background: transparent;")
        author_layout.addWidget(author_title)

        dev_lbl = QLabel("Développé par : <b>Fares Bel Haj Ali</b>")
        dev_lbl.setTextFormat(Qt.RichText)
        dev_col = "#0f172a" if is_light else "#f8fafc"
        dev_lbl.setStyleSheet(f"font-size: 12px; color: {dev_col}; border: none; background: transparent;")
        author_layout.addWidget(dev_lbl)

        accent_col = "#0284c7" if is_light else "#38bdf8"
        contacts_lbl = QLabel(
            f"📞 <b>Tél :</b> <span style='color: {accent_col};'>+216 22 392 646</span> &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"✉️ <b>Email :</b> <a href='mailto:belhadj.fares@gmail.com' style='color: {accent_col}; text-decoration: none;'>belhadj.fares@gmail.com</a><br>"
            f"🌐 <b>GitHub :</b> <a href='https://github.com/cryzo-py' style='color: {accent_col}; text-decoration: none;'>https://github.com/cryzo-py</a>"
        )
        contacts_lbl.setTextFormat(Qt.RichText)
        contacts_lbl.setOpenExternalLinks(True)
        contacts_lbl.setStyleSheet(f"font-size: 11.5px; color: {text_col}; border: none; background: transparent;")
        author_layout.addWidget(contacts_lbl)

        copyright_lbl = QLabel("© Copyright 2024–2026 <b>Fares Bel Haj Ali</b>. Tous droits réservés.")
        copyright_lbl.setTextFormat(Qt.RichText)
        copy_col = "#64748b" if is_light else "#94a3b8"
        copyright_lbl.setStyleSheet(f"font-size: 10.5px; color: {copy_col}; border: none; background: transparent; padding-top: 2px;")
        author_layout.addWidget(copyright_lbl)

        layout.addWidget(author_frame)

        layout.addStretch()

        # 4. Bouton Fermer
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_close = QPushButton("Fermer")
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.setFixedSize(110, 32)
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                font-weight: 600;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
            QPushButton:pressed {
                background-color: #1e40af;
            }
        """)
        btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)
