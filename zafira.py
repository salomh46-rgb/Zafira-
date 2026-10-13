#!/usr/bin/env python3
"""
Zafira Language CLI
Ishlatish:
    python zafira.py run hello.zf       — Faylni bajaradi
    python zafira.py repl               — Interaktiv rejim (REPL)
    python zafira.py tokens hello.zf    — Tokenlarni ko'rsatadi (debug)
    python zafira.py ast hello.zf       — AST ni ko'rsatadi (debug)
    python zafira.py playground         — Veb interaktiv playgroundni ochadi
"""

import sys
import os
import pprint

# Windows terminalida UTF-8 chiqishi uchun
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(__file__))

import subprocess
import shutil
from typing import Optional, List, Dict, Any, Tuple

from src.lexer import Lexer, LexerError
from src.parser import Parser, ParseError
from src.interpreter import Interpreter, ZafiraError
from src.transpiler import Transpiler


from src.package_manager import (
    init_project, run_project, test_project, build_project,
    install_dependencies, add_dependency
)


ZAFIRA_VERSION = "1.0.0"

BANNER = f"""
╔══════════════════════════════════════════════╗
║   🔷  Z A F I R A   L A N G U A G E  🔷     ║
║        v{ZAFIRA_VERSION}  |  Silicon-Native          ║
║   "Qattiq, tiniq, sinmas — xuddi sapfir"     ║
╚══════════════════════════════════════════════╝
"""


def run_file(filepath: str):
    """Zafira faylini o'qib bajaradi"""
    if not os.path.exists(filepath):
        print(f"[Zafira] Fayl topilmadi: {filepath}")
        sys.exit(1)
    if not filepath.endswith('.zf'):
        print(f"[Zafira] Ogohlantirish: Zafira fayllari '.zf' kengaytmasida bo'lishi kerak")

    with open(filepath, encoding='utf-8') as f:
        source = f.read()

    execute_source(source, filepath)


def execute_source(source: str, filename: str = '<stdin>', raise_exceptions: bool = False):
    """Manba kodni bajaradi"""
    try:
        # 1. Tokenizatsiya
        lexer = Lexer(source)
        tokens = lexer.tokenize()

        # 2. Parsing (AST)
        parser = Parser(tokens)
        program = parser.parse()

        curr_file = filename if (filename and filename != '<stdin>') else None
        # 2.5. Type Checking (faqat seal funksiyalar)
        from src.type_checker import TypeChecker, TypeCheckError
        try:
            checker = TypeChecker(current_file=curr_file)
            checker.check(program)
        except TypeCheckError as e:
            if raise_exceptions:
                raise
            print(f"[TYPE XATO] {e}")
            sys.exit(1)

        # 3. Interpretation
        interpreter = Interpreter(current_file=curr_file)
        return interpreter.run(program)

    except LexerError as e:
        if raise_exceptions:
            raise
        print(f"\n[XATO] Lekser Xatosi ({filename}):\n   {e}")
        sys.exit(1)
    except ParseError as e:
        if raise_exceptions:
            raise
        print(f"\n[XATO] Parser Xatosi ({filename}):\n   {e}")
        sys.exit(1)
    except ZafiraError as e:
        if raise_exceptions:
            raise
        print(f"\n[XATO] Ijro Xatosi ({filename}):\n   {e}")
        sys.exit(1)
    except Exception as e:
        if raise_exceptions:
            raise
        print(f"\n[XATO] Ichki Xato ({filename}):\n   {type(e).__name__}: {e}")
        sys.exit(1)


def show_tokens(filepath: str):
    """Tokenlarni chiqaradi (debug uchun)"""
    with open(filepath, encoding='utf-8') as f:
        source = f.read()
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    print(f"\n{'─'*50}")
    print(f"  📋  TOKENLAR: {filepath}")
    print(f"{'─'*50}")
    for tok in tokens:
        print(f"  {tok}")


def show_ast(filepath: str):
    """AST ni chiqaradi (debug uchun)"""
    with open(filepath, encoding='utf-8') as f:
        source = f.read()
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    program = parser.parse()
    print(f"\n{'─'*50}")
    print(f"  🌳  AST DARAXTI: {filepath}")
    print(f"{'─'*50}")
    pprint.pprint(program, width=80)


def repl():
    """Interaktiv REPL (Read-Eval-Print Loop)"""
    print(BANNER)
    print("  Chiqish uchun: exit() yoki Ctrl+C\n")
    interpreter = Interpreter()
    from src.lexer import Lexer
    from src.parser import Parser

    while True:
        try:
            source = input("zf> ").strip()
            if not source:
                continue
            if source in ('exit()', 'quit()', ':q'):
                print("\n  🔷  Zafira dan chiqildi. Xayr!\n")
                break
            try:
                tokens = Lexer(source).tokenize()
                program = Parser(tokens).parse()
                result = interpreter.run(program)
                if result is not None:
                    from src.interpreter import _zf_str
                    print(f"=> {_zf_str(result)}")
            except Exception as e:
                print(f"  🔴 {e}")
        except (KeyboardInterrupt, EOFError):
            print("\n\n  🔷  Zafira dan chiqildi. Xayr!\n")
            break


def transpile_file(filepath: str) -> str:
    """Zafira faylini C kodiga transpile qiladi va konsolga chiqaradi"""
    if not os.path.exists(filepath):
        print(f"[Zafira] Fayl topilmadi: {filepath}")
        sys.exit(1)

    with open(filepath, encoding='utf-8') as f:
        source = f.read()

    try:
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        program = parser.parse()

        transpiler = Transpiler()
        c_code = transpiler.transpile(program)

        c_path = os.path.splitext(filepath)[0] + '.c'
        with open(c_path, 'w', encoding='utf-8') as f:
            f.write(c_code)

        print(c_code)
        print(f"\n[Zafira] C kodi muvaffaqiyatli yaratildi: {c_path}")
        return c_path
    except (LexerError, ParseError) as e:
        print(f"\n[XATO] Transpilyatsiya xatosi ({filepath}):\n   {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[XATO] Ichki Xato ({filepath}):\n   {type(e).__name__}: {e}")
        sys.exit(1)


def compile_file(filepath: str, output_path: Optional[str] = None, standalone: bool = True) -> Optional[str]:
    """
    Zafira faylini C ga transpile qiladi va tizimdagi C kompilyatori yordamida
    mustaqil (.exe / ELF) native binar faylga aylantiradi.
    """
    if not os.path.exists(filepath):
        print(f"[Zafira XATO] Fayl topilmadi: {filepath}")
        sys.exit(1)

    c_path = transpile_file(filepath)
    if not output_path:
        base, _ = os.path.splitext(filepath)
        output_path = base + ('.exe' if sys.platform == 'win32' else '')

    from src.transpiler import compile_to_binary, CompilerNotFoundError, CompilationError

    try:
        res = compile_to_binary(c_path, output_path=output_path)
        print(f"\n[Zafira] Standalone binar dastur muvaffaqiyatli yaratildi! 🚀")
        print(f"  ├── 📁 Binar fayl:    {res['binary_path']}")
        print(f"  ├── ⚙️  Kompilyator:   {res['compiler_path']} ({res['compiler']})")
        print(f"  ├── ⚡ Hajmi:        {res['size_str']} ({res['size_bytes']:,} bayt)")
        print(f"  └── 🏃 Ishga tushir:  {res['binary_path']}")
        return res['binary_path']
    except CompilerNotFoundError as e:
        print(f"\n{e}")
        return None
    except CompilationError as e:
        print(f"\n[Zafira XATO] {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[Zafira XATO] Binar yaratishda kutilmagan xato: {e}")
        sys.exit(1)


def pack_cli(target: str = '.', output_path: Optional[str] = None, force_c_only: bool = False) -> Optional[str]:
    """
    Zafira loyihasi yoki faylini barcha bog'langan lokal modullari bilan bitta
    mustaqil binar (.exe / ELF) yoki Single Translation Unit C manba kodiga paketlaydi.
    """
    from src.packager import pack_project

    try:
        print(f"\n[Zafira Pack] Standalone AOT paketlash boshlandi... 📦")
        res = pack_project(project_dir=target, output_path=output_path, force_c_only=force_c_only)
        print(f"[Zafira Pack] Standalone paket muvaffaqiyatli yaratildi! 🚀")
        print(f"  ├── 📁 Kirish fayli:     {res['entry_file']}")
        print(f"  ├── 🔗 Birlashtirildi:   {len(res['bundled_files'])} ta .zf fayl")
        print(f"  ├── ⚙️  Kompilyator:     {res['compiler']}")
        print(f"  ├── ⚡ Chiqish:          {res['output_path']} ({res['size_str']})")
        if res.get('c_source_path') and res['output_path'] != res['c_source_path']:
            print(f"  ├── 📄 C manba kodi:     {res['c_source_path']}")
        print(f"  └── 🏃 Ishga tushirish:  {res['output_path']}\n")
        return res['output_path']
    except Exception as e:
        print(f"\n[Zafira Pack XATO] {e}")
        sys.exit(1)


def main():
    args = sys.argv[1:]

    if not args:
        print(BANNER)
        print("Foydalanish:")
        print("  python zafira.py init <nomi>          — Yangi loyiha yaratish (ZPM)")
        print("  python zafira.py install [loyiha]     — Qaramliklarni o'rnatish (zafira install)")
        print("  python zafira.py add <paket> [loyiha] — Yangi paket qo'shish (zafira add)")
        print("  python zafira.py run [fayl/loyiha]    — Fayl yoki loyihani bajarish")
        print("  python zafira.py build [loyiha]       — Loyihani transpilyatsiya qilish (C ga)")
        print("  python zafira.py test [loyiha]        — Loyiha testlarini ishga tushirish")
        print("  python zafira.py transpile <fayl.zf>  — C kodiga aylantir (.c)")
        print("  python zafira.py compile <fayl.zf> [-o <chiqish.exe>] [--standalone] — Binar dasturga kompilyatsiya qil (.exe)")
        print("  python zafira.py pack [loyiha/fayl.zf] [-o <chiqish.exe>] — AOT Single-Binary Standalone Packager")
        print("  python zafira.py repl                 — Interaktiv rejim")
        print("  python zafira.py tokens <fayl.zf>     — Tokenlarni ko'rsat")
        print("  python zafira.py ast <fayl.zf>        — AST ni ko'rsat")
        print("  python zafira.py playground [--port]  — Web Interactive Playground (Online Studio)")
        return

    command = args[0]

    if command == 'init':
        if len(args) < 2:
            print("[Zafira] Loyiha nomi ko'rsatilmadi: python zafira.py init <loyiha_nomi>")
            sys.exit(1)
        project_name = args[1]
        target_path = args[2] if len(args) > 2 else '.'
        init_project(project_name, target_path)

    elif command == 'install':
        project_dir = args[1] if len(args) > 1 else '.'
        install_dependencies(project_dir)

    elif command == 'add':
        if len(args) < 2:
            print("[Zafira] Paket nomi yoki manzili ko'rsatilmadi:")
            print("  python zafira.py add <paket> [loyiha]")
            sys.exit(1)
        package_spec = args[1]
        project_dir = args[2] if len(args) > 2 else '.'
        add_dependency(package_spec, project_dir)

    elif command == 'build':
        project_dir = args[1] if len(args) > 1 else '.'
        build_project(project_dir)

    elif command == 'test':
        project_dir = args[1] if len(args) > 1 else '.'
        res = test_project(project_dir)
        if res.get("failed", 0) > 0:
            sys.exit(1)
        sys.exit(0)

    elif command == 'run':
        if len(args) < 2:
            if os.path.exists("zafira.json"):
                run_project(".")
            else:
                print("[Zafira] Fayl nomi yoki loyiha ko'rsatilmagan: python zafira.py run <fayl.zf>")
                sys.exit(1)
        else:
            target = args[1]
            if os.path.isdir(target) or target.endswith('.json'):
                run_project(target)
            else:
                run_file(target)

    elif command == 'transpile':
        if len(args) < 2:
            print("[Zafira] Fayl nomi ko'rsatilmagan: python zafira.py transpile <fayl.zf>")
            sys.exit(1)
        transpile_file(args[1])

    elif command == 'compile':
        compile_args = args[1:]
        if not compile_args:
            print("[Zafira] Fayl nomi ko'rsatilmagan:")
            print("  python zafira.py compile <fayl.zf> [-o <chiqish.exe>] [--standalone / --native]")
            sys.exit(1)

        target_file = None
        output_file = None
        standalone = True

        i = 0
        while i < len(compile_args):
            arg = compile_args[i]
            if arg in ('-o', '--output'):
                if i + 1 < len(compile_args):
                    output_file = compile_args[i + 1]
                    i += 2
                    continue
                else:
                    print("[Zafira XATO] -o parametri uchun chiqish fayli ko'rsatilmadi!")
                    sys.exit(1)
            elif arg.startswith('-o='):
                output_file = arg[3:]
                i += 1
                continue
            elif arg.startswith('--output='):
                output_file = arg[9:]
                i += 1
                continue
            elif arg in ('--standalone', '-s', '--native', '-n'):
                standalone = True
                i += 1
                continue
            elif not target_file and not arg.startswith('-'):
                target_file = arg
                i += 1
                continue
            else:
                i += 1

        if not target_file:
            print("[Zafira] Fayl nomi ko'rsatilmagan:")
            print("  python zafira.py compile <fayl.zf> [-o <chiqish.exe>] [--standalone]")
            sys.exit(1)

        compile_file(target_file, output_path=output_file, standalone=standalone)

    elif command == 'pack':
        pack_args = args[1:]
        target_path = '.'
        output_file = None
        force_c_only = False

        i = 0
        while i < len(pack_args):
            arg = pack_args[i]
            if arg in ('-o', '--output'):
                if i + 1 < len(pack_args):
                    output_file = pack_args[i + 1]
                    i += 2
                    continue
                else:
                    print("[Zafira XATO] -o parametri uchun chiqish fayli ko'rsatilmadi!")
                    sys.exit(1)
            elif arg.startswith('-o='):
                output_file = arg[3:]
                i += 1
                continue
            elif arg.startswith('--output='):
                output_file = arg[9:]
                i += 1
                continue
            elif arg in ('--c-only', '-c'):
                force_c_only = True
                i += 1
                continue
            elif not arg.startswith('-'):
                target_path = arg
                i += 1
                continue
            else:
                i += 1

        pack_cli(target=target_path, output_path=output_file, force_c_only=force_c_only)

    elif command == 'repl':
        repl()

    elif command == 'tokens':
        if len(args) < 2:
            print("[Zafira] Fayl nomi ko'rsatilmagan")
            sys.exit(1)
        show_tokens(args[1])

    elif command == 'ast':
        if len(args) < 2:
            print("[Zafira] Fayl nomi ko'rsatilmagan")
            sys.exit(1)
        show_ast(args[1])

    elif command == 'playground':
        port = 5000
        open_browser = True
        idx = 1
        while idx < len(args):
            arg = args[idx]
            if arg in ('--port', '-p') and idx + 1 < len(args):
                try:
                    port = int(args[idx + 1])
                    idx += 1
                except ValueError:
                    pass
            elif arg.startswith('--port='):
                try:
                    port = int(arg.split('=', 1)[1])
                except ValueError:
                    pass
            elif arg == '--no-browser':
                open_browser = False
            elif arg.isdigit():
                port = int(arg)
            idx += 1

        from src.playground_server import start_playground_server
        start_playground_server(port=port, open_browser=open_browser)

    else:
        print(f"[Zafira] Noma'lum buyruq: '{command}'")
        print("  python zafira.py --help  —  yordam")
        sys.exit(1)


if __name__ == '__main__':
    main()

