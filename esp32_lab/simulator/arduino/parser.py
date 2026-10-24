"""
Parseur récursif descendant pour Arduino C / C++.
Transforme une liste de tokens en un Arbre Syntaxique Abstrait (AST).
"""

from __future__ import annotations
from typing import Optional, Any
from .lexer import Token, ArduinoLexer
from .ast_nodes import (
    ASTNode, Program, Block, VarDecl, ClassInstanceDecl, FuncDef,
    ExprStmt, IfStmt, WhileStmt, DoWhileStmt, ForStmt, SwitchStmt,
    ReturnStmt, BreakStmt, ContinueStmt, Assignment, BinaryOp,
    UnaryOp, TernaryOp, CallExpr, MemberExpr, IndexExpr, Identifier,
    Literal, ArrayLiteral
)

TYPE_NAMES = {
    "void", "int", "long", "float", "double", "bool", "boolean", "char",
    "byte", "uint8_t", "uint16_t", "uint32_t", "int8_t", "int16_t", "int32_t",
    "unsigned", "signed", "short", "String", "Servo", "LiquidCrystal"
}

ASSIGN_OPS = {"=", "+=", "-=", "*=", "/=", "%=", "&=", "|=", "^=", "<<=", ">>="}

FORBIDDEN_ATTRIBUTES = {
    "__class__", "__bases__", "__subclasses__", "__globals__", "__dict__",
    "__builtins__", "__code__", "__closure__", "__mro__", "__reduce__",
    "__reduce_ex__", "__getattribute__", "__getattr__", "__setattr__",
    "__delattr__", "__init_subclass__", "__module__", "__name__", "__qualname__"
}


class ArduinoParser:
    """Parseur syntaxique de code Arduino C/C++."""

    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0

    def parse(self) -> Program:
        """Parse le programme complet et renvoie le nœud racine Program."""
        prog = Program()
        while not self.is_at_end():
            # Ignorer les points-virgules esseulés
            if self.match_del(";"):
                continue
            decl = self.parse_top_level_declaration()
            if decl:
                prog.statements.append(decl)
        return prog

    # -------------------------------------------------------------------------
    # Navigation dans le flux de tokens
    # -------------------------------------------------------------------------

    def peek(self, offset: int = 0) -> Token:
        idx = self.pos + offset
        if idx >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[idx]

    def is_at_end(self) -> bool:
        return self.peek().type == "EOF"

    def advance(self) -> Token:
        if not self.is_at_end():
            self.pos += 1
        return self.tokens[self.pos - 1]

    def check(self, token_type: str, value: Any = None) -> bool:
        if self.is_at_end():
            return False
        tok = self.peek()
        if tok.type != token_type:
            return False
        if value is not None and tok.value != value:
            return False
        return True

    def check_del(self, delim: str) -> bool:
        return self.check("DELIMITER", delim)

    def check_op(self, op: str) -> bool:
        return self.check("OPERATOR", op)

    def match_del(self, delim: str) -> bool:
        if self.check_del(delim):
            self.advance()
            return True
        return False

    def match_op(self, op: str) -> bool:
        if self.check_op(op):
            self.advance()
            return True
        return False

    def consume(self, token_type: str, value: Any = None, err_msg: str = "") -> Token:
        tok = self.peek()
        if self.check(token_type, value):
            return self.advance()
        msg = err_msg or f"Attendu '{value or token_type}', trouvé '{tok.value}'"
        raise SyntaxError(f"{msg} (Ligne {tok.line}, Colonne {tok.col})")

    def consume_del(self, delim: str, err_msg: str = "") -> Token:
        return self.consume("DELIMITER", delim, err_msg or f"Attendu '{delim}'")

    def is_type_name(self, tok: Token, next_tok: Optional[Token] = None) -> bool:
        if tok.value == "Serial":
            return False
        if tok.value in TYPE_NAMES:
            return True
        if tok.type == "KEYWORD" and tok.value in ("unsigned", "signed", "const", "static"):
            return True
        # Un nom de classe utilisateur n'est un type que s'il est suivi d'un identifiant de variable
        if tok.type == "IDENTIFIER" and tok.value and tok.value[0].isupper():
            if next_tok and next_tok.type == "IDENTIFIER":
                return True
        return False

    # -------------------------------------------------------------------------
    # Analyse de haut niveau (Fonctions & Variables globales)
    # -------------------------------------------------------------------------

    def parse_top_level_declaration(self) -> Optional[ASTNode]:
        tok = self.peek()

        # Modificateurs optionnels: const, static, unsigned
        is_const = False
        while self.peek().value in ("const", "static"):
            if self.advance().value == "const":
                is_const = True

        if self.is_type_name(self.peek(), self.peek(1)):
            type_str = self._parse_full_type_name()
            # Prochain token: identifiant du nom
            if self.check("IDENTIFIER"):
                name_tok = self.advance()
                name = name_tok.value

                # 1. Fonction ou déclaration d'instance avec arguments (LiquidCrystal lcd(...);)
                if self.check_del("("):
                    if self._is_func_def_ahead():
                        return self._finish_function_definition(type_str, name, name_tok.line, name_tok.col)
                    else:
                        return self._finish_var_or_instance_decl(type_str, name, is_const, name_tok.line, name_tok.col)

                # 2. Variable globale / Tableau / Instance de classe par défaut
                return self._finish_var_or_instance_decl(type_str, name, is_const, name_tok.line, name_tok.col)
            else:
                raise SyntaxError(f"Nom de variable ou fonction attendu après le type '{type_str}' (Ligne {tok.line})")

        # Autre déclaration ou expression
        return self.parse_statement()

    def _parse_full_type_name(self) -> str:
        parts = []
        while not self.is_at_end():
            tok = self.peek()
            if tok.value in ("unsigned", "signed", "const", "static") or self.is_type_name(tok):
                parts.append(str(self.advance().value))
            elif tok.value == "*":  # Pointeur
                parts.append("*")
                self.advance()
            else:
                break
        return " ".join(parts) if parts else "int"

    def _is_func_def_ahead(self) -> bool:
        idx = self.pos + 1
        depth = 1
        while idx < len(self.tokens):
            tok = self.tokens[idx]
            if tok.type == "DELIMITER" and tok.value == "(":
                depth += 1
            elif tok.type == "DELIMITER" and tok.value == ")":
                depth -= 1
                if depth == 0:
                    next_tok = self.tokens[idx + 1] if idx + 1 < len(self.tokens) else None
                    if next_tok and next_tok.type == "DELIMITER" and next_tok.value == "{":
                        return True
                    return False
            idx += 1
        return False

    def _finish_function_definition(self, ret_type: str, name: str, line: int, col: int) -> FuncDef:
        self.consume_del("(")
        params: list[tuple[str, str]] = []
        if not self.check_del(")"):
            while True:
                p_type = self._parse_full_type_name()
                p_name = ""
                if self.check("IDENTIFIER"):
                    p_name = self.advance().value
                params.append((p_type, p_name))
                if not self.match_del(","):
                    break
        self.consume_del(")")

        # Si prototype suivi de ';' au lieu de corps
        if self.match_del(";"):
            return FuncDef(ret_type, name, params, None, line=line, col=col)

        # Corps de la fonction { ... }
        body = self.parse_block()
        return FuncDef(ret_type, name, params, body, line=line, col=col)

    def _finish_var_or_instance_decl(self, type_name: str, name: str, is_const: bool, line: int, col: int) -> ASTNode:
        # Cas 1 : Tableau : type name[size] = { ... };
        if self.match_del("["):
            size_expr = None
            if not self.check_del("]"):
                size_expr = self.parse_expression()
            self.consume_del("]")

            array_inits = None
            if self.match_op("="):
                array_inits = self._parse_array_initializer()
            self.match_del(";")
            return VarDecl(type_name, name, None, is_const=is_const, is_array=True, array_size=size_expr, array_elements=array_inits, line=line, col=col)

        # Cas 2 : Instance d'objet avec constructeur : Servo s; ou LiquidCrystal lcd(12, 11, 5, 4, 3, 2);
        if self.match_del("("):
            args = []
            if not self.check_del(")"):
                while True:
                    args.append(self.parse_expression())
                    if not self.match_del(","):
                        break
            self.consume_del(")")
            self.match_del(";")
            return ClassInstanceDecl(type_name, name, args, line=line, col=col)

        # Cas 3 : Variable simple : type name = init; ou type name;
        init_expr = None
        if self.match_op("="):
            init_expr = self.parse_expression()
        self.match_del(";")
        if type_name in ("Servo", "LiquidCrystal") or (type_name and type_name[0].isupper() and type_name not in TYPE_NAMES):
            return ClassInstanceDecl(type_name, name, [], line=line, col=col)
        return VarDecl(type_name, name, init_expr, is_const=is_const, line=line, col=col)

    def _parse_array_initializer(self) -> list[ASTNode]:
        self.consume_del("{")
        elements = []
        if not self.check_del("}"):
            while True:
                elements.append(self.parse_expression())
                if not self.match_del(","):
                    break
                if self.check_del("}"):  # Autoriser la virgule finale {1, 2, 3,}
                    break
        self.consume_del("}")
        return elements

    # -------------------------------------------------------------------------
    # Instructions (Statements)
    # -------------------------------------------------------------------------

    def parse_statement(self) -> ASTNode:
        tok = self.peek()

        # Bloc { ... }
        if self.check_del("{"):
            return self.parse_block()

        # if / else
        if tok.type == "KEYWORD" and tok.value == "if":
            return self.parse_if()

        # while
        if tok.type == "KEYWORD" and tok.value == "while":
            return self.parse_while()

        # do ... while
        if tok.type == "KEYWORD" and tok.value == "do":
            return self.parse_do_while()

        # for
        if tok.type == "KEYWORD" and tok.value == "for":
            return self.parse_for()

        # switch
        if tok.type == "KEYWORD" and tok.value == "switch":
            return self.parse_switch()

        # return
        if tok.type == "KEYWORD" and tok.value == "return":
            self.advance()
            val = None
            if not self.check_del(";"):
                val = self.parse_expression()
            self.match_del(";")
            return ReturnStmt(val, line=tok.line, col=tok.col)

        # break
        if tok.type == "KEYWORD" and tok.value == "break":
            self.advance()
            self.match_del(";")
            return BreakStmt(line=tok.line, col=tok.col)

        # continue
        if tok.type == "KEYWORD" and tok.value == "continue":
            self.advance()
            self.match_del(";")
            return ContinueStmt(line=tok.line, col=tok.col)

        # Déclaration de variable locale (si commence par un type)
        if self.is_type_name(tok, self.peek(1)):
            type_str = self._parse_full_type_name()
            if self.check("IDENTIFIER"):
                name_tok = self.advance()
                return self._finish_var_or_instance_decl(type_str, name_tok.value, False, name_tok.line, name_tok.col)

        # Expression statement (ex: digitalWrite(13, HIGH); ou x++;)
        expr = self.parse_expression()
        self.match_del(";")
        return ExprStmt(expr, line=tok.line, col=tok.col)

    def parse_block(self) -> Block:
        tok = self.consume_del("{")
        statements = []
        while not self.is_at_end() and not self.check_del("}"):
            if self.match_del(";"):
                continue
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)
        self.consume_del("}")
        return Block(statements, line=tok.line, col=tok.col)

    def parse_if(self) -> IfStmt:
        tok = self.consume("KEYWORD", "if")
        self.consume_del("(")
        cond = self.parse_expression()
        self.consume_del(")")
        then_branch = self.parse_statement()
        else_branch = None
        if self.peek().type == "KEYWORD" and self.peek().value == "else":
            self.advance()
            else_branch = self.parse_statement()
        return IfStmt(cond, then_branch, else_branch, line=tok.line, col=tok.col)

    def parse_while(self) -> WhileStmt:
        tok = self.consume("KEYWORD", "while")
        self.consume_del("(")
        cond = self.parse_expression()
        self.consume_del(")")
        body = self.parse_statement()
        return WhileStmt(cond, body, line=tok.line, col=tok.col)

    def parse_do_while(self) -> DoWhileStmt:
        tok = self.consume("KEYWORD", "do")
        body = self.parse_statement()
        self.consume("KEYWORD", "while")
        self.consume_del("(")
        cond = self.parse_expression()
        self.consume_del(")")
        self.match_del(";")
        return DoWhileStmt(body, cond, line=tok.line, col=tok.col)

    def parse_for(self) -> ForStmt:
        tok = self.consume("KEYWORD", "for")
        self.consume_del("(")

        # Initialisation : peut être une déclaration ou une expression ou vide
        init_node = None
        if not self.check_del(";"):
            if self.is_type_name(self.peek()):
                type_str = self._parse_full_type_name()
                name_tok = self.consume("IDENTIFIER")
                init_node = self._finish_var_or_instance_decl(type_str, name_tok.value, False, name_tok.line, name_tok.col)
            else:
                init_node = self.parse_expression()
                self.consume_del(";")
        else:
            self.consume_del(";")

        # Condition
        cond_node = None
        if not self.check_del(";"):
            cond_node = self.parse_expression()
        self.consume_del(";")

        # Pas / Step
        step_node = None
        if not self.check_del(")"):
            step_node = self.parse_expression()
        self.consume_del(")")

        body = self.parse_statement()
        return ForStmt(init_node, cond_node, step_node, body, line=tok.line, col=tok.col)

    def parse_switch(self) -> SwitchStmt:
        tok = self.consume("KEYWORD", "switch")
        self.consume_del("(")
        expr = self.parse_expression()
        self.consume_del(")")
        self.consume_del("{")

        cases: list[tuple[Optional[ASTNode], list[ASTNode]]] = []
        while not self.is_at_end() and not self.check_del("}"):
            if self.peek().type == "KEYWORD" and self.peek().value == "case":
                self.advance()
                case_val = self.parse_expression()
                self.consume("OPERATOR", ":")
                case_body = []
                while not self.is_at_end() and not (self.peek().type == "KEYWORD" and self.peek().value in ("case", "default")) and not self.check_del("}"):
                    case_body.append(self.parse_statement())
                cases.append((case_val, case_body))
            elif self.peek().type == "KEYWORD" and self.peek().value == "default":
                self.advance()
                self.consume("OPERATOR", ":")
                default_body = []
                while not self.is_at_end() and not (self.peek().type == "KEYWORD" and self.peek().value in ("case", "default")) and not self.check_del("}"):
                    default_body.append(self.parse_statement())
                cases.append((None, default_body))
            else:
                self.advance()

        self.consume_del("}")
        return SwitchStmt(expr, cases, line=tok.line, col=tok.col)

    # -------------------------------------------------------------------------
    # Expressions (Priorité des opérateurs)
    # -------------------------------------------------------------------------

    def parse_expression(self) -> ASTNode:
        return self.parse_assignment()

    def parse_assignment(self) -> ASTNode:
        expr = self.parse_ternary()

        if self.peek().type == "OPERATOR" and self.peek().value in ASSIGN_OPS:
            op_tok = self.advance()
            val = self.parse_assignment()
            return Assignment(expr, op_tok.value, val, line=op_tok.line, col=op_tok.col)

        return expr

    def parse_ternary(self) -> ASTNode:
        expr = self.parse_logical_or()
        if self.match_op("?"):
            true_expr = self.parse_expression()
            self.consume("OPERATOR", ":")
            false_expr = self.parse_ternary()
            return TernaryOp(expr, true_expr, false_expr, line=expr.line, col=expr.col)
        return expr

    def parse_logical_or(self) -> ASTNode:
        expr = self.parse_logical_and()
        while self.match_op("||"):
            right = self.parse_logical_and()
            expr = BinaryOp(expr, "||", right, line=expr.line, col=expr.col)
        return expr

    def parse_logical_and(self) -> ASTNode:
        expr = self.parse_bitwise_or()
        while self.match_op("&&"):
            right = self.parse_bitwise_or()
            expr = BinaryOp(expr, "&&", right, line=expr.line, col=expr.col)
        return expr

    def parse_bitwise_or(self) -> ASTNode:
        expr = self.parse_bitwise_xor()
        while self.match_op("|"):
            right = self.parse_bitwise_xor()
            expr = BinaryOp(expr, "|", right, line=expr.line, col=expr.col)
        return expr

    def parse_bitwise_xor(self) -> ASTNode:
        expr = self.parse_bitwise_and()
        while self.match_op("^"):
            right = self.parse_bitwise_and()
            expr = BinaryOp(expr, "^", right, line=expr.line, col=expr.col)
        return expr

    def parse_bitwise_and(self) -> ASTNode:
        expr = self.parse_equality()
        while self.match_op("&"):
            right = self.parse_equality()
            expr = BinaryOp(expr, "&", right, line=expr.line, col=expr.col)
        return expr

    def parse_equality(self) -> ASTNode:
        expr = self.parse_relational()
        while self.peek().type == "OPERATOR" and self.peek().value in ("==", "!="):
            op = self.advance().value
            right = self.parse_relational()
            expr = BinaryOp(expr, op, right, line=expr.line, col=expr.col)
        return expr

    def parse_relational(self) -> ASTNode:
        expr = self.parse_shift()
        while self.peek().type == "OPERATOR" and self.peek().value in ("<", "<=", ">", ">="):
            op = self.advance().value
            right = self.parse_shift()
            expr = BinaryOp(expr, op, right, line=expr.line, col=expr.col)
        return expr

    def parse_shift(self) -> ASTNode:
        expr = self.parse_additive()
        while self.peek().type == "OPERATOR" and self.peek().value in ("<<", ">>"):
            op = self.advance().value
            right = self.parse_additive()
            expr = BinaryOp(expr, op, right, line=expr.line, col=expr.col)
        return expr

    def parse_additive(self) -> ASTNode:
        expr = self.parse_multiplicative()
        while self.peek().type == "OPERATOR" and self.peek().value in ("+", "-"):
            op = self.advance().value
            right = self.parse_multiplicative()
            expr = BinaryOp(expr, op, right, line=expr.line, col=expr.col)
        return expr

    def parse_multiplicative(self) -> ASTNode:
        expr = self.parse_unary()
        while self.peek().type == "OPERATOR" and self.peek().value in ("*", "/", "%"):
            op = self.advance().value
            right = self.parse_unary()
            expr = BinaryOp(expr, op, right, line=expr.line, col=expr.col)
        return expr

    def parse_unary(self) -> ASTNode:
        tok = self.peek()
        # Préfixe : !, ~, -, +, ++, --
        if tok.type == "OPERATOR" and tok.value in ("!", "~", "-", "+", "++", "--"):
            op = self.advance().value
            operand = self.parse_unary()
            return UnaryOp(op, operand, is_prefix=True, line=tok.line, col=tok.col)
        return self.parse_postfix()

    def parse_postfix(self) -> ASTNode:
        expr = self.parse_primary()

        while True:
            # Appel de fonction: expr(arg1, arg2)
            if self.match_del("("):
                args = []
                if not self.check_del(")"):
                    while True:
                        args.append(self.parse_expression())
                        if not self.match_del(","):
                            break
                self.consume_del(")")
                expr = CallExpr(expr, args, line=expr.line, col=expr.col)

            # Accès à un membre: expr.member ou expr->member
            elif self.match_op(".") or self.match_op("->"):
                member_tok = self.consume("IDENTIFIER", err_msg="Nom de membre attendu après '.'")
                if member_tok.value.startswith("_") or member_tok.value in FORBIDDEN_ATTRIBUTES:
                    raise SyntaxError(f"Accès refusé au membre protégé ou spécial '{member_tok.value}' (Ligne {member_tok.line})")
                expr = MemberExpr(expr, member_tok.value, line=expr.line, col=expr.col)

            # Indexation de tableau: expr[index]
            elif self.match_del("["):
                idx_expr = self.parse_expression()
                self.consume_del("]")
                expr = IndexExpr(expr, idx_expr, line=expr.line, col=expr.col)

            # Postfixe ++ ou --
            elif self.peek().type == "OPERATOR" and self.peek().value in ("++", "--"):
                op = self.advance().value
                expr = UnaryOp(op, expr, is_prefix=False, line=expr.line, col=expr.col)

            else:
                break

        return expr

    def parse_primary(self) -> ASTNode:
        tok = self.peek()

        # Parenthèses (expr)
        if self.match_del("("):
            # Vérifier si c'est un cast de type, ex: (int)val ou (float)val
            if self.is_type_name(self.peek()):
                type_name = self._parse_full_type_name()
                self.consume_del(")")
                inner = self.parse_unary()
                return CallExpr(Identifier(type_name, line=tok.line, col=tok.col), [inner], line=tok.line, col=tok.col)
            expr = self.parse_expression()
            self.consume_del(")")
            return expr

        # Nombre
        if tok.type == "NUMBER":
            self.advance()
            hint = "float" if isinstance(tok.value, float) else "int"
            return Literal(tok.value, hint, line=tok.line, col=tok.col)

        # Chaîne
        if tok.type == "STRING":
            self.advance()
            return Literal(tok.value, "string", line=tok.line, col=tok.col)

        # Caractère
        if tok.type == "CHAR":
            self.advance()
            return Literal(tok.value, "char", line=tok.line, col=tok.col)

        # Identifiant ou appel de type
        if tok.type in ("IDENTIFIER", "KEYWORD"):
            name = self.advance().value
            return Identifier(name, line=tok.line, col=tok.col)

        # Accolades {1, 2, 3} comme tableau littéral
        if self.check_del("{"):
            elements = self._parse_array_initializer()
            return ArrayLiteral(elements, line=tok.line, col=tok.col)

        raise SyntaxError(f"Expression inattendue '{tok.value}' (Ligne {tok.line}, Colonne {tok.col})")
