"""
Zafira Language - std.crypto moduli
Kriptografiya, xeshlash, HMAC, Base64 va tasodifiy ma'lumotlar bilan ishlash.
"""

import base64
import binascii
import hashlib
import hmac
import secrets
from typing import Any
import uuid

from src.interpreter import ZafiraError, ZafiraList


def _crypto_sha256(*args) -> str:
    """
    Matnning SHA-256 xesh qiymatini (hex digest) hisoblaydi.
    """
    if len(args) != 1:
        raise ZafiraError(f"crypto.sha256() 1 ta argument kutadi, lekin {len(args)} ta berildi")
    text = args[0]
    if text is None:
        raise ZafiraError("crypto.sha256() argumenti null bo'lishi mumkin emas")
    if not isinstance(text, str):
        raise ZafiraError(f"crypto.sha256() uchun satr (String) kutilgan edi, lekin '{type(text).__name__}' berildi")
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def _crypto_sha512(*args) -> str:
    """
    Matnning SHA-512 xesh qiymatini (hex digest) hisoblaydi.
    """
    if len(args) != 1:
        raise ZafiraError(f"crypto.sha512() 1 ta argument kutadi, lekin {len(args)} ta berildi")
    text = args[0]
    if text is None:
        raise ZafiraError("crypto.sha512() argumenti null bo'lishi mumkin emas")
    if not isinstance(text, str):
        raise ZafiraError(f"crypto.sha512() uchun satr (String) kutilgan edi, lekin '{type(text).__name__}' berildi")
    return hashlib.sha512(text.encode('utf-8')).hexdigest()


def _crypto_md5(*args) -> str:
    """
    Matnning MD5 xesh qiymatini (hex digest) hisoblaydi.
    """
    if len(args) != 1:
        raise ZafiraError(f"crypto.md5() 1 ta argument kutadi, lekin {len(args)} ta berildi")
    text = args[0]
    if text is None:
        raise ZafiraError("crypto.md5() argumenti null bo'lishi mumkin emas")
    if not isinstance(text, str):
        raise ZafiraError(f"crypto.md5() uchun satr (String) kutilgan edi, lekin '{type(text).__name__}' berildi")
    return hashlib.md5(text.encode('utf-8')).hexdigest()


def _crypto_hmac_sha256(*args) -> str:
    """
    HMAC-SHA256 xesh imzosini (hex digest) hisoblaydi.
    key: maxfiy kalit (String)
    message: xabar matni (String)
    """
    if len(args) != 2:
        raise ZafiraError(f"crypto.hmac_sha256() 2 ta argument (key, message) kutadi, lekin {len(args)} ta berildi")
    key, message = args[0], args[1]
    if key is None:
        raise ZafiraError("crypto.hmac_sha256() kalit (key) null bo'lishi mumkin emas")
    if not isinstance(key, str):
        raise ZafiraError(f"crypto.hmac_sha256() kalit (key) satr (String) bo'lishi kerak, lekin '{type(key).__name__}' berildi")
    if message is None:
        raise ZafiraError("crypto.hmac_sha256() xabar (message) null bo'lishi mumkin emas")
    if not isinstance(message, str):
        raise ZafiraError(f"crypto.hmac_sha256() xabar (message) satr (String) bo'lishi kerak, lekin '{type(message).__name__}' berildi")
    return hmac.new(key.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).hexdigest()


def _crypto_base64_encode(*args) -> str:
    """
    Matnni Base64 formatiga kodlaydi.
    """
    if len(args) != 1:
        raise ZafiraError(f"crypto.base64_encode() 1 ta argument kutadi, lekin {len(args)} ta berildi")
    text = args[0]
    if text is None:
        raise ZafiraError("crypto.base64_encode() argumenti null bo'lishi mumkin emas")
    if not isinstance(text, str):
        raise ZafiraError(f"crypto.base64_encode() uchun satr (String) kutilgan edi, lekin '{type(text).__name__}' berildi")
    return base64.b64encode(text.encode('utf-8')).decode('utf-8')


def _crypto_base64_decode(*args) -> str:
    """
    Base64 formatidagi matnni asl holatiga dekodlaydi.
    """
    if len(args) != 1:
        raise ZafiraError(f"crypto.base64_decode() 1 ta argument kutadi, lekin {len(args)} ta berildi")
    encoded_text = args[0]
    if encoded_text is None:
        raise ZafiraError("crypto.base64_decode() argumenti null bo'lishi mumkin emas")
    if not isinstance(encoded_text, str):
        raise ZafiraError(f"crypto.base64_decode() uchun satr (String) kutilgan edi, lekin '{type(encoded_text).__name__}' berildi")
    try:
        raw_bytes = base64.b64decode(encoded_text.encode('utf-8'), validate=True)
        return raw_bytes.decode('utf-8')
    except (binascii.Error, ValueError) as e:
        raise ZafiraError(f"Noto'g'ri Base64 satri: {e}")
    except UnicodeDecodeError as e:
        raise ZafiraError(f"Base64 dekodlangan ma'lumot to'g'ri UTF-8 matn emas: {e}")
    except Exception as e:
        raise ZafiraError(f"Base64 dekodlash xatosi: {e}")


def _crypto_uuid(*args) -> str:
    """
    Tasodifiy UUID v4 identifikatorini (String) hosil qiladi.
    """
    if args:
        raise ZafiraError(f"crypto.uuid() argument qabul qilmaydi, lekin {len(args)} ta berildi")
    return str(uuid.uuid4())


def _crypto_random_bytes(*args) -> ZafiraList:
    """
    n baytli kriptografik xavfsiz tasodifiy baytlar ro'yxatini (0-255 sonlari) qaytaradi.
    """
    if len(args) != 1:
        raise ZafiraError(f"crypto.random_bytes() 1 ta argument (n) kutadi, lekin {len(args)} ta berildi")
    n = args[0]
    if n is None:
        raise ZafiraError("crypto.random_bytes() n parametri null bo'lishi mumkin emas")
    if isinstance(n, bool) or not isinstance(n, int):
        raise ZafiraError(f"crypto.random_bytes() n parametri butun son (Int) bo'lishi kerak, lekin '{type(n).__name__}' berildi")
    if n < 0:
        raise ZafiraError(f"crypto.random_bytes() n parametri manfiy bo'lishi mumkin emas: {n}")
    raw = secrets.token_bytes(n)
    return ZafiraList([int(b) for b in raw])


def _crypto_random_hex(*args) -> str:
    """
    n baytli kriptografik xavfsiz tasodifiy hex tokenini (satr) hosil qiladi.
    Natija 2*n uzunlikdagi hex satr bo'ladi.
    """
    if len(args) != 1:
        raise ZafiraError(f"crypto.random_hex() 1 ta argument (n) kutadi, lekin {len(args)} ta berildi")
    n = args[0]
    if n is None:
        raise ZafiraError("crypto.random_hex() n parametri null bo'lishi mumkin emas")
    if isinstance(n, bool) or not isinstance(n, int):
        raise ZafiraError(f"crypto.random_hex() n parametri butun son (Int) bo'lishi kerak, lekin '{type(n).__name__}' berildi")
    if n < 0:
        raise ZafiraError(f"crypto.random_hex() n parametri manfiy bo'lishi mumkin emas: {n}")
    return secrets.token_hex(n)


def create_crypto_module():
    """std.crypto ZafiraModule nusxasini yaratadi."""
    from src.stdlib import ZafiraModule
    return ZafiraModule('crypto', {
        'sha256': _crypto_sha256,
        'sha512': _crypto_sha512,
        'md5': _crypto_md5,
        'hmac_sha256': _crypto_hmac_sha256,
        'base64_encode': _crypto_base64_encode,
        'base64_decode': _crypto_base64_decode,
        'uuid': _crypto_uuid,
        'random_bytes': _crypto_random_bytes,
        'random_hex': _crypto_random_hex,
    })
