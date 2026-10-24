"""
Interpréteur AST pour Arduino C / C++.
Exécute fidèlement le code Arduino en pilotant GPIOManager, ADCManager, PWMManager
et les composants connectés en direct sur la scène de simulation.
"""

from __future__ import annotations
import math
import random
import time
from typing import Any, Callable, Optional

from ..gpio import GPIOManager, GPIOMode, GPIOPull
from ..adc import ADCManager
from ..pwm import PWMManager
from .ast_nodes import (
    ASTNode, Program, Block, VarDecl, ClassInstanceDecl, FuncDef,
    ExprStmt, IfStmt, WhileStmt, DoWhileStmt, ForStmt, SwitchStmt,
    ReturnStmt, BreakStmt, ContinueStmt, Assignment, BinaryOp,
    UnaryOp, TernaryOp, CallExpr, MemberExpr, IndexExpr, Identifier,
    Literal, ArrayLiteral
)
from .libraries.servo import VirtualServo
from .libraries.liquidcrystal import VirtualLiquidCrystal


class ArduinoStopException(Exception):
    """Levée pour interrompre immédiatement l'exécution quand la simulation est stoppée."""
    pass


class ArduinoReturn(Exception):
    """Exception de contrôle de flux pour l'instruction 'return'."""
    def __init__(self, value: Any = None):
        self.value = value


class ArduinoBreak(Exception):
    """Exception de contrôle de flux pour l'instruction 'break'."""
    pass


class ArduinoContinue(Exception):
    """Exception de contrôle de flux pour l'instruction 'continue'."""
    pass


FORBIDDEN_ATTRIBUTES = {
    "__class__", "__bases__", "__subclasses__", "__globals__", "__dict__",
    "__builtins__", "__code__", "__closure__", "__mro__", "__reduce__",
    "__reduce_ex__", "__getattribute__", "__getattr__", "__setattr__",
    "__delattr__", "__init_subclass__", "__module__", "__name__", "__qualname__"
}


def is_forbidden_attribute(name: str) -> bool:
    """Vérifie si un nom d'attribut/méthode est privé, protégé ou dunder."""
    return bool(name and (name.startswith("_") or name in FORBIDDEN_ATTRIBUTES))


class ArduinoRuntimeError(Exception):
    """Erreur d'exécution avec localisation de ligne et colonne."""
    def __init__(self, message: str, line: int = 1, col: int = 1):
        super().__init__(f"{message} (Ligne {line}, Colonne {col})")
        self.message = message
        self.line = line
        self.col = col


class ArduinoSerial:
    """Objet Serial Arduino simulé."""

    def __init__(self, output_callback: Callable[[str], None]):
        self.output_callback = output_callback
        self.baud_rate = 9600
        self.rx_buffer: list[int] = []

    def begin(self, baud: int):
        self.baud_rate = int(baud)

    def print(self, val: Any):
        s = str(val)
        if isinstance(val, bool):
            s = "1" if val else "0"
        self.output_callback(s)

    def println(self, val: Any = ""):
        self.print(val)
        self.output_callback("\n")

    def write(self, val: Any) -> int:
        if isinstance(val, int):
            self.output_callback(chr(val))
        else:
            self.output_callback(str(val))
        return 1

    def available(self) -> int:
        return len(self.rx_buffer)

    def read(self) -> int:
        return self.rx_buffer.pop(0) if self.rx_buffer else -1


class ArduinoInterpreter:
    """Interpréteur exécutant un AST de sketch Arduino."""

    def __init__(
        self,
        gpio_manager: Optional[GPIOManager] = None,
        adc_manager: Optional[ADCManager] = None,
        pwm_manager: Optional[PWMManager] = None,
        board_profile: Optional[Any] = None,
        output_callback: Optional[Callable[[str], None]] = None,
        stop_check: Optional[Callable[[], bool]] = None
    ):
        self.gpio_manager = gpio_manager
        self.adc_manager = adc_manager
        self.pwm_manager = pwm_manager
        self.board_profile = board_profile or getattr(gpio_manager, "board_profile", None)
        self.output_callback = output_callback or (lambda s: print(s, end=""))
        self.stop_check = stop_check or (lambda: False)

        self.start_time: float = time.time()
        self.serial = ArduinoSerial(self.output_callback)

        # Environnements : variables globales et pile de portées locales
        self.globals: dict[str, Any] = {}
        self.functions: dict[str, FuncDef] = {}
        self.scope_stack: list[dict[str, Any]] = []

        self._init_builtins()

    def set_board_profile(self, profile: Any):
        """Met à jour le profil de carte actif et réaligne les constantes associées."""
        self.board_profile = profile
        if profile and getattr(profile, "built_in_led", None) is not None:
            self.globals["LED_BUILTIN"] = profile.built_in_led

    def _init_builtins(self):
        """Initialise les constantes et fonctions intégrées au langage Arduino."""
        builtin_led = 13
        if self.board_profile and getattr(self.board_profile, "built_in_led", None) is not None:
            builtin_led = self.board_profile.built_in_led

        self.globals.update({
            # Constantes de niveau logique
            "HIGH": 1,
            "LOW": 0,
            # Modes de broches
            "INPUT": 0,
            "OUTPUT": 1,
            "INPUT_PULLUP": 2,
            # Broches courantes
            "LED_BUILTIN": builtin_led,
            # Broches analogiques (Arduino Uno : A0=14 .. A5=19)
            "A0": 14,
            "A1": 15,
            "A2": 16,
            "A3": 17,
            "A4": 18,
            "A5": 19,
            # Booléens
            "true": 1,
            "false": 0,
            # Mathématiques
            "PI": math.pi,
            "HALF_PI": math.pi / 2.0,
            "TWO_PI": math.pi * 2.0,
            "DEG_TO_RAD": math.pi / 180.0,
            "RAD_TO_DEG": 180.0 / math.pi,
            # Objet Serial
            "Serial": self.serial,
        })

    def is_stopped(self) -> bool:
        return self.stop_check()

    def check_stop(self):
        if self.is_stopped():
            raise ArduinoStopException()

    # -------------------------------------------------------------------------
    # Gestion des portées de variables (Scopes)
    # -------------------------------------------------------------------------

    def push_scope(self):
        self.scope_stack.append({})

    def pop_scope(self):
        if self.scope_stack:
            self.scope_stack.pop()

    def declare_variable(self, name: str, value: Any):
        if self.scope_stack:
            self.scope_stack[-1][name] = value
        else:
            self.globals[name] = value

    def get_variable(self, name: str, line: int = 1, col: int = 1) -> Any:
        # 1. Chercher dans les scopes locaux du plus récent au plus ancien
        for scope in reversed(self.scope_stack):
            if name in scope:
                return scope[name]
        # 2. Chercher dans les globales
        if name in self.globals:
            return self.globals[name]
        # 3. Vérifier si c'est un nom de broche comme D13 ou GPIO13
        if (name.startswith("D") or name.startswith("GPIO")) and name[1:].isdigit():
            clean = name[4:] if name.startswith("GPIO") else name[1:]
            return int(clean)

        raise ArduinoRuntimeError(f"Variable ou identifiant '{name}' non défini", line, col)

    def set_variable(self, name: str, value: Any, line: int = 1, col: int = 1):
        for scope in reversed(self.scope_stack):
            if name in scope:
                scope[name] = value
                return
        if name in self.globals:
            self.globals[name] = value
            return
        # Si non trouvée, déclarer dans le scope actuel
        if self.scope_stack:
            self.scope_stack[-1][name] = value
        else:
            self.globals[name] = value

    # -------------------------------------------------------------------------
    # Exécution du cycle de vie Arduino (setup & loop)
    # -------------------------------------------------------------------------

    def run(self, program: Program):
        """Lance l'exécution complète du sketch (setup() puis boucle loop())."""
        self.start_time = time.time()

        # 1. Enregistrer toutes les fonctions et exécuter les déclarations globales
        for stmt in program.statements:
            self.check_stop()
            if isinstance(stmt, FuncDef):
                self.functions[stmt.name] = stmt
            else:
                self.execute_statement(stmt)

        # 2. Exécuter setup() une fois si présent
        if "setup" in self.functions:
            self.check_stop()
            self.call_function("setup", [])

        # 3. Exécuter loop() en boucle continue si présent
        if "loop" in self.functions:
            while not self.is_stopped():
                self.call_function("loop", [])
                # Laisser un court temps de respiration pour ne pas bloquer le thread UI
                time.sleep(0.001)

    # -------------------------------------------------------------------------
    # Exécution des instructions (Statements)
    # -------------------------------------------------------------------------

    def execute_statement(self, stmt: ASTNode):
        self.check_stop()

        if isinstance(stmt, Block):
            self.push_scope()
            try:
                for s in stmt.statements:
                    self.execute_statement(s)
            finally:
                self.pop_scope()

        elif isinstance(stmt, VarDecl):
            val = None
            if stmt.is_array:
                if stmt.array_elements is not None:
                    val = [self.evaluate_expression(elem) for elem in stmt.array_elements]
                elif stmt.array_size is not None:
                    size = int(self.evaluate_expression(stmt.array_size))
                    val = [0] * max(0, size)
                else:
                    val = []
            elif stmt.init is not None:
                val = self.evaluate_expression(stmt.init)
            else:
                # Valeur par défaut selon le type
                val = 0.0 if stmt.type_name in ("float", "double") else 0
            self.declare_variable(stmt.name, val)

        elif isinstance(stmt, ClassInstanceDecl):
            # Instanciation d'objets comme Servo ou LiquidCrystal
            evaluated_args = [self.evaluate_expression(a) for a in stmt.args]
            instance = self._instantiate_class(stmt.class_name, evaluated_args, stmt.line, stmt.col)
            self.declare_variable(stmt.name, instance)

        elif isinstance(stmt, ExprStmt):
            if stmt.expr:
                self.evaluate_expression(stmt.expr)

        elif isinstance(stmt, IfStmt):
            cond_val = self.evaluate_expression(stmt.condition)
            if self._is_truthy(cond_val):
                self.execute_statement(stmt.then_branch)
            elif stmt.else_branch:
                self.execute_statement(stmt.else_branch)

        elif isinstance(stmt, WhileStmt):
            while not self.is_stopped() and self._is_truthy(self.evaluate_expression(stmt.condition)):
                try:
                    self.execute_statement(stmt.body)
                except ArduinoBreak:
                    break
                except ArduinoContinue:
                    continue

        elif isinstance(stmt, DoWhileStmt):
            while not self.is_stopped():
                try:
                    self.execute_statement(stmt.body)
                except ArduinoBreak:
                    break
                except ArduinoContinue:
                    pass
                if not self._is_truthy(self.evaluate_expression(stmt.condition)):
                    break

        elif isinstance(stmt, ForStmt):
            self.push_scope()
            try:
                if stmt.init:
                    self.execute_statement(stmt.init)
                while not self.is_stopped():
                    if stmt.condition and not self._is_truthy(self.evaluate_expression(stmt.condition)):
                        break
                    try:
                        self.execute_statement(stmt.body)
                    except ArduinoBreak:
                        break
                    except ArduinoContinue:
                        pass
                    if stmt.step:
                        self.evaluate_expression(stmt.step)
            finally:
                self.pop_scope()

        elif isinstance(stmt, SwitchStmt):
            switch_val = self.evaluate_expression(stmt.expr)
            matched = False
            executed = False
            default_body = None

            for case_expr, case_body in stmt.cases:
                if case_expr is None:
                    default_body = case_body
                    continue
                if not matched:
                    c_val = self.evaluate_expression(case_expr)
                    if switch_val == c_val:
                        matched = True

                if matched:
                    try:
                        for s in case_body:
                            self.execute_statement(s)
                        executed = True
                    except ArduinoBreak:
                        executed = True
                        break

            if not executed and default_body:
                try:
                    for s in default_body:
                        self.execute_statement(s)
                except ArduinoBreak:
                    pass

        elif isinstance(stmt, ReturnStmt):
            ret_val = self.evaluate_expression(stmt.value) if stmt.value else None
            raise ArduinoReturn(ret_val)

        elif isinstance(stmt, BreakStmt):
            raise ArduinoBreak()

        elif isinstance(stmt, ContinueStmt):
            raise ArduinoContinue()

    # -------------------------------------------------------------------------
    # Évaluation des expressions
    # -------------------------------------------------------------------------

    def evaluate_expression(self, expr: ASTNode) -> Any:
        self.check_stop()

        if isinstance(expr, Literal):
            return expr.value

        elif isinstance(expr, Identifier):
            return self.get_variable(expr.name, expr.line, expr.col)

        elif isinstance(expr, ArrayLiteral):
            return [self.evaluate_expression(elem) for elem in expr.elements]

        elif isinstance(expr, Assignment):
            return self._eval_assignment(expr)

        elif isinstance(expr, UnaryOp):
            return self._eval_unary(expr)

        elif isinstance(expr, BinaryOp):
            return self._eval_binary(expr)

        elif isinstance(expr, TernaryOp):
            cond = self.evaluate_expression(expr.condition)
            return self.evaluate_expression(expr.true_expr) if self._is_truthy(cond) else self.evaluate_expression(expr.false_expr)

        elif isinstance(expr, CallExpr):
            return self._eval_call(expr)

        elif isinstance(expr, MemberExpr):
            if is_forbidden_attribute(expr.member_name):
                raise ArduinoRuntimeError(f"Accès refusé au membre protégé ou spécial '{expr.member_name}'", expr.line, expr.col)
            obj = self.evaluate_expression(expr.object_expr)
            if hasattr(obj, expr.member_name):
                return getattr(obj, expr.member_name)
            raise ArduinoRuntimeError(f"Membre '{expr.member_name}' inexistant sur l'objet", expr.line, expr.col)

        elif isinstance(expr, IndexExpr):
            arr = self.evaluate_expression(expr.array_expr)
            idx = int(self.evaluate_expression(expr.index_expr))
            if isinstance(arr, (list, tuple)):
                if 0 <= idx < len(arr):
                    return arr[idx]
                raise ArduinoRuntimeError(f"Index de tableau hors limites ({idx} >= {len(arr)})", expr.line, expr.col)
            elif isinstance(arr, str):
                if 0 <= idx < len(arr):
                    return arr[idx]
                raise ArduinoRuntimeError(f"Index de chaîne hors limites ({idx})", expr.line, expr.col)
            raise ArduinoRuntimeError("L'expression indexée n'est pas un tableau ou une chaîne", expr.line, expr.col)

        return None

    def _eval_assignment(self, expr: Assignment) -> Any:
        rhs_val = self.evaluate_expression(expr.value)

        # Cible : variable simple
        if isinstance(expr.target, Identifier):
            name = expr.target.name
            if expr.op == "=":
                final_val = rhs_val
            else:
                cur_val = self.get_variable(name, expr.line, expr.col)
                final_val = self._apply_binary_op(cur_val, expr.op[:-1], rhs_val, expr.line, expr.col)
            self.set_variable(name, final_val, expr.line, expr.col)
            return final_val

        # Cible : élément de tableau arr[idx] = val
        elif isinstance(expr.target, IndexExpr):
            arr = self.evaluate_expression(expr.target.array_expr)
            idx = int(self.evaluate_expression(expr.target.index_expr))
            if isinstance(arr, list):
                if 0 <= idx < len(arr):
                    if expr.op == "=":
                        arr[idx] = rhs_val
                    else:
                        arr[idx] = self._apply_binary_op(arr[idx], expr.op[:-1], rhs_val, expr.line, expr.col)
                    return arr[idx]
                raise ArduinoRuntimeError(f"Index {idx} hors limites pour l'assignation", expr.line, expr.col)

        # Cible : membre d'objet obj.member = val
        elif isinstance(expr.target, MemberExpr):
            if is_forbidden_attribute(expr.target.member_name):
                raise ArduinoRuntimeError(f"Accès refusé au membre protégé ou spécial '{expr.target.member_name}'", expr.line, expr.col)
            obj = self.evaluate_expression(expr.target.object_expr)
            if expr.op == "=":
                setattr(obj, expr.target.member_name, rhs_val)
            else:
                cur = getattr(obj, expr.target.member_name)
                setattr(obj, expr.target.member_name, self._apply_binary_op(cur, expr.op[:-1], rhs_val, expr.line, expr.col))
            return rhs_val

        raise ArduinoRuntimeError("Cible d'assignation invalide", expr.line, expr.col)

    def _eval_unary(self, expr: UnaryOp) -> Any:
        op = expr.op

        # Incrémentation et Décrémentation ++ et --
        if op in ("++", "--"):
            if not isinstance(expr.operand, Identifier):
                raise ArduinoRuntimeError(f"L'opérateur {op} requiert une variable lvalue", expr.line, expr.col)
            name = expr.operand.name
            cur_val = self.get_variable(name, expr.line, expr.col)
            delta = 1 if op == "++" else -1
            new_val = cur_val + delta
            self.set_variable(name, new_val, expr.line, expr.col)
            # Préfixe (++x) renvoie new_val, Postfixe (x++) renvoie cur_val
            return new_val if expr.is_prefix else cur_val

        val = self.evaluate_expression(expr.operand)
        if op == "-":
            return -val
        elif op == "+":
            return +val
        elif op == "!":
            return 0 if self._is_truthy(val) else 1
        elif op == "~":
            return ~int(val)

        return val

    def _eval_binary(self, expr: BinaryOp) -> Any:
        # Court-circuit pour && et ||
        if expr.op == "&&":
            left_val = self.evaluate_expression(expr.left)
            if not self._is_truthy(left_val):
                return 0
            right_val = self.evaluate_expression(expr.right)
            return 1 if self._is_truthy(right_val) else 0

        if expr.op == "||":
            left_val = self.evaluate_expression(expr.left)
            if self._is_truthy(left_val):
                return 1
            right_val = self.evaluate_expression(expr.right)
            return 1 if self._is_truthy(right_val) else 0

        left_val = self.evaluate_expression(expr.left)
        right_val = self.evaluate_expression(expr.right)
        return self._apply_binary_op(left_val, expr.op, right_val, expr.line, expr.col)

    def _apply_binary_op(self, left: Any, op: str, right: Any, line: int = 1, col: int = 1) -> Any:
        # Concaténation de chaînes
        if op == "+" and (isinstance(left, str) or isinstance(right, str)):
            return str(left) + str(right)

        if op == "+":
            return left + right
        elif op == "-":
            return left - right
        elif op == "*":
            return left * right
        elif op == "/":
            if right == 0:
                raise ArduinoRuntimeError("Division par zéro", line, col)
            return int(left // right) if isinstance(left, int) and isinstance(right, int) else left / right
        elif op == "%":
            if right == 0:
                raise ArduinoRuntimeError("Modulo par zéro", line, col)
            return left % right
        elif op == "==":
            return 1 if left == right else 0
        elif op == "!=":
            return 1 if left != right else 0
        elif op == "<":
            return 1 if left < right else 0
        elif op == "<=":
            return 1 if left <= right else 0
        elif op == ">":
            return 1 if left > right else 0
        elif op == ">=":
            return 1 if left >= right else 0
        elif op == "&":
            return int(left) & int(right)
        elif op == "|":
            return int(left) | int(right)
        elif op == "^":
            return int(left) ^ int(right)
        elif op == "<<":
            return int(left) << int(right)
        elif op == ">>":
            return int(left) >> int(right)

        raise ArduinoRuntimeError(f"Opérateur inconnu '{op}'", line, col)

    def _eval_call(self, expr: CallExpr) -> Any:
        args = [self.evaluate_expression(a) for a in expr.args]

        # Appel de membre : obj.method(...)
        if isinstance(expr.callee, MemberExpr):
            if is_forbidden_attribute(expr.callee.member_name):
                raise ArduinoRuntimeError(f"Accès refusé à la méthode protégée ou spéciale '{expr.callee.member_name}'", expr.line, expr.col)
            obj = self.evaluate_expression(expr.callee.object_expr)
            method_name = expr.callee.member_name
            if hasattr(obj, method_name):
                method = getattr(obj, method_name)
                return method(*args)
            raise ArduinoRuntimeError(f"Méthode '{method_name}' non trouvée sur l'objet", expr.line, expr.col)

        # Appel d'identifiant direct
        if isinstance(expr.callee, Identifier):
            name = expr.callee.name

            # 1. Fonctions matérielles Arduino intégrées
            if name == "pinMode":
                return self._builtin_pin_mode(*args)
            elif name == "digitalWrite":
                return self._builtin_digital_write(*args)
            elif name == "digitalRead":
                return self._builtin_digital_read(*args)
            elif name == "analogRead":
                return self._builtin_analog_read(*args)
            elif name == "analogWrite":
                return self._builtin_analog_write(*args)
            elif name == "delay":
                return self._builtin_delay(*args)
            elif name == "delayMicroseconds":
                return self._builtin_delay_us(*args)
            elif name == "millis":
                return int((time.time() - self.start_time) * 1000.0)
            elif name == "micros":
                return int((time.time() - self.start_time) * 1000000.0)
            elif name == "map":
                val, in_min, in_max, out_min, out_max = args
                if in_max == in_min:
                    return out_min
                return int((val - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)
            elif name == "constrain":
                val, low, high = args
                return max(low, min(high, val))
            elif name == "min":
                return min(args[0], args[1])
            elif name == "max":
                return max(args[0], args[1])
            elif name == "abs":
                return abs(args[0])
            elif name == "sq":
                return args[0] * args[0]
            elif name == "sqrt":
                return math.sqrt(args[0])
            elif name == "random":
                if len(args) == 1:
                    return random.randint(0, max(0, int(args[0]) - 1))
                elif len(args) >= 2:
                    return random.randint(int(args[0]), int(args[1]) - 1)
            elif name == "randomSeed":
                random.seed(int(args[0]))
                return None
            elif name in ("String", "int", "float", "long", "byte", "char", "boolean", "bool"):
                return self._cast_type(name, args)

            # 2. Fonctions définies par l'utilisateur
            if name in self.functions:
                return self.call_function(name, args)

            # 3. Variable stockant un callable
            try:
                fn = self.get_variable(name, expr.line, expr.col)
                if callable(fn):
                    return fn(*args)
            except ArduinoRuntimeError:
                pass

            raise ArduinoRuntimeError(f"Fonction '{name}' non définie", expr.line, expr.col)

        raise ArduinoRuntimeError("Expression non appelable", expr.line, expr.col)

    def call_function(self, name: str, args: list[Any]) -> Any:
        func_def = self.functions[name]
        self.push_scope()
        try:
            # Lier les arguments aux paramètres
            for idx, (p_type, p_name) in enumerate(func_def.params):
                val = args[idx] if idx < len(args) else 0
                if p_name:
                    self.declare_variable(p_name, val)

            # Exécuter le corps de la fonction
            if func_def.body:
                for stmt in func_def.body.statements:
                    self.execute_statement(stmt)
        except ArduinoReturn as ret:
            return ret.value
        finally:
            self.pop_scope()
        return None

    # -------------------------------------------------------------------------
    # Fonctions matérielles Arduino intégrées
    # -------------------------------------------------------------------------

    def _parse_pin_arg(self, pin_val: Any) -> int:
        if isinstance(pin_val, str):
            p_upper = pin_val.upper()
            if p_upper.startswith("A") and p_upper[1:].isdigit():
                return 14 + int(p_upper[1:])
            elif p_upper.startswith("D") and p_upper[1:].isdigit():
                return int(p_upper[1:])
            elif p_upper.startswith("GPIO") and p_upper[4:].isdigit():
                return int(p_upper[4:])
            elif p_upper.isdigit():
                return int(p_upper)
            return 13
        return int(pin_val)

    def _builtin_pin_mode(self, pin: Any, mode: Any):
        pin_num = self._parse_pin_arg(pin)
        mode_val = int(mode)
        if self.gpio_manager:
            if mode_val == 1:
                self.gpio_manager.configure(pin_num, GPIOMode.OUT, GPIOPull.PULL_NONE)
            elif mode_val == 2:
                self.gpio_manager.configure(pin_num, GPIOMode.IN, GPIOPull.PULL_UP)
            else:
                self.gpio_manager.configure(pin_num, GPIOMode.IN, GPIOPull.PULL_NONE)

    def _builtin_digital_write(self, pin: Any, val: Any):
        pin_num = self._parse_pin_arg(pin)
        logic_val = 1 if self._is_truthy(val) else 0
        if self.gpio_manager:
            self.gpio_manager.write(pin_num, logic_val)

    def _builtin_digital_read(self, pin: Any) -> int:
        pin_num = self._parse_pin_arg(pin)
        if self.gpio_manager:
            return 1 if self.gpio_manager.read(pin_num) else 0
        return 0

    def _builtin_analog_read(self, pin: Any) -> int:
        # En Arduino Uno, analogRead(0) équivaut à analogRead(A0)
        if isinstance(pin, int) and 0 <= pin <= 5:
            pin_num = 14 + pin
        else:
            pin_num = self._parse_pin_arg(pin)

        if self.adc_manager:
            return self.adc_manager.read(pin_num)
        return 0

    def _builtin_analog_write(self, pin: Any, val: Any):
        pin_num = self._parse_pin_arg(pin)
        duty_val = max(0, min(255, int(val)))
        if self.pwm_manager:
            try:
                self.pwm_manager.configure(pin_num)
                max_duty = getattr(self.board_profile, "pwm_max_duty", 255) if self.board_profile else 255
                if max_duty > 0 and max_duty != 255:
                    scaled_duty = int(round(duty_val * max_duty / 255.0))
                else:
                    scaled_duty = duty_val
                self.pwm_manager.set_duty(pin_num, scaled_duty)
            except Exception:
                pass

    def _builtin_delay(self, ms: Any):
        ms_val = max(0, float(ms))
        end_time = time.time() + (ms_val / 1000.0)
        while time.time() < end_time:
            self.check_stop()
            time.sleep(min(0.01, end_time - time.time()))

    def _builtin_delay_us(self, us: Any):
        us_val = max(0, float(us))
        end_time = time.time() + (us_val / 1000000.0)
        while time.time() < end_time:
            self.check_stop()
            time.sleep(min(0.001, end_time - time.time()))

    def _cast_type(self, type_name: str, args: list[Any]) -> Any:
        arg = args[0] if args else 0
        if type_name == "String":
            return str(arg)
        elif type_name in ("int", "long", "byte"):
            try:
                return int(float(arg))
            except Exception:
                return 0
        elif type_name in ("float", "double"):
            try:
                return float(arg)
            except Exception:
                return 0.0
        elif type_name in ("bool", "boolean"):
            return 1 if self._is_truthy(arg) else 0
        elif type_name == "char":
            return str(arg)[0] if str(arg) else '\0'
        return arg

    def _instantiate_class(self, class_name: str, args: list[Any], line: int, col: int) -> Any:
        if class_name == "Servo":
            return VirtualServo(gpio_manager=self.gpio_manager, pwm_manager=self.pwm_manager)
        elif class_name == "LiquidCrystal":
            return VirtualLiquidCrystal(*args)
        raise ArduinoRuntimeError(f"Classe inconnue '{class_name}'", line, col)

    def _is_truthy(self, val: Any) -> bool:
        if isinstance(val, (int, float)):
            return val != 0
        return bool(val)
