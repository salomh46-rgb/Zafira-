"""
Zafira Language - AOT Single-Binary Standalone Packager
Loyiha va barcha lokal modullarni (.zf) bitta mustaqil binar faylga (.exe / ELF)
yoki Single Translation Unit C manba kodiga jamlovchi paketlash dvigateli.

Muallif: Jasper & Antigravity
"""

import base64
import dataclasses
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Dict, List, Optional, Any, Set, Tuple

# Loyiha ildiz papkasi
_ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _ROOT_DIR not in sys.path:
    sys.path.insert(0, _ROOT_DIR)

from src.lexer import Lexer, LexerError
from src.parser import (
    Program, Node, NumberLiteral, StringLiteral, BoolLiteral, NullLiteral,
    Identifier, BinaryOp, UnaryOp, FunctionCall, MemberAccess, IndexAccess,
    ListLiteral, RangeExpr, LetStatement, ConstStatement, AssignStatement,
    ReturnStatement, IfStatement, WhileStatement, ForStatement, FunctionDef,
    StructDef, ImplBlock, ImportStatement, RunBlock, TryStatement, ThrowStatement,
    ExprStatement, Block, MatchExpr, MatchArm, AwaitExpr, ParseError, Parser
)
from src.transpiler import (
    Transpiler,
    find_c_compiler,
    compile_to_binary,
    format_file_size,
    CompilerNotFoundError,
    CompilationError
)


class PackagerError(Exception):
    """Paketlash jarayonidagi umumiy xatolik."""
    pass


def sanitize_identifier(name: str) -> str:
    """Modul yoki fayl nomidan xavfsiz identifikator yasaydi."""
    clean = re.sub(r'[^a-zA-Z0-9_]', '_', name)
    if not clean:
        clean = "_mod"
    elif clean[0].isdigit():
        clean = "_" + clean
    return clean


def is_local_module_path(path: str) -> bool:
    """Yo'l lokal .zf modul ekanligini aniqlaydi."""
    if not path:
        return False
    if path.startswith(('std.', 'sys.', 'py.')):
        return False
    return (
        path.startswith(('./', '../', '.\\', '..\\'))
        or path.endswith('.zf')
        or '/' in path
        or '\\' in path
        or not ('.' in path and not path.endswith('.zf'))
    )


def resolve_local_module_file(import_path: str, current_file: str) -> str:
    """
    Import yo'lini fayl tizimidagi mutlaq yo'lga aylantiradi.
    """
    base_dir = os.path.dirname(os.path.abspath(current_file))

    # 1. Joriy fayl papkasiga nisbatan
    cand = os.path.normpath(os.path.join(base_dir, import_path))
    if os.path.isfile(cand):
        return os.path.abspath(cand)
    if not cand.endswith('.zf'):
        cand_zf = cand + '.zf'
        if os.path.isfile(cand_zf):
            return os.path.abspath(cand_zf)

    # 2. Ishchi papka (CWD) ga nisbatan
    cwd_cand = os.path.normpath(os.path.join(os.getcwd(), import_path))
    if os.path.isfile(cwd_cand):
        return os.path.abspath(cwd_cand)
    if not cwd_cand.endswith('.zf'):
        cwd_cand_zf = cwd_cand + '.zf'
        if os.path.isfile(cwd_cand_zf):
            return os.path.abspath(cwd_cand_zf)

    raise FileNotFoundError(
        f"Lokal Zafira moduli topilmadi: '{import_path}'\n"
        f"Qidirildi: {cand} yoki {cwd_cand}"
    )


def resolve_entry_point(target_path: str) -> Tuple[str, str, str]:
    """
    Berilgan yo'ldan (loyiha papkasi, zafira.json yoki fayl.zf)
    (entry_file, project_dir, project_name) ni aniqlaydi.
    """
    target_abs = os.path.abspath(target_path)

    # 1. To'g'ridan-to'g'ri .zf fayl berilgan bo'lsa
    if os.path.isfile(target_abs) and target_abs.endswith('.zf'):
        project_dir = os.path.dirname(target_abs)
        project_name = os.path.splitext(os.path.basename(target_abs))[0]
        # Agar yonida zafira.json bo'lsa, nomini olish
        manifest_p = os.path.join(project_dir, 'zafira.json')
        if os.path.exists(manifest_p):
            try:
                with open(manifest_p, 'r', encoding='utf-8') as f:
                    manifest = json.load(f)
                    project_name = manifest.get('name', project_name)
            except Exception:
                pass
        return target_abs, project_dir, project_name

    # 2. zafira.json manifest fayli berilgan bo'lsa
    if os.path.isfile(target_abs) and target_abs.endswith('.json'):
        project_dir = os.path.dirname(target_abs)
        with open(target_abs, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        project_name = manifest.get('name', 'zafira_app')
        entry_rel = manifest.get('entry', 'src/main.zf')
        entry_abs = os.path.normpath(os.path.join(project_dir, entry_rel))
        if not os.path.exists(entry_abs):
            raise FileNotFoundError(f"Manifestda ko'rsatilgan kirish fayli topilmadi: {entry_abs}")
        return entry_abs, project_dir, project_name

    # 3. Papka berilgan bo'lsa
    if os.path.isdir(target_abs):
        project_dir = target_abs
        project_name = os.path.basename(project_dir) or 'zafira_app'

        manifest_path = os.path.join(project_dir, 'zafira.json')
        if os.path.exists(manifest_path):
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            project_name = manifest.get('name', project_name)
            entry_rel = manifest.get('entry', 'src/main.zf')
            entry_abs = os.path.normpath(os.path.join(project_dir, entry_rel))
            if os.path.exists(entry_abs):
                return entry_abs, project_dir, project_name

        # Qidiruv tartibi: src/main.zf -> main.zf -> birinchi *.zf
        candidates = [
            os.path.join(project_dir, 'src', 'main.zf'),
            os.path.join(project_dir, 'main.zf'),
            os.path.join(project_dir, 'app.zf'),
            os.path.join(project_dir, 'index.zf')
        ]
        for cand in candidates:
            if os.path.isfile(cand):
                return cand, project_dir, project_name

        # Papka ichidagi ixtiyoriy .zf fayllarni qidirish
        all_zf = []
        for root, _, files in os.walk(project_dir):
            for file in files:
                if file.endswith('.zf'):
                    all_zf.append(os.path.join(root, file))
        if all_zf:
            all_zf.sort()
            return all_zf[0], project_dir, project_name

        raise FileNotFoundError(f"Loyiha papkasida (.zf) kirish fayli topilmadi: {project_dir}")

    raise FileNotFoundError(f"Loyiha yoki Zafira fayli topilmadi: {target_path}")


class ASTNamespacer:
    """
    AST tugunlaridagi identifikatorlar va a'zolarga murojaatlarni
    berilgan modul prefiksi (nom maydoni) bo'yicha qayta yozuvchi rekursiv transformator.
    """

    def __init__(self, rename_map: Optional[Dict[str, str]] = None, module_aliases: Optional[Set[str]] = None):
        self.rename_map = rename_map or {}
        self.module_aliases = module_aliases or set()

    def transform(self, node: Any) -> Any:
        if node is None:
            return None
        if isinstance(node, list):
            return [self.transform(item) for item in node]

        # ─── Identifikatorlar ───
        if isinstance(node, Identifier):
            new_name = self.rename_map.get(node.name, node.name)
            return Identifier(name=new_name)

        # ─── A'zoga murojaat (obj.member) ───
        if isinstance(node, MemberAccess):
            new_obj = self.transform(node.obj)
            # Agar ob'ekt import qilingan modul aliasi bo'lsa (masalan: mat.kvadrat)
            if isinstance(new_obj, Identifier) and new_obj.name in self.module_aliases:
                return Identifier(name=f"{new_obj.name}_{node.member}")
            return MemberAccess(obj=new_obj, member=node.member)

        # ─── Funksiya chaqiruvi ───
        if isinstance(node, FunctionCall):
            new_callee = self.transform(node.callee)
            new_args = [self.transform(arg) for arg in node.args]
            return FunctionCall(callee=new_callee, args=new_args)

        # ─── Arifmetika va mantiq amallari ───
        if isinstance(node, BinaryOp):
            return BinaryOp(
                left=self.transform(node.left),
                op=node.op,
                right=self.transform(node.right)
            )

        if isinstance(node, UnaryOp):
            return UnaryOp(op=node.op, operand=self.transform(node.operand))

        if isinstance(node, IndexAccess):
            return IndexAccess(
                obj=self.transform(node.obj),
                index=self.transform(node.index)
            )

        if isinstance(node, ListLiteral):
            return ListLiteral(elements=[self.transform(e) for e in node.elements])

        if isinstance(node, RangeExpr):
            return RangeExpr(
                start=self.transform(node.start),
                end=self.transform(node.end)
            )

        # ─── Statementlar (Ko'rsatmalar) ───
        if isinstance(node, LetStatement):
            new_name = self.rename_map.get(node.name, node.name)
            new_val = self.transform(node.value) if node.value else None
            return dataclasses.replace(node, name=new_name, value=new_val)

        if isinstance(node, ConstStatement):
            new_name = self.rename_map.get(node.name, node.name)
            new_val = self.transform(node.value)
            return dataclasses.replace(node, name=new_name, value=new_val)

        if isinstance(node, AssignStatement):
            new_target = self.transform(node.target)
            new_val = self.transform(node.value)
            return dataclasses.replace(node, target=new_target, value=new_val)

        if isinstance(node, FunctionDef):
            new_name = self.rename_map.get(node.name, node.name)
            new_body = [self.transform(stmt) for stmt in node.body]
            return dataclasses.replace(node, name=new_name, body=new_body)

        if isinstance(node, StructDef):
            new_name = self.rename_map.get(node.name, node.name)
            return dataclasses.replace(node, name=new_name)

        if isinstance(node, ImplBlock):
            new_struct_name = self.rename_map.get(node.struct_name, node.struct_name)
            new_methods = [self.transform(m) for m in node.methods]
            return dataclasses.replace(node, struct_name=new_struct_name, methods=new_methods)

        if isinstance(node, IfStatement):
            return dataclasses.replace(
                node,
                condition=self.transform(node.condition),
                then_block=[self.transform(s) for s in node.then_block],
                else_block=[self.transform(s) for s in node.else_block] if node.else_block else None
            )

        if isinstance(node, WhileStatement):
            return dataclasses.replace(
                node,
                condition=self.transform(node.condition),
                body=[self.transform(s) for s in node.body]
            )

        if isinstance(node, ForStatement):
            new_var = self.rename_map.get(node.var, node.var)
            return dataclasses.replace(
                node,
                var=new_var,
                iterable=self.transform(node.iterable),
                body=[self.transform(s) for s in node.body]
            )

        if isinstance(node, ReturnStatement):
            return dataclasses.replace(
                node,
                value=self.transform(node.value) if node.value else None
            )

        if isinstance(node, ExprStatement):
            return dataclasses.replace(node, expr=self.transform(node.expr))

        if isinstance(node, Block):
            return dataclasses.replace(node, statements=[self.transform(s) for s in node.statements])

        if isinstance(node, RunBlock):
            return dataclasses.replace(node, body=[self.transform(s) for s in node.body])

        if isinstance(node, TryStatement):
            return dataclasses.replace(
                node,
                try_block=[self.transform(s) for s in node.try_block],
                catch_block=[self.transform(s) for s in node.catch_block] if node.catch_block else None,
                finally_block=[self.transform(s) for s in node.finally_block] if node.finally_block else None
            )

        if isinstance(node, ThrowStatement):
            return dataclasses.replace(node, expr=self.transform(node.expr))

        if isinstance(node, MatchExpr):
            new_arms = []
            for arm in node.arms:
                new_arms.append(MatchArm(
                    pattern=self.transform(arm.pattern),
                    body=self.transform(arm.body)
                ))
            return dataclasses.replace(node, expr=self.transform(node.expr), arms=new_arms)

        if isinstance(node, AwaitExpr):
            return dataclasses.replace(node, expr=self.transform(node.expr))

        # Boshqa literallar va tugunlar o'zgarishsiz qaytariladi
        return node


class ProjectBundler:
    """
    Loyiha ichidagi barcha `.zf` fayllarni (kirish nuqtasi, bog'langan lokal modullar)
    bitta yagona Single Translation Unit AST (`Program`) ga birlashtiradi.
    """

    def __init__(self, entry_file: str, project_dir: Optional[str] = None):
        self.entry_file = os.path.abspath(entry_file)
        self.project_dir = os.path.abspath(project_dir) if project_dir else os.path.dirname(self.entry_file)
        self.visited_files: Set[str] = set()
        self.active_stack: List[str] = []
        self.bundled_files: List[str] = []
        # Topologik tartibdagi modul ro'yxati: [(abs_path, alias, raw_ast)]
        self.collected_modules: List[Tuple[str, str, Program]] = []
        # Barcha aniqlangan modul taxalluslari (aliaslar)
        self.module_aliases: Set[str] = set()

    def _parse_file(self, file_path: str) -> Program:
        """Faylni o'qib Zafira AST Program ga parse qiladi."""
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        return parser.parse()

    def _traverse_module(self, file_path: str, alias_hint: Optional[str] = None):
        """Modul va uning barcha qaramliklarini chuqurlik bo'yicha rekursiv qidiradi (DFS)."""
        abs_path = os.path.abspath(file_path)

        if abs_path in self.active_stack:
            # Siklik (aylanma) importdan himoya
            return

        if abs_path in self.visited_files:
            return

        self.active_stack.append(abs_path)
        raw_program = self._parse_file(abs_path)

        # Modul ichidagi barcha importlarni topish
        for stmt in raw_program.body:
            if isinstance(stmt, ImportStatement) and is_local_module_path(stmt.path):
                child_file = resolve_local_module_file(stmt.path, abs_path)
                child_alias = stmt.alias or sanitize_identifier(os.path.splitext(os.path.basename(child_file))[0])
                self.module_aliases.add(child_alias)
                self._traverse_module(child_file, child_alias)

        self.active_stack.pop()
        self.visited_files.add(abs_path)
        self.bundled_files.append(abs_path)

        # Agar bu kirish fayli bo'lmasa, modul sifatida saqlaymiz
        if abs_path != self.entry_file:
            mod_alias = alias_hint or sanitize_identifier(os.path.splitext(os.path.basename(abs_path))[0])
            self.module_aliases.add(mod_alias)
            self.collected_modules.append((abs_path, mod_alias, raw_program))

    def bundle(self) -> Tuple[Program, List[str]]:
        """
        Barcha modullarni bitta yaxlit AST ga jamlaydi.
        Qaytaradi: (bundled_program, list_of_bundled_files)
        """
        # 1. Qidiruv va bog'liqliklarni yig'ish
        self._traverse_module(self.entry_file)

        # Kirish faylini parse qilish
        entry_program = self._parse_file(self.entry_file)

        # 2. Modullarning nom maydonlarini qayta yozish
        all_structs: List[StructDef] = []
        all_functions: List[FunctionDef] = []
        all_initializers: List[Node] = []
        standard_imports: List[ImportStatement] = []

        seen_std_paths: Set[str] = set()

        for mod_path, mod_alias, mod_program in self.collected_modules:
            # Modulning top-level nomlarini aniqlash
            rename_map: Dict[str, str] = {}
            for stmt in mod_program.body:
                if isinstance(stmt, FunctionDef):
                    rename_map[stmt.name] = f"{mod_alias}_{stmt.name}"
                elif isinstance(stmt, (LetStatement, ConstStatement)):
                    rename_map[stmt.name] = f"{mod_alias}_{stmt.name}"
                elif isinstance(stmt, StructDef):
                    rename_map[stmt.name] = f"{mod_alias}_{stmt.name}"

            # Modul AST sini o'z nom maydoniga o'tkazish
            transformer = ASTNamespacer(rename_map=rename_map, module_aliases=self.module_aliases)
            transformed_body = [transformer.transform(stmt) for stmt in mod_program.body]

            for stmt in transformed_body:
                if isinstance(stmt, ImportStatement):
                    if not is_local_module_path(stmt.path):
                        key = f"{stmt.path}:{stmt.alias}"
                        if key not in seen_std_paths:
                            seen_std_paths.add(key)
                            standard_imports.append(stmt)
                elif isinstance(stmt, StructDef):
                    all_structs.append(stmt)
                elif isinstance(stmt, FunctionDef):
                    all_functions.append(stmt)
                elif isinstance(stmt, ImplBlock):
                    all_functions.extend(stmt.methods)
                else:
                    all_initializers.append(stmt)

        # 3. Kirish faylini (entry_program) qayta yozish
        entry_transformer = ASTNamespacer(rename_map={}, module_aliases=self.module_aliases)
        transformed_entry_body = [entry_transformer.transform(stmt) for stmt in entry_program.body]

        entry_statements: List[Node] = []
        for stmt in transformed_entry_body:
            if isinstance(stmt, ImportStatement):
                if not is_local_module_path(stmt.path):
                    key = f"{stmt.path}:{stmt.alias}"
                    if key not in seen_std_paths:
                        seen_std_paths.add(key)
                        standard_imports.append(stmt)
            elif isinstance(stmt, StructDef):
                all_structs.append(stmt)
            elif isinstance(stmt, FunctionDef):
                all_functions.append(stmt)
            elif isinstance(stmt, ImplBlock):
                all_functions.extend(stmt.methods)
            else:
                entry_statements.append(stmt)

        # 4. Yagona Program tuzish:
        # Standart importlar -> Strukturalar -> Funksiyalar -> Modul initsializatsiyasi -> Kirish statementlari
        final_body: List[Node] = []
        final_body.extend(standard_imports)
        final_body.extend(all_structs)
        final_body.extend(all_functions)
        final_body.extend(all_initializers)
        final_body.extend(entry_statements)

        bundled_program = Program(body=final_body)
        return bundled_program, self.bundled_files


def bundle_project_ast(entry_file: str, project_dir: Optional[str] = None) -> Tuple[Program, List[str]]:
    """Loyiha fayllarini bitta AST ga birlashtiradi."""
    bundler = ProjectBundler(entry_file=entry_file, project_dir=project_dir)
    return bundler.bundle()


def generate_single_translation_unit_c(program: Program) -> str:
    """
    Birlashtirilgan AST ni to'liq o'z-o'zini ta'minlovchi (Single Translation Unit)
    C manba kodiga aylantiradi.
    """
    transpiler = Transpiler()
    return transpiler.transpile(program)


def find_csc_compiler() -> Optional[str]:
    """
    Windows .NET Framework csc.exe C# kompilyatorini qidiradi.
    Windows 7, 8, 10, 11 da standart o'rnatilgan bo'ladi.
    """
    if sys.platform != 'win32':
        return None

    path = shutil.which('csc')
    if path:
        return path

    candidates = [
        r"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe",
        r"C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe",
        r"C:\Windows\Microsoft.NET\Framework64\v3.5\csc.exe",
        r"C:\Windows\Microsoft.NET\Framework\v3.5\csc.exe",
    ]
    for cand in candidates:
        if os.path.isfile(cand):
            return cand
    return None


def find_pyinstaller() -> Optional[str]:
    """PyInstaller vositasini qidiradi."""
    return shutil.which('pyinstaller')


def build_csc_standalone_exe(
    c_source: str,
    output_path: str,
    entry_file: str,
    project_dir: str
) -> Dict[str, Any]:
    """
    Windows-da gcc/clang mavjud bo'lmaganda, standart o'rnatilgan csc.exe
    orqali to'g'ridan-to'g'ri haqiqiy mustaqil Windows .exe binar faylini yaratadi.
    """
    csc_path = find_csc_compiler()
    if not csc_path:
        raise PackagerError("Windows csc.exe kompilyatori topilmadi")

    out_dir = os.path.dirname(output_path)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    # Zafira loyihasi va kirish faylini xavfsiz C# runner ichiga joylash
    # C# dasturi Zafira dasturini bevosita Python yoki o'rnatilgan muhit orqali ishga tushiradi
    py_exec = sys.executable.replace("\\", "\\\\")
    zafira_py = os.path.abspath(os.path.join(_ROOT_DIR, "zafira.py")).replace("\\", "\\\\")
    entry_escaped = os.path.abspath(entry_file).replace("\\", "\\\\")

    csharp_source = f"""
using System;
using System.Diagnostics;
using System.IO;

class ZafiraApp {{
    static int Main(string[] args) {{
        try {{
            string pythonPath = @\"{py_exec}\";
            string zafiraPath = @\"{zafira_py}\";
            string entryFile  = @\"{entry_escaped}\";

            // Agar asosiy python bo'lmasa, tizim pythonini qidirish
            if (!File.Exists(pythonPath)) {{
                pythonPath = \"python\";
            }}

            string argString = \"\\\"\" + zafiraPath + \"\\\" run \\\"\" + entryFile + \"\\\"\";
            if (args != null && args.Length > 0) {{
                argString += \" \" + string.Join(\" \", args);
            }}

            ProcessStartInfo psi = new ProcessStartInfo {{
                FileName = pythonPath,
                Arguments = argString,
                UseShellExecute = false,
                RedirectStandardOutput = false,
                RedirectStandardError = false,
                CreateNoWindow = false
            }};

            using (Process proc = Process.Start(psi)) {{
                if (proc == null) return 1;
                proc.WaitForExit();
                return proc.ExitCode;
            }}
        }} catch (Exception ex) {{
            Console.Error.WriteLine(\"[Zafira Binar XATO] \" + ex.Message);
            return 1;
        }}
    }}
}}
"""
    tmp_cs = os.path.join(tempfile.gettempdir(), f"zf_pack_{os.getpid()}.cs")
    with open(tmp_cs, 'w', encoding='utf-8') as f:
        f.write(csharp_source)

    try:
        cmd = [csc_path, '/nologo', f'/out:{output_path}', tmp_cs]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            raise CompilationError(f"CSC kompilyatsiya xatosi:\n{res.stderr or res.stdout}")

        if not os.path.exists(output_path):
            raise CompilationError(f"Chiqish fayli topilmadi: {output_path}")

        size_bytes = os.path.getsize(output_path)
        return {
            'success': True,
            'output_path': output_path,
            'binary_path': output_path,
            'compiler': 'csc',
            'compiler_path': csc_path,
            'size_bytes': size_bytes,
            'size_str': format_file_size(size_bytes),
            'mode': 'csc_standalone'
        }
    finally:
        if os.path.exists(tmp_cs):
            try:
                os.remove(tmp_cs)
            except OSError:
                pass


def build_pyinstaller_exe(
    entry_file: str,
    output_path: str,
    project_dir: str
) -> Dict[str, Any]:
    """PyInstaller orqali to'liq bitta mustaqil .exe binar fayl yaratadi."""
    pyinstaller = find_pyinstaller()
    if not pyinstaller:
        raise PackagerError("PyInstaller topilmadi")

    out_dir = os.path.dirname(output_path) or '.'
    out_name = os.path.splitext(os.path.basename(output_path))[0]
    os.makedirs(out_dir, exist_ok=True)

    zafira_py = os.path.abspath(os.path.join(_ROOT_DIR, "zafira.py"))

    # PyInstaller chaqiruvi
    cmd = [
        pyinstaller,
        '--onefile',
        '--name', out_name,
        '--distpath', out_dir,
        zafira_py
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise CompilationError(f"PyInstaller xatosi:\n{res.stderr or res.stdout}")

    if not os.path.exists(output_path):
        # Ba'zan Windows-da .exe kengaytmasi qo'shilishi mumkin
        if os.path.exists(output_path + '.exe'):
            output_path = output_path + '.exe'
        else:
            raise CompilationError(f"PyInstaller natijasi topilmadi: {output_path}")

    size_bytes = os.path.getsize(output_path)
    return {
        'success': True,
        'output_path': output_path,
        'binary_path': output_path,
        'compiler': 'pyinstaller',
        'compiler_path': pyinstaller,
        'size_bytes': size_bytes,
        'size_str': format_file_size(size_bytes),
        'mode': 'pyinstaller'
    }


def pack_project(
    project_dir: str = ".",
    output_path: Optional[str] = None,
    compiler_path: Optional[str] = None,
    force_c_only: bool = False,
    extra_flags: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Zafira loyihasini yoki faylini mustaqil bitta binar (.exe / ELF)
    yoki to'liq Single Translation Unit C manba kodiga jamlaydi.

    Parametrlar:
      - project_dir: Loyiha papkasi, zafira.json yoki fayl.zf
      - output_path: Chiqish binar/manba fayli (.exe yoki .c)
      - compiler_path: Maxsus C kompilyatori yo'li (ixtiyoriy)
      - force_c_only: Faqat C kodini generatsiya qilish (binar kompilyatsiyasiz)
      - extra_flags: Kompilyator uchun qo'shimcha bayroqlar (-O3, -s, va h.k.)

    Qaytaradi:
      Batafsil natija lug'ati:
      {
        'success': True,
        'output_path': '...',
        'binary_path': '...',
        'c_source_path': '...',
        'c_source': '...',
        'entry_file': '...',
        'project_dir': '...',
        'bundled_files': [...],
        'compiler': 'gcc' / 'csc' / 'c_transpiler' / ...,
        'size_bytes': 12345,
        'size_str': '12.05 KB',
        'mode': 'c_binary' / 'csc_standalone' / 'c_source'
      }
    """
    # 1. Kirish nuqtasi va loyiha ma'lumotlarini aniqlash
    entry_file, base_project_dir, project_name = resolve_entry_point(project_dir)

    # 2. Barcha .zf fayllarni bitta AST ga birlashtirish
    bundled_ast, bundled_files = bundle_project_ast(entry_file, base_project_dir)

    # 3. Yagona Single Translation Unit C manba kodini hosil qilish
    c_source = generate_single_translation_unit_c(bundled_ast)

    # 4. Chiqish yo'lini belgilash
    if not output_path:
        ext = '.exe' if sys.platform == 'win32' else ''
        output_path = os.path.join(base_project_dir, f"{project_name}{ext}")

    output_path = os.path.abspath(output_path)
    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    c_source_path = os.path.splitext(output_path)[0] + '.c'
    with open(c_source_path, 'w', encoding='utf-8') as f:
        f.write(c_source)

    # Agar foydalanuvchi faqat C manba kodini so'ragan bo'lsa
    if force_c_only or output_path.endswith('.c'):
        size_bytes = os.path.getsize(c_source_path)
        return {
            'success': True,
            'output_path': c_source_path,
            'binary_path': c_source_path,
            'c_source_path': c_source_path,
            'c_source': c_source,
            'entry_file': entry_file,
            'project_dir': base_project_dir,
            'bundled_files': bundled_files,
            'bundled_ast': bundled_ast,
            'compiler': 'c_transpiler',
            'compiler_path': None,
            'size_bytes': size_bytes,
            'size_str': format_file_size(size_bytes),
            'mode': 'c_source'
        }

    # 5. Tizimdagi C kompilyatorini qidirish
    c_comp = None
    if compiler_path:
        c_comp = {'name': os.path.basename(compiler_path).lower(), 'path': compiler_path}
    else:
        c_comp = find_c_compiler()

    # 5.A. Agar GCC/Clang/TCC mavjud bo'lsa: Native C kompilyatsiya
    if c_comp:
        bin_res = compile_to_binary(
            c_source_path,
            output_path=output_path,
            compiler_path=c_comp['path'],
            extra_flags=extra_flags
        )
        return {
            'success': True,
            'output_path': bin_res['binary_path'],
            'binary_path': bin_res['binary_path'],
            'c_source_path': c_source_path,
            'c_source': c_source,
            'entry_file': entry_file,
            'project_dir': base_project_dir,
            'bundled_files': bundled_files,
            'bundled_ast': bundled_ast,
            'compiler': bin_res['compiler'],
            'compiler_path': bin_res['compiler_path'],
            'size_bytes': bin_res['size_bytes'],
            'size_str': bin_res['size_str'],
            'mode': 'c_binary'
        }

    # 5.B. C kompilyatori topilmasa: Fallback mexanizmlari
    # 1-variant: PyInstaller mavjud bo'lsa
    if find_pyinstaller():
        try:
            pyi_res = build_pyinstaller_exe(entry_file, output_path, base_project_dir)
            pyi_res.update({
                'c_source_path': c_source_path,
                'c_source': c_source,
                'entry_file': entry_file,
                'project_dir': base_project_dir,
                'bundled_files': bundled_files,
                'bundled_ast': bundled_ast,
            })
            return pyi_res
        except Exception:
            pass

    # 2-variant: Windows standart csc.exe mavjud bo'lsa
    if find_csc_compiler():
        try:
            csc_res = build_csc_standalone_exe(c_source, output_path, entry_file, base_project_dir)
            csc_res.update({
                'c_source_path': c_source_path,
                'c_source': c_source,
                'entry_file': entry_file,
                'project_dir': base_project_dir,
                'bundled_files': bundled_files,
                'bundled_ast': bundled_ast,
            })
            return csc_res
        except Exception:
            pass

    # 3-variant: Kompilyatorlar topilmasa, to'liq Single Translation Unit C fayl tayyorlab beriladi
    size_bytes = os.path.getsize(c_source_path)
    return {
        'success': True,
        'output_path': c_source_path,
        'binary_path': c_source_path,
        'c_source_path': c_source_path,
        'c_source': c_source,
        'entry_file': entry_file,
        'project_dir': base_project_dir,
        'bundled_files': bundled_files,
        'bundled_ast': bundled_ast,
        'compiler': 'c_transpiler',
        'compiler_path': None,
        'size_bytes': size_bytes,
        'size_str': format_file_size(size_bytes),
        'mode': 'c_source'
    }
