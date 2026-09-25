"""
Coloration syntaxique pour l'éditeur de code MicroPython
"""

import re
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat


class PythonHighlighter(QSyntaxHighlighter):
    def __init__(self, document, theme_name: str = "dark"):
        super().__init__(document)
        self.rules = []
        self.theme_name = theme_name
        self._setup_rules()

    def set_theme(self, theme_name: str):
        if self.theme_name != theme_name:
            self.theme_name = theme_name
            self._setup_rules()
            self.rehighlight()

    def _setup_rules(self):
        self.rules.clear()
        is_light = (self.theme_name == "light")

        # Formats de texte haute lisibilité
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#be123c" if is_light else "#f43f5e")) # Rouge framboise profond / rose vif
        keyword_format.setFontWeight(QFont.Bold)

        builtin_format = QTextCharFormat()
        builtin_format.setForeground(QColor("#0369a1" if is_light else "#38bdf8")) # Bleu saphir foncé / bleu ciel
        builtin_format.setFontWeight(QFont.Bold)

        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#15803d" if is_light else "#4ade80")) # Vert émeraude sombre / vert fluo

        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#475569" if is_light else "#94a3b8")) # Gris ardoise contrasté
        comment_format.setFontItalic(True)

        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#b45309" if is_light else "#fbbf24")) # Ambre cuivré foncé / ambre vif

        # Mots-clés Python
        keywords = [
            r"\band\b", r"\bas\b", r"\bassert\b", r"\bbreak\b", r"\bclass\b", r"\bcontinue\b",
            r"\bdef\b", r"\bdel\b", r"\belif\b", r"\belse\b", r"\bexcept\b", r"\bfinally\b",
            r"\bfor\b", r"\bfrom\b", r"\bglobal\b", r"\bif\b", r"\bimport\b", r"\bin\b",
            r"\bis\b", r"\blambda\b", r"\bnot\b", r"\bor\b", r"\bpass\b", r"\braise\b",
            r"\breturn\b", r"\btry\b", r"\bwhile\b", r"\bwith\b", r"\byield\b",
            r"\bTrue\b", r"\bFalse\b", r"\bNone\b"
        ]
        for kw in keywords:
            self.rules.append((re.compile(kw), keyword_format))

        # Builtins & MicroPython API
        builtins = [
            r"\bmachine\b", r"\bPin\b", r"\bPWM\b", r"\bADC\b", r"\bI2C\b", r"\bSPI\b", r"\bUART\b",
            r"\btime\b", r"\bsleep\b", r"\bsleep_ms\b", r"\bsleep_us\b", r"\bticks_ms\b",
            r"\bprint\b", r"\brange\b", r"\blen\b", r"\bint\b", r"\bfloat\b", r"\bstr\b"
        ]
        for bi in builtins:
            self.rules.append((re.compile(bi), builtin_format))

        # Nombres
        self.rules.append((re.compile(r"\b[0-9]+(\.[0-9]+)?\b"), number_format))

        # Chaînes entre guillemets doubles ou simples
        self.rules.append((re.compile(r'"[^"\\]*(\\.[^"\\]*)*"'), string_format))
        self.rules.append((re.compile(r"'[^'\\]*(\\.[^'\\]*)*'"), string_format))

        # Commentaires
        self.rules.append((re.compile(r"#[^\n]*"), comment_format))

    def highlightBlock(self, text: str):
        for pattern, fmt in self.rules:
            for match in pattern.finditer(text):
                start, end = match.span()
                self.setFormat(start, end - start, fmt)
