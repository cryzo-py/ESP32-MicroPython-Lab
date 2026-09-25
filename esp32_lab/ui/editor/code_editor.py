"""
Éditeur de code MicroPython intégré (CodeEditor) avec numérotation et indentation
"""

from PySide6.QtCore import QRect, QSize, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QTextCharFormat, QTextCursor, QTextFormat
from PySide6.QtWidgets import QPlainTextEdit, QTextEdit, QWidget

from .syntax import PythonHighlighter


class LineNumberArea(QWidget):
    def __init__(self, editor: "CodeEditor"):
        super().__init__(editor)
        self.code_editor = editor

    def sizeHint(self) -> QSize:
        return QSize(self.code_editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.code_editor.line_number_area_paint_event(event)


class CodeEditor(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("CodeEditor")
        self.theme_name = "dark"
        self.line_number_area = LineNumberArea(self)
        self.highlighter = PythonHighlighter(self.document(), theme_name=self.theme_name)

        # Configuration typographique
        font = QFont("Consolas", 11)
        font.setStyleHint(QFont.Monospace)
        self.setFont(font)
        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(' ') * 4)

        # Connexion des signaux pour la numérotation
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)

        self.update_line_number_area_width(0)
        self.highlight_current_line()

        self._error_line = -1

    def set_theme(self, theme_name: str):
        """Met à jour le thème de l'éditeur (gouttière, surbrillance, coloration)."""
        self.theme_name = theme_name
        self.highlighter.set_theme(theme_name)
        self.highlight_current_line()
        self.line_number_area.update()

    def line_number_area_width(self) -> int:
        digits = 1
        max_num = max(1, self.blockCount())
        while max_num >= 10:
            max_num //= 10
            digits += 1
        space = 14 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))

    def highlight_current_line(self):
        extra_selections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            is_light = (self.theme_name == "light")
            line_color = QColor("#e0f2fe") if is_light else QColor("#1e293b")
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)

        self.setExtraSelections(extra_selections)

    def highlight_error_line(self, line_number: int):
        self._error_line = line_number
        extra_selections = []
        if line_number > 0:
            selection = QTextEdit.ExtraSelection()
            is_light = (self.theme_name == "light")
            err_color = QColor("#fee2e2") if is_light else QColor("#4c1d24")
            selection.format.setBackground(err_color) # Rouge doux en light, bordeaux en dark
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            cursor = QTextCursor(self.document().findBlockByNumber(line_number - 1))
            selection.cursor = cursor
            extra_selections.append(selection)
        self.setExtraSelections(extra_selections)

    def clear_error_highlight(self):
        self._error_line = -1
        self.highlight_current_line()

    def keyPressEvent(self, event):
        # Touche Tab -> 4 espaces
        if event.key() == Qt.Key_Tab:
            self.insertPlainText("    ")
            event.accept()
            return

        # Touche Entrée -> Indentation automatique
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            cursor = self.textCursor()
            line_text = cursor.block().text()
            indent = len(line_text) - len(line_text.lstrip(' '))
            
            # Si la ligne se termine par ':', augmenter l'indentation de 4
            extra_indent = 4 if line_text.rstrip().endswith(':') else 0
            super().keyPressEvent(event)
            self.insertPlainText(" " * (indent + extra_indent))
            event.accept()
            return

        super().keyPressEvent(event)

    def zoom_in(self, delta: int = 1):
        """Augmente la taille de la police du code."""
        font = self.font()
        new_size = min(28, font.pointSize() + delta)
        font.setPointSize(new_size)
        self.setFont(font)
        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(' ') * 4)
        self.update_line_number_area_width(0)

    def zoom_out(self, delta: int = 1):
        """Réduit la taille de la police du code."""
        font = self.font()
        new_size = max(7, font.pointSize() - delta)
        font.setPointSize(new_size)
        self.setFont(font)
        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(' ') * 4)
        self.update_line_number_area_width(0)

    def zoom_reset(self):
        """Réinitialise la taille de police par défaut (11pt)."""
        font = self.font()
        font.setPointSize(11)
        self.setFont(font)
        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(' ') * 4)
        self.update_line_number_area_width(0)

    def wheelEvent(self, event):
        """Support de Ctrl + Molette de la souris pour zoomer dans le code."""
        if event.modifiers() & Qt.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self.zoom_in()
            elif delta < 0:
                self.zoom_out()
            event.accept()
            return
        super().wheelEvent(event)

    def line_number_area_paint_event(self, event):
        painter = QPainter(self.line_number_area)
        is_light = (self.theme_name == "light")
        bg_color = QColor("#f1f5f9") if is_light else QColor("#151c2c")
        border_color = QColor("#cbd5e1") if is_light else QColor("#2a3449")
        num_color = QColor("#475569") if is_light else QColor("#64748b")
        active_num_color = QColor("#0284c7") if is_light else QColor("#38bdf8")

        painter.fillRect(event.rect(), bg_color)

        # Ligne de séparation droite subtile
        painter.setPen(border_color)
        w = self.line_number_area.width()
        painter.drawLine(w - 1, event.rect().top(), w - 1, event.rect().bottom())

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        current_block_num = self.textCursor().blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                if block_number + 1 == self._error_line:
                    painter.setPen(QColor("#e11d48" if is_light else "#f43f5e"))
                elif block_number == current_block_num:
                    painter.setPen(active_num_color)
                else:
                    painter.setPen(num_color)
                painter.drawText(0, int(top), self.line_number_area.width() - 8,
                                 self.fontMetrics().height(), Qt.AlignRight, number)

            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1
