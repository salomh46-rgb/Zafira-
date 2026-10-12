"""
Zafira Language - std.json moduli
JSON ma'lumotlarini parse qilish (o'qish) va stringify qilish (matnga aylantirish).
"""

import json
from typing import Any, Optional
from src.interpreter import ZafiraStruct, ZafiraList, ZafiraError


def _zafira_to_py(val: Any) -> Any:
    """ZafiraStruct va ZafiraList obyektlarini Python dict/list larga rekursiv aylantiradi."""
    if isinstance(val, ZafiraStruct):
        return {k: _zafira_to_py(v) for k, v in val.fields.items()}
    if isinstance(val, ZafiraList):
        return [_zafira_to_py(item) for item in val.items]
    if isinstance(val, dict):
        return {k: _zafira_to_py(v) for k, v in val.items()}
    if isinstance(val, (list, tuple)):
        return [_zafira_to_py(item) for item in val]
    return val


def _py_to_zafira(val: Any) -> Any:
    """Python dict/list ma'lumotlarini ZafiraStruct va ZafiraList ga rekursiv aylantiradi."""
    if isinstance(val, dict):
        return ZafiraStruct('JsonObject', {k: _py_to_zafira(v) for k, v in val.items()})
    if isinstance(val, list):
        return ZafiraList([_py_to_zafira(item) for item in val])
    return val


def _json_parse(s: Any) -> Any:
    """
    JSON matnini tahlil qiladi (parse).
    Natija: ZafiraStruct, ZafiraList yoki primitiv (Int, Float, String, Bool, Null).
    """
    if not isinstance(s, str):
        raise ZafiraError(f"json.parse() satr (String) kutilgan edi, lekin '{type(s).__name__}' berildi")
    try:
        data = json.loads(s)
        return _py_to_zafira(data)
    except json.JSONDecodeError as e:
        raise ZafiraError(f"JSON parse xatosi: {e}")
    except Exception as e:
        raise ZafiraError(f"JSON parse xatosi: {e}")


def _json_stringify(obj: Any, indent: Optional[Any] = None) -> str:
    """
    Zafira obyekti yoki qiymatini JSON satriga aylantiradi.
    indent: ixtiyoriy bo'sh joylar soni (pretty-print).
    """
    try:
        py_data = _zafira_to_py(obj)
        ind = int(indent) if indent is not None else None
        return json.dumps(py_data, ensure_ascii=False, indent=ind)
    except Exception as e:
        if isinstance(e, ZafiraError):
            raise
        raise ZafiraError(f"JSON stringify xatosi: {e}")


def create_json_module():
    """std.json ZafiraModule nusxasini yaratadi."""
    from src.stdlib import ZafiraModule
    return ZafiraModule('json', {
        'parse': _json_parse,
        'stringify': _json_stringify,
        'loads': _json_parse,
        'dumps': _json_stringify,
    })
