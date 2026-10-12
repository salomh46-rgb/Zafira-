"""
Zafira Package Manager (ZPM) & CLI Suite
Loyiha boshqaruvi: init, run, build, test
"""

import os
import sys
import json
import shutil
import hashlib
import datetime
import subprocess
from typing import Dict, Any, Optional, Tuple

# Windows terminalida UTF-8 chiqishi uchun
if sys.platform == 'win32':
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

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

    curr_file = filename if (filename and filename != '<stdin>') else None

    try:
        tokens = Lexer(source).tokenize()
        program = Parser(tokens).parse()

        try:
            checker = TypeChecker(current_file=curr_file)
            checker.check(program)
        except TypeCheckError as e:
            if raise_exceptions:
                raise
            print(f"[TYPE XATO] {e}")
            sys.exit(1)

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


def compute_package_hash(pkg_dir: str) -> str:
    """
    Papka ichidagi barcha fayllarning deterministik SHA-256 xeshini hisoblaydi.
    """
    hasher = hashlib.sha256()
    if not os.path.exists(pkg_dir):
        return "sha256:empty"

    file_entries = []
    for root, _, files in os.walk(pkg_dir):
        for f in files:
            full = os.path.join(root, f)
            rel = os.path.relpath(full, pkg_dir).replace('\\', '/')
            file_entries.append((rel, full))
    file_entries.sort(key=lambda x: x[0])
    for rel, full in file_entries:
        hasher.update(rel.encode('utf-8'))
        try:
            with open(full, 'rb') as fp:
                while chunk := fp.read(65536):
                    hasher.update(chunk)
        except OSError:
            pass
    return f"sha256:{hasher.hexdigest()}"


def parse_git_source(source_str: str) -> Tuple[str, Optional[str]]:
    """
    Git manba manzilini tahlil qiladi (shorthand, branch/tag, git+ prefix).
    Masalan:
      salomh46-rgb/zafira-utils -> https://github.com/salomh46-rgb/zafira-utils.git
      salomh46-rgb/zafira-utils@v1.0.0 -> (https://github.com/salomh46-rgb/zafira-utils.git, 'v1.0.0')
      https://github.com/user/repo.git#main -> (https://github.com/user/repo.git, 'main')
    """
    s = source_str.strip()
    if s.startswith('git+'):
        s = s[4:]
    branch_or_tag = None
    if '#' in s:
        s, branch_or_tag = s.split('#', 1)
    elif '@' in s and not s.startswith('git@'):
        s, branch_or_tag = s.split('@', 1)

    if not s.startswith(('http://', 'https://', 'git@', 'ssh://')):
        # GitHub shorthand e.g. 'owner/repo'
        git_url = f"https://github.com/{s}.git"
    else:
        git_url = s
        if 'github.com' in git_url and not git_url.endswith('.git') and not git_url.endswith('/'):
            git_url = git_url + '.git'

    return git_url, branch_or_tag


def install_dependencies(project_dir: str = ".", force: bool = False) -> Dict[str, Any]:
    """
    zafira.json dagi qaramliklarni o'qiydi va zafira_modules/<pkg_name> papkasiga o'rnatadi.
    zafira.lock faylini yaratadi yoki yangilaydi (versiya va sha256 yaxlitlik qulflari bilan).
    """
    if os.path.isfile(project_dir) and project_dir.endswith(".json"):
        base_dir = os.path.dirname(os.path.abspath(project_dir))
        manifest_path = project_dir
    else:
        base_dir = os.path.abspath(project_dir)
        manifest_path = os.path.join(base_dir, "zafira.json")

    if not os.path.exists(manifest_path):
        raise FileNotFoundError(f"zafira.json manifest fayli topilmadi: {manifest_path}")

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    dependencies = manifest.get("dependencies", {})
    if not isinstance(dependencies, dict):
        dependencies = {}

    modules_dir = os.path.join(base_dir, "zafira_modules")
    os.makedirs(modules_dir, exist_ok=True)

    lock_file = os.path.join(base_dir, "zafira.lock")
    lock_data = {
        "lockfile_version": 1,
        "zafira_version": "0.8.0-alpha",
        "packages": {}
    }
    if os.path.isfile(lock_file):
        try:
            with open(lock_file, "r", encoding="utf-8") as f:
                existing_lock = json.load(f)
                if isinstance(existing_lock, dict):
                    lock_data.update(existing_lock)
                    if "packages" not in lock_data or not isinstance(lock_data["packages"], dict):
                        lock_data["packages"] = {}
        except Exception:
            pass

    if not dependencies:
        print(f"[ZPM] Loyihada qaramliklar (dependencies) ko'rsatilmagan ({manifest_path}).")
        with open(lock_file, "w", encoding="utf-8") as f:
            json.dump(lock_data, f, indent=2, ensure_ascii=False)
        return lock_data

    print(f"\n[ZPM] Qaramliklar o'rnatilmoqda ({len(dependencies)} ta paket)...")

    for pkg_name, source_spec in dependencies.items():
        dest_dir = os.path.join(modules_dir, pkg_name)
        resolved_source = ""
        source_str = str(source_spec).strip()

        # 1. Lokal yo'l tekshiruvi
        cand_rel_base = os.path.normpath(os.path.join(base_dir, source_str))
        cand_rel_cwd = os.path.normpath(os.path.join(os.getcwd(), source_str))
        is_local = (
            source_str.startswith(('./', '../', '.\\', '..\\', '/', '\\'))
            or (len(source_str) > 2 and source_str[1] == ':' and source_str[2] in ('\\', '/'))
            or os.path.exists(cand_rel_base)
            or os.path.exists(cand_rel_cwd)
            or os.path.exists(source_str)
        )

        if is_local:
            if os.path.exists(cand_rel_base):
                local_source = cand_rel_base
            elif os.path.exists(cand_rel_cwd):
                local_source = cand_rel_cwd
            elif os.path.exists(source_str):
                local_source = os.path.abspath(source_str)
            else:
                raise FileNotFoundError(f"[ZPM XATO] Lokal paket yo'li topilmadi: '{source_str}' (paket: {pkg_name})")

            resolved_source = os.path.abspath(local_source)

            if os.path.isdir(local_source):
                if os.path.exists(dest_dir):
                    shutil.rmtree(dest_dir, ignore_errors=True)
                shutil.copytree(
                    local_source,
                    dest_dir,
                    ignore=shutil.ignore_patterns('.git', '__pycache__', 'zafira_modules', '*.pyc', '.pytest_cache')
                )
            elif os.path.isfile(local_source):
                if local_source.endswith('.zip'):
                    import zipfile
                    if os.path.exists(dest_dir):
                        shutil.rmtree(dest_dir, ignore_errors=True)
                    os.makedirs(dest_dir, exist_ok=True)
                    with zipfile.ZipFile(local_source, 'r') as zf:
                        zf.extractall(dest_dir)
                else:
                    if os.path.exists(dest_dir):
                        shutil.rmtree(dest_dir, ignore_errors=True)
                    os.makedirs(dest_dir, exist_ok=True)
                    shutil.copy2(local_source, os.path.join(dest_dir, "index.zf"))

        elif (
            source_str.startswith(('http://', 'https://'))
            and any(source_str.endswith(ext) for ext in ('.zip', '.tar.gz', '.tgz'))
        ):
            # Remote archive (.zip / .tar.gz)
            resolved_source = source_str
            if force or not os.path.exists(dest_dir) or not os.listdir(dest_dir):
                import urllib.request
                import zipfile
                import tarfile
                import tempfile

                if os.path.exists(dest_dir):
                    shutil.rmtree(dest_dir, ignore_errors=True)
                os.makedirs(dest_dir, exist_ok=True)

                req = urllib.request.Request(source_str, headers={'User-Agent': 'ZafiraPackageManager/0.8.0'})
                with tempfile.NamedTemporaryFile(delete=False) as tmp:
                    with urllib.request.urlopen(req, timeout=30) as resp:
                        shutil.copyfileobj(resp, tmp)
                    archive_tmp = tmp.name
                try:
                    if source_str.endswith('.zip'):
                        with zipfile.ZipFile(archive_tmp, 'r') as zf:
                            zf.extractall(dest_dir)
                    else:
                        with tarfile.open(archive_tmp, 'r:*') as tf:
                            tf.extractall(dest_dir)
                finally:
                    if os.path.exists(archive_tmp):
                        os.remove(archive_tmp)

        else:
            # Git repository yoki shorthand (user/repo)
            git_url, branch_tag = parse_git_source(source_str)
            resolved_source = git_url

            if not force and os.path.exists(dest_dir) and os.listdir(dest_dir):
                pass
            else:
                if os.path.exists(dest_dir):
                    shutil.rmtree(dest_dir, ignore_errors=True)
                os.makedirs(os.path.dirname(dest_dir), exist_ok=True)

                cmd = ["git", "clone", "--depth", "1"]
                if branch_tag:
                    cmd.extend(["--branch", branch_tag])
                cmd.extend([git_url, dest_dir])

                try:
                    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
                    if proc.returncode != 0:
                        raise RuntimeError(f"Git clone xatosi ({git_url}): {proc.stderr.strip() or proc.stdout.strip()}")
                except FileNotFoundError:
                    raise RuntimeError("Git dasturi tizimda topilmadi (PATH ga qo'shilmagan).")

                git_meta = os.path.join(dest_dir, ".git")
                if os.path.exists(git_meta):
                    shutil.rmtree(git_meta, ignore_errors=True)

        # Versiyani aniqlash
        pkg_version = "0.1.0"
        pkg_manifest = os.path.join(dest_dir, "zafira.json")
        if os.path.isfile(pkg_manifest):
            try:
                with open(pkg_manifest, "r", encoding="utf-8") as f:
                    m_data = json.load(f)
                    if "version" in m_data:
                        pkg_version = str(m_data["version"])
            except Exception:
                pass

        # SHA-256 xesh qulfi
        integrity_hash = compute_package_hash(dest_dir)

        lock_data["packages"][pkg_name] = {
            "version": pkg_version,
            "source": source_str,
            "resolved": resolved_source,
            "integrity": integrity_hash,
            "installed_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        print(f"  📦 [ZPM] '{pkg_name}' (v{pkg_version}) o'rnatildi -> zafira_modules/{pkg_name}")

    with open(lock_file, "w", encoding="utf-8") as f:
        json.dump(lock_data, f, indent=2, ensure_ascii=False)

    print(f"\n[ZPM] Muvaffaqiyatli yakunlandi! zafira.lock saqlandi.")
    return lock_data


def add_dependency(package_spec: str, project_dir: str = ".") -> Dict[str, Any]:
    """
    zafira.json manifestiga yangi qaramlikni qo'shadi va avtomatik ravishda install_dependencies ni chaqiradi.
    Misollar:
      add_dependency("salomh46-rgb/zafira-utils", project_dir)
      add_dependency("./lokal_lib", project_dir)
      add_dependency("my_utils=./lokal_lib", project_dir)
    """
    if os.path.isfile(project_dir) and project_dir.endswith(".json"):
        base_dir = os.path.dirname(os.path.abspath(project_dir))
        manifest_path = project_dir
    else:
        base_dir = os.path.abspath(project_dir)
        manifest_path = os.path.join(base_dir, "zafira.json")

    if not os.path.exists(manifest_path):
        raise FileNotFoundError(f"zafira.json manifest fayli topilmadi: {manifest_path}. Avval 'zafira init' buyrug'ini bajaring.")

    spec = package_spec.strip()
    if not spec:
        raise ValueError("Paket nomi yoki manzili ko'rsatilishi shart")

    if '=' in spec and not spec.startswith(('http://', 'https://', 'git@')):
        pkg_name, source_value = spec.split('=', 1)
        pkg_name = pkg_name.strip()
        source_value = source_value.strip()
    else:
        source_value = spec
        cand_local_base = os.path.normpath(os.path.join(base_dir, source_value))
        cand_local_cwd = os.path.normpath(os.path.join(os.getcwd(), source_value))

        if (
            source_value.startswith(('./', '../', '.\\', '..\\', '/', '\\'))
            or (len(source_value) > 2 and source_value[1] == ':' and source_value[2] in ('\\', '/'))
            or os.path.exists(cand_local_base)
            or os.path.exists(cand_local_cwd)
        ):
            local_target = cand_local_base if os.path.exists(cand_local_base) else cand_local_cwd
            pkg_name = None
            cand_m = os.path.join(local_target, "zafira.json")
            if os.path.isfile(cand_m):
                try:
                    with open(cand_m, "r", encoding="utf-8") as f:
                        pkg_name = json.load(f).get("name")
                except Exception:
                    pass
            if not pkg_name:
                base = os.path.basename(os.path.normpath(source_value))
                if base.endswith('.zf'):
                    base = base[:-3]
                pkg_name = base
        elif '/' in source_value:
            val = source_value
            if '#' in val:
                val = val.split('#', 1)[0]
            if '@' in val and not val.startswith('git@'):
                val = val.split('@', 1)[0]
            val = val.rstrip('/')
            if val.endswith('.git'):
                val = val[:-4]
            pkg_name = val.split('/')[-1]
        else:
            pkg_name = source_value

    pkg_name = pkg_name.strip()
    if not pkg_name:
        raise ValueError("Paket nomini aniqlab bo'lmadi")

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    if "dependencies" not in manifest or not isinstance(manifest["dependencies"], dict):
        manifest["dependencies"] = {}

    manifest["dependencies"][pkg_name] = source_value

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"[ZPM] '{pkg_name}': '{source_value}' zafira.json manifestiga qo'shildi.")

    lock_data = install_dependencies(base_dir)
    return {
        "name": pkg_name,
        "source": source_value,
        "lock": lock_data
    }
