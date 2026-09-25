"""
Panneau de Contrôle et Diagnostic des Règles Électriques (ERCPanelWidget).
Affiche en direct l'état de conformité électrique du circuit avec alertes et recommandations pédagogiques.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QIcon
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ...app.event_bus import get_event_bus
from ...core.erc_checker import ERCSeverity, ERCViolation


class ERCPanelWidget(QFrame):
    """Panneau listant les règles électriques et anomalies en temps réel."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background-color: #0b1329;
                border-top: 1px solid #1e293b;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(8)

        # En-tête du panneau
        header = QHBoxLayout()
        header.setSpacing(10)

        self.title_label = QLabel("🛡️ Diagnostic Électrique & Intégrité du Montage (ERC)")
        self.title_label.setStyleSheet("color: #38bdf8; font-weight: bold; font-size: 12px;")
        header.addWidget(self.title_label)

        self.summary_badge = QLabel("✅ Circuit Conforme (0 anomalie)")
        self.summary_badge.setStyleSheet("""
            background-color: #064e3b;
            color: #34d399;
            font-size: 11px;
            font-weight: 600;
            padding: 3px 8px;
            border-radius: 4px;
        """)
        header.addWidget(self.summary_badge)

        header.addStretch()

        self.btn_refresh = QPushButton("🔍 Re-vérifier")
        self.btn_refresh.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                color: #e2e8f0;
                border: 1px solid #334155;
                padding: 3px 10px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #334155; }
        """)
        header.addWidget(self.btn_refresh)
        layout.addLayout(header)

        # Zone déroulante contenant les cartes d'anomalies
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.container = QWidget()
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        self.container_layout.setSpacing(6)
        self.scroll.setWidget(self.container)

        layout.addWidget(self.scroll)

        # Écoute de l'EventBus
        self.event_bus = get_event_bus()
        self.event_bus.erc_violations_updated.connect(self.update_violations)

        self._render_empty_state()

    def _render_empty_state(self):
        """Affiche un état propre quand aucune anomalie n'est détectée."""
        while self.container_layout.count():
            item = self.container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        lbl = QLabel("✨ Aucune anomalie électrique détectée. Les liaisons d'alimentation et les protections sont correctes.")
        lbl.setStyleSheet("color: #94a3b8; font-size: 11px; padding: 12px; font-style: italic;")
        lbl.setAlignment(Qt.AlignCenter)
        self.container_layout.addWidget(lbl)
        self.container_layout.addStretch()

        self.summary_badge.setText("✅ Circuit Conforme (0 anomalie)")
        self.summary_badge.setStyleSheet("""
            background-color: #064e3b;
            color: #34d399;
            font-size: 11px;
            font-weight: 600;
            padding: 3px 8px;
            border-radius: 4px;
        """)

    def update_violations(self, violations: list):
        """Met à jour l'affichage avec la liste des violations ERC."""
        while self.container_layout.count():
            item = self.container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not violations:
            self._render_empty_state()
            return

        has_error = any(v.severity == ERCSeverity.ERROR for v in violations)
        has_warning = any(v.severity == ERCSeverity.WARNING for v in violations)

        if has_error:
            self.summary_badge.setText(f"❌ {len(violations)} anomalie(s) détectée(s) !")
            self.summary_badge.setStyleSheet("""
                background-color: #7f1d1d;
                color: #fca5a5;
                font-size: 11px;
                font-weight: 600;
                padding: 3px 8px;
                border-radius: 4px;
            """)
        elif has_warning:
            self.summary_badge.setText(f"⚠️ {len(violations)} avertissement(s)")
            self.summary_badge.setStyleSheet("""
                background-color: #78350f;
                color: #fde047;
                font-size: 11px;
                font-weight: 600;
                padding: 3px 8px;
                border-radius: 4px;
            """)

        for v in violations:
            card = QFrame()
            is_err = (v.severity == ERCSeverity.ERROR)
            border_col = "#ef4444" if is_err else "#eab308"
            bg_col = "#1a0b0b" if is_err else "#1a150b"

            card.setStyleSheet(f"""
                QFrame {{
                    background-color: {bg_col};
                    border-left: 4px solid {border_col};
                    border-radius: 4px;
                    padding: 6px;
                }}
            """)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(6, 4, 6, 4)
            card_layout.setSpacing(3)

            # Titre
            icon = "❌" if is_err else "⚠️"
            title = QLabel(f"{icon} <b>{v.title}</b>")
            title.setStyleSheet(f"color: {border_col}; font-size: 11px;")
            card_layout.addWidget(title)

            # Description
            desc = QLabel(v.message)
            desc.setWordWrap(True)
            desc.setStyleSheet("color: #e2e8f0; font-size: 11px;")
            card_layout.addWidget(desc)

            # Recommandation
            if v.recommendation:
                rec = QLabel(f"💡 <i>Conseil : {v.recommendation}</i>")
                rec.setWordWrap(True)
                rec.setStyleSheet("color: #94a3b8; font-size: 10px;")
                card_layout.addWidget(rec)

            self.container_layout.addWidget(card)

        self.container_layout.addStretch()

    def set_theme(self, theme_name: str):
        is_light = (theme_name == "light")
        bg = "#ffffff" if is_light else "#0b1329"
        border = "#e2e8f0" if is_light else "#1e293b"
        self.setStyleSheet(f"QFrame {{ background-color: {bg}; border-top: 1px solid {border}; }}")
