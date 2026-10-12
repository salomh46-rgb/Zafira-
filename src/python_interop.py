"""
Zafira Language - Python Interoperability (Interop) Moduli
Python kutubxonalarini (math, random, numpy, pandas, torch va h.k.)
Zafira tili muhitida to'g'ridan-to'g'ri ishlatish imkoniyatini beradi.
"""

import importlib
from typing import Any, Optional, Dict, List
from src.interpreter import ZafiraStruct, ZafiraList, ZafiraError, BUILTINS, _builtin_len


class _PyFields:
    """
    Python ob'ekti atributlari va lug'at elementlarini
    ZafiraStruct.fields interfeysiga bog'lovchi dinamik adapter.
    """

    def __init__(self, target: Any):
        self._target = target

    def __contains__(self, item: str) -> bool:
        if isinstance(self._target, dict):
            return item in self._target or hasattr(self._target, item)
        return hasattr(self._target, item)

    def __getitem__(self, item: str) -> Any:
        if isinstance(self._target, dict) and item in self._target:
            val = self._target[item]
            return PythonInterop.wrap_python_obj(val)
        if hasattr(self._target, item):
            val = getattr(self._target, item)
            return PythonInterop.wrap_python_obj(val)
        raise KeyError(item)

    def __setitem__(self, item: str, value: Any) -> None:
        unwrapped = PythonInterop.unwrap_zafira_obj(value)
        if isinstance(self._target, dict):
            self._target[item] = unwrapped
        else:
            setattr(self._target, item, unwrapped)

    def get(self, item: str, default: Any = None) -> Any:
        try:
            return self[item]
        except (KeyError, AttributeError):
            return default

    def items(self):
        if isinstance(self._target, dict):
            return [(k, PythonInterop.wrap_python_obj(v)) for k, v in self._target.items()]
        attrs = [attr for attr in dir(self._target) if not attr.startswith('_')]
        return [(attr, getattr(self._target, attr, None)) for attr in attrs[:15]]

    def keys(self) -> List[str]:
        if isinstance(self._target, dict):
            return list(self._target.keys())
        return [attr for attr in dir(self._target) if not attr.startswith('_')]

    def __iter__(self):
        return iter(self.keys())

    def __len__(self) -> int:
        if isinstance(self._target, dict):
            return len(self._target)
        return len(self.keys())

    def __repr__(self) -> str:
        return repr(self._target)


class PythonObjectWrapper(ZafiraStruct):
    """
    Python ob'ektlarini (modullar, sinf nusxalari va h.k.) ZafiraStruct
    sifatida o'rab, Zafira MemberAccess orqali kirishni ta'minlaydi.
    """

    def __init__(self, py_obj: Any, name: Optional[str] = None):
        type_name = name or type(py_obj).__name__
        super().__init__(type_name=f"py.{type_name}", fields=_PyFields(py_obj))
        self._py_obj = py_obj

    def __len__(self) -> int:
        if hasattr(self._py_obj, '__len__'):
            return len(self._py_obj)
        raise TypeError(f"'{self.type_name}' ob'ektida uzunlik mavjud emas")

    def __iter__(self):
        if hasattr(self._py_obj, '__iter__'):
            for item in self._py_obj:
                yield PythonInterop.wrap_python_obj(item)
        else:
            raise TypeError(f"'{self.type_name}' ob'ekti iteratsiya qilinmaydi")

    def __repr__(self) -> str:
        return repr(self._py_obj)

    def __str__(self) -> str:
        return str(self._py_obj)


class PythonCallableWrapper(PythonObjectWrapper):
    """
    Python funksiyalari, metodlari va sinf konstruktorlarini
    Zafira ichida chaqirilishini ta'minlovchi o'rovchi klass.
    """

    def __init__(self, py_callable: Any, name: Optional[str] = None):
        super().__init__(py_obj=py_callable, name=name)

    def __call__(self, *args, **kwargs) -> Any:
        unwrapped_args = [PythonInterop.unwrap_zafira_obj(a) for a in args]
        unwrapped_kwargs = {k: PythonInterop.unwrap_zafira_obj(v) for k, v in kwargs.items()}
        try:
            res = self._py_obj(*unwrapped_args, **unwrapped_kwargs)
        except ZafiraError:
            raise
        except Exception as e:
            raise ZafiraError(f"Python xatosi ({type(e).__name__}): {e}") from e
        return PythonInterop.wrap_python_obj(res)


# Standart len() funksiyasini Python ob'ektlari uchun kengaytirish
_orig_builtin_len = BUILTINS.get('len', _builtin_len)

def _interop_len(obj):
    if hasattr(obj, '_py_obj') and hasattr(obj._py_obj, '__len__'):
        return len(obj._py_obj)
    if hasattr(obj, '__len__') and not isinstance(obj, (ZafiraList, str)):
        try:
            return len(obj)
        except Exception:
            pass
    return _orig_builtin_len(obj)

BUILTINS['len'] = _interop_len


class PythonInterop:
    """
    Zafira dasturlash tili uchun Python bilan ikki tomonlama bog'lanish (Interop) dvigateli.
    """

    PIP_PACKAGE_MAP: Dict[str, str] = {
        'cv2': 'opencv-python',
        'sklearn': 'scikit-learn',
        'PIL': 'pillow',
        'yaml': 'pyyaml',
        'bs4': 'beautifulsoup4',
        'torch': 'torch',
        'pandas': 'pandas',
        'numpy': 'numpy',
    }

    MODULE_ALIASES: Dict[str, List[str]] = {
        'pandas': ['pd'],
        'numpy': ['np'],
        'matplotlib.pyplot': ['plt'],
        'tensorflow': ['tf'],
    }

    @staticmethod
    def import_module(path: str, env) -> bool:
        """
        Python modulini yuklab, Zafira muhitiga (Environment) o'rnatadi.
        path: 'py.torch', 'py.pandas', 'py.numpy', 'py.math' kabi
        returns: Muvaffaqiyatli yuklansa True, aks holda False
        """
        # 'py.' prefiksini olib tashlaymiz
        mod_path = path[3:] if path.startswith('py.') else path
        root_name = mod_path.split('.')[0]

        try:
            mod = importlib.import_module(mod_path)
        except (ModuleNotFoundError, ImportError):
            pip_name = PythonInterop.PIP_PACKAGE_MAP.get(root_name, root_name)
            print(f"[Zafira] Python moduli '{mod_path}' topilmadi! O'rnatish uchun: pip install {pip_name}")
            return False
        except Exception as e:
            print(f"[Zafira] Python moduli '{mod_path}' ni yuklashda xatolik yuz berdi: {e}")
            return False

        wrapped = PythonInterop.wrap_python_obj(mod)

        # Asosiy nom bilan ro'yxatdan o'tkazish
        env.set(root_name, wrapped)
        if '.' in mod_path:
            leaf_name = mod_path.split('.')[-1]
            if leaf_name != root_name:
                env.set(leaf_name, wrapped)

        # Maxsus aliaslar (masalan: pandas -> pd, numpy -> np)
        aliases = PythonInterop.MODULE_ALIASES.get(mod_path, [])
        if not aliases and root_name in PythonInterop.MODULE_ALIASES:
            aliases = PythonInterop.MODULE_ALIASES.get(root_name, [])

        for alias in aliases:
            env.set(alias, wrapped)

        # Muhitdagi len funksiyasini yangilash
        env.set('len', _interop_len)

        return True

    @staticmethod
    def wrap_python_obj(obj: Any) -> Any:
        """
        Python ob'ektlarini Zafira da ishlatilishi uchun o'rash.
        Primitiv turlar (int, float, str, bool, None) to'g'ridan-to'g'ri qaytariladi.
        List/tuple ZafiraList ga, funksiyalar esa PythonCallableWrapper ga o'raladi.
        """
        if obj is None or isinstance(obj, (bool, int, float, str)):
            return obj

        # Skalyar sonlar (masalan np.int64, np.float64) ni konvertatsiya qilish
        if hasattr(obj, 'item') and callable(getattr(obj, 'item')):
            try:
                if getattr(obj, 'ndim', None) == 0:
                    return obj.item()
            except Exception:
                pass

        if isinstance(obj, (list, tuple)):
            return ZafiraList([PythonInterop.wrap_python_obj(x) for x in obj])

        if isinstance(obj, (ZafiraList, ZafiraStruct)):
            return obj

        if callable(obj):
            return PythonCallableWrapper(obj)

        return PythonObjectWrapper(obj)

    @staticmethod
    def unwrap_zafira_obj(obj: Any) -> Any:
        """
        Zafira ob'ektlarini asl Python turiga qaytarish (Python funksiyalariga uzatishda).
        """
        if isinstance(obj, PythonObjectWrapper):
            return obj._py_obj
        if isinstance(obj, ZafiraList):
            return [PythonInterop.unwrap_zafira_obj(x) for x in obj.items]
        if isinstance(obj, ZafiraStruct):
            return {k: PythonInterop.unwrap_zafira_obj(v) for k, v in obj.fields.items()}
        return obj
