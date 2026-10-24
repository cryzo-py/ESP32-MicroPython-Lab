"""
Nœuds AST pour le parseur de code Arduino C / C++.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional


class ASTNode:
    """Classe de base pour tous les nœuds de l'AST."""
    line: int = 1
    col: int = 1


@dataclass
class Program(ASTNode):
    statements: list[ASTNode] = field(default_factory=list)
    line: int = 1
    col: int = 1


@dataclass
class Block(ASTNode):
    statements: list[ASTNode] = field(default_factory=list)
    line: int = 1
    col: int = 1


@dataclass
class VarDecl(ASTNode):
    type_name: str = "int"
    name: str = ""
    init: Optional[ASTNode] = None
    is_const: bool = False
    is_array: bool = False
    array_size: Optional[ASTNode] = None
    array_elements: Optional[list[ASTNode]] = None
    line: int = 1
    col: int = 1


@dataclass
class ClassInstanceDecl(ASTNode):
    class_name: str = ""
    name: str = ""
    args: list[ASTNode] = field(default_factory=list)
    line: int = 1
    col: int = 1


@dataclass
class FuncDef(ASTNode):
    return_type: str = "void"
    name: str = ""
    params: list[tuple[str, str]] = field(default_factory=list)  # [(type, name)]
    body: Optional[Block] = None
    line: int = 1
    col: int = 1


@dataclass
class ExprStmt(ASTNode):
    expr: Optional[ASTNode] = None
    line: int = 1
    col: int = 1


@dataclass
class IfStmt(ASTNode):
    condition: Optional[ASTNode] = None
    then_branch: Optional[ASTNode] = None
    else_branch: Optional[ASTNode] = None
    line: int = 1
    col: int = 1


@dataclass
class WhileStmt(ASTNode):
    condition: Optional[ASTNode] = None
    body: Optional[ASTNode] = None
    line: int = 1
    col: int = 1


@dataclass
class DoWhileStmt(ASTNode):
    body: Optional[ASTNode] = None
    condition: Optional[ASTNode] = None
    line: int = 1
    col: int = 1


@dataclass
class ForStmt(ASTNode):
    init: Optional[ASTNode] = None
    condition: Optional[ASTNode] = None
    step: Optional[ASTNode] = None
    body: Optional[ASTNode] = None
    line: int = 1
    col: int = 1


@dataclass
class SwitchStmt(ASTNode):
    expr: Optional[ASTNode] = None
    cases: list[tuple[Optional[ASTNode], list[ASTNode]]] = field(default_factory=list)
    line: int = 1
    col: int = 1


@dataclass
class ReturnStmt(ASTNode):
    value: Optional[ASTNode] = None
    line: int = 1
    col: int = 1


@dataclass
class BreakStmt(ASTNode):
    line: int = 1
    col: int = 1


@dataclass
class ContinueStmt(ASTNode):
    line: int = 1
    col: int = 1


@dataclass
class Assignment(ASTNode):
    target: Optional[ASTNode] = None
    op: str = "="
    value: Optional[ASTNode] = None
    line: int = 1
    col: int = 1


@dataclass
class BinaryOp(ASTNode):
    left: Optional[ASTNode] = None
    op: str = "+"
    right: Optional[ASTNode] = None
    line: int = 1
    col: int = 1


@dataclass
class UnaryOp(ASTNode):
    op: str = "-"
    operand: Optional[ASTNode] = None
    is_prefix: bool = True
    line: int = 1
    col: int = 1


@dataclass
class TernaryOp(ASTNode):
    condition: Optional[ASTNode] = None
    true_expr: Optional[ASTNode] = None
    false_expr: Optional[ASTNode] = None
    line: int = 1
    col: int = 1


@dataclass
class CallExpr(ASTNode):
    callee: Optional[ASTNode] = None
    args: list[ASTNode] = field(default_factory=list)
    line: int = 1
    col: int = 1


@dataclass
class MemberExpr(ASTNode):
    object_expr: Optional[ASTNode] = None
    member_name: str = ""
    line: int = 1
    col: int = 1


@dataclass
class IndexExpr(ASTNode):
    array_expr: Optional[ASTNode] = None
    index_expr: Optional[ASTNode] = None
    line: int = 1
    col: int = 1


@dataclass
class Identifier(ASTNode):
    name: str = ""
    line: int = 1
    col: int = 1


@dataclass
class Literal(ASTNode):
    value: Any = None
    type_hint: str = "auto"
    line: int = 1
    col: int = 1


@dataclass
class ArrayLiteral(ASTNode):
    elements: list[ASTNode] = field(default_factory=list)
    line: int = 1
    col: int = 1
