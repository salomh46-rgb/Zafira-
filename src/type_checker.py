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

from src.parser import (
    Program, Node, NumberLiteral, StringLiteral, BoolLiteral, NullLiteral,
    Identifier, BinaryOp, UnaryOp, FunctionCall, MemberAccess, IndexAccess,
    ListLiteral, RangeExpr, LetStatement, ConstStatement, AssignStatement,
    ReturnStatement, IfStatement, WhileStatement, ForStatement, FunctionDef,
    StructDef, ImportStatement, RunBlock, ExprStatement, Block
)


class TypeCheckError(Exception):
    """Zafira tili tip xatoligi istisnosi"""
    pass


# Zafira tilining asosiy tiplari
VALID_TYPES = {'Int', 'Float', 'String', 'Bool', 'List', 'Null', 'Any'}


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


class TypeEnvironment:
    """Tip tekshiruvi leksik doirasi (scope)."""
    def __init__(self, parent: Optional['TypeEnvironment'] = None):
        self.parent = parent
        self.symbols: Dict[str, Symbol] = {}
        self.functions: Dict[str, FunctionSignature] = {}
        self.structs: Dict[str, List[Tuple[str, str]]] = {}

    def declare(self, name: str, type_name: str = 'Any', is_const: bool = False, const_value: Any = None) -> Symbol:
        sym = Symbol(name=name, type_name=type_name, is_const=is_const, const_value=const_value)
        self.symbols[name] = sym
        return sym

    def declare_function(self, name: str, params: List[Tuple[str, Optional[str]]],
                         return_type: str = 'Any', mode: str = 'draft',
                         where_clause: Optional[Node] = None) -> FunctionSignature:
        fn_sig = FunctionSignature(name=name, params=params, return_type=return_type,
                                   mode=mode, where_clause=where_clause)
        self.functions[name] = fn_sig
        self.declare(name, type_name='Fn', is_const=True)
        return fn_sig

    def declare_struct(self, name: str, fields: List[Tuple[str, str]]):
        self.structs[name] = fields
        self.declare(name, type_name='Fn', is_const=True)

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
    return env


class TypeChecker:
    """AST daraxtini aylanib chiquvchi Zafira Statik Type Checker."""

    def __init__(self):
        self.root_env = create_root_env()

    def check(self, program: Program):
        """Program AST daraxtini bir marta (single-pass) aylanib chiqadi."""
        # 1. Top-level funksiyalar va structlarni ro'yxatga olamiz (forward-declaration / recursion uchun)
        for stmt in program.body:
            if isinstance(stmt, FunctionDef):
                self.root_env.declare_function(
                    name=stmt.name,
                    params=stmt.params,
                    return_type=stmt.return_type or 'Any',
                    mode=stmt.mode,
                    where_clause=stmt.where_clause
                )
            elif isinstance(stmt, StructDef):
                self.root_env.declare_struct(stmt.name, stmt.fields)

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
            self._check_expr(node.target.obj, env)
            idx_type = self._check_expr(node.target.index, env)
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

    def _check_ImportStatement(self, node: ImportStatement, env: TypeEnvironment, **kwargs):
        if node.path == 'sys.io':
            env.declare('print', type_name='Fn', is_const=True)
            env.declare('input', type_name='Fn', is_const=True)
        elif node.path.startswith('py.'):
            mod_path = node.path[3:]
            root_name = mod_path.split('.')[0]
            env.declare(root_name, type_name='Any', is_const=True)
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

    def _check_RunBlock(self, node: RunBlock, env: TypeEnvironment,
                        current_fn: Optional[FunctionDef] = None,
                        returns_found: Optional[List[str]] = None, **kwargs):
        child_env = TypeEnvironment(parent=env)
        for s in node.body:
            self._check_stmt(s, child_env, current_fn=current_fn, returns_found=returns_found)

    def _check_ExprStatement(self, node: ExprStatement, env: TypeEnvironment, **kwargs):
        self._check_expr(node.expr, env)

    def _check_Block(self, node: Block, env: TypeEnvironment,
                     current_fn: Optional[FunctionDef] = None,
                     returns_found: Optional[List[str]] = None, **kwargs):
        child_env = TypeEnvironment(parent=env)
        for s in node.statements:
            self._check_stmt(s, child_env, current_fn=current_fn, returns_found=returns_found)

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

                return fn.return_type or 'Any'
            else:
                # 'draft' funksiyalar erkin qoldiriladi
                for a in node.args: self._check_expr(a, env)
                return fn.return_type or 'Any'

        elif isinstance(callee, MemberAccess):
            obj_type = self._check_expr(callee.obj, env)
            for a in node.args: self._check_expr(a, env)
            if obj_type == 'List':
                if callee.member in ('push',): return 'Null'
                if callee.member in ('pop',): return 'Any'
            if obj_type == 'String':
                if callee.member in ('upper', 'lower', 'trim'): return 'String'
            return 'Any'

        else:
            self._check_expr(callee, env)
            for a in node.args: self._check_expr(a, env)
            return 'Any'

    def _infer_MemberAccess(self, node: MemberAccess, env: TypeEnvironment) -> str:
        obj_type = self._check_expr(node.obj, env)
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
            for fname, ftype in fields:
                if fname == node.member:
                    return ftype
            raise TypeCheckError(f"'{obj_type}' strukturasida '{node.member}' maydoni mavjud emas!")
        return 'Any'

    def _infer_IndexAccess(self, node: IndexAccess, env: TypeEnvironment) -> str:
        obj_type = self._check_expr(node.obj, env)
        idx_type = self._check_expr(node.index, env)
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
