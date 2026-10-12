"""
Zafira Package Manager (ZPM) & CLI Suite
Loyiha boshqaruvi: init, run, build, test
"""

import os
import sys
import json
from typing import Dict, Any, Optional

# Loyiha ildiz papkasini sys.path ga qo'shish
_ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _ROOT_DIR not in sys.path:
    sys.path.insert(0, _ROOT_DIR)


def execute_source(source: str, filename: str = '<stdin>', raise_exceptions: bool = False):
    """
    Manba kodni bajaradi.
    zafira.py moduli orqali bajaradi, agar import qilinmasa bevosita lekser/parser/interpreter ni ishlatadi.
    """
    try:
        from zafira import execute_source as zf_exec
        return zf_exec(source, filename=filename, raise_exceptions=raise_exceptions)
    except (ImportError, AttributeError):
        pass

    from src.lexer import Lexer, LexerError
    from src.parser import Parser, ParseError
    from src.interpreter import Interpreter, ZafiraError
    from src.type_checker import TypeChecker, TypeCheckError

    try:
        tokens = Lexer(source).tokenize()
        program = Parser(tokens).parse()

        try:
            checker = TypeChecker()
            checker.check(program)
        except TypeCheckError as e:
            if raise_exceptions:
                raise
            print(f"[TYPE XATO] {e}")
            sys.exit(1)

        interpreter = Interpreter()
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


def init_project(name: str, path: str = ".") -> str:
    """
    Yangi Zafira loyihasini yaratadi.
    - Loyiha uchun papka yaratadi
    - zafira.json manifestini hosil qiladi
    - src/main.zf boshlang'ich faylini yaratadi
    - tests/test_main.zf namuna test faylini yaratadi
    """
    if not name or not name.strip():
        raise ValueError("Loyiha nomi ko'rsatilishi shart")

    name = name.strip()
    norm_path = os.path.normpath(path)

    if os.path.basename(os.path.abspath(norm_path)) == name:
        project_dir = norm_path
    else:
        project_dir = os.path.join(norm_path, name)

    os.makedirs(project_dir, exist_ok=True)
    src_dir = os.path.join(project_dir, "src")
    tests_dir = os.path.join(project_dir, "tests")
    os.makedirs(src_dir, exist_ok=True)
    os.makedirs(tests_dir, exist_ok=True)

    manifest_data = {
        "name": name,
        "version": "0.1.0",
        "author": "Jasper",
        "entry": "src/main.zf",
        "dependencies": {}
    }
    manifest_path = os.path.join(project_dir, "zafira.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2, ensure_ascii=False)

    main_zf_content = f"""// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// {name} - Zafira dasturi 🔷
// Fayl: src/main.zf
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

let xabar = "Salom, Zafira!"
print(xabar)
"""
    main_zf_path = os.path.join(src_dir, "main.zf")
    with open(main_zf_path, "w", encoding="utf-8") as f:
        f.write(main_zf_content)

    test_zf_content = f"""// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// {name} - Namuna Test 🔷
// Fayl: tests/test_main.zf
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

let a = 10
let b = 20
let natija = a + b

if natija == 30 {{
    print("test_main muvaffaqiyatli o'tdi: a + b == 30")
}} else {{
    print("test_main xato!")
    1 / 0
}}
"""
    test_zf_path = os.path.join(tests_dir, "test_main.zf")
    with open(test_zf_path, "w", encoding="utf-8") as f:
        f.write(test_zf_content)

    print(f"[Zafira] Yangi loyiha yaratildi: {project_dir}")
    print(f"  ├── zafira.json")
    print(f"  ├── src/main.zf")
    print(f"  └── tests/test_main.zf")

    return project_dir


def load_manifest(project_dir: str = ".") -> Dict[str, Any]:
    """zafira.json manifest faylini o'qiydi"""
    if os.path.isfile(project_dir) and project_dir.endswith(".json"):
        manifest_path = project_dir
    else:
        manifest_path = os.path.join(project_dir, "zafira.json")

    if not os.path.exists(manifest_path):
        raise FileNotFoundError(f"zafira.json manifest fayli topilmadi: {manifest_path}")

    with open(manifest_path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_project(project_dir: str = ".") -> Any:
    """
    zafira.json ni o'qiydi va belgilangan entry faylni avtomatik execute_source orqali ishga tushiradi.
    """
    if os.path.isfile(project_dir) and project_dir.endswith(".json"):
        base_dir = os.path.dirname(project_dir)
    else:
        base_dir = project_dir

    manifest = load_manifest(base_dir)
    entry_rel = manifest.get("entry", "src/main.zf")
    entry_path = os.path.normpath(os.path.join(base_dir, entry_rel))

    if not os.path.exists(entry_path):
        raise FileNotFoundError(f"Kirish (entry) fayli topilmadi: {entry_path}")

    with open(entry_path, "r", encoding="utf-8") as f:
        source = f.read()

    return execute_source(source, filename=entry_path)


def test_project(project_dir: str = ".") -> Dict[str, Any]:
    """
    tests/*.zf fayllarini topadi va ularni navbatma-navbat bajaradi,
    test natijalarini (PASSED/FAILED) hisoblaydi.
    """
    if os.path.isfile(project_dir) and project_dir.endswith(".json"):
        base_dir = os.path.dirname(project_dir)
    else:
        base_dir = project_dir

    tests_dir = os.path.join(base_dir, "tests")
    if not os.path.isdir(tests_dir):
        print(f"[Zafira Test] 'tests/' papkasi topilmadi: {tests_dir}")
        return {"total": 0, "passed": 0, "failed": 0, "results": {}}

    test_files = [
        os.path.join(tests_dir, f)
        for f in os.listdir(tests_dir)
        if f.endswith(".zf") and os.path.isfile(os.path.join(tests_dir, f))
    ]
    test_files.sort()

    total = len(test_files)
    if total == 0:
        print(f"[Zafira Test] Sinov fayllari (*.zf) topilmadi: {tests_dir}")
        return {"total": 0, "passed": 0, "failed": 0, "results": {}}

    passed = 0
    failed = 0
    results: Dict[str, str] = {}

    print(f"\n[Zafira Test] Jami {total} ta test topildi ({tests_dir}). Ishga tushirilmoqda...")

    for t_path in test_files:
        test_name = os.path.basename(t_path)
        try:
            with open(t_path, "r", encoding="utf-8") as f:
                source = f.read()
            execute_source(source, filename=t_path, raise_exceptions=True)
            passed += 1
            results[test_name] = "PASSED"
            print(f"  ✅ [PASSED] {test_name}")
        except (Exception, SystemExit) as e:
            failed += 1
            results[test_name] = f"FAILED: {e}"
            print(f"  ❌ [FAILED] {test_name} -> {e}")

    print(f"\n{'─'*50}")
    print(f"  🧪 Zafira Test Natijalari: Jami: {total} | O'tdi: {passed} | Yiqildi: {failed}")
    print(f"{'─'*50}\n")

    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "results": results,
    }


def build_project(project_dir: str = ".") -> str:
    """
    zafira.json ni o'qiydi va entry faylni C kodiga transpile qiladi.
    """
    if os.path.isfile(project_dir) and project_dir.endswith(".json"):
        base_dir = os.path.dirname(project_dir)
    else:
        base_dir = project_dir

    manifest = load_manifest(base_dir)
    entry_rel = manifest.get("entry", "src/main.zf")
    entry_path = os.path.normpath(os.path.join(base_dir, entry_rel))

    if not os.path.exists(entry_path):
        raise FileNotFoundError(f"Kirish (entry) fayli topilmadi: {entry_path}")

    from zafira import transpile_file
    c_path = transpile_file(entry_path)
    return c_path
