"""
Zafira Language - C Transpiler
AST ni to'g'ridan-to'g'ri bajariladigan C kodiga aylantiradi.
Mustaqil (Self-contained) C Runtime va Native Binar Kompilyator.
Muallif: Jasper & Antigravity
"""

import json
import os
import re
import shutil
import subprocess
import sys
from typing import Dict, List, Optional, Any, Set

from src.parser import (
    Program, Node, NumberLiteral, StringLiteral, BoolLiteral, NullLiteral,
    Identifier, BinaryOp, UnaryOp, FunctionCall, MemberAccess, IndexAccess,
    ListLiteral, RangeExpr, LetStatement, ConstStatement, AssignStatement,
    ReturnStatement, IfStatement, WhileStatement, ForStatement, FunctionDef,
    StructDef, ImplBlock, ImportStatement, RunBlock, ExprStatement, Block, AwaitExpr
)


# Zafira tiplari -> C tiplari mapping
TYPE_MAPPING = {
    'Int': 'int64_t',
    'int': 'int64_t',
    'Float': 'double',
    'float': 'double',
    'String': 'char*',
    'string': 'char*',
    'str': 'char*',
    'Bool': 'int',
    'bool': 'int',
    'List': 'ZfList*',
    'list': 'ZfList*',
    'Any': 'ZfAny',
    'any': 'ZfAny',
    'void': 'void',
    'Null': 'ZfAny',
    'null': 'ZfAny',
}

C_KEYWORDS = {
    'auto', 'break', 'case', 'char', 'const', 'continue', 'default', 'do',
    'double', 'else', 'enum', 'extern', 'float', 'for', 'goto', 'if',
    'int', 'long', 'register', 'return', 'short', 'signed', 'sizeof', 'static',
    'struct', 'switch', 'typedef', 'union', 'unsigned', 'void', 'volatile', 'while'
}

COMPILER_INSTALL_HELP = """
[Zafira Ogohlantirish] Tizimda C kompilyatori ('gcc', 'clang' yoki 'tcc') topilmadi!
Standalone binar (.exe) dastur yaratish uchun quyidagi kompilyatorlardan birini o'rnating:

1. GCC (MinGW-w64) o'rnatish (Windows uchun tavsiya etiladi):
   winget install -e --id BrechtSanders.winlibs.llvm-posix-seh
   yoki MSYS2 orqali:
   winget install -e --id MSYS2.MSYS2
   va MSYS2 terminalida: pacman -S mingw-w64-x86_64-gcc

2. Clang (LLVM) o'rnatish:
   winget install -e --id LLVM.LLVM

3. TCC (Tiny C Compiler - o'ta yengil va tezkor, ~2MB):
   https://bellard.org/tcc/
   Yuklab olib, C:\\tcc papkasiga tashlang va tizim PATH ga qo'shing.

O'rnatgandan so'ng yangi terminal oching va buyruqni qayta ishga tushiring.
Generatsiya qilingan mustaqil C manba kodi saqlandi.
Qo'lda kompilyatsiya qilish:
   gcc <manba.c> -o <dastur.exe> -O2 -lm
"""


class CompilerNotFoundError(Exception):
    """C kompilyatori (gcc, clang, tcc) topilmaganda yuzaga keladigan xatolik"""
    pass


class CompilationError(Exception):
    """Kompilyatsiya jarayonida xatolik yuz berganda yuzaga keladigan xatolik"""
    pass


def find_c_compiler() -> Optional[Dict[str, str]]:
    """
    Tizimda mavjud bo'lgan C kompilyatorini (gcc, clang, tcc) qidiradi.
    Avval PATH dan, keyin Windows standart papkalaridan tekshiradi.
    Topilsa: {'name': 'gcc', 'path': '...'}
    Topilmasa: None
    """
    # 1. PATH tekshirish
    for name in ['gcc', 'clang', 'tcc']:
        path = shutil.which(name)
        if path:
            return {'name': name, 'path': path}

    # 2. Windows-da standart joylashuvlarni tekshirish
    if sys.platform == 'win32':
        candidates = [
            # TCC
            ('tcc', r'C:\tcc\tcc.exe'),
            ('tcc', r'D:\tcc\tcc.exe'),
            ('tcc', os.path.expanduser(r'~\AppData\Local\Programs\tcc\tcc.exe')),
            # MinGW / MSYS2
            ('gcc', r'C:\msys64\mingw64\bin\gcc.exe'),
            ('gcc', r'C:\msys64\ucrt64\bin\gcc.exe'),
            ('gcc', r'C:\msys64\clang64\bin\clang.exe'),
            ('gcc', r'C:\msys64\usr\bin\gcc.exe'),
            ('gcc', r'C:\MinGW\bin\gcc.exe'),
            ('gcc', r'C:\mingw64\bin\gcc.exe'),
            ('gcc', r'C:\w64devkit\bin\gcc.exe'),
            ('gcc', os.path.expanduser(r'~\scoop\apps\gcc\current\bin\gcc.exe')),
            ('gcc', os.path.expanduser(r'~\scoop\apps\mingw\current\bin\gcc.exe')),
            # Clang / LLVM
            ('clang', r'C:\Program Files\LLVM\bin\clang.exe'),
            ('clang', r'C:\Program Files (x86)\LLVM\bin\clang.exe'),
            ('clang', os.path.expanduser(r'~\scoop\apps\llvm\current\bin\clang.exe')),
        ]
        for name, p in candidates:
            if os.path.isfile(p):
                return {'name': name, 'path': p}

    return None


def format_file_size(size_bytes: int) -> str:
    """Fayl hajmini formatlaydi (masalan, 24.50 KB)"""
    if size_bytes < 1024:
        return f"{size_bytes} bayt"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"


def compile_to_binary(
    c_source_path: str,
    output_path: Optional[str] = None,
    compiler_path: Optional[str] = None,
    extra_flags: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    C manba kodini (.c) standalone binar faylga (.exe) aylantiradi.
    """
    if not os.path.exists(c_source_path):
        raise FileNotFoundError(f"C manba fayli topilmadi: {c_source_path}")

    if not output_path:
        base, _ = os.path.splitext(c_source_path)
        output_path = base + ('.exe' if sys.platform == 'win32' else '')

    compiler_info = None
    if compiler_path:
        compiler_info = {'name': os.path.basename(compiler_path).lower(), 'path': compiler_path}
    else:
        compiler_info = find_c_compiler()

    if not compiler_info:
        raise CompilerNotFoundError(COMPILER_INSTALL_HELP)

    c_name = compiler_info['name']
    c_bin = compiler_info['path']

    out_dir = os.path.dirname(output_path)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    cmd = [c_bin, c_source_path, '-o', output_path]
    if 'gcc' in c_name or 'clang' in c_name:
        cmd.extend(['-O2', '-lm'])
    elif 'tcc' in c_name:
        cmd.extend(['-lm'])

    if extra_flags:
        cmd.extend(extra_flags)

    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        err_msg = res.stderr or res.stdout or "Noma'lum xato"
        raise CompilationError(f"Kompilyatsiya xatosi ({c_name}):\n{err_msg}")

    if not os.path.exists(output_path):
        raise CompilationError(f"Kompilyatsiya tugadi, lekin chiqish fayli topilmadi: {output_path}")

    size_bytes = os.path.getsize(output_path)
    return {
        'success': True,
        'binary_path': output_path,
        'compiler': c_name,
        'compiler_path': c_bin,
        'size_bytes': size_bytes,
        'size_str': format_file_size(size_bytes)
    }


class Transpiler:
    """
    Zafira AST ni C dasturlash tili kodiga aylantiruvchi transpiler.
    """

    def __init__(self):
        self.output: List[str] = []
        self.indent: int = 0
        self.functions: Dict[str, str] = {}    # fn nomi -> return_type (Zafira tipi)
        self.variables: Dict[str, str] = {}    # o'zgaruvchi nomi -> Zafira tipi
        self.structs: Set[str] = set()         # struct nomlari

    def emit(self, line: str = ""):
        """Joriy chekinish (indent) bilan C kod qatorini yozadi"""
        if line:
            self.output.append('    ' * self.indent + line)
        else:
            self.output.append("")

    def to_c_ident(self, name: str) -> str:
        """Zafira identifikatorini (masalan 'qo\'sh') C uchun xavfsiz nomga aylantiradi"""
        res = name.replace("'", "_").replace("’", "_").replace("`", "_")
        clean = []
        for ch in res:
            if ch.isalnum() or ch == '_':
                clean.append(ch)
            else:
                clean.append('_')
        out = "".join(clean)
        if not out:
            out = "_zf_anon"
        elif out[0].isdigit():
            out = "_" + out
        if out == 'main':
            out = 'zf_main'
        elif out in C_KEYWORDS:
            out = f"zf_{out}"
        return out

    def map_type(self, zf_type: Optional[str]) -> str:
        """Zafira tipini C tipiga o'giradi"""
        if not zf_type:
            return 'void'
        if zf_type in TYPE_MAPPING:
            return TYPE_MAPPING[zf_type]
        if zf_type in self.structs:
            return self.to_c_ident(zf_type)
        return 'ZfAny'

    def infer_type(self, node: Optional[Node]) -> str:
        """AST tugunining Zafira tipini taxmin qiladi (type inference)"""
        if node is None:
            return 'Null'
        if isinstance(node, NumberLiteral):
            if isinstance(node.value, float) and not node.value.is_integer():
                return 'Float'
            return 'Int'
        if isinstance(node, StringLiteral):
            return 'String'
        if isinstance(node, BoolLiteral):
            return 'Bool'
        if isinstance(node, NullLiteral):
            return 'Null'
        if isinstance(node, Identifier):
            return self.variables.get(node.name, 'Any')
        if isinstance(node, FunctionCall):
            if isinstance(node.callee, Identifier):
                cname = node.callee.name
                if cname in ('String', 'input'):
                    return 'String'
                if cname in ('Int', 'len'):
                    return 'Int'
                if cname == 'Float':
                    return 'Float'
                if cname in self.functions:
                    return self.functions[cname] or 'void'
            elif isinstance(node.callee, MemberAccess):
                mem = node.callee.member
                if mem in ('len', 'uzunlik', 'pop', 'first', 'last'):
                    return 'Int'
                if mem in ('upper', 'lower', 'trim'):
                    return 'String'
            return 'Any'
        if isinstance(node, MemberAccess):
            if node.member in ('len', 'uzunlik', 'first', 'last'):
                return 'Int'
            if node.member in ('upper', 'lower', 'trim'):
                return 'String'
            return 'Any'
        if isinstance(node, IndexAccess):
            obj_t = self.infer_type(node.obj)
            if obj_t == 'String':
                return 'String'
            return 'Int'
        if isinstance(node, BinaryOp):
            lt = self.infer_type(node.left)
            rt = self.infer_type(node.right)
            if node.op == '+':
                if lt == 'String' or rt == 'String':
                    return 'String'
                if lt == 'Float' or rt == 'Float':
                    return 'Float'
                return 'Int'
            if node.op in ('-', '*', '/', '%', '**'):
                if node.op == '*' and (lt == 'String' or rt == 'String'):
                    return 'String'
                if lt == 'Float' or rt == 'Float' or node.op == '/':
                    return 'Float'
                return 'Int'
            if node.op in ('==', '!=', '<', '<=', '>', '>=', 'and', 'or'):
                return 'Bool'
        if isinstance(node, RangeExpr):
            return 'List'
        if isinstance(node, ListLiteral):
            return 'List'
        return 'Any'

    def transpile(self, program: Program) -> str:
        """
        AST dasturini to'liq C manba kodi matniga aylantiradi.
        """
        self.output = []
        self.indent = 0
        self.functions = {}
        self.variables = {}
        self.structs = set()

        # 1. Barcha struct va funksiyalarni ro'yxatga olish
        for stmt in program.body:
            if isinstance(stmt, StructDef):
                self.structs.add(stmt.name)
            elif isinstance(stmt, FunctionDef):
                if stmt.mode == 'seal':
                    self.functions[stmt.name] = stmt.return_type or 'void'
                else:
                    self.functions[stmt.name] = 'Any'

        # 2. C Header qismi va Self-Contained Runtime
        self.emit("// ══════════════════════════════════════════════════════════════")
        self.emit("//  Zafira Dasturlash Tili - C Transpiler Chiqishi")
        self.emit("//  Mustaqil (Self-contained) C Runtime & Native Kompilyator")
        self.emit("// ══════════════════════════════════════════════════════════════")
        self.emit("")
        self.emit("#include <stdio.h>")
        self.emit("#include <stdlib.h>")
        self.emit("#include <string.h>")
        self.emit("#include <stdint.h>")
        self.emit("#include <math.h>")
        self.emit("#include <ctype.h>")
        self.emit("#include <stdarg.h>")
        self.emit("")
        self.emit("// ─── Zafira Asosiy Tiplari ───")
        self.emit("typedef void* ZfAny;")
        self.emit("#define ZF_NULL NULL")
        self.emit("#define ZF_TRUE 1")
        self.emit("#define ZF_FALSE 0")
        self.emit("")
        self.emit("// ─── Zafira List (Dinamik massiv) ───")
        self.emit("typedef struct {")
        self.emit("    int64_t* items;")
        self.emit("    int64_t length;")
        self.emit("    int64_t capacity;")
        self.emit("} ZfList;")
        self.emit("")
        self.emit("static inline ZfList* zf_list_create(int64_t initial_cap) {")
        self.emit("    if (initial_cap < 4) initial_cap = 4;")
        self.emit("    ZfList* list = (ZfList*)malloc(sizeof(ZfList));")
        self.emit("    if (!list) return NULL;")
        self.emit("    list->items = (int64_t*)malloc(sizeof(int64_t) * initial_cap);")
        self.emit("    list->length = 0;")
        self.emit("    list->capacity = initial_cap;")
        self.emit("    return list;")
        self.emit("}")
        self.emit("")
        self.emit("static inline void zf_list_push(ZfList* list, int64_t val) {")
        self.emit("    if (!list) return;")
        self.emit("    if (list->length >= list->capacity) {")
        self.emit("        int64_t new_cap = list->capacity * 2;")
        self.emit("        if (new_cap < 4) new_cap = 4;")
        self.emit("        int64_t* new_items = (int64_t*)realloc(list->items, sizeof(int64_t) * new_cap);")
        self.emit("        if (!new_items) return;")
        self.emit("        list->items = new_items;")
        self.emit("        list->capacity = new_cap;")
        self.emit("    }")
        self.emit("    list->items[list->length++] = val;")
        self.emit("}")
        self.emit("")
        self.emit("static inline int64_t zf_list_pop(ZfList* list) {")
        self.emit("    if (!list || list->length == 0) return 0;")
        self.emit("    return list->items[--list->length];")
        self.emit("}")
        self.emit("")
        self.emit("static inline int64_t zf_list_len(ZfList* list) {")
        self.emit("    return list ? list->length : 0;")
        self.emit("}")
        self.emit("")
        self.emit("static inline int64_t zf_list_get(ZfList* list, int64_t idx) {")
        self.emit("    if (!list) return 0;")
        self.emit("    if (idx < 0) idx = list->length + idx;")
        self.emit("    if (idx < 0 || idx >= list->length) {")
        self.emit("        fprintf(stderr, \"[Zafira XATO] Indeks [%lld] chegaradan tashqarida (uzunlik: %lld)\\n\", (long long)idx, (long long)list->length);")
        self.emit("        return 0;")
        self.emit("    }")
        self.emit("    return list->items[idx];")
        self.emit("}")
        self.emit("")
        self.emit("static inline void zf_list_set(ZfList* list, int64_t idx, int64_t val) {")
        self.emit("    if (!list) return;")
        self.emit("    if (idx < 0) idx = list->length + idx;")
        self.emit("    if (idx < 0 || idx >= list->length) {")
        self.emit("        fprintf(stderr, \"[Zafira XATO] Indeks [%lld] chegaradan tashqarida (uzunlik: %lld)\\n\", (long long)idx, (long long)list->length);")
        self.emit("        return;")
        self.emit("    }")
        self.emit("    list->items[idx] = val;")
        self.emit("}")
        self.emit("")
        self.emit("static inline ZfList* zf_list_new(int64_t count, ...) {")
        self.emit("    ZfList* list = zf_list_create(count > 0 ? count : 4);")
        self.emit("    va_list args;")
        self.emit("    va_start(args, count);")
        self.emit("    for (int64_t i = 0; i < count; i++) {")
        self.emit("        int64_t val = va_arg(args, int64_t);")
        self.emit("        zf_list_push(list, val);")
        self.emit("    }")
        self.emit("    va_end(args);")
        self.emit("    return list;")
        self.emit("}")
        self.emit("")
        self.emit("static inline ZfList* zf_list_from_range(int64_t start, int64_t end) {")
        self.emit("    int64_t count = end > start ? (end - start) : 0;")
        self.emit("    ZfList* list = zf_list_create(count > 0 ? count : 4);")
        self.emit("    for (int64_t i = start; i < end; i++) {")
        self.emit("        zf_list_push(list, i);")
        self.emit("    }")
        self.emit("    return list;")
        self.emit("}")
        self.emit("")
        self.emit("static inline char* zf_str_list(ZfList* list) {")
        self.emit("    if (!list) {")
        self.emit("        char* res = (char*)malloc(3);")
        self.emit("        strcpy(res, \"[]\");")
        self.emit("        return res;")
        self.emit("    }")
        self.emit("    size_t cap = 32 + (size_t)list->length * 24;")
        self.emit("    char* buf = (char*)malloc(cap);")
        self.emit("    buf[0] = '[';")
        self.emit("    buf[1] = '\\0';")
        self.emit("    for (int64_t i = 0; i < list->length; i++) {")
        self.emit("        char temp[32];")
        self.emit("        snprintf(temp, 32, \"%lld\", (long long)list->items[i]);")
        self.emit("        strcat(buf, temp);")
        self.emit("        if (i < list->length - 1) strcat(buf, \", \");")
        self.emit("    }")
        self.emit("    strcat(buf, \"]\");")
        self.emit("    return buf;")
        self.emit("}")
        self.emit("")
        self.emit("// ─── Zafira Satr (String) Funksiyalari ───")
        self.emit("static inline char* zf_str_concat(const char* s1, const char* s2) {")
        self.emit("    if (!s1) s1 = \"\";")
        self.emit("    if (!s2) s2 = \"\";")
        self.emit("    size_t len1 = strlen(s1);")
        self.emit("    size_t len2 = strlen(s2);")
        self.emit("    char* res = (char*)malloc(len1 + len2 + 1);")
        self.emit("    if (!res) return \"\";")
        self.emit("    strcpy(res, s1);")
        self.emit("    strcat(res, s2);")
        self.emit("    return res;")
        self.emit("}")
        self.emit("")
        self.emit("static inline char* zf_str_int(int64_t val) {")
        self.emit("    char* buf = (char*)malloc(32);")
        self.emit("    snprintf(buf, 32, \"%lld\", (long long)val);")
        self.emit("    return buf;")
        self.emit("}")
        self.emit("")
        self.emit("static inline char* zf_str_float(double val) {")
        self.emit("    char* buf = (char*)malloc(32);")
        self.emit("    snprintf(buf, 32, \"%g\", val);")
        self.emit("    return buf;")
        self.emit("}")
        self.emit("")
        self.emit("static inline char* zf_str_bool(int val) {")
        self.emit("    return val ? \"true\" : \"false\";")
        self.emit("}")
        self.emit("")
        self.emit("static inline int64_t zf_to_int(const char* s) {")
        self.emit("    return s ? atoll(s) : 0;")
        self.emit("}")
        self.emit("")
        self.emit("static inline double zf_to_float(const char* s) {")
        self.emit("    return s ? atof(s) : 0.0;")
        self.emit("}")
        self.emit("")
        self.emit("static inline int zf_str_eq(const char* s1, const char* s2) {")
        self.emit("    if (s1 == s2) return 1;")
        self.emit("    if (!s1 || !s2) return 0;")
        self.emit("    return strcmp(s1, s2) == 0;")
        self.emit("}")
        self.emit("")
        self.emit("static inline int zf_str_neq(const char* s1, const char* s2) {")
        self.emit("    return !zf_str_eq(s1, s2);")
        self.emit("}")
        self.emit("")
        self.emit("static inline char* zf_str_repeat(const char* s, int64_t count) {")
        self.emit("    if (!s || count <= 0) {")
        self.emit("        char* res = (char*)malloc(1);")
        self.emit("        res[0] = '\\0';")
        self.emit("        return res;")
        self.emit("    }")
        self.emit("    size_t len = strlen(s);")
        self.emit("    char* res = (char*)malloc(len * count + 1);")
        self.emit("    if (!res) return \"\";")
        self.emit("    res[0] = '\\0';")
        self.emit("    for (int64_t i = 0; i < count; i++) {")
        self.emit("        memcpy(res + i * len, s, len);")
        self.emit("    }")
        self.emit("    res[len * count] = '\\0';")
        self.emit("    return res;")
        self.emit("}")
        self.emit("")
        self.emit("static inline char* zf_str_upper(const char* s) {")
        self.emit("    if (!s) return \"\";")
        self.emit("    size_t len = strlen(s);")
        self.emit("    char* res = (char*)malloc(len + 1);")
        self.emit("    for (size_t i = 0; i < len; i++) {")
        self.emit("        res[i] = (char)toupper((unsigned char)s[i]);")
        self.emit("    }")
        self.emit("    res[len] = '\\0';")
        self.emit("    return res;")
        self.emit("}")
        self.emit("")
        self.emit("static inline char* zf_str_lower(const char* s) {")
        self.emit("    if (!s) return \"\";")
        self.emit("    size_t len = strlen(s);")
        self.emit("    char* res = (char*)malloc(len + 1);")
        self.emit("    for (size_t i = 0; i < len; i++) {")
        self.emit("        res[i] = (char)tolower((unsigned char)s[i]);")
        self.emit("    }")
        self.emit("    res[len] = '\\0';")
        self.emit("    return res;")
        self.emit("}")
        self.emit("")
        self.emit("static inline char* zf_str_trim(const char* s) {")
        self.emit("    if (!s) return \"\";")
        self.emit("    while (*s == ' ' || *s == '\\t' || *s == '\\n' || *s == '\\r') s++;")
        self.emit("    if (*s == 0) {")
        self.emit("        char* res = (char*)malloc(1);")
        self.emit("        res[0] = '\\0';")
        self.emit("        return res;")
        self.emit("    }")
        self.emit("    const char* end = s + strlen(s) - 1;")
        self.emit("    while (end > s && (*end == ' ' || *end == '\\t' || *end == '\\n' || *end == '\\r')) end--;")
        self.emit("    size_t len = (size_t)(end - s + 1);")
        self.emit("    char* res = (char*)malloc(len + 1);")
        self.emit("    memcpy(res, s, len);")
        self.emit("    res[len] = '\\0';")
        self.emit("    return res;")
        self.emit("}")
        self.emit("")
        self.emit("// ─── Arifmetik Amallar ───")
        self.emit("static inline int64_t zf_pow_int(int64_t base, int64_t exp) {")
        self.emit("    if (exp < 0) return 0;")
        self.emit("    int64_t res = 1;")
        self.emit("    while (exp > 0) {")
        self.emit("        if (exp & 1) res *= base;")
        self.emit("        base *= base;")
        self.emit("        exp >>= 1;")
        self.emit("    }")
        self.emit("    return res;")
        self.emit("}")
        self.emit("")
        self.emit("// ─── Standart Kiritish (Input) ───")
        self.emit("static inline char* zf_input(const char* prompt) {")
        self.emit("    if (prompt && strlen(prompt) > 0) {")
        self.emit("        printf(\"%s\", prompt);")
        self.emit("        fflush(stdout);")
        self.emit("    }")
        self.emit("    char* buf = (char*)malloc(1024);")
        self.emit("    if (!buf) return \"\";")
        self.emit("    if (fgets(buf, 1024, stdin)) {")
        self.emit("        size_t len = strlen(buf);")
        self.emit("        if (len > 0 && buf[len - 1] == '\\n') buf[len - 1] = '\\0';")
        self.emit("        if (len > 1 && buf[len - 2] == '\\r') buf[len - 2] = '\\0';")
        self.emit("        return buf;")
        self.emit("    }")
        self.emit("    buf[0] = '\\0';")
        self.emit("    return buf;")
        self.emit("}")
        self.emit("")

        # 3. Structlarni chiqarish
        structs = [s for s in program.body if isinstance(s, StructDef)]
        if structs:
            self.emit("// ─── Strukturalar ───")
            for st in structs:
                self.transpile_struct(st)

        # 4. Funksiyalar va top-level statementlarni ajratish
        functions = [s for s in program.body if isinstance(s, FunctionDef)]
        top_stmts = [s for s in program.body if not isinstance(s, (StructDef, ImplBlock, FunctionDef, ImportStatement))]

        # 5. Forward declarations (prototiplar)
        if functions:
            self.emit("// ─── Funksiyalar prototiplari ───")
            for fn in functions:
                proto = self.get_function_signature(fn)
                self.emit(f"{proto};")
            self.emit("")

        # 6. Funksiyalar tanasini chiqarish
        if functions:
            self.emit("// ─── Funksiyalar ta'riflari ───")
            for fn in functions:
                self.transpile_function(fn)

        # 7. main() funksiyasi
        self.emit("// ─── Asosiy Kirish Nuqtasi (main) ───")
        self.emit("int main(int argc, char** argv) {")
        self.indent += 1

        for stmt in top_stmts:
            self.transpile_statement(stmt)

        # Agar Zafira da main() funksiyasi ta'riflangan bo'lsa, uni chaqirish
        if 'main' in self.functions:
            self.emit("zf_main();")

        self.emit("return 0;")
        self.indent -= 1
        self.emit("}")
        self.emit("")

        return "\n".join(self.output)

    def transpile_struct(self, node: StructDef):
        """Struct ta'rifini C typedef struct ga aylantiradi"""
        c_name = self.to_c_ident(node.name)
        self.emit(f"typedef struct {c_name} {{")
        self.indent += 1
        for fname, ftype in node.fields:
            c_type = self.map_type(ftype)
            c_fname = self.to_c_ident(fname)
            self.emit(f"{c_type} {c_fname};")
        self.indent -= 1
        self.emit(f"}} {c_name};")
        self.emit("")

    def get_function_signature(self, node: FunctionDef) -> str:
        """Funksiya sarlavhasi (imzosi)ni tuzadi"""
        c_name = self.to_c_ident(node.name)
        if node.mode == 'seal':
            ret_type = self.map_type(node.return_type) if node.return_type else 'void'
            params = []
            for pname, ptype in node.params:
                c_ptype = self.map_type(ptype) if ptype else 'int64_t'
                params.append(f"{c_ptype} {self.to_c_ident(pname)}")
        else:
            # draft fn -> barcha turlar ZfAny (void*) bo'ladi
            ret_type = 'ZfAny'
            params = [f"ZfAny {self.to_c_ident(pname)}" for pname, _ in node.params]

        params_str = ", ".join(params) if params else "void"
        return f"{ret_type} {c_name}({params_str})"

    def transpile_function(self, node: FunctionDef):
        """Funksiyani C kodiga aylantiradi"""
        sig = self.get_function_signature(node)
        self.emit(f"{sig} {{")
        self.indent += 1

        saved_vars = dict(self.variables)
        for pname, ptype in node.params:
            if node.mode == 'seal':
                self.variables[pname] = ptype or 'Int'
            else:
                self.variables[pname] = 'Any'

        for stmt in node.body:
            self.transpile_statement(stmt)

        self.variables = saved_vars
        self.indent -= 1
        self.emit("}")
        self.emit("")

    def transpile_statement(self, node: Node):
        """Operator (statement)ni C kodiga aylantiradi"""
        if isinstance(node, LetStatement):
            self.transpile_let(node)
        elif isinstance(node, ConstStatement):
            self.transpile_const(node)
        elif isinstance(node, AssignStatement):
            if isinstance(node.target, IndexAccess):
                obj_c = self.transpile_expr(node.target.obj)
                idx_c = self.transpile_expr(node.target.index)
                val_c = self.transpile_expr(node.value)
                obj_type = self.infer_type(node.target.obj)
                if obj_type == 'String':
                    self.emit(f"{obj_c}[{idx_c}] = {val_c};")
                else:
                    self.emit(f"zf_list_set({obj_c}, {idx_c}, (int64_t)({val_c}));")
            else:
                target = self.transpile_expr(node.target)
                val = self.transpile_expr(node.value)
                self.emit(f"{target} = {val};")
        elif isinstance(node, ReturnStatement):
            if node.value is not None:
                val = self.transpile_expr(node.value)
                self.emit(f"return {val};")
            else:
                self.emit("return;")
        elif isinstance(node, IfStatement):
            self.transpile_if(node)
        elif isinstance(node, WhileStatement):
            cond = self.transpile_expr(node.condition)
            self.emit(f"while ({cond}) {{")
            self.indent += 1
            for s in node.body:
                self.transpile_statement(s)
            self.indent -= 1
            self.emit("}")
        elif isinstance(node, ForStatement):
            self.transpile_for(node)
        elif isinstance(node, ExprStatement):
            self.transpile_expr_statement(node)
        elif isinstance(node, RunBlock):
            self.emit(f"// Silicon runtime: {node.target}")
            self.emit("{")
            self.indent += 1
            for s in node.body:
                self.transpile_statement(s)
            self.indent -= 1
            self.emit("}")
        elif isinstance(node, Block):
            self.emit("{")
            self.indent += 1
            for s in node.statements:
                self.transpile_statement(s)
            self.indent -= 1
            self.emit("}")

    def transpile_let(self, node: LetStatement):
        """LetStatement ni C o'zgaruvchisiga aylantiradi"""
        c_name = self.to_c_ident(node.name)
        zf_type = node.type_hint or self.infer_type(node.value)
        self.variables[node.name] = zf_type
        c_type = self.map_type(zf_type)

        if node.value is not None:
            val_expr = self.transpile_expr(node.value)
            self.emit(f"{c_type} {c_name} = {val_expr};")
        else:
            self.emit(f"{c_type} {c_name};")

    def transpile_const(self, node: ConstStatement):
        """ConstStatement ni const C o'zgaruvchisiga aylantiradi"""
        c_name = self.to_c_ident(node.name)
        zf_type = node.type_hint or self.infer_type(node.value)
        self.variables[node.name] = zf_type
        c_type = self.map_type(zf_type)
        val_expr = self.transpile_expr(node.value)
        self.emit(f"const {c_type} {c_name} = {val_expr};")

    def transpile_if(self, node: IfStatement):
        """IfStatement (if/else if/else) ni C shartli blokiga aylantiradi"""
        cond = self.transpile_expr(node.condition)
        self.emit(f"if ({cond}) {{")
        self.indent += 1
        for s in node.then_block:
            self.transpile_statement(s)
        self.indent -= 1

        curr = node
        while curr.else_block:
            if len(curr.else_block) == 1 and isinstance(curr.else_block[0], IfStatement):
                elif_node = curr.else_block[0]
                elif_cond = self.transpile_expr(elif_node.condition)
                self.emit(f"}} else if ({elif_cond}) {{")
                self.indent += 1
                for s in elif_node.then_block:
                    self.transpile_statement(s)
                self.indent -= 1
                curr = elif_node
            else:
                self.emit("} else {")
                self.indent += 1
                for s in curr.else_block:
                    self.transpile_statement(s)
                self.indent -= 1
                break
        self.emit("}")

    def transpile_for(self, node: ForStatement):
        """ForStatement ni C for tsikliga aylantiradi"""
        c_var = self.to_c_ident(node.var)
        self.variables[node.var] = 'Int'

        if isinstance(node.iterable, RangeExpr):
            start_c = self.transpile_expr(node.iterable.start)
            end_c = self.transpile_expr(node.iterable.end)
            self.emit(f"for (int64_t {c_var} = {start_c}; {c_var} < {end_c}; {c_var}++) {{")
            self.indent += 1
            for s in node.body:
                self.transpile_statement(s)
            self.indent -= 1
            self.emit("}")
        else:
            iter_c = self.transpile_expr(node.iterable)
            loop_idx = f"_zf_i_{c_var}"
            self.emit(f"for (int64_t {loop_idx} = 0; {loop_idx} < zf_list_len({iter_c}); {loop_idx}++) {{")
            self.indent += 1
            self.emit(f"int64_t {c_var} = zf_list_get({iter_c}, {loop_idx});")
            for s in node.body:
                self.transpile_statement(s)
            self.indent -= 1
            self.emit("}")

    def transpile_expr_statement(self, node: ExprStatement):
        """ExprStatement ni C qatoriga aylantiradi, print() ni printf ga o'giradi"""
        expr = node.expr

        # print(...) maxsus qoidasi: print -> C printf
        if isinstance(expr, FunctionCall) and isinstance(expr.callee, Identifier) and expr.callee.name == 'print':
            self.transpile_print_call(expr.args)
            return

        expr_c = self.transpile_expr(expr)
        self.emit(f"{expr_c};")

    def transpile_print_call(self, args: List[Node]):
        """print(...) ni C printf(...) chaqiruviga aylantiradi"""
        if not args:
            self.emit('printf("\\n");')
            return

        format_parts = []
        c_args = []

        for arg in args:
            arg_type = self.infer_type(arg)
            arg_c = self.transpile_expr(arg)

            if arg_type == 'String':
                format_parts.append("%s")
                c_args.append(arg_c)
            elif arg_type == 'Int':
                format_parts.append("%lld")
                c_args.append(f"(long long)({arg_c})")
            elif arg_type == 'Float':
                format_parts.append("%g")
                c_args.append(arg_c)
            elif arg_type == 'Bool':
                format_parts.append("%s")
                c_args.append(f"({arg_c} ? \"true\" : \"false\")")
            elif arg_type == 'List':
                format_parts.append("%s")
                c_args.append(f"zf_str_list({arg_c})")
            else:
                # Noma'lum yoki satr ifodasi
                format_parts.append("%s")
                c_args.append(arg_c)

        fmt_str = " ".join(format_parts) + "\\n"
        args_str = ", ".join(c_args)
        self.emit(f'printf("{fmt_str}", {args_str});')

    def transpile_expr(self, node: Node) -> str:
        """Iborani (Expression) C ifodasiga aylantiradi"""
        if isinstance(node, AwaitExpr):
            return self.transpile_expr(node.expr)

        if isinstance(node, NumberLiteral):
            if isinstance(node.value, float) and not node.value.is_integer():
                return str(node.value)
            return str(int(node.value))

        if isinstance(node, StringLiteral):
            return json.dumps(node.value, ensure_ascii=False)

        if isinstance(node, BoolLiteral):
            return "ZF_TRUE" if node.value else "ZF_FALSE"

        if isinstance(node, NullLiteral):
            return "ZF_NULL"

        if isinstance(node, Identifier):
            return self.to_c_ident(node.name)

        if isinstance(node, BinaryOp):
            return self.transpile_binary_op(node)

        if isinstance(node, UnaryOp):
            operand_c = self.transpile_expr(node.operand)
            if node.op == '-':
                return f"(-{operand_c})"
            if node.op == 'not':
                return f"(!{operand_c})"
            return f"({node.op}{operand_c})"

        if isinstance(node, FunctionCall):
            return self.transpile_function_call(node)

        if isinstance(node, MemberAccess):
            obj_c = self.transpile_expr(node.obj)
            mem = node.member
            if mem in ('len', 'uzunlik'):
                obj_type = self.infer_type(node.obj)
                if obj_type == 'String':
                    return f"((int64_t)strlen({obj_c}))"
                return f"zf_list_len({obj_c})"
            elif mem == 'first':
                return f"zf_list_get({obj_c}, 0)"
            elif mem == 'last':
                return f"zf_list_get({obj_c}, zf_list_len({obj_c}) - 1)"
            mem_c = self.to_c_ident(mem)
            return f"{obj_c}.{mem_c}"

        if isinstance(node, IndexAccess):
            obj_c = self.transpile_expr(node.obj)
            idx_c = self.transpile_expr(node.index)
            obj_type = self.infer_type(node.obj)
            if obj_type == 'String':
                return f"{obj_c}[{idx_c}]"
            return f"zf_list_get({obj_c}, {idx_c})"

        if isinstance(node, RangeExpr):
            start_c = self.transpile_expr(node.start)
            end_c = self.transpile_expr(node.end)
            return f"zf_list_from_range({start_c}, {end_c})"

        if isinstance(node, ListLiteral):
            count = len(node.elements)
            if count == 0:
                return "zf_list_create(4)"
            elements_c = [f"(int64_t)({self.transpile_expr(e)})" for e in node.elements]
            return f"zf_list_new({count}, {', '.join(elements_c)})"

        return "ZF_NULL"

    def transpile_binary_op(self, node: BinaryOp) -> str:
        """Ikkilik amal (BinaryOp)ni C ifodasiga aylantiradi"""
        left_type = self.infer_type(node.left)
        right_type = self.infer_type(node.right)

        # Satrlarni birlashtirish (+)
        if node.op == '+':
            if left_type == 'String' or right_type == 'String':
                left_c = self.transpile_expr(node.left)
                right_c = self.transpile_expr(node.right)
                if left_type != 'String':
                    left_c = self.wrap_to_string(node.left, left_c)
                if right_type != 'String':
                    right_c = self.wrap_to_string(node.right, right_c)
                return f"zf_str_concat({left_c}, {right_c})"

        left_c = self.transpile_expr(node.left)
        right_c = self.transpile_expr(node.right)

        # Satrlarni solishtirish (== va !=)
        if (left_type == 'String' and right_type == 'String') or \
           (isinstance(node.left, StringLiteral) and isinstance(node.right, StringLiteral)):
            if node.op == '==':
                return f"zf_str_eq({left_c}, {right_c})"
            if node.op == '!=':
                return f"zf_str_neq({left_c}, {right_c})"

        # Satr ko'paytirish (*)
        if node.op == '*':
            if left_type == 'String' and right_type in ('Int', 'Any'):
                return f"zf_str_repeat({left_c}, {right_c})"
            if right_type == 'String' and left_type in ('Int', 'Any'):
                return f"zf_str_repeat({right_c}, {left_c})"

        if node.op == '**':
            if left_type == 'Int' and right_type == 'Int':
                return f"zf_pow_int({left_c}, {right_c})"
            return f"pow({left_c}, {right_c})"

        if node.op == 'and':
            return f"({left_c} && {right_c})"
        if node.op == 'or':
            return f"({left_c} || {right_c})"

        return f"({left_c} {node.op} {right_c})"

    def wrap_to_string(self, node: Node, expr_c: str) -> str:
        """Ifodani mos zf_str_* funksiyasi bilan o'raydi"""
        t = self.infer_type(node)
        if t == 'Int':
            return f"zf_str_int({expr_c})"
        if t == 'Float':
            return f"zf_str_float({expr_c})"
        if t == 'Bool':
            return f"zf_str_bool({expr_c})"
        if t == 'List':
            return f"zf_str_list({expr_c})"
        return f"zf_str_int({expr_c})"

    def transpile_function_call(self, node: FunctionCall) -> str:
        """Funksiya chaqiruvini C ga aylantiradi"""
        if isinstance(node.callee, MemberAccess):
            obj = node.callee.obj
            member = node.callee.member
            obj_c = self.transpile_expr(obj)
            if member == 'push' and node.args:
                arg_c = self.transpile_expr(node.args[0])
                return f"zf_list_push({obj_c}, (int64_t)({arg_c}))"
            if member == 'pop':
                return f"zf_list_pop({obj_c})"
            if member in ('len', 'uzunlik'):
                obj_t = self.infer_type(obj)
                if obj_t == 'String':
                    return f"((int64_t)strlen({obj_c}))"
                return f"zf_list_len({obj_c})"
            if member == 'upper':
                return f"zf_str_upper({obj_c})"
            if member == 'lower':
                return f"zf_str_lower({obj_c})"
            if member == 'trim':
                return f"zf_str_trim({obj_c})"
            if member == 'first':
                return f"zf_list_get({obj_c}, 0)"
            if member == 'last':
                return f"zf_list_get({obj_c}, zf_list_len({obj_c}) - 1)"

        if isinstance(node.callee, Identifier):
            name = node.callee.name

            # String(...) casting
            if name == 'String' and node.args:
                arg = node.args[0]
                arg_c = self.transpile_expr(arg)
                arg_t = self.infer_type(arg)
                if arg_t == 'Int':
                    return f"zf_str_int({arg_c})"
                if arg_t == 'Float':
                    return f"zf_str_float({arg_c})"
                if arg_t == 'Bool':
                    return f"zf_str_bool({arg_c})"
                if arg_t == 'String':
                    return arg_c
                if arg_t == 'List':
                    return f"zf_str_list({arg_c})"
                return f"zf_str_int({arg_c})"

            # Int(...) casting
            if name == 'Int' and node.args:
                arg_c = self.transpile_expr(node.args[0])
                return f"zf_to_int({arg_c})"

            # Float(...) casting
            if name == 'Float' and node.args:
                arg_c = self.transpile_expr(node.args[0])
                return f"zf_to_float({arg_c})"

            # len(...)
            if name == 'len' and node.args:
                arg = node.args[0]
                arg_c = self.transpile_expr(arg)
                arg_t = self.infer_type(arg)
                if arg_t == 'String':
                    return f"((int64_t)strlen({arg_c}))"
                return f"zf_list_len({arg_c})"

            # input(...)
            if name == 'input':
                prompt_c = self.transpile_expr(node.args[0]) if node.args else '""'
                return f"zf_input({prompt_c})"

            c_func_name = self.to_c_ident(name)
        else:
            c_func_name = self.transpile_expr(node.callee)

        args_c = [self.transpile_expr(a) for a in node.args]
        return f"{c_func_name}({', '.join(args_c)})"
