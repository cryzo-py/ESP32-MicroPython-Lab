"""
Générateur de Comptes-Rendus de Travaux Pratiques (TP Report Generator)
Produit un document HTML5 moderne, complet et autonome, prêt pour l'impression ou l'export PDF.
"""

import base64
import html
from datetime import datetime
from pathlib import Path
from typing import Any

from collections import Counter
from .courses import Lesson
from .evaluator import EvaluationResult
from .models.project import ProjectModel
from .bom_exporter import classify_connection_wire


class LabReportGenerator:
    """Générateur de rapports pédagogiques professionnels."""

    def generate_html(
        self,
        lesson: Lesson,
        project: ProjectModel,
        eval_result: EvaluationResult,
        student_name: str = "Étudiant",
        image_bytes: bytes | None = None,
    ) -> str:
        date_str = datetime.now().strftime("%d/%m/%Y à %H:%M")
        img_tag = ""
        if image_bytes:
            b64_data = base64.b64encode(image_bytes).decode("ascii")
            img_tag = f"""
            <div class="circuit-snapshot">
                <h3>Montage Réalisé sur la Platine d'Expérimentation</h3>
                <img src="data:image/png;base64,{b64_data}" alt="Montage Circuit" />
            </div>
            """

        # Table des composants (BOM)
        bom_rows = ""
        for comp in project.components:
            if comp.type == "breadboard":
                continue
            props_desc = ", ".join(f"{k}: {v}" for k, v in comp.properties.items()) if comp.properties else "-"
            bom_rows += f"""
            <tr>
                <td><code>{html.escape(comp.id)}</code></td>
                <td><b>{html.escape(comp.type.upper())}</b></td>
                <td>{html.escape(comp.name or comp.type)}</td>
                <td>{html.escape(props_desc)}</td>
            </tr>
            """

        # Câbles Dupont ventilés par type (M-M, M-F, F-F)
        wire_counts = Counter(classify_connection_wire(c) for c in project.connections)
        wire_names = {
            "MM": ("Câble Dupont Mâle-Mâle (M-M)", "Cavaliers de platine d'expérimentation"),
            "MF": ("Câble Dupont Mâle-Femelle (M-F)", "Liaisons Platine <-> Carte ESP32 / Modules"),
            "FF": ("Câble Dupont Femelle-Femelle (F-F)", "Liaisons directes Carte ESP32 <-> Modules"),
        }
        for wtype in ("MM", "MF", "FF"):
            qty = wire_counts.get(wtype, 0)
            if qty > 0:
                name, desc = wire_names[wtype]
                bom_rows += f"""
                <tr>
                    <td><code>{wtype} (x{qty})</code></td>
                    <td><b>CÂBLE DUPONT</b></td>
                    <td>{name}</td>
                    <td>{qty} fil(s) — {desc}</td>
                </tr>
                """

        # Critères d'évaluation
        criteria_rows = ""
        for crit in eval_result.criteria:
            icon = "✅" if crit.passed else "❌"
            status_color = "#10b981" if crit.passed else "#ef4444"
            criteria_rows += f"""
            <tr>
                <td>{icon} <b>{crit.title}</b></td>
                <td style="text-align: center; color: {status_color}; font-weight: bold;">{crit.points} / {crit.max_points} pts</td>
                <td>{html.escape(crit.feedback)}</td>
            </tr>
            """

        code = project.get_main_code()
        # Échappement HTML basique
        code_html = code.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        html_output = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Compte-Rendu : {lesson.title}</title>
    <style>
        body {{
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
            margin: 0;
            padding: 30px;
            background-color: #f8fafc;
            color: #0f172a;
            line-height: 1.5;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: #ffffff;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
        }}
        .header {{
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 20px;
            margin-bottom: 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .logo-title h1 {{
            margin: 0;
            font-size: 22px;
            color: #0284c7;
        }}
        .logo-title h2 {{
            margin: 5px 0 0 0;
            font-size: 16px;
            color: #475569;
            font-weight: 500;
        }}
        .meta-box {{
            text-align: right;
            font-size: 13px;
            color: #64748b;
        }}
        .score-card {{
            background: #f0fdf4;
            border: 1px solid #bbf7d0;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .score-val {{
            font-size: 32px;
            font-weight: 800;
            color: #16a34a;
        }}
        .section-title {{
            font-size: 16px;
            font-weight: 700;
            color: #0f172a;
            margin-top: 30px;
            margin-bottom: 12px;
            border-left: 4px solid #0284c7;
            padding-left: 10px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
            font-size: 13px;
        }}
        th, td {{
            padding: 10px 12px;
            border: 1px solid #e2e8f0;
            text-align: left;
        }}
        th {{
            background: #f1f5f9;
            font-weight: 600;
            color: #334155;
        }}
        pre {{
            background: #0f172a;
            color: #f8fafc;
            padding: 16px;
            border-radius: 6px;
            overflow-x: auto;
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 12px;
            line-height: 1.4;
        }}
        .circuit-snapshot img {{
            max-width: 100%;
            border-radius: 6px;
            border: 1px solid #cbd5e1;
            margin-top: 10px;
        }}
        .footer {{
            margin-top: 40px;
            border-top: 1px solid #e2e8f0;
            padding-top: 15px;
            text-align: center;
            font-size: 12px;
            color: #94a3b8;
        }}
        @media print {{
            body {{ background: white; padding: 0; }}
            .container {{ box-shadow: none; padding: 0; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo-title">
                <h1>ESP32 MicroPython Lab</h1>
                <h2>Compte-Rendu : {lesson.title}</h2>
            </div>
            <div class="meta-box">
                <div><b>Apprenant :</b> {student_name}</div>
                <div><b>Date :</b> {date_str}</div>
                <div><b>Chapitre :</b> {lesson.chapter_title}</div>
            </div>
        </div>

        <div class="score-card">
            <div>
                <h3 style="margin: 0; color: #15803d;">Résultat de l'Évaluation Automatisée</h3>
                <p style="margin: 4px 0 0 0; color: #166534; font-size: 14px;">{html.escape(eval_result.general_feedback)}</p>
            </div>
            <div class="score-val">{eval_result.score} / {eval_result.max_score} pts</div>
        </div>

        <div class="section-title">1. Grille d'Évaluation Détaillée</div>
        <table>
            <thead>
                <tr>
                    <th>Critère</th>
                    <th style="width: 120px; text-align: center;">Points</th>
                    <th>Observations & Diagnostic</th>
                </tr>
            </thead>
            <tbody>
                {criteria_rows}
            </tbody>
        </table>

        {img_tag}

        <div class="section-title">2. Nomenclature du Matériel Utilisé (Bill of Materials)</div>
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Composant</th>
                    <th>Désignation</th>
                    <th>Paramètres physiques</th>
                </tr>
            </thead>
            <tbody>
                {bom_rows}
            </tbody>
        </table>

        <div class="section-title">3. Code Source MicroPython (main.py)</div>
        <pre><code>{code_html}</code></pre>

        <div class="footer">
            Rapport généré automatiquement par la plateforme d'apprentissage ESP32 MicroPython Lab
        </div>
    </div>
</body>
</html>
"""
        return html_output

    def save_report(
        self,
        filepath: Path | str,
        lesson: Lesson,
        project: ProjectModel,
        eval_result: EvaluationResult,
        student_name: str = "Étudiant",
        image_bytes: bytes | None = None,
    ):
        content = self.generate_html(lesson, project, eval_result, student_name, image_bytes)
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)