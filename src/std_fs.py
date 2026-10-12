"""
Zafira Language - std.fs moduli
Fayllar tizimi (File System) bilan ishlash: o'qish, yozish, tekshirish, papkalar, nusxa olish.
"""

import os
import shutil
from typing import Any
from src.interpreter import ZafiraError, ZafiraList, _zf_str


def _clean_path(path: Any, fn_name: str) -> str:
    """Yo'l (path) satr bo'lishini tekshiradi va qaytaradi."""
    if path is None:
        raise ZafiraError(f"fs.{fn_name}() yo'li (path) null bo'lishi mumkin emas")
    if not isinstance(path, (str, os.PathLike)):
        raise ZafiraError(f"fs.{fn_name}() yo'li (path) satr (String) bo'lishi kerak, lekin '{type(path).__name__}' berildi")
    return str(path)


def _fs_read_text(path: Any) -> str:
    """Fayl matnini satr (string) sifatida o'qiydi."""
    p = _clean_path(path, 'read_text')
    try:
        if not os.path.exists(p):
            raise ZafiraError(f"Fayl topilmadi: '{p}'")
        if os.path.isdir(p):
            raise ZafiraError(f"Ko'rsatilgan yo'l fayl emas, papka: '{p}'")
        with open(p, 'r', encoding='utf-8') as f:
            return f.read()
    except ZafiraError:
        raise
    except FileNotFoundError:
        raise ZafiraError(f"Fayl topilmadi: '{p}'")
    except PermissionError:
        raise ZafiraError(f"Faylni o'qishga ruxsat yo'q: '{p}'")
    except IsADirectoryError:
        raise ZafiraError(f"Ko'rsatilgan yo'l fayl emas, papka: '{p}'")
    except UnicodeDecodeError as e:
        raise ZafiraError(f"Faylni UTF-8 formatida o'qib bo'lmadi: '{p}' ({e})")
    except OSError as e:
        raise ZafiraError(f"Faylni o'qishda xatolik: {e}")


def _fs_write_text(path: Any, content: Any) -> None:
    """Faylga matn yozadi (ustiga yozadi)."""
    p = _clean_path(path, 'write_text')
    text = content if isinstance(content, str) else _zf_str(content)
    try:
        if os.path.isdir(p):
            raise ZafiraError(f"Ko'rsatilgan yo'l papka: '{p}'")
        with open(p, 'w', encoding='utf-8') as f:
            f.write(text)
    except ZafiraError:
        raise
    except FileNotFoundError:
        raise ZafiraError(f"Yo'l topilmadi yoki papka mavjud emas: '{p}'")
    except PermissionError:
        raise ZafiraError(f"Faylga yozishga ruxsat yo'q: '{p}'")
    except IsADirectoryError:
        raise ZafiraError(f"Ko'rsatilgan yo'l papka: '{p}'")
    except OSError as e:
        raise ZafiraError(f"Faylga yozishda xatolik: {e}")


def _fs_append_text(path: Any, content: Any) -> None:
    """Fayl oxiriga matn qo'shadi."""
    p = _clean_path(path, 'append_text')
    text = content if isinstance(content, str) else _zf_str(content)
    try:
        if os.path.isdir(p):
            raise ZafiraError(f"Ko'rsatilgan yo'l papka: '{p}'")
        with open(p, 'a', encoding='utf-8') as f:
            f.write(text)
    except ZafiraError:
        raise
    except FileNotFoundError:
        raise ZafiraError(f"Yo'l topilmadi yoki papka mavjud emas: '{p}'")
    except PermissionError:
        raise ZafiraError(f"Faylga qo'shishga ruxsat yo'q: '{p}'")
    except IsADirectoryError:
        raise ZafiraError(f"Ko'rsatilgan yo'l papka: '{p}'")
    except OSError as e:
        raise ZafiraError(f"Faylga qo'shishda xatolik: {e}")


def _fs_exists(path: Any) -> bool:
    """Fayl yoki papka mavjudligini tekshiradi."""
    p = _clean_path(path, 'exists')
    return os.path.exists(p)


def _fs_is_file(path: Any) -> bool:
    """Yo'l mavjud fayl ekanligini tekshiradi."""
    p = _clean_path(path, 'is_file')
    return os.path.isfile(p)


def _fs_is_dir(path: Any) -> bool:
    """Yo'l mavjud papka ekanligini tekshiradi."""
    p = _clean_path(path, 'is_dir')
    return os.path.isdir(p)


def _fs_list_dir(path: Any) -> ZafiraList:
    """Papka ichidagi fayl va papkalar nomlarini ro'yxat (ZafiraList) sifatida qaytaradi."""
    p = _clean_path(path, 'list_dir')
    try:
        if not os.path.exists(p):
            raise ZafiraError(f"Papka topilmadi: '{p}'")
        if not os.path.isdir(p):
            raise ZafiraError(f"Ko'rsatilgan yo'l papka emas: '{p}'")
        entries = os.listdir(p)
        return ZafiraList(entries)
    except ZafiraError:
        raise
    except FileNotFoundError:
        raise ZafiraError(f"Papka topilmadi: '{p}'")
    except NotADirectoryError:
        raise ZafiraError(f"Ko'rsatilgan yo'l papka emas: '{p}'")
    except PermissionError:
        raise ZafiraError(f"Papkani o'qishga ruxsat yo'q: '{p}'")
    except OSError as e:
        raise ZafiraError(f"Papkani ro'yxatga olishda xatolik: {e}")


def _fs_make_dir(path: Any, recursive: Any = True) -> None:
    """Papka yaratadi. recursive=True bo'lsa barcha ota-papkalarni ham yaratadi."""
    p = _clean_path(path, 'make_dir')
    is_rec = bool(recursive)
    try:
        if is_rec:
            if os.path.isfile(p):
                raise ZafiraError(f"Papka yaratib bo'lmadi, fayl mavjud: '{p}'")
            os.makedirs(p, exist_ok=True)
        else:
            os.mkdir(p)
    except ZafiraError:
        raise
    except FileExistsError:
        raise ZafiraError(f"Papka allaqachon mavjud: '{p}'")
    except FileNotFoundError:
        raise ZafiraError(f"Ota-papka topilmadi: '{p}'")
    except PermissionError:
        raise ZafiraError(f"Papka yaratishga ruxsat yo'q: '{p}'")
    except OSError as e:
        raise ZafiraError(f"Papka yaratishda xatolik: {e}")


def _fs_remove(path: Any) -> None:
    """Faylni o'chiradi."""
    p = _clean_path(path, 'remove')
    try:
        if not os.path.exists(p):
            raise ZafiraError(f"O'chirish uchun fayl topilmadi: '{p}'")
        if os.path.isdir(p):
            raise ZafiraError(f"remove() faqat fayllarni o'chiradi, '{p}' esa papka. remove_dir() dan foydalaning.")
        os.remove(p)
    except ZafiraError:
        raise
    except FileNotFoundError:
        raise ZafiraError(f"O'chirish uchun fayl topilmadi: '{p}'")
    except PermissionError:
        raise ZafiraError(f"Faylni o'chirishga ruxsat yo'q: '{p}'")
    except OSError as e:
        raise ZafiraError(f"Faylni o'chirishda xatolik: {e}")


def _fs_remove_dir(path: Any, recursive: Any = False) -> None:
    """Papkani o'chiradi. recursive=False bo'lsa faqat bo'sh papkani o'chiradi."""
    p = _clean_path(path, 'remove_dir')
    is_rec = bool(recursive)
    try:
        if not os.path.exists(p):
            raise ZafiraError(f"O'chirish uchun papka topilmadi: '{p}'")
        if not os.path.isdir(p):
            raise ZafiraError(f"Ko'rsatilgan yo'l papka emas: '{p}'")
        if is_rec:
            shutil.rmtree(p)
        else:
            os.rmdir(p)
    except ZafiraError:
        raise
    except FileNotFoundError:
        raise ZafiraError(f"O'chirish uchun papka topilmadi: '{p}'")
    except PermissionError:
        raise ZafiraError(f"Papkani o'chirishga ruxsat yo'q: '{p}'")
    except OSError as e:
        if "directory not empty" in str(e).lower() or "bo'sh emas" in str(e).lower() or getattr(e, 'errno', None) in (39, 41, 145):
            raise ZafiraError(f"Papka bo'sh emas: '{p}'. recursive=true dan foydalaning.")
        raise ZafiraError(f"Papkani o'chirishda xatolik: {e}")


def _fs_file_size(path: Any) -> int:
    """Fayl hajmini baytlarda qaytaradi."""
    p = _clean_path(path, 'file_size')
    try:
        if not os.path.exists(p):
            raise ZafiraError(f"Fayl topilmadi: '{p}'")
        if os.path.isdir(p):
            raise ZafiraError(f"Ko'rsatilgan yo'l fayl emas, papka: '{p}'")
        return os.path.getsize(p)
    except ZafiraError:
        raise
    except FileNotFoundError:
        raise ZafiraError(f"Fayl topilmadi: '{p}'")
    except PermissionError:
        raise ZafiraError(f"Fayl hajmini bilishga ruxsat yo'q: '{p}'")
    except OSError as e:
        raise ZafiraError(f"Fayl hajmini olishda xatolik: {e}")


def _fs_copy(src: Any, dst: Any) -> None:
    """Fayldan nusxa oladi."""
    s = _clean_path(src, 'copy')
    d = _clean_path(dst, 'copy')
    try:
        if not os.path.exists(s):
            raise ZafiraError(f"Nusxa olish uchun manba fayl topilmadi: '{s}'")
        if os.path.isdir(s):
            raise ZafiraError(f"copy() faqat fayllardan nusxa oladi, '{s}' esa papka.")
        shutil.copy2(s, d)
    except ZafiraError:
        raise
    except FileNotFoundError:
        raise ZafiraError(f"Nusxa olish uchun fayl yoki manzil topilmadi: '{s}' -> '{d}'")
    except PermissionError:
        raise ZafiraError(f"Nusxa olishga ruxsat yo'q: '{s}' -> '{d}'")
    except shutil.SameFileError:
        raise ZafiraError(f"Manba va manzil bir xil fayl: '{s}'")
    except OSError as e:
        raise ZafiraError(f"Nusxa olishda xatolik: {e}")


def create_fs_module():
    """std.fs ZafiraModule nusxasini yaratadi."""
    from src.stdlib import ZafiraModule
    return ZafiraModule('fs', {
        'read_text': _fs_read_text,
        'write_text': _fs_write_text,
        'append_text': _fs_append_text,
        'exists': _fs_exists,
        'is_file': _fs_is_file,
        'is_dir': _fs_is_dir,
        'list_dir': _fs_list_dir,
        'make_dir': _fs_make_dir,
        'remove': _fs_remove,
        'remove_dir': _fs_remove_dir,
        'file_size': _fs_file_size,
        'copy': _fs_copy,
    })
