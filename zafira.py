#!/usr/bin/env python3
"""
Zafira Language CLI
Ishlatish:
    python zafira.py run hello.zf       — Faylni bajaradi
    python zafira.py repl               — Interaktiv rejim (REPL)
    python zafira.py tokens hello.zf    — Tokenlarni ko'rsatadi (debug)
    python zafira.py ast hello.zf       — AST ni ko'rsatadi (debug)
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

from src.lexer import Lexer, LexerError
from src.parser import Parser, ParseError
from src.interpreter import Interpreter, ZafiraError
from src.transpiler import Transpiler


ZAFIRA_VERSION = "0.1.0-alpha"

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


def execute_source(source: str, filename: str = '<stdin>'):
    """Manba kodni bajaradi"""
    try:
        # 1. Tokenizatsiya
        lexer = Lexer(source)
        tokens = lexer.tokenize()

        # 2. Parsing (AST)
        parser = Parser(tokens)
        program = parser.parse()

        # 2.5. Type Checking (faqat seal funksiyalar)
        from src.type_checker import TypeChecker, TypeCheckError
        try:
            checker = TypeChecker()
            checker.check(program)
        except TypeCheckError as e:
            print(f"[TYPE XATO] {e}")
            sys.exit(1)

        # 3. Interpretation
        interpreter = Interpreter()
        interpreter.run(program)

    except LexerError as e:
        print(f"\n[XATO] Lekser Xatosi ({filename}):\n   {e}")
        sys.exit(1)
    except ParseError as e:
        print(f"\n[XATO] Parser Xatosi ({filename}):\n   {e}")
        sys.exit(1)
    except ZafiraError as e:
        print(f"\n[XATO] Ijro Xatosi ({filename}):\n   {e}")
        sys.exit(1)
    except Exception as e:
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


def compile_file(filepath: str):
    """Zafira faylini C ga transpile qiladi va gcc yordamida binar fayl (.exe) yaratadi"""
    c_path = transpile_file(filepath)
    exe_name = os.path.splitext(filepath)[0] + ('.exe' if sys.platform == 'win32' else '')

    gcc_bin = shutil.which('gcc') or shutil.which('clang')
    if not gcc_bin:
        print(f"\n[Zafira Ogohlantirish] 'gcc' yoki 'clang' kompyilyatori tizimda topilmadi.")
        print(f"[Zafira] C kodi tayyor: {c_path}")
        print(f"[Zafira] Qo'lda kompilyatsiya qilish: gcc {c_path} -o {exe_name} -lm")
        return

    print(f"\n[Zafira] Kompilyator: {gcc_bin}")
    print(f"[Zafira] Kompilyatsiya qilinmoqda: {c_path} -> {exe_name} ...")
    cmd = [gcc_bin, c_path, '-o', exe_name, '-lm']
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"[Zafira XATO] Kompilyatsiya xatosi:\n{res.stderr}")
        sys.exit(1)

    print(f"[Zafira] Muvaffaqiyatli kompilyatsiya qilindi: {exe_name}")


def main():
    args = sys.argv[1:]

    if not args:
        print(BANNER)
        print("Foydalanish:")
        print("  python zafira.py run <fayl.zf>        — Faylni bajar")
        print("  python zafira.py transpile <fayl.zf>  — C kodiga aylantir (.c)")
        print("  python zafira.py compile <fayl.zf>    — Binar dasturga kompilyatsiya qil (.exe)")
        print("  python zafira.py repl                 — Interaktiv rejim")
        print("  python zafira.py tokens <fayl.zf>     — Tokenlarni ko'rsat")
        print("  python zafira.py ast <fayl.zf>        — AST ni ko'rsat")
        return

    command = args[0]

    if command == 'run':
        if len(args) < 2:
            print("[Zafira] Fayl nomi ko'rsatilmagan: python zafira.py run <fayl.zf>")
            sys.exit(1)
        run_file(args[1])

    elif command == 'transpile':
        if len(args) < 2:
            print("[Zafira] Fayl nomi ko'rsatilmagan: python zafira.py transpile <fayl.zf>")
            sys.exit(1)
        transpile_file(args[1])

    elif command == 'compile':
        if len(args) < 2:
            print("[Zafira] Fayl nomi ko'rsatilmagan: python zafira.py compile <fayl.zf>")
            sys.exit(1)
        compile_file(args[1])

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

    else:
        print(f"[Zafira] Noma'lum buyruq: '{command}'")
        print("  python zafira.py --help  —  yordam")
        sys.exit(1)


if __name__ == '__main__':
    main()

