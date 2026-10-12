"""
Zafira Language - Standart Kutubxona (stdlib)
Standart modullar: std.math, std.string, std.list, std.io
"""

import math
import sys
from typing import Any, Callable, Dict, List, Optional
from src.interpreter import ZafiraStruct, ZafiraList, ZafiraError, _zf_str


class ZafiraModule(ZafiraStruct):
    """
    Zafira tili standart kutubxona moduli.
    ZafiraStruct sifatida ishlaydi va MemberAccess (masalan: math.sqrt)
    orqali chaqiriladi.
    """

    def __init__(self, name: str, fields: Dict[str, Any]):
        super().__init__(type_name=f"std.{name}", fields=fields)
        self.name = name

    def __repr__(self) -> str:
        return f"<module '{self.type_name}'>"


# ─── YORDAMCHI FUNKSIYALAR ───

def _to_py_list(val: Any) -> list:
    if isinstance(val, ZafiraList):
        return val.items
    if isinstance(val, list):
        return val
    raise ZafiraError(f"Ro'yxat kutilgan edi, lekin '{type(val).__name__}' berildi")


def _call_callable(fn: Any, *args) -> Any:
    if callable(fn):
        return fn(*args)
    raise ZafiraError(f"'{fn!r}' funksiya emas")


# ─── 1. STD.MATH ───

def _math_sqrt(x):
    try:
        val = float(x)
        if val < 0:
            raise ZafiraError("Manfiy sondan kvadrat ildiz olib bo'lmaydi")
        return math.sqrt(val)
    except ValueError as e:
        raise ZafiraError(f"sqrt() xatosi: {e}")

def _math_pow(base, exp):
    try:
        return math.pow(float(base), float(exp))
    except Exception as e:
        raise ZafiraError(f"pow() xatosi: {e}")

def _math_abs(x):
    try:
        return abs(x)
    except Exception as e:
        raise ZafiraError(f"abs() xatosi: {e}")

def _math_floor(x):
    try:
        return math.floor(float(x))
    except Exception as e:
        raise ZafiraError(f"floor() xatosi: {e}")

def _math_ceil(x):
    try:
        return math.ceil(float(x))
    except Exception as e:
        raise ZafiraError(f"ceil() xatosi: {e}")

def _math_round(x, n=None):
    try:
        if n is not None:
            return round(float(x), int(n))
        return round(float(x))
    except Exception as e:
        raise ZafiraError(f"round() xatosi: {e}")

def _math_min(*args):
    if not args:
        raise ZafiraError("min() argumentlari kutilmoqda")
    if len(args) == 1:
        items = _to_py_list(args[0])
        if not items:
            raise ZafiraError("min() bo'sh ro'yxat uchun chaqirib bo'lmaydi")
        return min(items)
    return min(args)

def _math_max(*args):
    if not args:
        raise ZafiraError("max() argumentlari kutilmoqda")
    if len(args) == 1:
        items = _to_py_list(args[0])
        if not items:
            raise ZafiraError("max() bo'sh ro'yxat uchun chaqirib bo'lmaydi")
        return max(items)
    return max(args)

def _math_log(x, base=None):
    try:
        val = float(x)
        if val <= 0:
            raise ZafiraError("Logarifm argumenti musbat bo'lishi kerak")
        if base is not None:
            return math.log(val, float(base))
        return math.log(val)
    except Exception as e:
        if isinstance(e, ZafiraError): raise
        raise ZafiraError(f"log() xatosi: {e}")

def _math_sin(x):
    try:
        return math.sin(float(x))
    except Exception as e:
        raise ZafiraError(f"sin() xatosi: {e}")

def _math_cos(x):
    try:
        return math.cos(float(x))
    except Exception as e:
        raise ZafiraError(f"cos() xatosi: {e}")

def _math_tan(x):
    try:
        return math.tan(float(x))
    except Exception as e:
        raise ZafiraError(f"tan() xatosi: {e}")

MATH_MODULE = ZafiraModule('math', {
    'sqrt': _math_sqrt,
    'pow': _math_pow,
    'abs': _math_abs,
    'floor': _math_floor,
    'ceil': _math_ceil,
    'round': _math_round,
    'min': _math_min,
    'max': _math_max,
    'log': _math_log,
    'sin': _math_sin,
    'cos': _math_cos,
    'tan': _math_tan,
    'PI': math.pi,
    'pi': math.pi,
    'E': math.e,
    'e': math.e,
    'INF': math.inf,
    'inf': math.inf,
})


# ─── 2. STD.STRING ───

def _string_upper(s):
    return str(s).upper()

def _string_lower(s):
    return str(s).lower()

def _string_trim(s):
    return str(s).strip()

def _string_split(s, sep=None):
    raw = str(s)
    if sep is None:
        parts = raw.split()
    else:
        parts = raw.split(str(sep))
    return ZafiraList(parts)

def _string_join(lst, sep=""):
    items = _to_py_list(lst)
    return str(sep).join(_zf_str(i) for i in items)

def _string_replace(s, old, new, count=-1):
    raw = str(s)
    old_str = str(old)
    new_str = str(new)
    if count is None or int(count) < 0:
        return raw.replace(old_str, new_str)
    return raw.replace(old_str, new_str, int(count))

def _string_contains(s, sub):
    return str(sub) in str(s)

def _string_starts_with(s, prefix):
    return str(s).startswith(str(prefix))

def _string_ends_with(s, suffix):
    return str(s).endswith(str(suffix))

def _string_repeat(s, n):
    return str(s) * int(n)

def _string_reverse(s):
    return str(s)[::-1]

STRING_MODULE = ZafiraModule('string', {
    'upper': _string_upper,
    'lower': _string_lower,
    'trim': _string_trim,
    'split': _string_split,
    'join': _string_join,
    'replace': _string_replace,
    'contains': _string_contains,
    'starts_with': _string_starts_with,
    'ends_with': _string_ends_with,
    'repeat': _string_repeat,
    'reverse': _string_reverse,
})


# ─── 3. STD.LIST ───

def _list_sort(lst, key=None, reverse=False):
    items = list(_to_py_list(lst))
    if key is not None:
        items.sort(key=lambda x: _call_callable(key, x), reverse=bool(reverse))
    else:
        items.sort(reverse=bool(reverse))
    return ZafiraList(items)

def _list_reverse(lst):
    items = list(reversed(_to_py_list(lst)))
    return ZafiraList(items)

def _list_filter(lst, predicate):
    items = _to_py_list(lst)
    res = [x for x in items if bool(_call_callable(predicate, x))]
    return ZafiraList(res)

def _list_map(lst, transform):
    items = _to_py_list(lst)
    res = [_call_callable(transform, x) for x in items]
    return ZafiraList(res)

def _list_reduce(lst, fn, initial=None):
    items = _to_py_list(lst)
    if not items:
        if initial is not None:
            return initial
        raise ZafiraError("reduce() bo'sh ro'yxatda boshlang'ich qiymatsiz ishlatilmaydi")
    if initial is None:
        acc = items[0]
        rest = items[1:]
    else:
        acc = initial
        rest = items
    for item in rest:
        acc = _call_callable(fn, acc, item)
    return acc

def _list_find(lst, predicate):
    items = _to_py_list(lst)
    for item in items:
        if bool(_call_callable(predicate, item)):
            return item
    return None

def _list_contains(lst, target):
    items = _to_py_list(lst)
    return target in items

def _list_unique(lst):
    items = _to_py_list(lst)
    res = []
    seen = set()
    for item in items:
        try:
            if item not in seen:
                seen.add(item)
                res.append(item)
        except TypeError:
            if item not in res:
                res.append(item)
    return ZafiraList(res)

def _list_flatten(lst):
    items = _to_py_list(lst)
    res = []
    for item in items:
        if isinstance(item, (ZafiraList, list)):
            res.extend(_to_py_list(item))
        else:
            res.append(item)
    return ZafiraList(res)

def _list_sum(lst):
    items = _to_py_list(lst)
    return sum(items)

def _list_max(lst):
    items = _to_py_list(lst)
    if not items:
        raise ZafiraError("max() bo'sh ro'yxat uchun chaqirib bo'lmaydi")
    return max(items)

def _list_min(lst):
    items = _to_py_list(lst)
    if not items:
        raise ZafiraError("min() bo'sh ro'yxat uchun chaqirib bo'lmaydi")
    return min(items)

LIST_MODULE = ZafiraModule('list', {
    'sort': _list_sort,
    'reverse': _list_reverse,
    'filter': _list_filter,
    'map': _list_map,
    'reduce': _list_reduce,
    'find': _list_find,
    'contains': _list_contains,
    'unique': _list_unique,
    'flatten': _list_flatten,
    'sum': _list_sum,
    'max': _list_max,
    'min': _list_min,
})


# ─── 4. STD.IO ───

def _io_print(*args):
    print(*[_zf_str(a) for a in args], end='', flush=True)

def _io_println(*args):
    print(*[_zf_str(a) for a in args], flush=True)

def _io_readline(prompt=''):
    return input(_zf_str(prompt) if prompt else '')

def _io_write(text):
    sys.stdout.write(_zf_str(text))
    sys.stdout.flush()

IO_MODULE = ZafiraModule('io', {
    'print': _io_print,
    'println': _io_println,
    'readline': _io_readline,
    'write': _io_write,
})


# ─── STDLIB MODULES RO'YXATI ───

STDLIB_MODULES: Dict[str, ZafiraModule] = {
    'math': MATH_MODULE,
    'string': STRING_MODULE,
    'list': LIST_MODULE,
    'io': IO_MODULE,
}


def load_stdlib_module(path: str, env) -> None:
    parts = path.split('.')
    if len(parts) < 2:
        raise ZafiraError(f"Noto'g'ri modul yo'li: '{path}'")
    module_name = parts[1]  # 'std.math' -> 'math'
    module = STDLIB_MODULES.get(module_name)
    if module is None:
        raise ZafiraError(f"'{path}' moduli topilmadi")
    env.set(module_name, module)
