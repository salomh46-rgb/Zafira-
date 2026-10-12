"""
Zafira Language - std.datetime moduli
Sana va vaqt bilan ishlash, formatlash, timestamp olish va kechiktirish (sleep).
"""

import datetime
import time
from typing import Any, Optional
from src.interpreter import ZafiraError, ZafiraStruct


def _resolve_datetime(val: Any) -> datetime.datetime:
    """Turli Zafira qiymatlaridan (null, float/int, ZafiraStruct, str) datetime obyektini hosil qiladi."""
    if val is None:
        return datetime.datetime.now()
    if isinstance(val, (int, float)):
        try:
            return datetime.datetime.fromtimestamp(float(val))
        except Exception as e:
            raise ZafiraError(f"Noto'g'ri timestamp qiymati: {val} ({e})")
    if isinstance(val, ZafiraStruct):
        fields = val.fields
        if 'iso' in fields and isinstance(fields['iso'], str):
            try:
                return datetime.datetime.fromisoformat(fields['iso'])
            except Exception:
                pass
        try:
            return datetime.datetime(
                year=int(fields.get('year', 1970)),
                month=int(fields.get('month', 1)),
                day=int(fields.get('day', 1)),
                hour=int(fields.get('hour', 0)),
                minute=int(fields.get('minute', 0)),
                second=int(fields.get('second', 0)),
            )
        except Exception as e:
            raise ZafiraError(f"DateTime strukturasidan sana/vaqtni aniqlab bo'lmadi: {e}")
    if isinstance(val, str):
        try:
            return datetime.datetime.fromisoformat(val)
        except Exception as e:
            raise ZafiraError(f"Satrdan sana/vaqtni parse qilib bo'lmadi: '{val}' ({e})")
    raise ZafiraError(f"datetime uchun noto'g'ri sana/vaqt turi: '{type(val).__name__}'")


def _datetime_now() -> ZafiraStruct:
    """
    Joriy sana va vaqtni ZafiraStruct sifatida qaytaradi.
    Maydonlar: year, month, day, hour, minute, second, iso.
    """
    now = datetime.datetime.now()
    return ZafiraStruct('DateTime', {
        'year': now.year,
        'month': now.month,
        'day': now.day,
        'hour': now.hour,
        'minute': now.minute,
        'second': now.second,
        'iso': now.isoformat(),
    })


def _datetime_timestamp() -> float:
    """
    Joriy Unix timestamp (soniyalarda, Float) qaytaradi.
    """
    return float(time.time())


def _datetime_format(*args) -> str:
    """
    Sana/vaqtni berilgan format bo'yicha satrga aylantiradi.
    Chaqirish variantlari:
      format(timestamp_yoki_null, "%Y-%m-%d %H:%M:%S")
      format("%Y-%m-%d %H:%M:%S")  (joriy vaqt uchun)
    """
    if len(args) == 0:
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if len(args) == 1:
        arg = args[0]
        if isinstance(arg, str) and ('%' in arg or not arg.replace('.', '', 1).isdigit()):
            return datetime.datetime.now().strftime(arg)
        dt = _resolve_datetime(arg)
        return dt.strftime("%Y-%m-%d %H:%M:%S")

    ts_val, fmt = args[0], args[1]
    if not isinstance(fmt, str):
        raise ZafiraError(f"datetime.format() format satri (String) bo'lishi kerak, lekin '{type(fmt).__name__}' berildi")
    dt = _resolve_datetime(ts_val)
    try:
        return dt.strftime(fmt)
    except Exception as e:
        raise ZafiraError(f"datetime.format() xatosi: {e}")


def _datetime_sleep(seconds: Any) -> None:
    """
    Ijroni berilgan soniya davomida to'xtatib turadi.
    """
    try:
        s = float(seconds)
        if s < 0:
            raise ZafiraError("datetime.sleep() soniya manfiy bo'lishi mumkin emas")
        time.sleep(s)
        return None
    except ZafiraError:
        raise
    except Exception as e:
        raise ZafiraError(f"datetime.sleep() xatosi: {e}")


def _datetime_sleep_ms(milliseconds: Any) -> None:
    """
    Ijroni berilgan millisoniya davomida to'xtatib turadi.
    """
    try:
        ms = float(milliseconds)
        if ms < 0:
            raise ZafiraError("datetime.sleep_ms() millisoniya manfiy bo'lishi mumkin emas")
        time.sleep(ms / 1000.0)
        return None
    except ZafiraError:
        raise
    except Exception as e:
        raise ZafiraError(f"datetime.sleep_ms() xatosi: {e}")


def create_datetime_module():
    """std.datetime ZafiraModule nusxasini yaratadi."""
    from src.stdlib import ZafiraModule
    return ZafiraModule('datetime', {
        'now': _datetime_now,
        'timestamp': _datetime_timestamp,
        'format': _datetime_format,
        'sleep': _datetime_sleep,
        'sleep_ms': _datetime_sleep_ms,
    })
