"""
Zafira Language - Type Checker (Statik Tip Tekshiruvi)
Muallif: Jasper & Antigravity

Qoidalari:
1. AST daraxtini bir marta aylanib chiqadi (single-pass).
2. 'seal' deb belgilangan funksiyalarda:
   - Parametrlar tiplarini tekshiradi
   - Return turi mos kelishini tekshiradi
   - 'where' invariantini statik tekshiradi (imkon qadar)
3. 'const' o'zgaruvchilarga qayta tayinlashni aniqlaydi.
4. Aniqlanmagan o'zgaruvchilarni (undeclared variables) oldindan aniqlaydi / bashorat qiladi.
5. 'draft' funksiyalar erkin dinamik rejimda bo'lgani uchun tekshiruvdan o'tkazib yuboriladi.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set, Tuple
import difflib
import os

from src.parser import (
    Program, Node, NumberLiteral, StringLiteral, BoolLiteral, NullLiteral,
    Identifier, BinaryOp, UnaryOp, FunctionCall, MemberAccess, IndexAccess,
    ListLiteral, RangeExpr, LetStatement, ConstStatement, AssignStatement,
    ReturnStatement, IfStatement, WhileStatement, ForStatement, FunctionDef,
    StructDef, ImplBlock, ImportStatement, RunBlock, ExprStatement, Block, AwaitExpr,
    TryStatement, ThrowStatement, MatchExpr, MatchArm, Wildcard
)


class TypeCheckError(Exception):
    """Zafira tili tip xatoligi istisnosi"""
    pass


# Zafira tilining asosiy tiplari
VALID_TYPES = {'Int', 'Float', 'String', 'Bool', 'List', 'Null', 'Any', 'Task', 'Future'}


def is_type_compatible(expected: str, actual: str, struct_names: Optional[Set[str]] = None) -> bool:
    """Ikkita tipning o'zaro mosligini tekshiradi."""
    if expected == 'Any' or actual == 'Any':
        return True
    if expected == actual:
        return True
    # Int Float ga kengayishi mumkin (numeric widening)
    if expected == 'Float' and actual == 'Int':
        return True
    if struct_names and expected in struct_names and actual == expected:
        return True
    return False


def node_to_str(node: Node) -> str:
    """AST tugunini o'qilishi oson satr ko'rinishiga keltiradi."""
    if isinstance(node, Identifier):
        return node.name
    if isinstance(node, NumberLiteral):
        return str(node.value)
    if isinstance(node, StringLiteral):
        return f'"{node.value}"'
    if isinstance(node, BoolLiteral):
        return 'true' if node.value else 'false'
    if isinstance(node, NullLiteral):
        return 'null'
    if isinstance(node, BinaryOp):
        return f"{node_to_str(node.left)} {node.op} {node_to_str(node.right)}"
    if isinstance(node, UnaryOp):
        return f"{node.op} {node_to_str(node.operand)}"
    if isinstance(node, AwaitExpr):
        return f"await {node_to_str(node.expr)}"
    if isinstance(node, ThrowStatement):
        return f"throw {node_to_str(node.expr)}"
    return str(type(node).__name__)


def eval_static(node: Node, env: Dict[str, Any]) -> Any:
    """Iborani (expression) imkon qadar statik hisoblaydi.
    Agar dinamik yoki noma'lum qiymat uchrasa, None qaytaradi."""
    if isinstance(node, NumberLiteral):
        return node.value
    if isinstance(node, StringLiteral):
        return node.value
    if isinstance(node, BoolLiteral):
        return node.value
    if isinstance(node, NullLiteral):
        return None
    if isinstance(node, Identifier):
        return env.get(node.name, None)
    if isinstance(node, AwaitExpr):
        return eval_static(node.expr, env)
    if isinstance(node, UnaryOp):
        val = eval_static(node.operand, env)
        if val is not None:
            if node.op == '-':
                return -val
            if node.op == 'not':
                return not val
        return None
    if isinstance(node, BinaryOp):
        left = eval_static(node.left, env)
        right = eval_static(node.right, env)
        if left is not None and right is not None:
            try:
                op = node.op
                if op == '+': return left + right
                if op == '-': return left - right
                if op == '*': return left * right
                if op == '/':
                    return (left / right) if right != 0 else False
                if op == '%':
                    return (left % right) if right != 0 else False
                if op == '**': return left ** right
                if op == '==': return left == right
                if op == '!=': return left != right
                if op == '<': return left < right
                if op == '>': return left > right
                if op == '<=': return left <= right
                if op == '>=': return left >= right
                if op == 'and': return bool(left) and bool(right)
                if op == 'or': return bool(left) or bool(right)
            except Exception:
                return None
        return None
    return None


@dataclass
class Symbol:
    name: str
    type_name: str
    is_const: bool = False
    const_value: Any = None


@dataclass
class FunctionSignature:
    name: str
    params: List[Tuple[str, Optional[str]]]  # [(nomi, tip_hint), ...]
    return_type: str
    mode: str  # 'draft' | 'seal'
    where_clause: Optional[Node] = None
    is_async: bool = False


class TypeEnvironment:
    """Tip tekshiruvi leksik doirasi (scope)."""
    def __init__(self, parent: Optional['TypeEnvironment'] = None):
        self.parent = parent
        self.symbols: Dict[str, Symbol] = {}
        self.functions: Dict[str, FunctionSignature] = {}
        self.structs: Dict[str, List[Tuple[str, str]]] = {}
        self.struct_methods: Dict[str, Dict[str, FunctionSignature]] = {}

    def declare(self, name: str, type_name: str = 'Any', is_const: bool = False, const_value: Any = None) -> Symbol:
        sym = Symbol(name=name, type_name=type_name, is_const=is_const, const_value=const_value)
        self.symbols[name] = sym
        return sym

    def declare_function(self, name: str, params: List[Tuple[str, Optional[str]]],
                         return_type: str = 'Any', mode: str = 'draft',
                         where_clause: Optional[Node] = None,
                         is_async: bool = False) -> FunctionSignature:
        fn_sig = FunctionSignature(name=name, params=params, return_type=return_type,
                                   mode=mode, where_clause=where_clause, is_async=is_async)
        self.functions[name] = fn_sig
        self.declare(name, type_name='Fn', is_const=True)
        return fn_sig

    def declare_struct(self, name: str, fields: List[Tuple[str, str]]):
        self.structs[name] = fields
        self.declare(name, type_name='Fn', is_const=True)

    def declare_struct_method(self, struct_name: str, method: FunctionDef) -> FunctionSignature:
        if struct_name not in self.struct_methods:
            self.struct_methods[struct_name] = {}
        sig = FunctionSignature(
            name=method.name,
            params=method.params,
            return_type=method.return_type or 'Any',
            mode=method.mode,
            where_clause=method.where_clause,
            is_async=getattr(method, 'is_async', False)
        )
        self.struct_methods[struct_name][method.name] = sig
        return sig

    def lookup_struct_method(self, struct_name: str, method_name: str) -> Optional[FunctionSignature]:
        if struct_name in self.struct_methods and method_name in self.struct_methods[struct_name]:
            return self.struct_methods[struct_name][method_name]
        if self.parent:
            return self.parent.lookup_struct_method(struct_name, method_name)
        return None

    def lookup(self, name: str) -> Optional[Symbol]:
        if name in self.symbols:
            return self.symbols[name]
        if self.parent:
            return self.parent.lookup(name)
        return None

    def lookup_local(self, name: str) -> Optional[Symbol]:
        return self.symbols.get(name)

    def lookup_function(self, name: str) -> Optional[FunctionSignature]:
        if name in self.functions:
            return self.functions[name]
        if self.parent:
            return self.parent.lookup_function(name)
        return None

    def lookup_struct(self, name: str) -> Optional[List[Tuple[str, str]]]:
        if name in self.structs:
            return self.structs[name]
        if self.parent:
            return self.parent.lookup_struct(name)
        return None

    def all_structs(self) -> Set[str]:
        res = set(self.structs.keys())
        if self.parent:
            res.update(self.parent.all_structs())
        return res

    def get_const_dict(self) -> Dict[str, Any]:
        res = {}
        if self.parent:
            res.update(self.parent.get_const_dict())
        for name, sym in self.symbols.items():
            if sym.is_const and sym.const_value is not None:
                res[name] = sym.const_value
        return res

    def all_names(self) -> List[str]:
        names = list(self.symbols.keys()) + list(self.functions.keys()) + list(self.structs.keys())
        for m_dict in self.struct_methods.values():
            names.extend(m_dict.keys())
        if self.parent:
            names.extend(self.parent.all_names())
        return list(set(names))


def create_root_env() -> TypeEnvironment:
    """Zafira tili standart muhitini (builtins) yaratadi."""
    env = TypeEnvironment()
    env.declare_function('print', [('*args', 'Any')], return_type='Null', mode='draft')
    env.declare_function('input', [('prompt', 'Any')], return_type='String', mode='draft')
    env.declare_function('len', [('obj', 'Any')], return_type='Int', mode='draft')
    env.declare_function('range', [('start', 'Any'), ('end', 'Any')], return_type='List', mode='draft')
    env.declare_function('type', [('obj', 'Any')], return_type='String', mode='draft')
    env.declare_function('Int', [('val', 'Any')], return_type='Int', mode='draft')
    env.declare_function('Float', [('val', 'Any')], return_type='Float', mode='draft')
    env.declare_function('String', [('val', 'Any')], return_type='String', mode='draft')
    env.declare_function('sleep', [('secs', 'Any')], return_type='Null', mode='draft')
    env.declare_function('assert', [('cond', 'Any'), ('msg', 'Any')], return_type='Bool', mode='draft')
    return env


class TypeChecker:
    """AST daraxtini aylanib chiquvchi Zafira Statik Type Checker."""

    def __init__(self, current_file: Optional[str] = None):
        self.current_file = current_file
        self.root_env = create_root_env()

    def check(self, program: Program):
        """Program AST daraxtini bir marta (single-pass) aylanib chiqadi."""
        # 1. Top-level funksiyalar va structlarni ro'yxatga olamiz (forward-declaration / recursion uchun)
        for stmt in program.body:
            if isinstance(stmt, FunctionDef) and stmt.name:
                self.root_env.declare_function(
                    name=stmt.name,
                    params=stmt.params,
                    return_type=stmt.return_type or 'Any',
                    mode=stmt.mode,
                    where_clause=stmt.where_clause,
                    is_async=getattr(stmt, 'is_async', False)
                )
            elif isinstance(stmt, StructDef):
                self.root_env.declare_struct(stmt.name, stmt.fields)
            elif isinstance(stmt, ImplBlock):
                for method in stmt.methods:
                    self.root_env.declare_struct_method(stmt.struct_name, method)

        # 2. Asosiy blok va operatorlarni tartib bilan tekshiramiz
        for stmt in program.body:
            self._check_stmt(stmt, self.root_env)

    def _get_did_you_mean(self, name: str, env: TypeEnvironment) -> str:
        candidates = env.all_names()
        matches = difflib.get_close_matches(name, candidates, n=1, cutoff=0.55)
        if matches:
            return f" (Balki '{matches[0]}' nazarda tutilgandir?)"
        return ""

    # ─── STATEMENT TEKSHIRUVLARI ───

    def _check_stmt(self, stmt: Node, env: TypeEnvironment,
                    current_fn: Optional[FunctionDef] = None,
                    returns_found: Optional[List[str]] = None):
        method_name = f"_check_{type(stmt).__name__}"
        checker = getattr(self, method_name, None)
        if checker is not None:
            checker(stmt, env, current_fn=current_fn, returns_found=returns_found)
        else:
            raise TypeCheckError(f"Noma'lum operator tuguni: '{type(stmt).__name__}'")

    def _check_FunctionDef(self, node: FunctionDef, env: TypeEnvironment, **kwargs):
        # Qoida: 'draft' funksiyalar o'tkazib yuboriladi, faqat 'seal' funksiyalar tekshiriladi
        if node.mode != 'seal':
            return

        # 1. Parametr tiplarini tekshirish
        for pname, ptype in node.params:
            if ptype and ptype not in VALID_TYPES and ptype not in env.all_structs():
                raise TypeCheckError(f"'{node.name}' funksiyasining '{pname}' parametri uchun noma'lum tip: '{ptype}'")

        # 2. Return turi to'g'riligini tekshirish
        expected_ret = node.return_type or 'Any'
        if expected_ret not in VALID_TYPES and expected_ret not in env.all_structs():
            raise TypeCheckError(f"'{node.name}' funksiyasining return turi noma'lum: '{expected_ret}'")

        # 3. Funksiya ichki muhitini yaratish
        fn_env = TypeEnvironment(parent=env)
        for pname, ptype in node.params:
            fn_env.declare(pname, type_name=ptype or 'Any', is_const=False)

        # 4. 'where' invariantini tekshirish
        if node.where_clause:
            self._check_where_clause(node.where_clause, fn_env, node.name)

        # 5. Funksiya tanasini tekshirish
        fn_returns: List[str] = []
        for s in node.body:
            self._check_stmt(s, fn_env, current_fn=node, returns_found=fn_returns)

        # Agar funksiya qiymat qaytarishi kutilsa (Null/Any emas), return bo'lishi shart
        if expected_ret not in ('Null', 'Any') and not fn_returns:
            raise TypeCheckError(f"'{node.name}' funksiyasida return operatori topilmadi, lekin '{expected_ret}' qaytarilishi kutilgan!")

    def _check_where_clause(self, where_node: Node, fn_env: TypeEnvironment, fn_name: str):
        """'where' invariantini statik tahlil qiladi."""
        def check_identifiers(n: Node):
            if isinstance(n, Identifier):
                sym = fn_env.lookup(n.name)
                fn = fn_env.lookup_function(n.name)
                if sym is None and fn is None:
                    hint = self._get_did_you_mean(n.name, fn_env)
                    raise TypeCheckError(f"'{fn_name}' funksiyasining 'where' shartida e'lon qilinmagan o'zgaruvchi: '{n.name}'!{hint}")
            elif isinstance(n, BinaryOp):
                check_identifiers(n.left)
                check_identifiers(n.right)
            elif isinstance(n, UnaryOp):
                check_identifiers(n.operand)
            elif isinstance(n, AwaitExpr):
                check_identifiers(n.expr)
            elif isinstance(n, FunctionCall):
                check_identifiers(n.callee)
                for a in n.args:
                    check_identifiers(a)

        check_identifiers(where_node)
        self._check_expr(where_node, fn_env)

        # O'zgarmas shart bo'lsa (masalan where 0 > 1 yoki where false)
        const_dict = fn_env.get_const_dict()
        static_res = eval_static(where_node, const_dict)
        if static_res is False:
            where_str = node_to_str(where_node)
            raise TypeCheckError(f"'{fn_name}' funksiyasining 'where' sharti ({where_str}) doimo False (invarianti bajarilmaydi)!")

    def _check_LetStatement(self, node: LetStatement, env: TypeEnvironment, **kwargs):
        val_type = 'Any'
        if node.value:
            val_type = self._check_expr(node.value, env)

        if node.type_hint:
            if node.type_hint not in VALID_TYPES and node.type_hint not in env.all_structs():
                raise TypeCheckError(f"'{node.name}' uchun noma'lum tip: '{node.type_hint}'")
            if node.value and not is_type_compatible(node.type_hint, val_type, env.all_structs()):
                raise TypeCheckError(f"'{node.name}' o'zgaruvchisiga '{val_type}' berildi, lekin '{node.type_hint}' kutilgan edi!")
            var_type = node.type_hint
        else:
            var_type = val_type

        existing = env.lookup_local(node.name)
        if existing and existing.is_const:
            raise TypeCheckError(f"'{node.name}' — const, uni qayta e'lon qilib bo'lmaydi!")

        env.declare(node.name, type_name=var_type, is_const=False)

    def _check_ConstStatement(self, node: ConstStatement, env: TypeEnvironment, **kwargs):
        val_type = self._check_expr(node.value, env)

        if node.type_hint:
            if node.type_hint not in VALID_TYPES and node.type_hint not in env.all_structs():
                raise TypeCheckError(f"'{node.name}' uchun noma'lum tip: '{node.type_hint}'")
            if not is_type_compatible(node.type_hint, val_type, env.all_structs()):
                raise TypeCheckError(f"'{node.name}' o'zgarmasiga (const) '{val_type}' berildi, lekin '{node.type_hint}' kutilgan edi!")
            var_type = node.type_hint
        else:
            var_type = val_type

        const_val = eval_static(node.value, env.get_const_dict())
        existing = env.lookup_local(node.name)
        if existing and existing.is_const:
            raise TypeCheckError(f"'{node.name}' — const, uni qayta e'lon qilib bo'lmaydi!")

        env.declare(node.name, type_name=var_type, is_const=True, const_value=const_val)

    def _check_AssignStatement(self, node: AssignStatement, env: TypeEnvironment, **kwargs):
        val_type = self._check_expr(node.value, env)

        if isinstance(node.target, Identifier):
            name = node.target.name
            sym = env.lookup(name)
            if sym is None:
                hint = self._get_did_you_mean(name, env)
                raise TypeCheckError(f"'{name}' o'zgaruvchisi aniqlanmagan (e'lon qilinmagan)!{hint}")
            if sym.is_const:
                raise TypeCheckError(f"'{name}' — const, uni o'zgartirib bo'lmaydi!")
            if sym.type_name != 'Any' and not is_type_compatible(sym.type_name, val_type, env.all_structs()):
                raise TypeCheckError(f"'{name}' o'zgaruvchisiga {val_type} tayinlab bo'lmaydi, {sym.type_name} kutilgan!")
        elif isinstance(node.target, MemberAccess):
            obj_type = self._check_expr(node.target.obj, env)
            if obj_type in env.all_structs():
                fields = env.lookup_struct(obj_type)
                field_type = next((ft for fn, ft in fields if fn == node.target.member), None)
                if field_type is None:
                    raise TypeCheckError(f"'{obj_type}' strukturasida '{node.target.member}' maydoni yo'q!")
                if not is_type_compatible(field_type, val_type, env.all_structs()):
                    raise TypeCheckError(f"'{node.target.member}' maydoniga {val_type} tayinlab bo'lmaydi, {field_type} kutilgan!")
        elif isinstance(node.target, IndexAccess):
            obj_type = self._check_expr(node.target.obj, env)
            idx_type = self._check_expr(node.target.index, env)
            if obj_type in ('Any', 'JsonObject') or obj_type in env.all_structs():
                if not (is_type_compatible('Int', idx_type, env.all_structs()) or is_type_compatible('String', idx_type, env.all_structs())):
                    raise TypeCheckError(f"Indeks turi Int yoki String bo'lishi kerak, lekin '{idx_type}' berildi!")
            else:
                if not is_type_compatible('Int', idx_type, env.all_structs()):
                    raise TypeCheckError(f"Indeks turi Int bo'lishi kerak, lekin '{idx_type}' berildi!")
        else:
            raise TypeCheckError(f"Noto'g'ri tayinlash nishoni: {type(node.target).__name__}")

    def _check_ReturnStatement(self, node: ReturnStatement, env: TypeEnvironment,
                               current_fn: Optional[FunctionDef] = None,
                               returns_found: Optional[List[str]] = None, **kwargs):
        val_type = self._check_expr(node.value, env) if node.value else 'Null'
        if returns_found is not None:
            returns_found.append(val_type)

        if current_fn and current_fn.mode == 'seal':
            expected_ret = current_fn.return_type or 'Any'
            if not is_type_compatible(expected_ret, val_type, env.all_structs()):
                raise TypeCheckError(f"'{current_fn.name}' funksiyasidan {val_type} qaytarilyapti, {expected_ret} kutilgan!")

    def _check_IfStatement(self, node: IfStatement, env: TypeEnvironment,
                           current_fn: Optional[FunctionDef] = None,
                           returns_found: Optional[List[str]] = None, **kwargs):
        self._check_expr(node.condition, env)
        child_then = TypeEnvironment(parent=env)
        for s in node.then_block:
            self._check_stmt(s, child_then, current_fn=current_fn, returns_found=returns_found)
        if node.else_block:
            child_else = TypeEnvironment(parent=env)
            for s in node.else_block:
                self._check_stmt(s, child_else, current_fn=current_fn, returns_found=returns_found)

    def _check_WhileStatement(self, node: WhileStatement, env: TypeEnvironment,
                            current_fn: Optional[FunctionDef] = None,
                            returns_found: Optional[List[str]] = None, **kwargs):
        self._check_expr(node.condition, env)
        child_env = TypeEnvironment(parent=env)
        for s in node.body:
            self._check_stmt(s, child_env, current_fn=current_fn, returns_found=returns_found)

    def _check_ForStatement(self, node: ForStatement, env: TypeEnvironment,
                          current_fn: Optional[FunctionDef] = None,
                          returns_found: Optional[List[str]] = None, **kwargs):
        iter_type = self._check_expr(node.iterable, env)
        sym = env.lookup(node.var)
        if sym and sym.is_const:
            raise TypeCheckError(f"'{node.var}' — const, uni tsikl o'zgaruvchisi sifatida ishlatib bo'lmaydi!")

        child_env = TypeEnvironment(parent=env)
        var_type = 'Int' if isinstance(node.iterable, RangeExpr) else ('String' if iter_type == 'String' else 'Any')
        child_env.declare(node.var, type_name=var_type, is_const=False)
        for s in node.body:
            self._check_stmt(s, child_env, current_fn=current_fn, returns_found=returns_found)

    def _check_StructDef(self, node: StructDef, env: TypeEnvironment, **kwargs):
        for fname, ftype in node.fields:
            if ftype not in VALID_TYPES and ftype not in env.all_structs():
                raise TypeCheckError(f"'{node.name}' strukturasining '{fname}' maydoni uchun noma'lum tip: '{ftype}'")

    def _check_ImplBlock(self, node: ImplBlock, env: TypeEnvironment, **kwargs):
        # 1. Struct mavjudligini tasdiqlash
        if node.struct_name not in env.all_structs():
            hint = self._get_did_you_mean(node.struct_name, env)
            raise TypeCheckError(f"'{node.struct_name}' nomli struct topilmadi!{hint}")

        # 2. Metodlarni structga biriktirish va tekshirish
        for method in node.methods:
            env.declare_struct_method(node.struct_name, method)

            # Agar metod 'seal' bo'lsa, qat'iy tekshirish
            if method.mode == 'seal':
                for pname, ptype in method.params:
                    expected_ptype = node.struct_name if (pname == 'self' and ptype is None) else ptype
                    if expected_ptype and expected_ptype not in VALID_TYPES and expected_ptype not in env.all_structs():
                        raise TypeCheckError(f"'{method.name}' metodining '{pname}' parametri uchun noma'lum tip: '{expected_ptype}'")

                expected_ret = method.return_type or 'Any'
                if expected_ret not in VALID_TYPES and expected_ret not in env.all_structs():
                    raise TypeCheckError(f"'{method.name}' metodining return turi noma'lum: '{expected_ret}'")

                fn_env = TypeEnvironment(parent=env)
                for pname, ptype in method.params:
                    actual_type = node.struct_name if (pname == 'self' and ptype is None) else (ptype or 'Any')
                    fn_env.declare(pname, type_name=actual_type, is_const=False)

                if method.where_clause:
                    self._check_where_clause(method.where_clause, fn_env, method.name)

                fn_returns: List[str] = []
                for s in method.body:
                    self._check_stmt(s, fn_env, current_fn=method, returns_found=fn_returns)

                if expected_ret not in ('Null', 'Any') and not fn_returns:
                    raise TypeCheckError(f"'{method.name}' metodida return operatori topilmadi, lekin '{expected_ret}' qaytarilishi kutilgan!")

    def _check_ImportStatement(self, node: ImportStatement, env: TypeEnvironment, **kwargs):
        if node.path == 'sys.io':
            env.declare('print', type_name='Fn', is_const=True)
            env.declare('input', type_name='Fn', is_const=True)
        elif node.path.startswith('std.'):
            parts = node.path.split('.')
            if len(parts) >= 2:
                mod_name = parts[1]
                from src.stdlib import STDLIB_MODULES
                if mod_name not in STDLIB_MODULES:
                    raise TypeCheckError(f"'{node.path}' moduli topilmadi!")
                target_name = getattr(node, 'alias', None) or mod_name
                env.declare(target_name, type_name='Any', is_const=True)
                if mod_name == 'ffi':
                    env.declare_struct('FfiLibrary', [
                        ('name', 'String'), ('call', 'Fn'), ('has_symbol', 'Fn'), ('has', 'Fn')
                    ])
                    env.declare_struct('CInt', [('type', 'String'), ('value', 'Int')])
                    env.declare_struct('CFloat', [('type', 'String'), ('value', 'Float')])
                    env.declare_struct('CDouble', [('type', 'String'), ('value', 'Float')])
                    env.declare_struct('CString', [('type', 'String'), ('value', 'String')])
                    env.declare_struct('CBool', [('type', 'String'), ('value', 'Bool')])
        elif node.path.startswith('py.'):
            mod_path = node.path[3:]
            root_name = mod_path.split('.')[0]
            target_name = getattr(node, 'alias', None) or root_name
            env.declare(target_name, type_name='Any', is_const=True)
            if '.' in mod_path:
                leaf_name = mod_path.split('.')[-1]
                if leaf_name != root_name:
                    env.declare(leaf_name, type_name='Any', is_const=True)
            if root_name == 'pandas':
                env.declare('pd', type_name='Any', is_const=True)
            elif root_name == 'numpy':
                env.declare('np', type_name='Any', is_const=True)
            elif root_name == 'matplotlib':
                env.declare('plt', type_name='Any', is_const=True)
            elif root_name == 'tensorflow':
                env.declare('tf', type_name='Any', is_const=True)
        else:
            # Lokal modul importi (./matematika.zf, ../modul, matematika.zf)
            alias = getattr(node, 'alias', None)
            if alias:
                target_name = alias
            else:
                base_name = os.path.basename(node.path)
                if base_name.endswith('.zf'):
                    base_name = base_name[:-3]
                target_name = os.path.splitext(base_name)[0]
            env.declare(target_name, type_name='Any', is_const=True)

            # Agar fayl mavjud bo'lsa, undagi structlarni ham ro'yxatdan o'tkazamiz
            base_dir = os.path.dirname(os.path.abspath(self.current_file)) if self.current_file else os.getcwd()
            candidate = os.path.normpath(os.path.join(base_dir, node.path))
            target_file = None
            if os.path.isfile(candidate):
                target_file = candidate
            elif not candidate.endswith('.zf') and os.path.isfile(candidate + '.zf'):
                target_file = candidate + '.zf'

            if target_file:
                try:
                    with open(target_file, 'r', encoding='utf-8') as f:
                        sub_src = f.read()
                    from src.lexer import Lexer
                    from src.parser import Parser
                    sub_prog = Parser(Lexer(sub_src).tokenize()).parse()
                    for s in sub_prog.body:
                        if isinstance(s, StructDef):
                            env.declare_struct(s.name, s.fields)
                        elif isinstance(s, ImplBlock):
                            for m in s.methods:
                                env.declare_struct_method(s.struct_name, m)
                except Exception:
                    pass

    def _check_RunBlock(self, node: RunBlock, env: TypeEnvironment,
                        current_fn: Optional[FunctionDef] = None,
                        returns_found: Optional[List[str]] = None, **kwargs):
        child_env = TypeEnvironment(parent=env)
        for s in node.body:
            self._check_stmt(s, child_env, current_fn=current_fn, returns_found=returns_found)

    def _check_ExprStatement(self, node: ExprStatement, env: TypeEnvironment, **kwargs):
        self._check_expr(node.expr, env)

    def _check_MatchExpr(self, node: MatchExpr, env: TypeEnvironment,
                         current_fn: Optional[FunctionDef] = None,
                         returns_found: Optional[List[str]] = None, **kwargs):
        return self._infer_MatchExpr(node, env, current_fn=current_fn, returns_found=returns_found)

    def _check_Block(self, node: Block, env: TypeEnvironment,
                     current_fn: Optional[FunctionDef] = None,
                     returns_found: Optional[List[str]] = None, **kwargs):
        child_env = TypeEnvironment(parent=env)
        for s in node.statements:
            self._check_stmt(s, child_env, current_fn=current_fn, returns_found=returns_found)

    def _check_TryStatement(self, node: TryStatement, env: TypeEnvironment,
                            current_fn: Optional[FunctionDef] = None,
                            returns_found: Optional[List[str]] = None, **kwargs):
        child_try = TypeEnvironment(parent=env)
        for s in node.try_block:
            self._check_stmt(s, child_try, current_fn=current_fn, returns_found=returns_found)

        if node.catch_block is not None:
            child_catch = TypeEnvironment(parent=env)
            if node.catch_param:
                child_catch.declare(node.catch_param, type_name='Any', is_const=False)
            for s in node.catch_block:
                self._check_stmt(s, child_catch, current_fn=current_fn, returns_found=returns_found)

        if node.finally_block is not None:
            child_finally = TypeEnvironment(parent=env)
            for s in node.finally_block:
                self._check_stmt(s, child_finally, current_fn=current_fn, returns_found=returns_found)

    def _check_ThrowStatement(self, node: ThrowStatement, env: TypeEnvironment,
                             current_fn: Optional[FunctionDef] = None,
                             returns_found: Optional[List[str]] = None, **kwargs):
        self._check_expr(node.expr, env)

    # ─── EXPRESSION TEKSHIRUVLARI (TIP DEDUCTION) ───

    def _check_expr(self, expr: Node, env: TypeEnvironment) -> str:
        method_name = f"_infer_{type(expr).__name__}"
        inferer = getattr(self, method_name, None)
        if inferer is not None:
            return inferer(expr, env)
        raise TypeCheckError(f"Noma'lum ifoda tuguni: '{type(expr).__name__}'")

    def _infer_NumberLiteral(self, node: NumberLiteral, env: TypeEnvironment) -> str:
        if isinstance(node.value, int):
            return 'Int'
        return 'Float'

    def _infer_StringLiteral(self, node: StringLiteral, env: TypeEnvironment) -> str:
        return 'String'

    def _infer_BoolLiteral(self, node: BoolLiteral, env: TypeEnvironment) -> str:
        return 'Bool'

    def _infer_NullLiteral(self, node: NullLiteral, env: TypeEnvironment) -> str:
        return 'Null'

    def _infer_FunctionDef(self, node: FunctionDef, env: TypeEnvironment) -> str:
        return 'Fn'

    def _infer_Identifier(self, node: Identifier, env: TypeEnvironment) -> str:
        name = node.name
        sym = env.lookup(name)
        if sym is not None:
            return sym.type_name
        fn = env.lookup_function(name)
        if fn is not None:
            return 'Fn'
        st = env.lookup_struct(name)
        if st is not None:
            return 'Fn'

        hint = self._get_did_you_mean(name, env)
        raise TypeCheckError(f"'{name}' o'zgaruvchisi aniqlanmagan (undeclared variable)!{hint}")

    def _infer_BinaryOp(self, node: BinaryOp, env: TypeEnvironment) -> str:
        left_type = self._check_expr(node.left, env)
        right_type = self._check_expr(node.right, env)
        op = node.op

        if op == '+':
            if left_type == 'String' or right_type == 'String':
                return 'String'
            if left_type == 'Any' or right_type == 'Any':
                return 'Any'
            if left_type in ('Int', 'Float') and right_type in ('Int', 'Float'):
                return 'Float' if (left_type == 'Float' or right_type == 'Float') else 'Int'
            if left_type == 'List' and right_type == 'List':
                return 'List'
            raise TypeCheckError(f"'+' operatori '{left_type}' va '{right_type}' turlari uchun mos kelmaydi!")

        if op in ('-', '*', '%', '**'):
            if op == '*' and ((left_type == 'String' and right_type == 'Int') or (left_type == 'Int' and right_type == 'String')):
                return 'String'
            if left_type == 'Any' or right_type == 'Any':
                return 'Any'
            if left_type in ('Int', 'Float') and right_type in ('Int', 'Float'):
                if op == '%':
                    return 'Int' if (left_type == 'Int' and right_type == 'Int') else 'Float'
                if op == '**':
                    return 'Int' if (left_type == 'Int' and right_type == 'Int') else 'Float'
                return 'Float' if (left_type == 'Float' or right_type == 'Float') else 'Int'
            raise TypeCheckError(f"'{op}' operatori '{left_type}' va '{right_type}' turlari uchun mos kelmaydi!")

        if op == '/':
            if left_type == 'Any' or right_type == 'Any':
                return 'Float'
            if left_type in ('Int', 'Float') and right_type in ('Int', 'Float'):
                return 'Float'
            raise TypeCheckError(f"'/' operatori '{left_type}' va '{right_type}' turlari uchun mos kelmaydi!")

        if op in ('==', '!='):
            return 'Bool'

        if op in ('<', '>', '<=', '>='):
            if left_type == 'Any' or right_type == 'Any':
                return 'Bool'
            if (left_type in ('Int', 'Float') and right_type in ('Int', 'Float')) or (left_type == 'String' and right_type == 'String'):
                return 'Bool'
            raise TypeCheckError(f"'{op}' operatori '{left_type}' va '{right_type}' turlarini taqqoslay olmaydi!")

        if op in ('and', 'or'):
            return 'Bool'

        raise TypeCheckError(f"Noma'lum operator: '{op}'")

    def _infer_UnaryOp(self, node: UnaryOp, env: TypeEnvironment) -> str:
        op_type = self._check_expr(node.operand, env)
        if node.op == '-':
            if op_type in ('Int', 'Float'):
                return op_type
            if op_type == 'Any':
                return 'Any'
            raise TypeCheckError(f"Unary '-' operatori '{op_type}' uchun mos kelmaydi!")
        if node.op == 'not':
            return 'Bool'
        raise TypeCheckError(f"Noma'lum unary operator: '{node.op}'")

    def _infer_FunctionCall(self, node: FunctionCall, env: TypeEnvironment) -> str:
        callee = node.callee

        if isinstance(callee, Identifier):
            name = callee.name

            # 1. Built-in type casting va maxsus funksiyalar
            if name == 'String':
                for a in node.args: self._check_expr(a, env)
                return 'String'
            if name == 'Int':
                for a in node.args: self._check_expr(a, env)
                return 'Int'
            if name == 'Float':
                for a in node.args: self._check_expr(a, env)
                return 'Float'
            if name == 'print':
                for a in node.args: self._check_expr(a, env)
                return 'Null'
            if name == 'input':
                for a in node.args: self._check_expr(a, env)
                return 'String'
            if name == 'len':
                if len(node.args) != 1:
                    raise TypeCheckError(f"len() funksiyasi 1 ta argument kutadi, {len(node.args)} ta berildi")
                arg_t = self._check_expr(node.args[0], env)
                if arg_t not in ('List', 'String', 'Any'):
                    raise TypeCheckError(f"len() faqat List yoki String qabul qiladi, lekin '{arg_t}' berildi!")
                return 'Int'
            if name == 'range':
                for a in node.args: self._check_expr(a, env)
                return 'List'
            if name == 'type':
                for a in node.args: self._check_expr(a, env)
                return 'String'

            # 2. Struct konstruktori
            st = env.lookup_struct(name)
            if st is not None:
                for a in node.args: self._check_expr(a, env)
                return name

            # 3. Foydalanuvchi funksiyasi
            fn = env.lookup_function(name)
            if fn is None:
                sym = env.lookup(name)
                if sym and sym.type_name in ('Fn', 'Any'):
                    for a in node.args: self._check_expr(a, env)
                    return 'Any'
                hint = self._get_did_you_mean(name, env)
                raise TypeCheckError(f"'{name}' funksiyasi aniqlanmagan (e'lon qilinmagan)!{hint}")

            if fn.mode == 'seal':
                # Argumentlar sonini tekshirish
                if len(node.args) != len(fn.params):
                    raise TypeCheckError(f"'{name}' funksiyasi {len(fn.params)} ta argument kutadi, lekin {len(node.args)} ta berildi!")

                args_evaluated = []
                for (pname, ptype), arg_node in zip(fn.params, node.args):
                    arg_type = self._check_expr(arg_node, env)
                    expected_type = ptype or 'Any'
                    if not is_type_compatible(expected_type, arg_type, env.all_structs()):
                        raise TypeCheckError(f"'{name}' funksiyasining '{pname}' parametri uchun {arg_type} o'rniga {expected_type} kutilgan!")
                    val = eval_static(arg_node, env.get_const_dict())
                    args_evaluated.append((pname, val))

                # 'where' invariantini statik tekshirish (imkon qadar)
                if fn.where_clause:
                    arg_env = {pname: val for pname, val in args_evaluated if val is not None}
                    full_eval_env = {**env.get_const_dict(), **arg_env}
                    where_result = eval_static(fn.where_clause, full_eval_env)
                    if where_result is False:
                        where_str = node_to_str(fn.where_clause)
                        arg_vals_str = ', '.join(f"{p}={v}" for p, v in args_evaluated)
                        raise TypeCheckError(f"'{name}' funksiyasining 'where' invarianti statik tekshiruvda buzildi! Shart: ({where_str}), Argumentlar: ({arg_vals_str})")

                if getattr(fn, 'is_async', False):
                    return 'Task'

                return fn.return_type or 'Any'
            else:
                # 'draft' funksiyalar erkin qoldiriladi
                for a in node.args: self._check_expr(a, env)
                if getattr(fn, 'is_async', False):
                    return 'Task'
                return fn.return_type or 'Any'

        elif isinstance(callee, MemberAccess):
            obj_type = self._check_expr(callee.obj, env)
            for a in node.args: self._check_expr(a, env)
            if obj_type == 'List':
                if callee.member in ('push',): return 'Null'
                if callee.member in ('pop',): return 'Any'
            if obj_type == 'String':
                if callee.member in ('upper', 'lower', 'trim'): return 'String'
            if isinstance(callee.obj, Identifier) and callee.obj.name == 'fs':
                if callee.member in ('read_text',):
                    return 'String'
                if callee.member in ('exists', 'is_file', 'is_dir'):
                    return 'Bool'
                if callee.member in ('list_dir',):
                    return 'List'
                if callee.member in ('file_size',):
                    return 'Int'
                if callee.member in ('write_text', 'append_text', 'make_dir', 'remove', 'remove_dir', 'copy'):
                    return 'Null'
                raise TypeCheckError(f"std.fs modulida '{callee.member}' funksiyasi mavjud emas!")
            if isinstance(callee.obj, Identifier) and callee.obj.name == 'env':
                if callee.member in ('os', 'cwd'):
                    return 'String'
                if callee.member in ('has',):
                    return 'Bool'
                if callee.member in ('set', 'remove'):
                    return 'Null'
                if callee.member in ('args',):
                    return 'List'
                if callee.member in ('get', 'all'):
                    return 'Any'
                raise TypeCheckError(f"std.env modulida '{callee.member}' funksiyasi mavjud emas!")
            if isinstance(callee.obj, Identifier) and callee.obj.name == 'datetime':
                if callee.member in ('now',):
                    return 'Any'
                if callee.member in ('timestamp',):
                    return 'Float'
                if callee.member in ('format',):
                    return 'String'
                if callee.member in ('sleep', 'sleep_ms'):
                    return 'Null'
                raise TypeCheckError(f"std.datetime modulida '{callee.member}' funksiyasi mavjud emas!")
            if isinstance(callee.obj, Identifier) and callee.obj.name == 'crypto':
                if callee.member in (
                    'sha256', 'sha512', 'md5', 'hmac_sha256',
                    'base64_encode', 'base64_decode', 'uuid', 'random_hex'
                ):
                    return 'String'
                if callee.member in ('random_bytes',):
                    return 'List'
                raise TypeCheckError(f"std.crypto modulida '{callee.member}' funksiyasi mavjud emas!")
            if isinstance(callee.obj, Identifier) and callee.obj.name in ('regex', 're'):
                if callee.member in ('test', 'is_valid'):
                    return 'Bool'
                if callee.member in ('find',):
                    return 'Any'
                if callee.member in ('replace', 'replace_all'):
                    return 'String'
                if callee.member in ('find_all', 'split'):
                    return 'List'
                raise TypeCheckError(f"std.regex modulida '{callee.member}' funksiyasi mavjud emas!")
            if isinstance(callee.obj, Identifier) and callee.obj.name == 'ffi':
                if callee.member in ('load', 'libc'):
                    return 'FfiLibrary'
                if callee.member in ('c_int',):
                    return 'CInt'
                if callee.member in ('c_float',):
                    return 'CFloat'
                if callee.member in ('c_double',):
                    return 'CDouble'
                if callee.member in ('c_string',):
                    return 'CString'
                if callee.member in ('c_bool',):
                    return 'CBool'
                if callee.member in ('has_symbol', 'has'):
                    return 'Bool'
                if callee.member in ('call',):
                    return 'Any'
                raise TypeCheckError(f"std.ffi modulida '{callee.member}' funksiyasi mavjud emas!")
            if obj_type == 'FfiLibrary':
                if callee.member in ('has_symbol', 'has'):
                    return 'Bool'
                if callee.member in ('call',):
                    return 'Any'
                raise TypeCheckError(f"FfiLibrary strukturasida '{callee.member}' metodi mavjud emas!")
            if obj_type in env.all_structs():
                method_sig = env.lookup_struct_method(obj_type, callee.member)
                if method_sig is not None:
                    if method_sig.mode == 'seal':
                        expected_params = [p for p in method_sig.params if p[0] != 'self']
                        if len(node.args) != len(expected_params):
                            raise TypeCheckError(f"'{callee.member}' metodi {len(expected_params)} ta argument kutadi, lekin {len(node.args)} ta berildi!")
                        for (pname, ptype), arg_node in zip(expected_params, node.args):
                            arg_type = self._check_expr(arg_node, env)
                            expected_type = ptype or 'Any'
                            if not is_type_compatible(expected_type, arg_type, env.all_structs()):
                                raise TypeCheckError(f"'{callee.member}' metodining '{pname}' parametri uchun {arg_type} o'rniga {expected_type} kutilgan!")
                    if getattr(method_sig, 'is_async', False):
                        return 'Task'
                    return method_sig.return_type or 'Any'
            return 'Any'

        else:
            self._check_expr(callee, env)
            for a in node.args: self._check_expr(a, env)
            return 'Any'

    def _infer_MemberAccess(self, node: MemberAccess, env: TypeEnvironment) -> str:
        obj_type = self._check_expr(node.obj, env)
        if isinstance(node.obj, Identifier) and node.obj.name == 'fs':
            if node.member in (
                'read_text', 'write_text', 'append_text', 'exists',
                'is_file', 'is_dir', 'list_dir', 'make_dir',
                'remove', 'remove_dir', 'file_size', 'copy'
            ):
                return 'Fn'
            raise TypeCheckError(f"std.fs modulida '{node.member}' a'zosi mavjud emas!")
        if isinstance(node.obj, Identifier) and node.obj.name == 'env':
            if node.member in (
                'get', 'set', 'has', 'remove', 'all', 'args', 'os', 'cwd'
            ):
                return 'Fn'
            raise TypeCheckError(f"std.env modulida '{node.member}' a'zosi mavjud emas!")
        if isinstance(node.obj, Identifier) and node.obj.name == 'datetime':
            if node.member in (
                'now', 'timestamp', 'format', 'sleep', 'sleep_ms'
            ):
                return 'Fn'
            raise TypeCheckError(f"std.datetime modulida '{node.member}' a'zosi mavjud emas!")
        if isinstance(node.obj, Identifier) and node.obj.name == 'crypto':
            if node.member in (
                'sha256', 'sha512', 'md5', 'hmac_sha256',
                'base64_encode', 'base64_decode',
                'uuid', 'random_bytes', 'random_hex'
            ):
                return 'Fn'
            raise TypeCheckError(f"std.crypto modulida '{node.member}' a'zosi mavjud emas!")
        if isinstance(node.obj, Identifier) and node.obj.name in ('regex', 're'):
            if node.member in (
                'test', 'find', 'find_all', 'replace', 'replace_all', 'split', 'is_valid'
            ):
                return 'Fn'
            raise TypeCheckError(f"std.regex modulida '{node.member}' a'zosi mavjud emas!")
        if isinstance(node.obj, Identifier) and node.obj.name == 'ffi':
            if node.member in (
                'load', 'libc', 'c_int', 'c_float', 'c_double', 'c_string', 'c_bool',
                'call', 'has_symbol', 'has'
            ):
                return 'Fn'
            raise TypeCheckError(f"std.ffi modulida '{node.member}' a'zosi mavjud emas!")
        if obj_type == 'FfiLibrary':
            if node.member in ('call', 'has_symbol', 'has'):
                return 'Fn'
            if node.member == 'name':
                return 'String'
            raise TypeCheckError(f"FfiLibrary strukturasida '{node.member}' a'zosi mavjud emas!")
        if obj_type == 'List':
            if node.member == 'len': return 'Int'
            if node.member in ('first', 'last'): return 'Any'
            if node.member in ('push', 'pop'): return 'Fn'
            raise TypeCheckError(f"List turida '{node.member}' a'zosi mavjud emas!")
        if obj_type == 'String':
            if node.member == 'len': return 'Int'
            if node.member in ('upper', 'lower', 'trim'): return 'Fn'
            raise TypeCheckError(f"String turida '{node.member}' a'zosi mavjud emas!")
        if obj_type in env.all_structs():
            fields = env.lookup_struct(obj_type)
            if fields:
                for fname, ftype in fields:
                    if fname == node.member:
                        return ftype
            method_sig = env.lookup_struct_method(obj_type, node.member)
            if method_sig is not None:
                return 'Fn'
            raise TypeCheckError(f"'{obj_type}' strukturasida '{node.member}' maydoni yoki metodi mavjud emas!")
        return 'Any'

    def _infer_IndexAccess(self, node: IndexAccess, env: TypeEnvironment) -> str:
        obj_type = self._check_expr(node.obj, env)
        idx_type = self._check_expr(node.index, env)
        if obj_type in ('String', 'List'):
            if not is_type_compatible('Int', idx_type, env.all_structs()):
                raise TypeCheckError(f"Indeks turi Int bo'lishi kerak, lekin '{idx_type}' berildi!")
        elif obj_type == 'Any' or obj_type in env.all_structs():
            if not (is_type_compatible('Int', idx_type, env.all_structs()) or is_type_compatible('String', idx_type, env.all_structs())):
                raise TypeCheckError(f"Indeks turi Int yoki String bo'lishi kerak, lekin '{idx_type}' berildi!")
        else:
            if not is_type_compatible('Int', idx_type, env.all_structs()):
                raise TypeCheckError(f"Indeks turi Int bo'lishi kerak, lekin '{idx_type}' berildi!")
        if obj_type == 'String':
            return 'String'
        if obj_type == 'List':
            return 'Any'
        return 'Any'

    def _infer_ListLiteral(self, node: ListLiteral, env: TypeEnvironment) -> str:
        for el in node.elements:
            self._check_expr(el, env)
        return 'List'

    def _infer_RangeExpr(self, node: RangeExpr, env: TypeEnvironment) -> str:
        start_type = self._check_expr(node.start, env)
        end_type = self._check_expr(node.end, env)
        if not is_type_compatible('Int', start_type, env.all_structs()):
            raise TypeCheckError(f"Range boshlanish qiymati Int bo'lishi kerak, '{start_type}' berildi!")
        if not is_type_compatible('Int', end_type, env.all_structs()):
            raise TypeCheckError(f"Range tugash qiymati Int bo'lishi kerak, '{end_type}' berildi!")
        return 'List'

    def _infer_AwaitExpr(self, node: AwaitExpr, env: TypeEnvironment) -> str:
        # Agar await qilinayotgan ifoda bevosita funksiya chaqiruvi bo'lsa
        if isinstance(node.expr, FunctionCall) and isinstance(node.expr.callee, Identifier):
            name = node.expr.callee.name
            fn = env.lookup_function(name)
            if fn is not None:
                if fn.mode == 'seal':
                    if len(node.expr.args) != len(fn.params):
                        raise TypeCheckError(f"'{name}' funksiyasi {len(fn.params)} ta argument kutadi, lekin {len(node.expr.args)} ta berildi!")
                    for (pname, ptype), arg_node in zip(fn.params, node.expr.args):
                        arg_type = self._check_expr(arg_node, env)
                        expected_type = ptype or 'Any'
                        if not is_type_compatible(expected_type, arg_type, env.all_structs()):
                            raise TypeCheckError(f"'{name}' funksiyasining '{pname}' parametri uchun {arg_type} o'rniga {expected_type} kutilgan!")
                else:
                    for a in node.expr.args: self._check_expr(a, env)
                return fn.return_type or 'Any'

        inner_type = self._check_expr(node.expr, env)
        if inner_type in ('Task', 'Future'):
            return 'Any'
        return inner_type

    def _infer_Wildcard(self, node: Wildcard, env: TypeEnvironment) -> str:
        return 'Any'

    def _infer_MatchExpr(self, node: MatchExpr, env: TypeEnvironment,
                         current_fn: Optional[FunctionDef] = None,
                         returns_found: Optional[List[str]] = None) -> str:
        target_type = self._check_expr(node.expr, env)
        arm_types = []
        for arm in node.arms:
            arm_env = TypeEnvironment(parent=env)
            pattern = arm.pattern
            # Pattern tekshiruvi va yangi bog'lanish
            if isinstance(pattern, Wildcard) or (isinstance(pattern, Identifier) and pattern.name == '_'):
                pass
            elif isinstance(pattern, Identifier):
                sym = env.lookup(pattern.name)
                if sym is None and env.lookup_function(pattern.name) is None:
                    # Yangi o'zgaruvchi bog'lanishi (pattern binding)
                    arm_env.declare(pattern.name, type_name=target_type or 'Any', is_const=False)
                else:
                    self._check_expr(pattern, env)
            elif isinstance(pattern, RangeExpr):
                self._check_expr(pattern, env)
            else:
                self._check_expr(pattern, env)

            # Tana tekshiruvi
            if isinstance(arm.body, Block):
                for s in arm.body.statements:
                    self._check_stmt(s, arm_env, current_fn=current_fn, returns_found=returns_found)
                if arm.body.statements:
                    last_stmt = arm.body.statements[-1]
                    if isinstance(last_stmt, ExprStatement):
                        arm_types.append(self._check_expr(last_stmt.expr, arm_env))
                    elif isinstance(last_stmt, ReturnStatement):
                        arm_types.append(self._check_expr(last_stmt.value, arm_env) if last_stmt.value else 'Null')
                    else:
                        arm_types.append('Any')
                else:
                    arm_types.append('Any')
            elif isinstance(arm.body, ReturnStatement):
                self._check_stmt(arm.body, arm_env, current_fn=current_fn, returns_found=returns_found)
                arm_types.append(self._check_expr(arm.body.value, arm_env) if arm.body.value else 'Null')
            elif isinstance(arm.body, ThrowStatement):
                self._check_stmt(arm.body, arm_env, current_fn=current_fn, returns_found=returns_found)
                arm_types.append('Any')
            elif isinstance(arm.body, AssignStatement):
                self._check_stmt(arm.body, arm_env, current_fn=current_fn, returns_found=returns_found)
                arm_types.append('Any')
            else:
                body_type = self._check_expr(arm.body, arm_env)
                arm_types.append(body_type)

        non_any_types = [t for t in arm_types if t != 'Any']
        if not non_any_types:
            return 'Any'

        first_t = non_any_types[0]
        for t in non_any_types[1:]:
            if not is_type_compatible(first_t, t, env.all_structs()) and not is_type_compatible(t, first_t, env.all_structs()):
                raise TypeCheckError(f"Match shoxobchalarining tiplari mos kelmaydi: '{first_t}' va '{t}'!")

        return first_t


