"""
Zafira Language - Interpreter (Draft Mode)
AST daraxtini bevosita bajaradi.
"""

import concurrent.futures
import asyncio
import time
from typing import Any, Dict, List, Optional
from src.parser import (
    Program, Node, NumberLiteral, StringLiteral, BoolLiteral, NullLiteral,
    Identifier, BinaryOp, UnaryOp, FunctionCall, MemberAccess, IndexAccess,
    ListLiteral, RangeExpr, LetStatement, ConstStatement, AssignStatement,
    ReturnStatement, IfStatement, WhileStatement, ForStatement, FunctionDef,
    StructDef, ImportStatement, RunBlock, ExprStatement, AwaitExpr
)


class ZafiraReturn(Exception):
    def __init__(self, value: Any):
        self.value = value


class ZafiraError(Exception):
    pass


class ZafiraTask:
    """Zafira asinxron vazifasi (Task / Future)"""
    def __init__(self, future: concurrent.futures.Future, name: str = "<anonymous>"):
        self.future = future
        self.name = name

    def result(self, timeout: Optional[float] = None) -> Any:
        try:
            return self.future.result(timeout=timeout)
        except ZafiraReturn as ret:
            return ret.value
        except ZafiraError:
            raise
        except Exception as e:
            raise ZafiraError(f"Asinxron vazifa xatosi ('{self.name}'): {e}")

    def done(self) -> bool:
        return self.future.done()

    def wait(self, timeout: Optional[float] = None) -> Any:
        return self.result(timeout=timeout)

    def __repr__(self):
        status = "bajarildi" if self.done() else "kutilmoqda"
        return f"<Task '{self.name}' status={status}>"


class ZafiraFunction:
    def __init__(self, node: FunctionDef, env: 'Environment', interpreter: Optional['Interpreter'] = None):
        self.node = node
        self.closure = env
        self.interpreter = interpreter

    def __call__(self, *args):
        if self.interpreter is None:
            raise ZafiraError("ZafiraFunction interpreterga bog'lanmagan")
        return self.interpreter.call_function(self, list(args))

    def __repr__(self):
        name = self.node.name if self.node.name else "<anonymous>"
        prefix = "async fn" if getattr(self.node, 'is_async', False) else "fn"
        return f"<{prefix} {name}>"


class ZafiraStruct:
    def __init__(self, type_name: str, fields: Dict[str, Any]):
        self.type_name = type_name
        self.fields = fields

    def __repr__(self):
        flds = ', '.join(f"{k}: {v!r}" for k, v in self.fields.items())
        return f"{self.type_name}{{ {flds} }}"


class ZafiraList:
    def __init__(self, items: List[Any]):
        self.items = items

    def __repr__(self):
        return f"[{', '.join(repr(i) for i in self.items)}]"

    def __len__(self):
        return len(self.items)


# ─── MUHIT (ENVIRONMENT) ───

class Environment:
    def __init__(self, parent: Optional['Environment'] = None):
        self._vars: Dict[str, Any] = {}
        self._consts: set = set()
        self.parent = parent

    def get(self, name: str) -> Any:
        if name in self._vars:
            return self._vars[name]
        if self.parent:
            return self.parent.get(name)
        raise ZafiraError(f"'{name}' o'zgaruvchisi aniqlanmagan")

    def set(self, name: str, value: Any):
        if name in self._consts:
            raise ZafiraError(f"'{name}' — const, uni o'zgartirib bo'lmaydi!")
        self._vars[name] = value

    def define_const(self, name: str, value: Any):
        self._vars[name] = value
        self._consts.add(name)

    def assign(self, name: str, value: Any):
        if name in self._vars:
            if name in self._consts:
                raise ZafiraError(f"'{name}' — const, uni o'zgartirib bo'lmaydi!")
            self._vars[name] = value
            return
        if self.parent:
            self.parent.assign(name, value)
        else:
            raise ZafiraError(f"'{name}' o'zgaruvchisi aniqlanmagan")


# ─── STANDART KUTUBXONA ───

def _builtin_print(*args):
    print(*[_zf_str(a) for a in args])


def _builtin_input(prompt=''):
    return input(prompt)


def _builtin_len(obj):
    if isinstance(obj, (ZafiraList, str)):
        return len(obj) if isinstance(obj, str) else len(obj.items)
    raise ZafiraError(f"len() uchun noto'g'ri tur: {type(obj)}")


def _builtin_range(start, end=None, step=1):
    if end is None:
        start, end = 0, start
    return ZafiraList(list(range(int(start), int(end), int(step))))


def _builtin_type(obj):
    from src.ai_engine import Tensor
    mapping = {int: 'Int', float: 'Float', str: 'String',
               bool: 'Bool', ZafiraList: 'List', ZafiraFunction: 'Fn',
               ZafiraTask: 'Task',
               Tensor: 'Tensor',
               ZafiraStruct: lambda x: x.type_name}
    for k, v in mapping.items():
        if isinstance(obj, k):
            return v(obj) if callable(v) else v
    return 'Null'


def _builtin_int(v):
    try: return int(v)
    except: raise ZafiraError(f"Int ga o'tkazib bo'lmadi: {v!r}")


def _builtin_float(v):
    try: return float(v)
    except: raise ZafiraError(f"Float ga o'tkazib bo'lmadi: {v!r}")


def _builtin_str(v):
    return _zf_str(v)


def _builtin_sleep(secs):
    try:
        time.sleep(float(secs))
        return None
    except Exception as e:
        raise ZafiraError(f"sleep xatosi: {e}")


def _zf_str(v) -> str:
    if v is None:
        return 'null'
    if isinstance(v, bool):
        return 'true' if v else 'false'
    if isinstance(v, (ZafiraList, ZafiraStruct, ZafiraTask)):
        return repr(v)
    from src.ai_engine import Tensor
    if isinstance(v, Tensor):
        return str(v)
    return str(v)


def _builtin_assert(cond, msg="Shart bajarilmadi"):
    if not cond:
        raise ZafiraError(f"AssertionError: {msg}")
    return True


BUILTINS = {
    'print': _builtin_print,
    'input': _builtin_input,
    'len': _builtin_len,
    'range': _builtin_range,
    'type': _builtin_type,
    'Int': _builtin_int,
    'Float': _builtin_float,
    'String': _builtin_str,
    'sleep': _builtin_sleep,
    'assert': _builtin_assert,
}


# ─── INTERPRETER ───

class Interpreter:
    def __init__(self):
        self.global_env = Environment()
        for name, fn in BUILTINS.items():
            self.global_env.set(name, fn)
        self._struct_defs: Dict[str, List[tuple]] = {}
        self._thread_pool = concurrent.futures.ThreadPoolExecutor(
            max_workers=32, thread_name_prefix="ZafiraAsync"
        )

    def close(self):
        if hasattr(self, '_thread_pool') and self._thread_pool:
            self._thread_pool.shutdown(wait=False)

    def __del__(self):
        try:
            self.close()
        except:
            pass

    def run(self, program: Program):
        return self._exec_block(program.body, self.global_env)

    def _exec_block(self, stmts: List[Node], env: Environment) -> Any:
        result = None
        for stmt in stmts:
            result = self._exec(stmt, env)
        return result

    def _exec(self, node: Node, env: Environment) -> Any:
        method = f"_exec_{type(node).__name__}"
        handler = getattr(self, method, None)
        if handler is None:
            raise ZafiraError(f"Ichki xato: '{type(node).__name__}' uchun handler yo'q")
        return handler(node, env)

    # ─── LITERAL HANDLERLAR ───

    def _exec_NumberLiteral(self, node, env): return node.value
    def _exec_StringLiteral(self, node, env): return node.value
    def _exec_BoolLiteral(self, node, env): return node.value
    def _exec_NullLiteral(self, node, env): return None

    def _exec_Identifier(self, node, env):
        return env.get(node.name)

    def _exec_ListLiteral(self, node, env):
        items = [self._exec(el, env) for el in node.elements]
        return ZafiraList(items)

    def _exec_RangeExpr(self, node, env):
        start = int(self._exec(node.start, env))
        end = int(self._exec(node.end, env))
        return ZafiraList(list(range(start, end)))

    # ─── OPERATORLAR ───

    def _exec_BinaryOp(self, node, env):
        left = self._exec(node.left, env)
        right = self._exec(node.right, env)
        op = node.op
        from src.ai_engine import Tensor
        if op == '+':
            if isinstance(left, Tensor) or isinstance(right, Tensor):
                if isinstance(left, Tensor):
                    return left.add(right)
                return right.add(left)
            if isinstance(left, str) or isinstance(right, str):
                return _zf_str(left) + _zf_str(right)
            return left + right
        if op == '-':
            if isinstance(left, Tensor):
                return left.sub(right)
            return left - right
        if op == '*':
            if isinstance(left, Tensor):
                return left.mul(right)
            if isinstance(right, Tensor):
                return right.mul(left)
            if isinstance(left, str) and isinstance(right, int):
                return left * right
            return left * right
        if op == '/':
            if right == 0:
                raise ZafiraError("Nolga bo'lish mumkin emas!")
            return left / right
        if op == '%': return left % right
        if op == '**': return left ** right
        if op == '==': return left == right
        if op == '!=': return left != right
        if op == '<': return left < right
        if op == '>': return left > right
        if op == '<=': return left <= right
        if op == '>=': return left >= right
        if op == 'and': return bool(left) and bool(right)
        if op == 'or': return bool(left) or bool(right)
        raise ZafiraError(f"Noma'lum operator: {op}")

    def _exec_UnaryOp(self, node, env):
        val = self._exec(node.operand, env)
        if node.op == '-': return -val
        if node.op == 'not': return not val
        raise ZafiraError(f"Noma'lum unary operator: {node.op}")

    def _exec_AwaitExpr(self, node, env):
        target = self._exec(node.expr, env)
        if isinstance(target, ZafiraTask):
            return target.result()
        if isinstance(target, concurrent.futures.Future):
            return target.result()
        if hasattr(target, 'result') and callable(getattr(target, 'result')):
            return target.result()
        if asyncio.iscoroutine(target) or isinstance(target, asyncio.Future):
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            if loop.is_running():
                future = asyncio.run_coroutine_threadsafe(target, loop)
                return future.result()
            return loop.run_until_complete(target)
        return target

    # ─── STATEMENT HANDLERLAR ───

    def _exec_ExprStatement(self, node, env):
        return self._exec(node.expr, env)

    def _exec_LetStatement(self, node, env):
        value = self._exec(node.value, env) if node.value else None
        env.set(node.name, value)
        return None

    def _exec_ConstStatement(self, node, env):
        value = self._exec(node.value, env)
        env.define_const(node.name, value)
        return None

    def _exec_AssignStatement(self, node, env):
        value = self._exec(node.value, env)
        if isinstance(node.target, Identifier):
            env.assign(node.target.name, value)
        elif isinstance(node.target, MemberAccess):
            obj = self._exec(node.target.obj, env)
            if isinstance(obj, ZafiraStruct):
                obj.fields[node.target.member] = value
            else:
                raise ZafiraError("Faqat struct maydonlari o'zgartirilishi mumkin")
        elif isinstance(node.target, IndexAccess):
            obj = self._exec(node.target.obj, env)
            raw_idx = self._exec(node.target.index, env)
            if isinstance(obj, ZafiraStruct) and isinstance(raw_idx, str):
                obj.fields[raw_idx] = value
            elif isinstance(obj, ZafiraList):
                idx = int(raw_idx)
                obj.items[idx] = value
        return None

    def _exec_ReturnStatement(self, node, env):
        value = self._exec(node.value, env) if node.value else None
        raise ZafiraReturn(value)

    def _exec_IfStatement(self, node, env):
        cond = self._exec(node.condition, env)
        if cond:
            child_env = Environment(parent=env)
            return self._exec_block(node.then_block, child_env)
        elif node.else_block:
            child_env = Environment(parent=env)
            return self._exec_block(node.else_block, child_env)
        return None

    def _exec_WhileStatement(self, node, env):
        result = None
        while self._exec(node.condition, env):
            child_env = Environment(parent=env)
            try:
                result = self._exec_block(node.body, child_env)
            except ZafiraReturn:
                raise
        return result

    def _exec_ForStatement(self, node, env):
        iterable = self._exec(node.iterable, env)
        items = iterable.items if isinstance(iterable, ZafiraList) else list(iterable)
        result = None
        for item in items:
            child_env = Environment(parent=env)
            child_env.set(node.var, item)
            try:
                result = self._exec_block(node.body, child_env)
            except ZafiraReturn:
                raise
        return result

    def _exec_FunctionDef(self, node, env):
        fn = ZafiraFunction(node=node, env=env, interpreter=self)
        if node.name:
            env.set(node.name, fn)
        return fn

    def _exec_StructDef(self, node, env):
        self._struct_defs[node.name] = node.fields
        # Constructor funksiyani muhitga qo'shamiz
        def constructor(*args, **kwargs):
            fields = {}
            for i, (name, _) in enumerate(node.fields):
                if i < len(args):
                    fields[name] = args[i]
                elif name in kwargs:
                    fields[name] = kwargs[name]
                else:
                    fields[name] = None
            return ZafiraStruct(node.name, fields)
        env.set(node.name, constructor)
        return None

    def _exec_ImportStatement(self, node, env):
        if node.path.startswith('py.'):
            from src.python_interop import PythonInterop
            PythonInterop.import_module(node.path, env)
        elif node.path.startswith('std.'):
            from src.stdlib import load_stdlib_module
            load_stdlib_module(node.path, env)
        elif node.path == 'sys.io':
            env.set('print', _builtin_print)
            env.set('input', _builtin_input)
        else:
            print(f"[Zafira] '{node.path}' moduli hozircha qo'llab-quvvatlanmaydi")
        return None

    def _exec_RunBlock(self, node, env):
        target = node.target
        if target not in ('@gpu', '@npu', '@auto', '@cpu'):
            raise ZafiraError(f"Noma'lum hardware target: {target}")

        from src.ai_engine import silicon_context, get_active_device
        device_name = target.lstrip('@')
        with silicon_context(device_name):
            active_device = get_active_device()
            print(f"[Zafira Silicon Runtime] {target} bloki faollashtirildi (Apparat: {active_device.upper()})")
            child_env = Environment(parent=env)
            child_env.set('__device__', active_device)
            return self._exec_block(node.body, child_env)

    # ─── FUNKSIYA CHAQIRISH ───

    def _call_sync_function(self, fn: ZafiraFunction, args: list) -> Any:
        call_env = Environment(parent=fn.closure)
        for (pname, _), arg in zip(fn.node.params, args):
            call_env.set(pname, arg)
        try:
            return self._exec_block(fn.node.body, call_env)
        except ZafiraReturn as ret:
            return ret.value
        return None

    def call_function(self, fn: ZafiraFunction, args: list) -> Any:
        # where (invariant) tekshiruvi
        if fn.node.where_clause:
            check_env = Environment(parent=fn.closure)
            for (pname, _), arg in zip(fn.node.params, args):
                check_env.set(pname, arg)
            ok = self._exec(fn.node.where_clause, check_env)
            if not ok:
                raise ZafiraError(
                    f"'{fn.node.name}' funksiyasi 'where' sharti bajarilmadi! "
                    f"Chaqirildi: {args}"
                )

        if getattr(fn.node, 'is_async', False):
            future = self._thread_pool.submit(self._call_sync_function, fn, args)
            return ZafiraTask(future=future, name=fn.node.name or "<anonymous>")

        return self._call_sync_function(fn, args)

    def _exec_FunctionCall(self, node, env):
        callee = self._exec(node.callee, env)
        args = [self._exec(a, env) for a in node.args]

        if isinstance(callee, ZafiraFunction):
            return self.call_function(callee, args)

        # Python builtin funksiya
        if callable(callee):
            return callee(*args)

        raise ZafiraError(f"{callee!r} — funksiya emas!")

    def _exec_MemberAccess(self, node, env):
        obj = self._exec(node.obj, env)
        member = node.member

        if isinstance(obj, ZafiraTask):
            if member == 'done':
                return obj.done
            if member == 'result':
                return obj.result
            if member == 'wait':
                return obj.wait
            raise ZafiraError(f"Task da '{member}' metodi yo'q")

        if isinstance(obj, ZafiraStruct):
            if member in obj.fields:
                return obj.fields[member]
            raise ZafiraError(f"'{obj.type_name}' da '{member}' maydoni yo'q")

        if isinstance(obj, ZafiraList):
            # Ro'yxat metodlari
            if member == 'push':
                return lambda item: obj.items.append(item)
            if member == 'pop':
                return lambda: obj.items.pop()
            if member == 'len':
                return len(obj.items)
            if member == 'first':
                return obj.items[0] if obj.items else None
            if member == 'last':
                return obj.items[-1] if obj.items else None
            raise ZafiraError(f"List da '{member}' metodi yo'q")

        if isinstance(obj, str):
            if member == 'len': return len(obj)
            if member == 'upper': return obj.upper()
            if member == 'lower': return obj.lower()
            if member == 'trim': return obj.strip()
            raise ZafiraError(f"String da '{member}' metodi yo'q")

        from src.ai_engine import Tensor
        if isinstance(obj, Tensor):
            if member == 'shape':
                return obj.shape
            if member == 'device':
                return obj.device
            if member in ('data', 'to_list', 'tolist'):
                return obj.to_list()
            if hasattr(obj, member):
                attr = getattr(obj, member)
                if callable(attr):
                    return attr
            raise ZafiraError(f"Tensor turida '{member}' metodi yoki maydoni yo'q")

        raise ZafiraError(f"'{type(obj).__name__}' turida '{member}' yo'q")

    def _exec_IndexAccess(self, node, env):
        obj = self._exec(node.obj, env)
        raw_idx = self._exec(node.index, env)
        if isinstance(obj, ZafiraStruct) and isinstance(raw_idx, str):
            if raw_idx in obj.fields:
                return obj.fields[raw_idx]
            raise ZafiraError(f"'{obj.type_name}' da '{raw_idx}' maydoni yo'q")
        idx = int(raw_idx)
        if isinstance(obj, ZafiraList):
            try:
                return obj.items[idx]
            except IndexError:
                raise ZafiraError(f"Indeks [{idx}] chegaradan tashqarida (uzunlik: {len(obj.items)})")
        if isinstance(obj, str):
            try:
                return obj[idx]
            except IndexError:
                raise ZafiraError(f"String indeksi [{idx}] chegaradan tashqarida")
        from src.ai_engine import Tensor
        if isinstance(obj, Tensor):
            try:
                return obj[idx]
            except IndexError:
                raise ZafiraError(f"Tensor indeksi [{idx}] chegaradan tashqarida (shape: {obj.shape})")
        raise ZafiraError(f"'{type(obj).__name__}' indekslash qo'llab-quvvatlanmaydi")
