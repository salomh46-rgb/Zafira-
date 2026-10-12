"""
Zafira Language - std.env moduli
Muhit o'zgaruvchilari (Environment Variables), CLI argumentlar, OS va joriy ishchi katalog bilan ishlash.
"""

import os
import sys
from typing import Any, Optional, List
from src.interpreter import ZafiraError, ZafiraList, ZafiraStruct, _zf_str


_custom_cli_args: Optional[List[str]] = None


def set_custom_args(args: Optional[List[str]]) -> None:
    """Testlar yoki maxsus buyruqlar uchun CLI argumentlarini vaqtinchalik sozlash."""
    global _custom_cli_args
    _custom_cli_args = args


def _env_get(key: Any, default: Any = None) -> Any:
    """
    Muhit o'zgaruvchisi qiymatini oladi.
    Agar topilmasa, default qiymat qaytariladi (sukut bo'yicha null).
    """
    if not isinstance(key, str):
        raise ZafiraError(f"env.get() o'zgaruvchi nomi (key) satr (String) bo'lishi kerak, lekin '{type(key).__name__}' berildi")
    return os.environ.get(key, default)


def _env_set(key: Any, val: Any) -> None:
    """
    Muhit o'zgaruvchisini o'rnatadi yoki yangilaydi.
    """
    if not isinstance(key, str):
        raise ZafiraError(f"env.set() o'zgaruvchi nomi (key) satr (String) bo'lishi kerak, lekin '{type(key).__name__}' berildi")
    val_str = val if isinstance(val, str) else _zf_str(val)
    os.environ[key] = val_str
    return None


def _env_has(key: Any) -> bool:
    """
    Ko'rsatilgan nomli muhit o'zgaruvchisi mavjudligini tekshiradi.
    """
    if not isinstance(key, str):
        raise ZafiraError(f"env.has() o'zgaruvchi nomi (key) satr (String) bo'lishi kerak, lekin '{type(key).__name__}' berildi")
    return key in os.environ


def _env_remove(key: Any) -> None:
    """
    Muhit o'zgaruvchisini o'chiradi.
    """
    if not isinstance(key, str):
        raise ZafiraError(f"env.remove() o'zgaruvchi nomi (key) satr (String) bo'lishi kerak, lekin '{type(key).__name__}' berildi")
    os.environ.pop(key, None)
    return None


def _env_all() -> ZafiraStruct:
    """
    Barcha muhit o'zgaruvchilarini ZafiraStruct (JsonObject) sifatida qaytaradi.
    """
    return ZafiraStruct('JsonObject', dict(os.environ))


def _env_args() -> ZafiraList:
    """
    CLI buyruq argumentlarini ZafiraList sifatida qaytaradi.
    """
    if _custom_cli_args is not None:
        return ZafiraList([str(a) for a in _custom_cli_args])
    return ZafiraList([str(a) for a in sys.argv])


def _env_os() -> str:
    """
    Joriy operatsion tizim nomini qaytaradi ("windows", "linux", "darwin").
    """
    plat = sys.platform.lower()
    if plat.startswith('win'):
        return "windows"
    if plat.startswith('linux'):
        return "linux"
    if plat == 'darwin':
        return "darwin"
    return plat


def _env_cwd() -> str:
    """
    Joriy ishchi katalogni (Current Working Directory) qaytaradi.
    """
    return os.getcwd()


def create_env_module():
    """std.env ZafiraModule nusxasini yaratadi."""
    from src.stdlib import ZafiraModule
    return ZafiraModule('env', {
        'get': _env_get,
        'set': _env_set,
        'has': _env_has,
        'remove': _env_remove,
        'all': _env_all,
        'args': _env_args,
        'os': _env_os,
        'cwd': _env_cwd,
    })
