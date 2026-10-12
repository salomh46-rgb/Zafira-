"""
Zafira Language - AI & Tensor Engine (Silicon-Native Runtime)
Modullar: Tensor, SiliconDevice, std.ai funksiyalari
"""

import math
import sys
import ctypes
from typing import Any, List, Union, Optional, Tuple
from contextlib import contextmanager

from src.interpreter import ZafiraError, ZafiraList, _zf_str


class TensorShape(ZafiraList):
    """
    Tensor o'lchami (shape).
    Ham ZafiraList (Zafira tili muhiti uchun), ham Python list/tuple bilan solishtiriladi.
    """
    def __init__(self, dims: List[int]):
        super().__init__([int(d) for d in dims])

    def __eq__(self, other):
        if isinstance(other, (list, tuple)):
            return self.items == list(other)
        if isinstance(other, ZafiraList):
            return self.items == other.items
        return False

    def __iter__(self):
        return iter(self.items)

    def __getitem__(self, idx):
        return self.items[idx]

    def __repr__(self):
        return f"[{', '.join(str(i) for i in self.items)}]"

    def to_list(self) -> list:
        return list(self.items)


# ─── SILICON HARDWARE RUNTIME ───

class SiliconRuntime:
    """
    Silicon apparat drayveri: CPU, CUDA/GPU, NPU boshqaruvi.
    """
    def __init__(self):
        self._current_device: str = 'cpu'
        self._cuda_available: Optional[bool] = None

    def is_cuda_available(self) -> bool:
        if self._cuda_available is not None:
            return self._cuda_available
        try:
            if sys.platform == 'win32':
                ctypes.windll.LoadLibrary('nvcuda.dll')
                self._cuda_available = True
            else:
                ctypes.cdll.LoadLibrary('libcuda.so')
                self._cuda_available = True
        except Exception:
            self._cuda_available = False
        return self._cuda_available

    def detect_best_device(self) -> str:
        if self.is_cuda_available():
            return 'gpu'
        return 'cpu'

    def get_current_device(self) -> str:
        return self._current_device

    def set_current_device(self, device: str) -> None:
        dev = device.lower().lstrip('@')
        if dev not in ('cpu', 'gpu', 'cuda', 'npu', 'auto'):
            raise ZafiraError(f"Noma'lum apparat qurilmasi: '{device}'")
        if dev == 'auto':
            dev = self.detect_best_device()
        self._current_device = dev

    @contextmanager
    def device_context(self, device: str):
        prev = self._current_device
        self.set_current_device(device)
        try:
            yield self._current_device
        finally:
            self._current_device = prev


_SILICON = SiliconRuntime()


def get_active_device() -> str:
    return _SILICON.get_current_device()


def set_active_device(device: str) -> None:
    _SILICON.set_current_device(device)


def silicon_context(device: str):
    return _SILICON.device_context(device)


# ─── YORDAMCHI REKURSIV KONVERTATSIYA ───

def _extract_raw(val: Any) -> Any:
    if isinstance(val, Tensor):
        return val._to_nested_py_list()
    if isinstance(val, ZafiraList):
        return [_extract_raw(x) for x in val.items]
    if isinstance(val, (list, tuple)):
        return [_extract_raw(x) for x in val]
    if isinstance(val, (int, float)):
        return float(val)
    raise ZafiraError(f"Tensor uchun yaroqsiz qiymat turi: '{type(val).__name__}'")


# ─── TENSOR KLASSI ───

class Tensor:
    """
    Zafira Silicon-native Tensor klassi.
    1D va 2D massivlarni to'liq qo'llab-quvvatlaydi.
    """
    def __init__(self, data: Any, device: Optional[str] = None):
        self.device = device or get_active_device()

        if isinstance(data, Tensor):
            self.data = [row[:] if isinstance(row, list) else row for row in data.data]
            self.ndim = data.ndim
            self._shape = list(data.shape.items)
            self.device = device or data.device
            return

        raw = _extract_raw(data)

        if not isinstance(raw, list):
            raw = [raw]

        if not raw:
            self.data = []
            self.ndim = 1
            self._shape = [0]
            return

        # 1D yoki 2D ekanini aniqlash
        if isinstance(raw[0], list):
            self.ndim = 2
            cols = len(raw[0])
            for i, row in enumerate(raw):
                if not isinstance(row, list):
                    raise ZafiraError("2D matritsaning barcha elementlari ro'yxat (qator) bo'lishi kerak")
                if len(row) != cols:
                    raise ZafiraError(
                        f"Matritsa qatorlari uzunligi teng emas: 0-qator={cols}, {i}-qator={len(row)}"
                    )
                for item in row:
                    if not isinstance(item, (int, float)):
                        raise ZafiraError(f"Matritsa elementi son bo'lishi kerak, '{item}' berildi")
            self.data = raw
            self._shape = [len(raw), cols]
        else:
            self.ndim = 1
            for item in raw:
                if isinstance(item, list):
                    raise ZafiraError("1D vektorda ichki ro'yxat bo'lishi mumkin emas")
                if not isinstance(item, (int, float)):
                    raise ZafiraError(f"Vektor elementi son bo'lishi kerak, '{item}' berildi")
            self.data = raw
            self._shape = [len(raw)]

    @property
    def shape(self) -> TensorShape:
        return TensorShape(self._shape)

    def _to_nested_py_list(self) -> Any:
        if self.ndim == 1:
            return list(self.data)
        return [list(r) for r in self.data]

    def _flatten(self) -> List[float]:
        if self.ndim == 1:
            return list(self.data)
        res = []
        for row in self.data:
            res.extend(row)
        return res

    def to_list(self) -> ZafiraList:
        """Zafira muhiti uchun ZafiraList qaytaradi"""
        if self.ndim == 1:
            return ZafiraList(list(self.data))
        return ZafiraList([ZafiraList(list(r)) for r in self.data])

    def tolist(self) -> list:
        return self._to_nested_py_list()

    def to(self, device: str) -> 'Tensor':
        return Tensor(self, device=device)

    # ─── MATEMATIK VA ALGEBRAIK OPERATSIYALAR ───

    def dot(self, other: Any) -> Any:
        """
        Skalyar ko'paytma (vektorlar) yoki Matritsalar ko'paytmasi (matmul).
        """
        if not isinstance(other, Tensor):
            other = Tensor(other)

        # 1. 1D dot 1D -> skalyar float
        if self.ndim == 1 and other.ndim == 1:
            if self._shape[0] != other._shape[0]:
                raise ZafiraError(
                    f"Vektorlar dot o'lchami mos kelmadi: {self.shape} dot {other.shape}"
                )
            return sum(a * b for a, b in zip(self.data, other.data))

        # 2. 2D dot 2D -> 2D Tensor
        if self.ndim == 2 and other.ndim == 2:
            m, k1 = self._shape
            k2, n = other._shape
            if k1 != k2:
                raise ZafiraError(
                    f"Matritsalar ko'paytmasi uchun o'lchamlar mos kelmadi: [{m}, {k1}] dot [{k2}, {n}]"
                )
            res = [[0.0] * n for _ in range(m)]
            for i in range(m):
                for k in range(k1):
                    val_a = self.data[i][k]
                    for j in range(n):
                        res[i][j] += val_a * other.data[k][j]
            return Tensor(res, device=self.device)

        # 3. 2D dot 1D -> 1D Tensor
        if self.ndim == 2 and other.ndim == 1:
            m, k1 = self._shape
            k2 = other._shape[0]
            if k1 != k2:
                raise ZafiraError(
                    f"Matritsa va vektor o'lchami mos kelmadi: [{m}, {k1}] dot [{k2}]"
                )
            res = [0.0] * m
            for i in range(m):
                res[i] = sum(self.data[i][k] * other.data[k] for k in range(k1))
            return Tensor(res, device=self.device)

        # 4. 1D dot 2D -> 1D Tensor
        if self.ndim == 1 and other.ndim == 2:
            k1 = self._shape[0]
            k2, n = other._shape
            if k1 != k2:
                raise ZafiraError(
                    f"Vektor va matritsa o'lchami mos kelmadi: [{k1}] dot [{k2}, {n}]"
                )
            res = [0.0] * n
            for j in range(n):
                res[j] = sum(self.data[k] * other.data[k][j] for k in range(k1))
            return Tensor(res, device=self.device)

        raise ZafiraError(f"Qo'llab-quvvatlanmagan dot o'lchamlari: {self.shape} dot {other.shape}")

    def add(self, other: Any) -> 'Tensor':
        if isinstance(other, (int, float)):
            val = float(other)
            if self.ndim == 1:
                return Tensor([x + val for x in self.data], device=self.device)
            return Tensor([[x + val for x in row] for row in self.data], device=self.device)

        if not isinstance(other, Tensor):
            other = Tensor(other)

        if self._shape != other._shape:
            raise ZafiraError(f"Tensor o'lchamlari mos kelmadi: {self.shape} + {other.shape}")

        if self.ndim == 1:
            return Tensor([a + b for a, b in zip(self.data, other.data)], device=self.device)
        res = [
            [a + b for a, b in zip(r1, r2)]
            for r1, r2 in zip(self.data, other.data)
        ]
        return Tensor(res, device=self.device)

    def sub(self, other: Any) -> 'Tensor':
        if isinstance(other, (int, float)):
            val = float(other)
            if self.ndim == 1:
                return Tensor([x - val for x in self.data], device=self.device)
            return Tensor([[x - val for x in row] for row in self.data], device=self.device)

        if not isinstance(other, Tensor):
            other = Tensor(other)

        if self._shape != other._shape:
            raise ZafiraError(f"Tensor o'lchamlari mos kelmadi: {self.shape} - {other.shape}")

        if self.ndim == 1:
            return Tensor([a - b for a, b in zip(self.data, other.data)], device=self.device)
        res = [
            [a - b for a, b in zip(r1, r2)]
            for r1, r2 in zip(self.data, other.data)
        ]
        return Tensor(res, device=self.device)

    def mul(self, other: Any) -> 'Tensor':
        if isinstance(other, (int, float)):
            val = float(other)
            if self.ndim == 1:
                return Tensor([x * val for x in self.data], device=self.device)
            return Tensor([[x * val for x in row] for row in self.data], device=self.device)

        if not isinstance(other, Tensor):
            other = Tensor(other)

        # Hadamard (element-wise) ko'paytma
        if self._shape != other._shape:
            raise ZafiraError(f"Tensor o'lchamlari mos kelmadi: {self.shape} * {other.shape}")

        if self.ndim == 1:
            return Tensor([a * b for a, b in zip(self.data, other.data)], device=self.device)
        res = [
            [a * b for a, b in zip(r1, r2)]
            for r1, r2 in zip(self.data, other.data)
        ]
        return Tensor(res, device=self.device)

    def sum(self) -> float:
        if self.ndim == 1:
            return sum(self.data)
        return sum(sum(row) for row in self.data)

    def mean(self) -> float:
        total_items = self._shape[0] if self.ndim == 1 else self._shape[0] * self._shape[1]
        if total_items == 0:
            return 0.0
        return self.sum() / total_items

    def cosine_similarity(self, other: Any) -> float:
        """
        AI vektor qidiruvi uchun kosinus o'xshashlik.
        """
        if not isinstance(other, Tensor):
            other = Tensor(other)

        vec1 = self._flatten()
        vec2 = other._flatten()

        if len(vec1) != len(vec2):
            raise ZafiraError(
                f"Kosinus o'xshashlik uchun vektorlar uzunligi teng bo'lishi kerak: {len(vec1)} != {len(vec2)}"
            )

        dot_val = sum(a * b for a, b in zip(vec1, vec2))
        norm_a = math.sqrt(sum(a * a for a in vec1))
        norm_b = math.sqrt(sum(b * b for b in vec2))

        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0

        val = dot_val / (norm_a * norm_b)
        return max(-1.0, min(1.0, val))

    # Python operator drayverlari
    def __add__(self, other): return self.add(other)
    def __radd__(self, other): return self.add(other)
    def __sub__(self, other): return self.sub(other)
    def __rsub__(self, other): return Tensor(other).sub(self)
    def __mul__(self, other): return self.mul(other)
    def __rmul__(self, other): return self.mul(other)
    def __matmul__(self, other): return self.dot(other)

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        if self.ndim == 1:
            return self.data[idx]
        return Tensor(self.data[idx], device=self.device)

    def __iter__(self):
        return iter(self.data)

    def __repr__(self) -> str:
        dev_info = f", device='{self.device}'" if self.device != 'cpu' else ""
        if self.ndim == 1:
            items_str = ', '.join(f"{x:.4g}" if isinstance(x, float) else str(x) for x in self.data)
            return f"Tensor([{items_str}], shape={self.shape}{dev_info})"
        rows_str = ', '.join(
            f"[{', '.join(f'{x:.4g}' if isinstance(x, float) else str(x) for x in row)}]"
            for row in self.data
        )
        return f"Tensor([{rows_str}], shape={self.shape}{dev_info})"

    def __str__(self) -> str:
        return self.__repr__()


# ─── STD.AI MODUL FUNKSIYALARI ───

def _ai_tensor(data: Any) -> Tensor:
    return Tensor(data)


def _ai_zeros(rows: Any, cols: Any = None) -> Tensor:
    r = int(rows)
    if r < 0:
        raise ZafiraError("Qatorlar soni manfiy bo'lishi mumkin emas")
    if cols is None:
        return Tensor([0.0] * r)
    c = int(cols)
    if c < 0:
        raise ZafiraError("Ustunlar soni manfiy bo'lishi mumkin emas")
    return Tensor([[0.0] * c for _ in range(r)])


def _ai_ones(rows: Any, cols: Any = None) -> Tensor:
    r = int(rows)
    if r < 0:
        raise ZafiraError("Qatorlar soni manfiy bo'lishi mumkin emas")
    if cols is None:
        return Tensor([1.0] * r)
    c = int(cols)
    if c < 0:
        raise ZafiraError("Ustunlar soni manfiy bo'lishi mumkin emas")
    return Tensor([[1.0] * c for _ in range(r)])


def _ai_similarity(vec1: Any, vec2: Any) -> float:
    t1 = vec1 if isinstance(vec1, Tensor) else Tensor(vec1)
    t2 = vec2 if isinstance(vec2, Tensor) else Tensor(vec2)
    return t1.cosine_similarity(t2)


def _ai_embedding_mock(text: Any) -> Tensor:
    """
    Matn uchun 8 o'lchamli normalizatsiyalangan vektor (lokal testlar uchun).
    L2 norm = 1.0.
    """
    raw_str = _zf_str(text)
    raw = [0.0] * 8
    if not raw_str:
        raw = [1.0] + [0.0] * 7
    else:
        for i, b in enumerate(raw_str.encode('utf-8')):
            idx = i % 8
            raw[idx] += float(b) * (1.0 + (i % 5) * 0.2)
            raw[(idx + 3) % 8] += float(b ^ 0xAA) * 0.3

    norm = math.sqrt(sum(x * x for x in raw))
    if norm == 0.0:
        normalized = [1.0 / math.sqrt(8)] * 8
    else:
        normalized = [x / norm for x in raw]

    return Tensor(normalized)


def _ai_device() -> str:
    """
    Joriy mavjud apparat ('cpu', 'cuda', 'gpu', 'npu') haqida ma'lumot beradi.
    """
    return get_active_device()


def _ai_devices() -> ZafiraList:
    devs = ['cpu']
    if _SILICON.is_cuda_available():
        devs.append('cuda')
        devs.append('gpu')
    devs.append('npu')
    return ZafiraList(devs)


AI_MODULE_FIELDS = {
    'tensor': _ai_tensor,
    'zeros': _ai_zeros,
    'ones': _ai_ones,
    'similarity': _ai_similarity,
    'embedding_mock': _ai_embedding_mock,
    'device': _ai_device,
    'devices': _ai_devices,
}
