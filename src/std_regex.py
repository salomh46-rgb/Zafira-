"""
Zafira Language - std.regex moduli
Regular Ifodalar (RegEx) bilan ishlash: test, find, find_all, replace, replace_all, split, is_valid.
"""

import re
from typing import Any, Optional
from src.interpreter import ZafiraError, ZafiraList


def _compile_pattern(pattern: Any, fn_name: str) -> re.Pattern:
    """Regex patternni tekshiradi, kompilyatsiya qiladi va xato bo'lsa ZafiraError tashlaydi."""
    if pattern is None:
        raise ZafiraError(f"regex.{fn_name}() uchun 'pattern' null bo'lishi mumkin emas")
    if not isinstance(pattern, str):
        raise ZafiraError(f"regex.{fn_name}() uchun 'pattern' satr (String) kutilgan edi, lekin '{type(pattern).__name__}' berildi")
    try:
        return re.compile(pattern)
    except re.error as e:
        raise ZafiraError(f"regex.{fn_name}() noto'g'ri regex ifodasi '{pattern}': {e}")


def _check_text(text: Any, fn_name: str) -> str:
    """Matn argumenti satr (String) ekanligini tekshiradi."""
    if text is None:
        raise ZafiraError(f"regex.{fn_name}() uchun 'text' null bo'lishi mumkin emas")
    if not isinstance(text, str):
        raise ZafiraError(f"regex.{fn_name}() uchun 'text' satr (String) kutilgan edi, lekin '{type(text).__name__}' berildi")
    return text


def _check_replacement(replacement: Any, fn_name: str) -> str:
    """Almashtirish (replacement) argumentini tekshiradi."""
    if replacement is None:
        raise ZafiraError(f"regex.{fn_name}() uchun 'replacement' null bo'lishi mumkin emas")
    if not isinstance(replacement, str):
        raise ZafiraError(f"regex.{fn_name}() uchun 'replacement' satr (String) kutilgan edi, lekin '{type(replacement).__name__}' berildi")
    return replacement


def _regex_test(pattern: Any, text: Any) -> bool:
    """
    Matn pattern regex qoidasiga mos kelishini tekshiradi.
    Mos kelsa True, aks holda False qaytaradi.
    """
    compiled = _compile_pattern(pattern, 'test')
    t = _check_text(text, 'test')
    return compiled.search(t) is not None


def _regex_find(pattern: Any, text: Any) -> Optional[str]:
    """
    Matndan regex pattern bo'yicha birinchi mos kelgan qismni qaytaradi.
    Moslik topilmasa None (Zafira null) qaytaradi.
    """
    compiled = _compile_pattern(pattern, 'find')
    t = _check_text(text, 'find')
    m = compiled.search(t)
    return m.group(0) if m is not None else None


def _regex_find_all(pattern: Any, text: Any) -> ZafiraList:
    """
    Matndan regex pattern bo'yicha barcha mos kelgan qismlar ro'yxatini (ZafiraList) qaytaradi.
    """
    compiled = _compile_pattern(pattern, 'find_all')
    t = _check_text(text, 'find_all')
    matches = [m.group(0) for m in compiled.finditer(t)]
    return ZafiraList(matches)


def _regex_replace(pattern: Any, replacement: Any, text: Any) -> str:
    """
    Matndagi regex pattern ga mos kelgan birinchi qismni replacement bilan almashtiradi.
    """
    compiled = _compile_pattern(pattern, 'replace')
    repl = _check_replacement(replacement, 'replace')
    t = _check_text(text, 'replace')
    try:
        return compiled.sub(repl, t, count=1)
    except re.error as e:
        raise ZafiraError(f"regex.replace() almashtirishda xatolik: {e}")


def _regex_replace_all(pattern: Any, replacement: Any, text: Any) -> str:
    """
    Matndagi regex pattern ga mos kelgan barcha qismlarni replacement bilan almashtiradi.
    """
    compiled = _compile_pattern(pattern, 'replace_all')
    repl = _check_replacement(replacement, 'replace_all')
    t = _check_text(text, 'replace_all')
    try:
        return compiled.sub(repl, t, count=0)
    except re.error as e:
        raise ZafiraError(f"regex.replace_all() almashtirishda xatolik: {e}")


def _regex_split(pattern: Any, text: Any) -> ZafiraList:
    """
    Matnni regex pattern bo'yicha bo'lib, qismlar ro'yxatini (ZafiraList) qaytaradi.
    """
    compiled = _compile_pattern(pattern, 'split')
    t = _check_text(text, 'split')
    parts = compiled.split(t)
    return ZafiraList(parts)


def _regex_is_valid(pattern: Any) -> bool:
    """
    Pattern to'g'ri regex ekanligini tekshiradi.
    To'g'ri bo'lsa True, noto'g'ri sintaksis yoki xato bo'lsa False qaytaradi.
    """
    if not isinstance(pattern, str):
        return False
    try:
        re.compile(pattern)
        return True
    except (re.error, Exception):
        return False


def create_regex_module():
    """std.regex ZafiraModule nusxasini yaratadi."""
    from src.stdlib import ZafiraModule
    return ZafiraModule('regex', {
        'test': _regex_test,
        'find': _regex_find,
        'find_all': _regex_find_all,
        'replace': _regex_replace,
        'replace_all': _regex_replace_all,
        'split': _regex_split,
        'is_valid': _regex_is_valid,
    })
