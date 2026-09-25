"""
Bibliothèque de composants (ComponentPaletteWidget) avec miniatures photoréalistes et Drag & Drop natif.
"""

from PySide6.QtCore import QByteArray, QDataStream, QIODevice, QMimeData, QPoint, QPointF, QRectF, Qt, Signal
from PySide6.QtGui import (
    QBrush,
    QColor,
    QDrag,
    QFont,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QRadialGradient,
)
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


def render_component_thumbnail(comp_type: str, size: int = 44) -> QPixmap:
    """Génère une miniature photoréaliste vectorielle d'un composant physique,
    avec la forme, l'orientation et les broches identiques au rendu sur la platine.
    """
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)

    painter = QPainter(pix)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setRenderHint(QPainter.SmoothPixmapTransform)

    cx = size / 2.0
    cy = size / 2.0
    s = size / 44.0  # facteur d'échelle

    if comp_type == "led":
        # Rendu identique à LEDGraphicsItem sur la platine :
        # Dôme époxy rouge avec reflet spéculaire, collerette, électrodes internes et 2 pattes verticales descendantes

        # 1. Pattes métalliques descendantes argentées
        painter.setPen(QPen(QColor("#94a3b8"), 1.8 * s, Qt.SolidLine, Qt.RoundCap))
        # Anode (longue à gauche)
        painter.drawLine(QPointF(cx - 3.5 * s, cy + 6 * s), QPointF(cx - 3.5 * s, cy + 18 * s))
        # Cathode (légèrement plus courte à droite)
        painter.drawLine(QPointF(cx + 3.5 * s, cy + 6 * s), QPointF(cx + 3.5 * s, cy + 15 * s))

        # Petites ombres/embouts aux extrémités des pattes
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor("#334155")))
        painter.drawRect(QRectF(cx - 4.5 * s, cy + 16 * s, 2 * s, 2 * s))
        painter.drawRect(QRectF(cx + 2.5 * s, cy + 13 * s, 2 * s, 2 * s))

        # 2. Électrodes internes visibles par transparence
        painter.setPen(QPen(QColor(226, 232, 240, 160), 1.2 * s))
        painter.drawLine(QPointF(cx - 2.5 * s, cy + 5 * s), QPointF(cx - 2.5 * s, cy - 2 * s))
        painter.drawLine(QPointF(cx + 2.5 * s, cy + 5 * s), QPointF(cx + 2.5 * s, cy - 1 * s))
        # Enclume (triangle cathode)
        painter.setBrush(QBrush(QColor(241, 245, 249, 180)))
        path_anvil = QPainterPath()
        path_anvil.moveTo(cx + 2.5 * s, cy - 1 * s)
        path_anvil.lineTo(cx + 0.5 * s, cy - 4 * s)
        path_anvil.lineTo(cx + 4.0 * s, cy - 4 * s)
        path_anvil.closeSubpath()
        painter.drawPath(path_anvil)

        # 3. Dôme époxy rouge
        grad = QRadialGradient(cx - 2.5 * s, cy - 4 * s, 11 * s)
        grad.setColorAt(0.0, QColor(254, 202, 202, 230))
        grad.setColorAt(0.35, QColor(239, 68, 68, 220))
        grad.setColorAt(0.8, QColor(185, 28, 28, 230))
        grad.setColorAt(1.0, QColor(127, 29, 29, 240))

        painter.setPen(QPen(QColor(153, 27, 27, 200), 1.0 * s))
        painter.setBrush(QBrush(grad))

        path_bulb = QPainterPath()
        path_bulb.moveTo(cx - 7.5 * s, cy + 5 * s)
        path_bulb.lineTo(cx - 7.5 * s, cy - 2 * s)
        path_bulb.arcTo(QRectF(cx - 7.5 * s, cy - 15 * s, 15 * s, 16 * s), 180, -180)
        path_bulb.lineTo(cx + 7.5 * s, cy + 5 * s)
        path_bulb.closeSubpath()
        painter.drawPath(path_bulb)

        # Collerette à la base avec méplat à droite
        painter.drawRoundedRect(QRectF(cx - 8.5 * s, cy + 4 * s, 16.5 * s, 3.5 * s), 1.2 * s, 1.2 * s)

        # 4. Reflet spéculaire brillant (lumière de laboratoire)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(255, 255, 255, 210)))
        path_spec = QPainterPath()
        path_spec.addEllipse(QPointF(cx - 3.5 * s, cy - 7 * s), 2.2 * s, 3.8 * s)
        painter.drawPath(path_spec)

    elif comp_type == "resistor":
        # Rendu identique à ResistorGraphicsItem sur la platine :
        # Résistance VERTICALE axiale 1/4W, corps céramique renflé (dumbbell), anneaux EIA (Rouge, Rouge, Marron, Or), pattes étamées

        # 1. Fils métalliques étamés (vers le haut et le bas)
        lead_grad = QLinearGradient(cx - 1.2 * s, cy, cx + 1.2 * s, cy)
        lead_grad.setColorAt(0.0, QColor("#64748b"))
        lead_grad.setColorAt(0.4, QColor("#f8fafc"))
        lead_grad.setColorAt(1.0, QColor("#475569"))

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(lead_grad))
        # Patte haute
        painter.drawRoundedRect(QRectF(cx - 1.2 * s, cy - 19 * s, 2.4 * s, 9 * s), 0.8 * s, 0.8 * s)
        # Patte basse
        painter.drawRoundedRect(QRectF(cx - 1.2 * s, cy + 10 * s, 2.4 * s, 9 * s), 0.8 * s, 0.8 * s)

        # 2. Corps céramique renflé vertical (Dumbbell body 1/4W)
        body_grad = QLinearGradient(cx - 6 * s, cy, cx + 6 * s, cy)
        body_grad.setColorAt(0.0, QColor("#d4c39e"))
        body_grad.setColorAt(0.3, QColor("#fef3c7"))
        body_grad.setColorAt(0.7, QColor("#e2d5ba"))
        body_grad.setColorAt(1.0, QColor("#a1885b"))

        painter.setPen(QPen(QColor("#786542"), 0.8 * s))
        painter.setBrush(QBrush(body_grad))

        # Tracé dumbbell (renflé aux extrémités, plus fin au centre)
        path_body = QPainterPath()
        path_body.moveTo(cx - 5.5 * s, cy - 11 * s)
        path_body.quadTo(cx - 3.8 * s, cy, cx - 5.5 * s, cy + 11 * s)
        path_body.lineTo(cx + 5.5 * s, cy + 11 * s)
        path_body.quadTo(cx + 3.8 * s, cy, cx + 5.5 * s, cy - 11 * s)
        path_body.closeSubpath()
        painter.drawPath(path_body)

        # Bourrelets arrondis aux extrémités
        painter.drawRoundedRect(QRectF(cx - 5.8 * s, cy - 12 * s, 11.6 * s, 3.5 * s), 1.5 * s, 1.5 * s)
        painter.drawRoundedRect(QRectF(cx - 5.8 * s, cy + 8.5 * s, 11.6 * s, 3.5 * s), 1.5 * s, 1.5 * s)

        # 3. Anneaux de couleur EIA horizontaux : Rouge (2), Rouge (2), Marron (x10), Or (5%)
        bands = [
            (QColor("#dc2626"), -6.5 * s), # Rouge
            (QColor("#dc2626"), -2.5 * s), # Rouge
            (QColor("#78350f"), 1.8 * s),  # Marron
            (QColor("#fbbf24"), 6.2 * s),  # Or
        ]
        painter.setPen(Qt.NoPen)
        for col, y_offset in bands:
            painter.setBrush(QBrush(col))
            bw = 9.0 * s if abs(y_offset) < 4 * s else 10.5 * s
            painter.drawRect(QRectF(cx - bw / 2.0, cy + y_offset, bw, 2.2 * s))

        # 4. Reflet spéculaire cylindrique vertical
        painter.setBrush(QBrush(QColor(255, 255, 255, 90)))
        painter.drawRoundedRect(QRectF(cx - 3.0 * s, cy - 10 * s, 1.8 * s, 20 * s), 0.8 * s, 0.8 * s)

    elif comp_type == "button":
        # 1. Broches métalliques coudées
        painter.setPen(QPen(QColor("#94a3b8"), 2.0 * s))
        painter.drawLine(QPointF(cx - 15 * s, cy - 6 * s), QPointF(cx - 10 * s, cy - 6 * s))
        painter.drawLine(QPointF(cx - 15 * s, cy + 6 * s), QPointF(cx - 10 * s, cy + 6 * s))
        painter.drawLine(QPointF(cx + 10 * s, cy - 6 * s), QPointF(cx + 15 * s, cy - 6 * s))
        painter.drawLine(QPointF(cx + 10 * s, cy + 6 * s), QPointF(cx + 15 * s, cy + 6 * s))

        # 2. Boîtier plastique noir mat
        painter.setPen(QPen(QColor("#0f172a"), 1.0 * s))
        painter.setBrush(QBrush(QColor("#1e293b")))
        painter.drawRoundedRect(QRectF(cx - 11 * s, cy - 11 * s, 22 * s, 22 * s), 2.5 * s, 2.5 * s)

        # 3. Plaque supérieure argentée nickelée
        silver_grad = QLinearGradient(cx - 8 * s, cy - 8 * s, cx + 8 * s, cy + 8 * s)
        silver_grad.setColorAt(0.0, QColor("#f1f5f9"))
        silver_grad.setColorAt(0.5, QColor("#94a3b8"))
        silver_grad.setColorAt(1.0, QColor("#cbd5e1"))
        painter.setBrush(QBrush(silver_grad))
        painter.drawRoundedRect(QRectF(cx - 8.5 * s, cy - 8.5 * s, 17 * s, 17 * s), 2 * s, 2 * s)

        # 4 rivets aux coins
        painter.setBrush(QBrush(QColor("#475569")))
        for rx, ry in [(-6.5, -6.5), (6.5, -6.5), (-6.5, 6.5), (6.5, 6.5)]:
            painter.drawEllipse(QPointF(cx + rx * s, cy + ry * s), 1.0 * s, 1.0 * s)

        # 4. Bouton poussoir central bleu
        btn_grad = QRadialGradient(cx, cy, 5 * s)
        btn_grad.setColorAt(0.0, QColor("#60a5fa"))
        btn_grad.setColorAt(0.8, QColor("#2563eb"))
        btn_grad.setColorAt(1.0, QColor("#1e40af"))
        painter.setPen(QPen(QColor("#1e3a8a"), 0.8 * s))
        painter.setBrush(QBrush(btn_grad))
        painter.drawEllipse(QPointF(cx, cy), 4.8 * s, 4.8 * s)

    elif comp_type == "potentiometer":
        # 1. 3 Broches descendantes
        painter.setPen(QPen(QColor("#cbd5e1"), 2.0 * s))
        painter.drawLine(QPointF(cx - 7 * s, cy + 10 * s), QPointF(cx - 7 * s, cy + 18 * s))
        painter.drawLine(QPointF(cx, cy + 10 * s), QPointF(cx, cy + 18 * s))
        painter.drawLine(QPointF(cx + 7 * s, cy + 10 * s), QPointF(cx + 7 * s, cy + 18 * s))

        # 2. Boîtier bleu cylindrique
        pot_grad = QRadialGradient(cx, cy - 2 * s, 13 * s)
        pot_grad.setColorAt(0.0, QColor("#38bdf8"))
        pot_grad.setColorAt(0.7, QColor("#0284c7"))
        pot_grad.setColorAt(1.0, QColor("#075985"))
        painter.setPen(QPen(QColor("#0369a1"), 1.2 * s))
        painter.setBrush(QBrush(pot_grad))
        painter.drawEllipse(QPointF(cx, cy - 2 * s), 12 * s, 12 * s)

        # 3. Axe laiton moleté avec flèche
        brass_grad = QLinearGradient(cx - 5 * s, cy - 7 * s, cx + 5 * s, cy + 3 * s)
        brass_grad.setColorAt(0.0, QColor("#fef08a"))
        brass_grad.setColorAt(0.5, QColor("#ca8a04"))
        brass_grad.setColorAt(1.0, QColor("#854d0e"))
        painter.setPen(QPen(QColor("#713f12"), 0.8 * s))
        painter.setBrush(QBrush(brass_grad))
        painter.drawEllipse(QPointF(cx, cy - 2 * s), 6 * s, 6 * s)

        # Ligne de repère blanche
        painter.setPen(QPen(QColor("#ffffff"), 1.8 * s, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(QPointF(cx, cy - 2 * s), QPointF(cx - 4 * s, cy - 6 * s))

    elif comp_type == "relay":
        # 1. Boîtier bleu Songle cubique
        blue_grad = QLinearGradient(cx - 15 * s, cy - 11 * s, cx + 15 * s, cy + 11 * s)
        blue_grad.setColorAt(0.0, QColor("#2563eb"))
        blue_grad.setColorAt(0.5, QColor("#1d4ed8"))
        blue_grad.setColorAt(1.0, QColor("#1e3a8a"))
        painter.setPen(QPen(QColor("#172554"), 1.0 * s))
        painter.setBrush(QBrush(blue_grad))
        painter.drawRoundedRect(QRectF(cx - 14 * s, cy - 11 * s, 28 * s, 22 * s), 2.5 * s, 2.5 * s)

        # Sérigraphie Songle
        painter.setFont(QFont("Consolas", int(5 * s), QFont.Bold))
        painter.setPen(QColor("#ffffff"))
        painter.drawText(QRectF(cx - 14 * s, cy - 9 * s, 28 * s, 8 * s), Qt.AlignCenter, "SONGLE")
        painter.setFont(QFont("Segoe UI", int(4 * s)))
        painter.setPen(QColor("#93c5fd"))
        painter.drawText(QRectF(cx - 14 * s, cy - 2 * s, 28 * s, 6 * s), Qt.AlignCenter, "5VDC 10A")

        # Bornier vert à gauche
        painter.setPen(QPen(QColor("#14532d"), 0.8 * s))
        painter.setBrush(QBrush(QColor("#15803d")))
        painter.drawRect(QRectF(cx - 18 * s, cy - 8 * s, 4 * s, 16 * s))
        # 3 vis métalliques
        painter.setBrush(QBrush(QColor("#cbd5e1")))
        for vy in [-5, 0, 5]:
            painter.drawEllipse(QPointF(cx - 16 * s, cy + vy * s), 1.2 * s, 1.2 * s)

    elif comp_type == "neopixel":
        # Anneau noir avec 8 puces 5050
        painter.setPen(QPen(QColor("#334155"), 1.0 * s))
        painter.setBrush(QBrush(QColor("#0f172a")))
        painter.drawEllipse(QPointF(cx, cy), 15 * s, 15 * s)
        painter.setBrush(QBrush(QColor("#1e293b")))
        painter.drawEllipse(QPointF(cx, cy), 7 * s, 7 * s)

        # 8 LEDs 5050 multicolores
        import math
        rainbow = [QColor("#ef4444"), QColor("#f97316"), QColor("#eab308"), QColor("#22c55e"),
                   QColor("#06b6d4"), QColor("#3b82f6"), QColor("#a855f7"), QColor("#ec4899")]
        for i, col in enumerate(rainbow):
            angle = i * (2 * math.pi / 8)
            lx = cx + 11 * s * math.cos(angle)
            ly = cy + 11 * s * math.sin(angle)
            painter.setPen(QPen(QColor("#f59e0b"), 0.6 * s))
            painter.setBrush(QBrush(col))
            painter.drawRect(QRectF(lx - 2 * s, ly - 2 * s, 4 * s, 4 * s))

    elif comp_type == "servo":
        # Boîtier bleu SG90
        painter.setPen(QPen(QColor("#0284c7"), 1.0 * s))
        painter.setBrush(QBrush(QColor(14, 165, 233, 200)))
        painter.drawRoundedRect(QRectF(cx - 13 * s, cy - 8 * s, 26 * s, 16 * s), 2 * s, 2 * s)

        # Palonnier blanc orienté
        painter.setPen(QPen(QColor("#cbd5e1"), 0.8 * s))
        painter.setBrush(QBrush(QColor("#ffffff")))
        path = QPainterPath()
        path.addEllipse(QPointF(cx - 4 * s, cy - 2 * s), 4 * s, 4 * s)
        path.addRoundedRect(QRectF(cx - 4 * s, cy - 14 * s, 5 * s, 14 * s), 2 * s, 2 * s)
        painter.drawPath(path)
        # Vis centrale
        painter.setBrush(QBrush(QColor("#64748b")))
        painter.drawEllipse(QPointF(cx - 1.5 * s, cy - 2 * s), 1.5 * s, 1.5 * s)

    elif comp_type == "buzzer":
        # Cylindre noir
        b_grad = QRadialGradient(cx - 3 * s, cy - 3 * s, 13 * s)
        b_grad.setColorAt(0.0, QColor("#475569"))
        b_grad.setColorAt(0.7, QColor("#1e293b"))
        b_grad.setColorAt(1.0, QColor("#0f172a"))
        painter.setPen(QPen(QColor("#020617"), 1.0 * s))
        painter.setBrush(QBrush(b_grad))
        painter.drawEllipse(QPointF(cx, cy), 13 * s, 13 * s)
        # Trou acoustique central
        painter.setBrush(QBrush(QColor("#020617")))
        painter.drawEllipse(QPointF(cx, cy), 3.5 * s, 3.5 * s)
        # Repère +
        painter.setFont(QFont("Arial", int(7 * s), QFont.Bold))
        painter.setPen(QColor("#ef4444"))
        painter.drawText(QRectF(cx - 11 * s, cy - 12 * s, 10 * s, 10 * s), Qt.AlignCenter, "+")

    elif comp_type == "dht22":
        # Coque blanche avec ouïes de ventilation
        painter.setPen(QPen(QColor("#94a3b8"), 1.0 * s))
        painter.setBrush(QBrush(QColor("#ffffff")))
        painter.drawRoundedRect(QRectF(cx - 12 * s, cy - 15 * s, 24 * s, 26 * s), 3 * s, 3 * s)
        # Grillage
        painter.setPen(QPen(QColor("#0284c7"), 1.2 * s))
        for gy in range(-8, 6, 3):
            painter.drawLine(QPointF(cx - 8 * s, cy + gy * s), QPointF(cx + 8 * s, cy + gy * s))
        # 4 pattes en bas
        painter.setPen(QPen(QColor("#94a3b8"), 1.6 * s))
        for px in [-6, -2, 2, 6]:
            painter.drawLine(QPointF(cx + px * s, cy + 11 * s), QPointF(cx + px * s, cy + 18 * s))

    elif comp_type in ("oled", "lcd16x2", "tft", "lcd"):
        # Écran graphique I2C
        painter.setPen(QPen(QColor("#1e293b"), 1.0 * s))
        painter.setBrush(QBrush(QColor("#1e40af" if "lcd" in comp_type else "#0f172a")))
        painter.drawRoundedRect(QRectF(cx - 16 * s, cy - 12 * s, 32 * s, 24 * s), 2 * s, 2 * s)
        # Dalle active
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor("#84cc16" if "lcd" in comp_type else "#0284c7")))
        painter.drawRect(QRectF(cx - 13 * s, cy - 9 * s, 26 * s, 18 * s))
        # Lignes de texte pixel
        painter.setPen(QPen(QColor("#022c22" if "lcd" in comp_type else "#ffffff"), 1.0 * s))
        painter.drawLine(QPointF(cx - 10 * s, cy - 3 * s), QPointF(cx + 8 * s, cy - 3 * s))
        painter.drawLine(QPointF(cx - 10 * s, cy + 2 * s), QPointF(cx + 4 * s, cy + 2 * s))

    elif comp_type == "hcsr04":
        # PCB bleu avec 2 capsules alu
        painter.setPen(QPen(QColor("#1e40af"), 1.0 * s))
        painter.setBrush(QBrush(QColor("#2563eb")))
        painter.drawRoundedRect(QRectF(cx - 18 * s, cy - 9 * s, 36 * s, 18 * s), 2 * s, 2 * s)
        # 2 transducteurs alu
        c_grad = QRadialGradient(cx - 8 * s, cy, 6 * s)
        c_grad.setColorAt(0.0, QColor("#f1f5f9"))
        c_grad.setColorAt(0.7, QColor("#94a3b8"))
        c_grad.setColorAt(1.0, QColor("#475569"))
        painter.setBrush(QBrush(c_grad))
        painter.drawEllipse(QPointF(cx - 8 * s, cy), 6 * s, 6 * s)
        painter.drawEllipse(QPointF(cx + 8 * s, cy), 6 * s, 6 * s)
        # Lettres T et R
        painter.setFont(QFont("Consolas", int(5 * s), QFont.Bold))
        painter.setPen(QColor("#0f172a"))
        painter.drawText(QRectF(cx - 11 * s, cy - 4 * s, 6 * s, 8 * s), Qt.AlignCenter, "T")
        painter.drawText(QRectF(cx + 5 * s, cy - 4 * s, 6 * s, 8 * s), Qt.AlignCenter, "R")

    elif comp_type == "breadboard":
        # Platine MB-102 réaliste : corps crème #fdfbf7, rainure centrale, lignes d'alimentation rouge et bleue, trous réalistes
        painter.setPen(QPen(QColor("#cbd5e1"), 1.0 * s))
        painter.setBrush(QBrush(QColor("#fdfbf7")))
        painter.drawRoundedRect(QRectF(cx - 19 * s, cy - 18 * s, 38 * s, 36 * s), 2.5 * s, 2.5 * s)

        # Rainure centrale DIP
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor("#e2e8f0")))
        painter.drawRoundedRect(QRectF(cx - 1.8 * s, cy - 15 * s, 3.6 * s, 30 * s), 1.0 * s, 1.0 * s)

        # Ligne d'alimentation gauche (Rouge +, Bleu -)
        painter.setPen(QPen(QColor("#dc2626"), 1.0 * s))
        painter.drawLine(QPointF(cx - 16.5 * s, cy - 14 * s), QPointF(cx - 16.5 * s, cy + 14 * s))
        painter.setPen(QPen(QColor("#2563eb"), 1.0 * s))
        painter.drawLine(QPointF(cx - 14.0 * s, cy - 14 * s), QPointF(cx - 14.0 * s, cy + 14 * s))

        # Ligne d'alimentation droite (Bleu -, Rouge +)
        painter.setPen(QPen(QColor("#2563eb"), 1.0 * s))
        painter.drawLine(QPointF(cx + 14.0 * s, cy - 14 * s), QPointF(cx + 14.0 * s, cy + 14 * s))
        painter.setPen(QPen(QColor("#dc2626"), 1.0 * s))
        painter.drawLine(QPointF(cx + 16.5 * s, cy - 14 * s), QPointF(cx + 16.5 * s, cy + 14 * s))

        # Matrice d'alvéoles carrées
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor("#1e293b")))
        for ry in range(-12, 13, 3):
            # Colonnes gauche (a, c, e)
            for rx in [-10, -7, -4]:
                painter.drawRect(QRectF(cx + rx * s, cy + ry * s, 1.4 * s, 1.4 * s))
            # Colonnes droite (f, h, j)
            for rx in [4, 7, 10]:
                painter.drawRect(QRectF(cx + rx * s, cy + ry * s, 1.4 * s, 1.4 * s))

    elif comp_type in ("esp32", "board"):
        # Carte ESP32 DevKit V1 identique à BoardGraphicsItem : PCB noir mat, antenne dorée, blindage métallique ESP-WROOM-32, broches dorées
        # 1. PCB noir mat
        painter.setPen(QPen(QColor("#2a3449"), 1.0 * s))
        painter.setBrush(QBrush(QColor("#131923")))
        painter.drawRoundedRect(QRectF(cx - 13 * s, cy - 18 * s, 26 * s, 36 * s), 2.5 * s, 2.5 * s)

        # Trous de fixation aux 4 coins
        painter.setPen(QPen(QColor("#fbbf24"), 0.8 * s))
        painter.setBrush(QBrush(QColor("#0f172a")))
        for hx, hy in [(-10.5, -15.5), (10.5, -15.5), (-10.5, 15.5), (10.5, 15.5)]:
            painter.drawEllipse(QPointF(cx + hx * s, cy + hy * s), 1.2 * s, 1.2 * s)

        # 2. Antenne méandre dorée en haut
        painter.setPen(QPen(QColor("#fbbf24"), 1.2 * s))
        painter.drawLine(QPointF(cx - 7 * s, cy - 16 * s), QPointF(cx + 7 * s, cy - 16 * s))
        painter.drawLine(QPointF(cx - 7 * s, cy - 14 * s), QPointF(cx - 2 * s, cy - 14 * s))
        painter.drawLine(QPointF(cx + 2 * s, cy - 14 * s), QPointF(cx + 7 * s, cy - 14 * s))

        # 3. Blindage métallique ESP-WROOM-32 avec sérigraphie
        can_grad = QLinearGradient(cx - 9 * s, cy - 11 * s, cx + 9 * s, cy + 3 * s)
        can_grad.setColorAt(0.0, QColor("#e2e8f0"))
        can_grad.setColorAt(0.6, QColor("#cbd5e1"))
        can_grad.setColorAt(1.0, QColor("#94a3b8"))

        painter.setPen(QPen(QColor("#64748b"), 0.8 * s))
        painter.setBrush(QBrush(can_grad))
        painter.drawRoundedRect(QRectF(cx - 9.5 * s, cy - 11 * s, 19 * s, 14 * s), 1.5 * s, 1.5 * s)

        painter.setFont(QFont("Consolas", int(3.5 * s), QFont.Bold))
        painter.setPen(QColor("#1e293b"))
        painter.drawText(QRectF(cx - 9 * s, cy - 8 * s, 18 * s, 5 * s), Qt.AlignCenter, "ESP-WROOM-32")

        # 4. Port USB-C en bas
        painter.setPen(QPen(QColor("#475569"), 0.8 * s))
        painter.setBrush(QBrush(QColor("#334155")))
        painter.drawRoundedRect(QRectF(cx - 5 * s, cy + 14 * s, 10 * s, 4.5 * s), 1.2 * s, 1.2 * s)

        # 5. LEDs d'état (Rouge power, Bleu GPIO 2)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor("#ef4444")))
        painter.drawRect(QRectF(cx - 6 * s, cy + 8 * s, 1.8 * s, 1.8 * s))
        painter.setBrush(QBrush(QColor("#38bdf8")))
        painter.drawRect(QRectF(cx + 4.2 * s, cy + 8 * s, 1.8 * s, 1.8 * s))

        # Boutons EN et BOOT
        painter.setBrush(QBrush(QColor("#475569")))
        painter.drawRect(QRectF(cx - 8.5 * s, cy + 12.5 * s, 2.5 * s, 3 * s))
        painter.drawRect(QRectF(cx + 6.0 * s, cy + 12.5 * s, 2.5 * s, 3 * s))

        # 6. Rangées de broches dorées de part et d'autre
        painter.setBrush(QBrush(QColor("#f59e0b")))
        for py in range(-12, 14, 2):
            painter.drawRect(QRectF(cx - 12.5 * s, cy + py * s, 1.6 * s, 1.4 * s))
            painter.drawRect(QRectF(cx + 10.9 * s, cy + py * s, 1.6 * s, 1.4 * s))

    elif comp_type in ("ldr", "photoresistor"):
        # Photorésistance : disque céramique beige, serpentin CdS bordeaux et 2 pattes
        painter.setPen(QPen(QColor("#cbd5e1"), 1.8 * s, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(QPointF(cx - 3 * s, cy + 6 * s), QPointF(cx - 3 * s, cy + 18 * s))
        painter.drawLine(QPointF(cx + 3 * s, cy + 6 * s), QPointF(cx + 3 * s, cy + 18 * s))

        disc_grad = QRadialGradient(cx, cy - 2 * s, 11 * s)
        disc_grad.setColorAt(0.0, QColor("#fed7aa"))
        disc_grad.setColorAt(0.7, QColor("#fb923c"))
        disc_grad.setColorAt(1.0, QColor("#c2410c"))
        painter.setPen(QPen(QColor("#9a3412"), 1.0 * s))
        painter.setBrush(QBrush(disc_grad))
        painter.drawEllipse(QPointF(cx, cy - 2 * s), 10 * s, 10 * s)

        # Tracé sinueux CdS
        painter.setPen(QPen(QColor("#7c2d12"), 1.5 * s, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        p = QPainterPath()
        p.moveTo(cx - 5 * s, cy - 6 * s)
        p.lineTo(cx + 5 * s, cy - 6 * s)
        p.lineTo(cx + 5 * s, cy - 2 * s)
        p.lineTo(cx - 5 * s, cy - 2 * s)
        p.lineTo(cx - 5 * s, cy + 2 * s)
        p.lineTo(cx + 5 * s, cy + 2 * s)
        painter.drawPath(p)

    elif comp_type in ("rgb_led", "rgbled"):
        # LED RGB 4 broches : dôme diffusant avec lueur multicolore et 4 pattes
        painter.setPen(QPen(QColor("#cbd5e1"), 1.5 * s, Qt.SolidLine, Qt.RoundCap))
        for px in (-4.5, -1.5, 1.5, 4.5):
            painter.drawLine(QPointF(cx + px * s, cy + 6 * s), QPointF(cx + px * s, cy + 18 * s))

        # Dôme époxy translucide
        dome_grad = QRadialGradient(cx, cy - 4 * s, 12 * s)
        dome_grad.setColorAt(0.0, QColor("#ffffff"))
        dome_grad.setColorAt(0.4, QColor("#f43f5e"))
        dome_grad.setColorAt(0.7, QColor("#10b981"))
        dome_grad.setColorAt(1.0, QColor("#3b82f6"))
        painter.setPen(QPen(QColor("#64748b"), 1.0 * s))
        painter.setBrush(QBrush(dome_grad))
        painter.drawEllipse(QPointF(cx, cy - 4 * s), 9 * s, 9 * s)
        # Collerette
        painter.drawRoundedRect(QRectF(cx - 10 * s, cy + 3 * s, 20 * s, 3 * s), 1 * s, 1 * s)

    elif comp_type in ("pir", "motion_sensor"):
        # Capteur PIR : PCB vert et lentille de Fresnel blanche facettée
        painter.setPen(QPen(QColor("#052e16"), 1.0 * s))
        painter.setBrush(QBrush(QColor("#15803d")))
        painter.drawRoundedRect(QRectF(cx - 16 * s, cy - 10 * s, 32 * s, 22 * s), 2.5 * s, 2.5 * s)

        # 2 potentiomètres orange
        painter.setBrush(QBrush(QColor("#f59e0b")))
        painter.drawRect(QRectF(cx - 14 * s, cy + 4 * s, 5 * s, 5 * s))
        painter.drawRect(QRectF(cx + 9 * s, cy + 4 * s, 5 * s, 5 * s))

        # Dôme blanc semi-sphérique
        fresnel_grad = QRadialGradient(cx, cy - 3 * s, 10 * s)
        fresnel_grad.setColorAt(0.0, QColor("#ffffff"))
        fresnel_grad.setColorAt(0.7, QColor("#f1f5f9"))
        fresnel_grad.setColorAt(1.0, QColor("#cbd5e1"))
        painter.setPen(QPen(QColor("#94a3b8"), 0.8 * s))
        painter.setBrush(QBrush(fresnel_grad))
        painter.drawEllipse(QPointF(cx, cy - 3 * s), 9 * s, 9 * s)

    elif comp_type in ("joystick", "thumbstick"):
        # Joystick : PCB bleu foncé, potentiomètres latéraux, chapeau ergonomique noir
        painter.setPen(QPen(QColor("#0f172a"), 1.0 * s))
        painter.setBrush(QBrush(QColor("#1e3a8a")))
        painter.drawRoundedRect(QRectF(cx - 15 * s, cy - 14 * s, 30 * s, 28 * s), 3 * s, 3 * s)

        # Anneau cardan
        painter.setPen(QPen(QColor("#64748b"), 1.0 * s))
        painter.setBrush(QBrush(QColor("#334155")))
        painter.drawEllipse(QPointF(cx, cy), 11 * s, 11 * s)

        # Chapeau noir avec cupule
        thumb_grad = QRadialGradient(cx - 2 * s, cy - 2 * s, 9 * s)
        thumb_grad.setColorAt(0.0, QColor("#475569"))
        thumb_grad.setColorAt(0.6, QColor("#1e293b"))
        thumb_grad.setColorAt(1.0, QColor("#020617"))
        painter.setPen(QPen(QColor("#020617"), 1.0 * s))
        painter.setBrush(QBrush(thumb_grad))
        painter.drawEllipse(QPointF(cx, cy), 8.5 * s, 8.5 * s)
        # Creux central
        painter.setBrush(QBrush(QColor("#0f172a")))
        painter.drawEllipse(QPointF(cx, cy), 4 * s, 4 * s)

    elif comp_type in ("switch", "slide_switch"):
        # Interrupteur à glissière : boîtier chromé et curseur plastique noir
        painter.setPen(QPen(QColor("#cbd5e1"), 1.5 * s, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(QPointF(cx - 6 * s, cy + 8 * s), QPointF(cx - 6 * s, cy + 16 * s))
        painter.drawLine(QPointF(cx, cy + 8 * s), QPointF(cx, cy + 16 * s))
        painter.drawLine(QPointF(cx + 6 * s, cy + 8 * s), QPointF(cx + 6 * s, cy + 16 * s))

        # Boîtier chromé
        case_grad = QLinearGradient(cx - 12 * s, cy - 4 * s, cx + 12 * s, cy + 8 * s)
        case_grad.setColorAt(0.0, QColor("#f1f5f9"))
        case_grad.setColorAt(0.5, QColor("#cbd5e1"))
        case_grad.setColorAt(1.0, QColor("#64748b"))
        painter.setPen(QPen(QColor("#475569"), 1.0 * s))
        painter.setBrush(QBrush(case_grad))
        painter.drawRoundedRect(QRectF(cx - 12 * s, cy - 4 * s, 24 * s, 12 * s), 2 * s, 2 * s)

        # Curseur noir à gauche
        painter.setPen(QPen(QColor("#020617"), 0.8 * s))
        painter.setBrush(QBrush(QColor("#1e293b")))
        painter.drawRoundedRect(QRectF(cx - 8 * s, cy - 10 * s, 7 * s, 8 * s), 1.5 * s, 1.5 * s)

    elif comp_type in ("w25q", "w25q32", "w25q64"):
        # W25Q SPI Flash (black rectangle, 6 pins)
        painter.setPen(Qt.black)
        painter.setBrush(QBrush(QColor(30, 30, 30)))
        painter.drawRect(QRectF(cx - 10 * s, cy - 8 * s, 20 * s, 16 * s))
        painter.setPen(Qt.white)
        painter.setFont(QFont("Arial", int(3 * s), QFont.Bold))
        painter.drawText(QRectF(cx - 10 * s, cy - 8 * s, 20 * s, 16 * s), Qt.AlignCenter, "W25Q")
    elif comp_type in ("bme280", "bmp280"):
        # Capteur BME280 : PCB violet, boîtier métallique avec orifice et 4 broches dorées
        painter.setPen(QPen(QColor("#7e22ce"), 1.0 * s))
        painter.setBrush(QBrush(QColor("#6b21a8")))
        painter.drawRoundedRect(QRectF(cx - 11 * s, cy - 12 * s, 22 * s, 24 * s), 2.5 * s, 2.5 * s)

        # Boîtier capteur métallique
        painter.setPen(QPen(QColor("#64748b"), 0.8 * s))
        painter.setBrush(QBrush(QColor("#cbd5e1")))
        painter.drawRoundedRect(QRectF(cx - 5 * s, cy - 6 * s, 10 * s, 8 * s), 1.2 * s, 1.2 * s)
        # Évent
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor("#1e293b")))
        painter.drawEllipse(QPointF(cx + 2 * s, cy - 2 * s), 1.0 * s, 1.0 * s)

        # 4 broches dorées en bas
        painter.setBrush(QBrush(QColor("#fbbf24")))
        for px in [-7.5, -2.5, 2.5, 7.5]:
            painter.drawRect(QRectF(cx + (px - 0.8) * s, cy + 8 * s, 1.6 * s, 3.5 * s))

    elif comp_type in ("mpu6050", "mpu_6050", "gy521"):
        # MPU-6050 : PCB bleu, puce noire QFN, repères axes X-Y
        painter.setPen(QPen(QColor("#2563eb"), 1.0 * s))
        painter.setBrush(QBrush(QColor("#1d4ed8")))
        painter.drawRoundedRect(QRectF(cx - 13 * s, cy - 11 * s, 26 * s, 22 * s), 2.5 * s, 2.5 * s)

        # Puce QFN centrale
        painter.setPen(QPen(QColor("#3f3f46"), 0.8 * s))
        painter.setBrush(QBrush(QColor("#18181b")))
        painter.drawRoundedRect(QRectF(cx - 5 * s, cy - 5 * s, 10 * s, 10 * s), 1.0 * s, 1.0 * s)

        # Repères d'axes X et Y
        painter.setPen(QPen(QColor("#ffffff"), 0.8 * s))
        painter.drawLine(QPointF(cx + 6 * s, cy - 2 * s), QPointF(cx + 10 * s, cy - 2 * s))
        painter.drawLine(QPointF(cx + 6 * s, cy - 2 * s), QPointF(cx + 6 * s, cy + 2 * s))

        # 5 broches dorées en bas
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor("#fbbf24")))
        for px in [-9, -4.5, 0, 4.5, 9]:
            painter.drawRect(QRectF(cx + (px - 0.8) * s, cy + 7 * s, 1.6 * s, 3.5 * s))

    elif comp_type in ("stepper", "stepper_motor", "28byj48"):
        # Moteur pas-à-pas : cylindre métallique argenté + axe laiton doré
        # Ombre et corps cylindrique
        painter.setPen(QPen(QColor("#475569"), 1.0 * s))
        painter.setBrush(QBrush(QColor("#cbd5e1")))
        painter.drawEllipse(QPointF(cx, cy), 12 * s, 12 * s)

        # Pattes de fixation
        painter.setBrush(QBrush(QColor("#94a3b8")))
        painter.drawRect(QRectF(cx - 15 * s, cy - 3 * s, 4 * s, 6 * s))
        painter.drawRect(QRectF(cx + 11 * s, cy - 3 * s, 4 * s, 6 * s))

        # Axe central en laiton
        painter.setPen(QPen(QColor("#854d0e"), 0.8 * s))
        painter.setBrush(QBrush(QColor("#ca8a04")))
        painter.drawEllipse(QPointF(cx, cy), 4.5 * s, 4.5 * s)
        painter.setPen(QPen(QColor("#451a03"), 0.8 * s))
        painter.drawLine(QPointF(cx - 2 * s, cy - 2 * s), QPointF(cx + 2 * s, cy - 2 * s))

    elif comp_type in ("tm1637", "7segment", "display_7seg"):
        # Afficheur 4 digits 7 segments TM1637 : boîtier noir avec 4 chiffres 88:88 rouges
        painter.setPen(QPen(QColor("#334155"), 1.0 * s))
        painter.setBrush(QBrush(QColor("#0f172a")))
        painter.drawRoundedRect(QRectF(cx - 15 * s, cy - 9 * s, 30 * s, 18 * s), 2.0 * s, 2.0 * s)

        # Écran sombre
        painter.setBrush(QBrush(QColor("#020617")))
        painter.drawRect(QRectF(cx - 12 * s, cy - 6 * s, 24 * s, 12 * s))

        # Chiffres 8 8 : 8 8 rouges
        painter.setFont(QFont("Consolas", int(6.5 * s), QFont.Bold))
        painter.setPen(QColor("#ef4444"))
        painter.drawText(QRectF(cx - 12 * s, cy - 6 * s, 24 * s, 12 * s), Qt.AlignCenter, "88:88")

    else:
        # Module générique
        painter.setPen(QPen(QColor("#38bdf8"), 1.5 * s))
        painter.setBrush(QBrush(QColor("#1e293b")))
        painter.drawRoundedRect(QRectF(cx - 12 * s, cy - 12 * s, 24 * s, 24 * s), 3 * s, 3 * s)

    painter.end()
    return pix


class ComponentCard(QFrame):
    clicked = Signal(str) # component_type

    def __init__(self, comp_type: str, name: str, parent=None):
        super().__init__(parent)
        self.comp_type = comp_type
        self.name = name
        self.setCursor(Qt.PointingHandCursor)
        self._drag_start_pos = None

        self.setProperty("class", "ComponentCard")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(84)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)
        layout.setAlignment(Qt.AlignCenter)

        # Vignette photoréaliste
        self.thumbnail = render_component_thumbnail(comp_type, 42)
        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setPixmap(self.thumbnail)
        layout.addWidget(self.icon_label)

        # Nom du composant
        self.name_label = QLabel(name)
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setWordWrap(True)
        self.name_label.setProperty("class", "ComponentCardLabel")
        layout.addWidget(self.name_label)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_start_pos = event.position().toPoint()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self._drag_start_pos:
            dist = (event.position().toPoint() - self._drag_start_pos).manhattanLength()
            if dist < QApplication.startDragDistance():
                self.clicked.emit(self.comp_type)
            self._drag_start_pos = None
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton) or not self._drag_start_pos:
            return
        if (event.position().toPoint() - self._drag_start_pos).manhattanLength() < QApplication.startDragDistance():
            return

        # Démarrer le Drag & Drop natif avec une image à l'échelle 1:1 du composant réel
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setData("application/x-esp32-component", self.comp_type.encode("utf-8"))
        mime_data.setText(self.comp_type)
        drag.setMimeData(mime_data)

        # Générer un aperçu fidèle à l'échelle 1:1 du composant et de ses broches réelles
        drag_pix, hotspot = self._create_realistic_drag_pixmap()
        drag.setPixmap(drag_pix)
        drag.setHotSpot(hotspot)

        drag.exec(Qt.CopyAction)

    def _create_realistic_drag_pixmap(self) -> tuple[QPixmap, QPoint]:
        """Crée une image fidèle à l'échelle 1:1 du composant avec ses vraies broches pour le Drag & Drop."""
        ctype = self.comp_type.lower()
        # Instancier temporairement le composant réel pour capturer son rendu exact 1:1
        item = None
        try:
            if ctype == "led":
                from ..canvas.items.led_item import LEDGraphicsItem
                item = LEDGraphicsItem("drag_preview", color_name="red")
            elif ctype == "resistor":
                from ..canvas.items.resistor_item import ResistorGraphicsItem
                item = ResistorGraphicsItem("drag_preview", resistance_value=220)
            elif ctype == "button":
                from ..canvas.items.button_item import ButtonGraphicsItem
                item = ButtonGraphicsItem("drag_preview")
            elif ctype == "potentiometer":
                from ..canvas.items.potentiometer_item import PotentiometerGraphicsItem
                item = PotentiometerGraphicsItem("drag_preview")
            elif ctype in ("esp32", "board"):
                from ..canvas.items.board_item import BoardGraphicsItem
                item = BoardGraphicsItem("drag_preview")
            elif ctype == "dht22":
                from ..canvas.items.dht22_item import DHT22GraphicsItem
                item = DHT22GraphicsItem("drag_preview")
            elif ctype == "oled":
                from ..canvas.items.oled_item import OLEDGraphicsItem
                item = OLEDGraphicsItem("drag_preview")
            elif ctype == "relay":
                from ..canvas.items.relay_item import RelayGraphicsItem
                item = RelayGraphicsItem("drag_preview")
            elif ctype == "servo":
                from ..canvas.items.servo_item import ServoGraphicsItem
                item = ServoGraphicsItem("drag_preview")
            elif ctype == "buzzer":
                from ..canvas.items.buzzer_item import BuzzerGraphicsItem
                item = BuzzerGraphicsItem("drag_preview")
            elif ctype in ("neopixel", "ws2812", "ws2812b"):
                from ..canvas.items.neopixel_item import NeoPixelGraphicsItem
                item = NeoPixelGraphicsItem("drag_preview")
            elif ctype == "hcsr04":
                from ..canvas.items.hcsr04_item import HCSR04GraphicsItem
                item = HCSR04GraphicsItem("drag_preview")
            elif ctype in ("lcd", "lcd16x2"):
                from ..canvas.items.lcd_item import LCDGraphicsItem
                item = LCDGraphicsItem("drag_preview")
            elif ctype in ("ldr", "photoresistor"):
                from ..canvas.items.ldr_item import LDRGraphicsItem
                item = LDRGraphicsItem("drag_preview")
            elif ctype in ("rgb_led", "rgbled"):
                from ..canvas.items.rgb_led_item import RGBLEDGraphicsItem
                item = RGBLEDGraphicsItem("drag_preview")
            elif ctype in ("pir", "motion_sensor"):
                from ..canvas.items.pir_item import PIRGraphicsItem
                item = PIRGraphicsItem("drag_preview")
            elif ctype in ("joystick", "thumbstick"):
                from ..canvas.items.joystick_item import JoystickGraphicsItem
                item = JoystickGraphicsItem("drag_preview")
            elif ctype in ("switch", "slide_switch"):
                from ..canvas.items.switch_item import SlideSwitchGraphicsItem
                item = SlideSwitchGraphicsItem("drag_preview")
            elif ctype in ("w25q", "w25q32", "w25q64"):
                from ..canvas.items.w25q_item import W25QItem
                item = W25QItem("drag_preview")
            elif ctype in ("bme280", "bmp280"):
                from ..canvas.items.bme280_item import BME280GraphicsItem
                item = BME280GraphicsItem("drag_preview")
            elif ctype in ("mpu6050", "mpu_6050", "gy521"):
                from ..canvas.items.mpu6050_item import MPU6050GraphicsItem
                item = MPU6050GraphicsItem("drag_preview")
            elif ctype in ("stepper", "stepper_motor", "28byj48"):
                from ..canvas.items.stepper_item import StepperMotorGraphicsItem
                item = StepperMotorGraphicsItem("drag_preview")
            elif ctype in ("tm1637", "7segment", "display_7seg"):
                from ..canvas.items.tm1637_item import TM1637GraphicsItem
                item = TM1637GraphicsItem("drag_preview")
        except Exception:
            item = None

        if item:
            rect = item.boundingRect()
            w = max(30, int(rect.width() + 8))
            h = max(30, int(rect.height() + 8))
            pix = QPixmap(w, h)
            pix.fill(Qt.transparent)
            painter = QPainter(pix)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            painter.setOpacity(0.92) # Légère translucidité naturelle pendant le drag
            # Centrer l'origine (0, 0) de l'item au hotspot
            offset_x = -rect.x() + 4
            offset_y = -rect.y() + 4
            painter.translate(offset_x, offset_y)
            item.paint(painter, None)
            # Dessiner aussi les items enfants (broches PhysicalPinItem) avec leur transformation relative
            for child in item.childItems():
                if hasattr(child, 'paint'):
                    painter.save()
                    painter.translate(child.pos())
                    child.paint(painter, None)
                    painter.restore()
            painter.end()
            return pix, QPoint(int(offset_x), int(offset_y))

        # Fallback si l'item n'a pas pu être instancié
        return self.thumbnail, QPoint(self.thumbnail.width() // 2, self.thumbnail.height() // 2)


class ComponentPaletteWidget(QWidget):
    component_selected = Signal(str) # type

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ComponentLibrary")
        self.setMinimumWidth(150)
        self._cards: list[tuple[ComponentCard, str, str]] = []

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 12, 10, 12)
        main_layout.setSpacing(10)

        # En-tête
        title = QLabel("📦 Bibliothèque de composants")
        title.setObjectName("ComponentLibraryTitle")
        main_layout.addWidget(title)

        # Barre de recherche rapide
        self.search_input = QLineEdit()
        self.search_input.setObjectName("SearchBox")
        self.search_input.setPlaceholderText("🔍 Rechercher...")
        self.search_input.textChanged.connect(self._filter_components)
        main_layout.addWidget(self.search_input)

        # Zone scrollable
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: #0f172a;
                width: 6px;
                margin: 0px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                background: #334155;
                border-radius: 3px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #0284c7;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        content_widget = QWidget()
        self.content_layout = QVBoxLayout(content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(12)

        # Catégories avec vrais composants miniatures
        self._add_category("Cartes & Platines", [
            ("esp32", "ESP32 DevKit"),
            ("breadboard", "Breadboard"),
        ])

        self._add_category("Basiques & Puissance", [
            ("led", "LED 5mm"),
            ("resistor", "Résistance"),
            ("button", "Bouton poussoir"),
            ("switch", "Interrupteur SPDT"),
            ("potentiometer", "Potentiomètre"),
            ("joystick", "Joystick 2 axes"),
            ("buzzer", "Buzzer"),
            ("relay", "Relais 5V"),
            ("servo", "Servo SG90"),
            ("stepper", "Moteur Pas-à-Pas"),
        ])

        self._add_category("Affichage & Lumière", [
            ("rgb_led", "LED RGB 5mm"),
            ("neopixel", "NeoPixel Ring"),
            ("oled", "OLED SSD1306"),
            ("lcd16x2", "LCD 16x2"),
            ("tm1637", "Afficheur 4 Digits"),
        ])

        self._add_category("Capteurs", [
            ("ldr", "Photorésistance LDR"),
            ("pir", "Capteur PIR"),
            ("dht22", "DHT22"),
            ("hcsr04", "HC-SR04"),
            ("bme280", "BME280 Météo"), ("w25q32", "W25Q32 Flash SPI"),
            ("mpu6050", "MPU-6050 6 axes"),
        ])

        self.content_layout.addStretch()
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

    def _add_category(self, title: str, items: list[tuple[str, str]]):
        cat_label = QLabel(title)
        cat_label.setObjectName("ComponentCategoryTitle")
        self.content_layout.addWidget(cat_label)

        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(6)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        for i, (ctype, name) in enumerate(items):
            r = i // 2
            c = i % 2
            card = ComponentCard(ctype, name)
            card.clicked.connect(self.component_selected)
            self._cards.append((card, name.lower(), title.lower()))
            grid.addWidget(card, r, c)

        self.content_layout.addLayout(grid)

    def _filter_components(self, query: str):
        q = query.strip().lower()
        for card, name, cat in self._cards:
            match = (q in name) or (q in cat) if q else True
            card.setVisible(match)
