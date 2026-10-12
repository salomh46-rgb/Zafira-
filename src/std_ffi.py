"""
Zafira Language - std.ffi moduli
C FFI (Foreign Function Interface) xavfsiz wrapper (Python ctypes asosida).
Standart C libc, msvcrt, kernel32 va dinamik kutubxonalarni (DLL / .so / .dylib)
yuklash hamda C funksiyalarini xavfsiz chaqirish imkoniyati.
"""

import ctypes
import ctypes.util
import os
import sys
from typing import Any, Dict, List, Optional, Union

from src.interpreter import ZafiraError, ZafiraList, ZafiraStruct, _zf_str


class CValue(ZafiraStruct):
    """
    FFI C turi qiymatini o'rab turuvchi ZafiraStruct.
    Zafira ichida c.value va c.type maydonlari orqali qiymatlarni olish mumkin.
    """

    def __init__(self, c_type: str, value: Any, c_obj: Any):
        t_name = f"C{c_type.capitalize()}"
        super().__init__(type_name=t_name, fields={
            'type': c_type,
            'value': value,
        })
        self.c_type = c_type
        self.c_obj = c_obj
        self._raw_ref = c_obj

    def __repr__(self) -> str:
        return f"{self.type_name}{{ type: '{self.c_type}', value: {self.fields['value']!r} }}"


class FfiLibrary(ZafiraStruct):
    """
    FFI orqali yuklangan dinamik kutubxona (C DLL / Shared Library).
    lib.call(...) va lib.has_symbol(...) metodlariga ega.
    """

    def __init__(self, name: str, cdll: ctypes.CDLL):
        self.lib_name = name
        self.cdll = cdll

        def _lib_call(func_name: Any, args: Any = None, return_type: Any = "int") -> Any:
            return _call_library_function(self.cdll, self.lib_name, func_name, args, return_type)

        def _lib_has_symbol(symbol_name: Any) -> bool:
            return _library_has_symbol(self.cdll, symbol_name)

        super().__init__(type_name='FfiLibrary', fields={
            'name': name,
            'call': _lib_call,
            'has_symbol': _lib_has_symbol,
            'has': _lib_has_symbol,
        })

    def __repr__(self) -> str:
        return f"<FfiLibrary '{self.lib_name}'>"


def _load_cdll(lib_name: Optional[str]) -> ctypes.CDLL:
    """Tizim yoki fayl yo'li bo'yicha dinamik kutubxonani (CDLL) yuklaydi."""
    is_win = sys.platform.startswith('win')
    norm = lib_name.strip() if isinstance(lib_name, str) else ""

    # 1. Standart C libc / msvcrt / ucrtbase
    if norm.lower() in ("", "c", "libc", "msvcrt", "ucrtbase"):
        if is_win:
            return ctypes.cdll.msvcrt
        found = ctypes.util.find_library('c')
        if found:
            return ctypes.CDLL(found)
        try:
            return ctypes.CDLL("libc.so.6")
        except Exception:
            return ctypes.CDLL(None)

    # 2. Standart C math kutubxonasi (libm)
    if norm.lower() in ("m", "libm"):
        if is_win:
            return ctypes.cdll.msvcrt
        found = ctypes.util.find_library('m')
        if found:
            return ctypes.CDLL(found)
        try:
            return ctypes.CDLL("libm.so.6")
        except Exception:
            pass

    # 3. Windows tizim kutubxonalari (kernel32, user32)
    if is_win and norm.lower() in ("kernel32", "kernel32.dll"):
        return ctypes.cdll.LoadLibrary("kernel32.dll")
    if is_win and norm.lower() in ("user32", "user32.dll"):
        return ctypes.cdll.LoadLibrary("user32.dll")

    # 4. Umumiy nom yoki fayl yo'li bo'yicha qidirish
    last_err = None
    try:
        return ctypes.CDLL(norm)
    except Exception as e:
        last_err = e

    if is_win:
        try:
            return ctypes.cdll.LoadLibrary(norm)
        except Exception as e:
            last_err = e

    found = ctypes.util.find_library(norm)
    if found:
        try:
            return ctypes.CDLL(found)
        except Exception as e:
            last_err = e

    if is_win and not norm.lower().endswith('.dll'):
        try:
            return ctypes.CDLL(f"{norm}.dll")
        except Exception as e:
            last_err = e
        try:
            return ctypes.cdll.LoadLibrary(f"{norm}.dll")
        except Exception as e:
            last_err = e

    raise ZafiraError(f"FFI xatosi: '{norm}' kutubxonasi topilmadi: {last_err}")


def _library_has_symbol(cdll: ctypes.CDLL, symbol_name: Any) -> bool:
    """Kutubxonada berilgan nomli simvol (funksiya) mavjudligini tekshiradi."""
    if not isinstance(symbol_name, str):
        raise ZafiraError(
            f"has_symbol() funksiya nomi satr (String) bo'lishi kerak, lekin '{type(symbol_name).__name__}' berildi"
        )
    if not symbol_name:
        return False

    if hasattr(cdll, symbol_name):
        return True

    try:
        cdll[symbol_name]
        return True
    except (AttributeError, KeyError, IndexError, ValueError, TypeError):
        pass

    # Linux/POSIX libm tekshiruvi (matematik funksiyalar uchun)
    if symbol_name in ("sqrt", "pow", "sin", "cos", "tan", "floor", "ceil", "log", "exp"):
        try:
            libm = _load_cdll("m")
            if hasattr(libm, symbol_name):
                return True
            libm[symbol_name]
            return True
        except Exception:
            pass

    return False


def _call_library_function(
    cdll: ctypes.CDLL,
    lib_name: str,
    func_name: Any,
    args: Any = None,
    return_type: Any = "int",
) -> Any:
    """Kutubxona funksiyasini argumentlar va qaytish turi bilan chaqiradi."""
    if not isinstance(func_name, str):
        raise ZafiraError(
            f"FFI chaqiruv xatosi: Funksiya nomi satr (String) bo'lishi kerak, lekin '{type(func_name).__name__}' berildi"
        )

    # Funksiyani olish
    c_func = None
    try:
        c_func = getattr(cdll, func_name)
    except AttributeError:
        try:
            c_func = cdll[func_name]
        except Exception:
            pass

    # Linux/POSIX tizimlarida sqrt, pow, sin, cos kabi matematik funksiyalar libc da emas, libm da joylashgan
    if c_func is None and lib_name.lower() in ("libc", "c", "") and func_name in ("sqrt", "pow", "sin", "cos", "tan", "floor", "ceil", "log", "exp"):
        try:
            libm = _load_cdll("m")
            c_func = getattr(libm, func_name, None) or libm[func_name]
        except Exception:
            pass

    if c_func is None:
        raise ZafiraError(
            f"FFI xatosi: '{func_name}' funksiyasi '{lib_name}' kutubxonasida topilmadi"
        )

    # Argumentlarni Zafira / Python turlaridan ajratib olish
    if args is None:
        raw_args = []
    elif isinstance(args, ZafiraList):
        raw_args = list(args.items)
    elif isinstance(args, list):
        raw_args = list(args)
    else:
        raw_args = [args]

    c_args = []
    keep_alive = []

    for a in raw_args:
        if isinstance(a, CValue):
            c_args.append(a.c_obj)
        elif isinstance(a, bool):
            c_args.append(ctypes.c_bool(a))
        elif isinstance(a, int):
            if -2147483648 <= a <= 2147483647:
                c_args.append(ctypes.c_int(a))
            else:
                c_args.append(ctypes.c_longlong(a))
        elif isinstance(a, float):
            c_args.append(ctypes.c_double(a))
        elif isinstance(a, str):
            encoded = a.encode('utf-8')
            keep_alive.append(encoded)
            c_args.append(ctypes.c_char_p(encoded))
        elif isinstance(a, bytes):
            keep_alive.append(a)
            c_args.append(ctypes.c_char_p(a))
        elif a is None:
            c_args.append(None)
        elif isinstance(a, (ctypes.c_int, ctypes.c_double, ctypes.c_float, ctypes.c_char_p, ctypes.c_void_p, ctypes.c_longlong, ctypes.c_bool)):
            c_args.append(a)
        else:
            encoded = _zf_str(a).encode('utf-8')
            keep_alive.append(encoded)
            c_args.append(ctypes.c_char_p(encoded))

    # Qaytish turi (return_type) konfiguratsiyasi
    r_type_str = str(return_type).lower().strip() if return_type is not None else "int"
    if r_type_str in ("int", "int32", "c_int", "i32"):
        c_func.restype = ctypes.c_int
    elif r_type_str in ("int64", "long", "longlong", "i64", "c_longlong"):
        c_func.restype = ctypes.c_longlong
    elif r_type_str in ("float", "double", "c_double", "c_float", "f64"):
        c_func.restype = ctypes.c_double
    elif r_type_str in ("float32", "f32"):
        c_func.restype = ctypes.c_float
    elif r_type_str in ("string", "str", "char*", "c_string", "c_char_p"):
        c_func.restype = ctypes.c_char_p
    elif r_type_str in ("void", "null", "none"):
        c_func.restype = None
    elif r_type_str in ("bool", "c_bool", "boolean"):
        c_func.restype = ctypes.c_bool
    elif r_type_str in ("pointer", "ptr", "void*", "c_void_p"):
        c_func.restype = ctypes.c_void_p
    elif r_type_str in ("size_t", "uint"):
        c_func.restype = ctypes.c_size_t
    else:
        raise ZafiraError(f"FFI xatosi: Noma'lum qaytarish turi (return_type): '{return_type}'")

    # Funksiyani chaqirish
    try:
        result = c_func(*c_args)
    except Exception as e:
        raise ZafiraError(f"FFI chaqiruv xatosi: '{func_name}' chaqirishda xatolik: {e}")

    # Natijani Zafira formatiga o'tkazish
    if r_type_str in ("string", "str", "char*", "c_string", "c_char_p"):
        if isinstance(result, bytes):
            return result.decode('utf-8', errors='replace')
        return result
    if r_type_str in ("void", "null", "none"):
        return None
    if r_type_str in ("bool", "c_bool", "boolean"):
        return bool(result)
    if r_type_str in ("int", "int32", "c_int", "i32", "int64", "long", "longlong", "i64"):
        return int(result) if result is not None else 0
    if r_type_str in ("float", "double", "c_double", "c_float", "f64", "float32", "f32"):
        return float(result) if result is not None else 0.0

    return result


def _ffi_load(lib_name: Any = None) -> FfiLibrary:
    """
    Dinamik C kutubxonasini yuklaydi va FfiLibrary struct nusxasini qaytaradi.
    Standart C kutubxonasi uchun 'c', 'libc' yoki null ko'rsatilishi mumkin.
    """
    if lib_name is not None and not isinstance(lib_name, str):
        raise ZafiraError(
            f"ffi.load() kutubxona nomi satr (String) bo'lishi kerak, lekin '{type(lib_name).__name__}' berildi"
        )
    cdll = _load_cdll(lib_name)
    display_name = lib_name if (isinstance(lib_name, str) and lib_name) else "libc"
    return FfiLibrary(display_name, cdll)


def _ffi_libc() -> FfiLibrary:
    """Tizim standart C kutubxonasini yuklaydi (msvcrt / libc)."""
    return _ffi_load("libc")


def _ffi_c_int(val: Any) -> CValue:
    """Qiymatni C 32-bit int turiga o'raydi."""
    try:
        iv = int(val)
        return CValue('int', iv, ctypes.c_int(iv))
    except (ValueError, TypeError) as e:
        raise ZafiraError(f"c_int() xatosi: '{val}' butun songa o'girilmadi: {e}")


def _ffi_c_float(val: Any) -> CValue:
    """Qiymatni C double/float turiga o'raydi."""
    try:
        fv = float(val)
        return CValue('float', fv, ctypes.c_double(fv))
    except (ValueError, TypeError) as e:
        raise ZafiraError(f"c_float() xatosi: '{val}' haqiqiy songa o'girilmadi: {e}")


def _ffi_c_double(val: Any) -> CValue:
    """Qiymatni C 64-bit double turiga o'raydi."""
    try:
        fv = float(val)
        return CValue('double', fv, ctypes.c_double(fv))
    except (ValueError, TypeError) as e:
        raise ZafiraError(f"c_double() xatosi: '{val}' haqiqiy songa o'girilmadi: {e}")


def _ffi_c_string(val: Any) -> CValue:
    """Qiymatni C char* satr turiga o'raydi."""
    if val is None:
        return CValue('string', None, ctypes.c_char_p(None))
    if isinstance(val, bytes):
        decoded = val.decode('utf-8', errors='replace')
        c_obj = ctypes.c_char_p(val)
        cv = CValue('string', decoded, c_obj)
        cv._raw_bytes = val
        return cv
    s = val if isinstance(val, str) else _zf_str(val)
    encoded = s.encode('utf-8')
    c_obj = ctypes.c_char_p(encoded)
    cv = CValue('string', s, c_obj)
    cv._raw_bytes = encoded
    return cv


def _ffi_c_bool(val: Any) -> CValue:
    """Qiymatni C bool turiga o'raydi."""
    bv = bool(val)
    return CValue('bool', bv, ctypes.c_bool(bv))


def _ffi_call_global(lib: Any, func_name: Any, args: Any = None, return_type: Any = "int") -> Any:
    """ffi.call(lib, func_name, args, return_type) global ko'rinishda chaqirish."""
    if isinstance(lib, FfiLibrary):
        return lib.fields['call'](func_name, args, return_type)
    if isinstance(lib, ZafiraStruct) and 'call' in lib.fields and callable(lib.fields['call']):
        return lib.fields['call'](func_name, args, return_type)
    raise ZafiraError("ffi.call(): birinchi argument FfiLibrary bo'lishi kerak")


def _ffi_has_symbol_global(lib: Any, name: Any) -> bool:
    """ffi.has_symbol(lib, name) global ko'rinishda tekshirish."""
    if isinstance(lib, FfiLibrary):
        return lib.fields['has_symbol'](name)
    if isinstance(lib, ZafiraStruct) and 'has_symbol' in lib.fields and callable(lib.fields['has_symbol']):
        return lib.fields['has_symbol'](name)
    raise ZafiraError("ffi.has_symbol(): birinchi argument FfiLibrary bo'lishi kerak")


def create_ffi_module():
    """std.ffi ZafiraModule nusxasini yaratadi."""
    from src.stdlib import ZafiraModule
    return ZafiraModule('ffi', {
        'load': _ffi_load,
        'libc': _ffi_libc,
        'c_int': _ffi_c_int,
        'c_float': _ffi_c_float,
        'c_double': _ffi_c_double,
        'c_string': _ffi_c_string,
        'c_bool': _ffi_c_bool,
        'call': _ffi_call_global,
        'has_symbol': _ffi_has_symbol_global,
        'has': _ffi_has_symbol_global,
    })
