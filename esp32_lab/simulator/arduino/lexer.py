"""
Analyseur lexical (Lexer) pour Arduino C / C++.
Gère le prétraitement (#define, #include), le nettoyage des commentaires,
et la tokenisation avec suivi précis des numéros de ligne et colonnes.
"""

from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class Token:
    type: str       # 'KEYWORD', 'IDENTIFIER', 'NUMBER', 'STRING', 'CHAR', 'OPERATOR', 'DELIMITER', 'EOF'
    value: Any
    line: int
    col: int

    def __repr__(self) -> str:
        return f"Token({self.type}, {repr(self.value)}, L{self.line}:C{self.col})"


KEYWORDS = {
    "if", "else", "while", "for", "do", "switch", "case", "default",
    "break", "continue", "return", "const", "static", "unsigned", "signed",
    "void", "int", "long", "float", "double", "bool", "boolean", "char",
    "byte", "uint8_t", "uint16_t", "uint32_t", "int8_t", "int16_t", "int32_t",
    "String", "struct", "class", "true", "false", "sizeof"
}

OPERATORS_3 = {"<<=", ">>="}
OPERATORS_2 = {
    "++", "--", "+=", "-=", "*=", "/=", "%=", "&=", "|=", "^=",
    "==", "!=", "<=", ">=", "&&", "||", "<<", ">>", "->", "::"
}
OPERATORS_1 = set("+-*/%=<>!&|^~?:.")
DELIMITERS = set("(){}[],;")


class ArduinoLexer:
    """Tokeniseur pour code source Arduino."""

    def __init__(self, source: str):
        self.original_source = source
        self.source = source
        self.pos = 0
        self.line = 1
        self.col = 1
        self.macros: dict[str, str] = {}
        self.included_libraries: set[str] = set()

    def tokenize(self) -> list[Token]:
        """Exécute le prétraitement et tokenise l'ensemble du code source."""
        self._preprocess()
        tokens: list[Token] = []

        while self.pos < len(self.source):
            ch = self.source[self.pos]

            # Espaces et sauts de ligne
            if ch == '\n':
                self.pos += 1
                self.line += 1
                self.col = 1
                continue
            elif ch.isspace():
                self.pos += 1
                self.col += 1
                continue

            # Commentaires mono-ligne ou multi-lignes
            if ch == '/' and self.pos + 1 < len(self.source):
                next_ch = self.source[self.pos + 1]
                if next_ch == '/':
                    # Commentaire mono-ligne
                    while self.pos < len(self.source) and self.source[self.pos] != '\n':
                        self.pos += 1
                    continue
                elif next_ch == '*':
                    # Commentaire multi-lignes
                    self.pos += 2
                    self.col += 2
                    while self.pos + 1 < len(self.source) and not (self.source[self.pos] == '*' and self.source[self.pos + 1] == '/'):
                        if self.source[self.pos] == '\n':
                            self.line += 1
                            self.col = 1
                        else:
                            self.col += 1
                        self.pos += 1
                    self.pos += 2  # Ignorer */
                    self.col += 2
                    continue

            start_col = self.col
            start_line = self.line

            # Chaînes de caractères ("...")
            if ch == '"':
                tokens.append(self._read_string())
                continue

            # Caractères littéraux ('...')
            if ch == "'":
                tokens.append(self._read_char())
                continue

            # Nombres (décimal, hexadécimal 0x, binaire 0b, flottant)
            if ch.isdigit() or (ch == '.' and self.pos + 1 < len(self.source) and self.source[self.pos + 1].isdigit()):
                tokens.append(self._read_number())
                continue

            # Identifiants et mots-clés
            if ch.isalpha() or ch == '_':
                tokens.append(self._read_identifier())
                continue

            # Opérateurs à 3 caractères
            if self.pos + 2 < len(self.source) and self.source[self.pos:self.pos + 3] in OPERATORS_3:
                op = self.source[self.pos:self.pos + 3]
                self.pos += 3
                self.col += 3
                tokens.append(Token("OPERATOR", op, start_line, start_col))
                continue

            # Opérateurs à 2 caractères
            if self.pos + 1 < len(self.source) and self.source[self.pos:self.pos + 2] in OPERATORS_2:
                op = self.source[self.pos:self.pos + 2]
                self.pos += 2
                self.col += 2
                tokens.append(Token("OPERATOR", op, start_line, start_col))
                continue

            # Opérateurs à 1 caractère
            if ch in OPERATORS_1:
                self.pos += 1
                self.col += 1
                tokens.append(Token("OPERATOR", ch, start_line, start_col))
                continue

            # Délimiteurs
            if ch in DELIMITERS:
                self.pos += 1
                self.col += 1
                tokens.append(Token("DELIMITER", ch, start_line, start_col))
                continue

            # Caractère inattendu
            err_ch = ch
            self.pos += 1
            self.col += 1
            raise SyntaxError(f"Caractère inattendu '{err_ch}' à la ligne {start_line}, colonne {start_col}")

        tokens.append(Token("EOF", None, self.line, self.col))
        return tokens

    def _preprocess(self):
        """
        Gère les directives #include et #define.
        Remplace les directives par des espaces/lignes vides pour préserver le numéro de ligne.
        """
        lines = self.source.splitlines(keepends=True)
        processed_lines = []

        for line_idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("#include"):
                # #include <Servo.h> ou #include "LiquidCrystal.h"
                m = re.search(r'#include\s*[<"]([^>"]+)[>"]', stripped)
                if m:
                    lib_name = m.group(1).replace(".h", "").strip()
                    self.included_libraries.add(lib_name)
                processed_lines.append("\n")  # Conserver le numéro de ligne
            elif stripped.startswith("#define"):
                # #define NOM VALEUR
                parts = stripped.split(None, 2)
                if len(parts) >= 2:
                    macro_name = parts[1]
                    macro_val = parts[2] if len(parts) > 2 else "1"
                    # Nettoyer les commentaires de fin de ligne
                    if "//" in macro_val:
                        macro_val = macro_val.split("//")[0].strip()
                    self.macros[macro_name] = macro_val
                processed_lines.append("\n")
            else:
                processed_lines.append(line)

        self.source = "".join(processed_lines)

    def _read_string(self) -> Token:
        start_line = self.line
        start_col = self.col
        self.pos += 1  # Sauter le premier guillemet
        self.col += 1
        chars = []

        while self.pos < len(self.source) and self.source[self.pos] != '"':
            ch = self.source[self.pos]
            if ch == '\\' and self.pos + 1 < len(self.source):
                nxt = self.source[self.pos + 1]
                escapes = {'n': '\n', 't': '\t', 'r': '\r', '"': '"', '\\': '\\', '0': '\0'}
                chars.append(escapes.get(nxt, nxt))
                self.pos += 2
                self.col += 2
            elif ch == '\n':
                self.line += 1
                self.col = 1
                chars.append(ch)
                self.pos += 1
            else:
                chars.append(ch)
                self.pos += 1
                self.col += 1

        if self.pos >= len(self.source):
            raise SyntaxError(f"Chaîne de caractères non terminée (ligne {start_line}, colonne {start_col})")

        self.pos += 1  # Sauter le guillemet fermant
        self.col += 1
        return Token("STRING", "".join(chars), start_line, start_col)

    def _read_char(self) -> Token:
        start_line = self.line
        start_col = self.col
        self.pos += 1
        self.col += 1
        ch_val = ''

        if self.pos < len(self.source) and self.source[self.pos] == '\\':
            self.pos += 1
            self.col += 1
            nxt = self.source[self.pos] if self.pos < len(self.source) else ''
            escapes = {'n': '\n', 't': '\t', 'r': '\r', "'": "'", '\\': '\\', '0': '\0'}
            ch_val = escapes.get(nxt, nxt)
            self.pos += 1
            self.col += 1
        elif self.pos < len(self.source):
            ch_val = self.source[self.pos]
            self.pos += 1
            self.col += 1

        if self.pos < len(self.source) and self.source[self.pos] == "'":
            self.pos += 1
            self.col += 1
        else:
            raise SyntaxError(f"Caractère littéral non terminé (ligne {start_line}, colonne {start_col})")

        return Token("CHAR", ch_val, start_line, start_col)

    def _read_number(self) -> Token:
        start_line = self.line
        start_col = self.col
        start_pos = self.pos

        # Hexadécimal 0x...
        if self.source[self.pos:self.pos + 2].lower() == "0x":
            self.pos += 2
            self.col += 2
            hex_start = self.pos
            while self.pos < len(self.source) and (self.source[self.pos].isdigit() or self.source[self.pos].lower() in "abcdef"):
                self.pos += 1
                self.col += 1
            val_str = self.source[hex_start:self.pos]
            val = int(val_str, 16) if val_str else 0
            # Ignorer les suffixes comme U, L, UL
            self._skip_int_suffixes()
            return Token("NUMBER", val, start_line, start_col)

        # Binaire 0b...
        if self.source[self.pos:self.pos + 2].lower() == "0b":
            self.pos += 2
            self.col += 2
            bin_start = self.pos
            while self.pos < len(self.source) and self.source[self.pos] in "01":
                self.pos += 1
                self.col += 1
            val_str = self.source[bin_start:self.pos]
            val = int(val_str, 2) if val_str else 0
            self._skip_int_suffixes()
            return Token("NUMBER", val, start_line, start_col)

        is_float = False
        while self.pos < len(self.source):
            ch = self.source[self.pos]
            if ch.isdigit():
                self.pos += 1
                self.col += 1
            elif ch == '.' and not is_float:
                is_float = True
                self.pos += 1
                self.col += 1
            elif ch.lower() == 'e' and (self.pos + 1 < len(self.source)):
                is_float = True
                self.pos += 1
                self.col += 1
                if self.source[self.pos] in "+-":
                    self.pos += 1
                    self.col += 1
            else:
                break

        num_str = self.source[start_pos:self.pos]
        # Ignorer suffixe f/F/u/U/l/L
        if self.pos < len(self.source) and self.source[self.pos].lower() in "ful":
            if self.source[self.pos].lower() == 'f':
                is_float = True
            self.pos += 1
            self.col += 1
            self._skip_int_suffixes()

        val = float(num_str) if is_float else int(num_str)
        return Token("NUMBER", val, start_line, start_col)

    def _skip_int_suffixes(self):
        while self.pos < len(self.source) and self.source[self.pos].lower() in "ul":
            self.pos += 1
            self.col += 1

    def _read_identifier(self) -> Token:
        start_line = self.line
        start_col = self.col
        start_pos = self.pos

        while self.pos < len(self.source) and (self.source[self.pos].isalnum() or self.source[self.pos] == '_'):
            self.pos += 1
            self.col += 1

        name = self.source[start_pos:self.pos]

        # Remplacement de macro #define si défini
        if name in self.macros:
            sub = self.macros[name]
            # Si le substitut est un simple nombre ou chaîne
            if sub.isdigit():
                return Token("NUMBER", int(sub), start_line, start_col)
            elif sub.startswith('"') and sub.endswith('"'):
                return Token("STRING", sub[1:-1], start_line, start_col)
            elif sub in ("true", "HIGH"):
                return Token("NUMBER", 1, start_line, start_col)
            elif sub in ("false", "LOW"):
                return Token("NUMBER", 0, start_line, start_col)

        if name in KEYWORDS:
            if name == "true":
                return Token("NUMBER", 1, start_line, start_col)
            elif name == "false":
                return Token("NUMBER", 0, start_line, start_col)
            return Token("KEYWORD", name, start_line, start_col)

        return Token("IDENTIFIER", name, start_line, start_col)
