"""
Zafira Language - ZPM Remote Dependency & Package Manager Unit Testlari
tests/test_zpm_remote.py

Tekshiriladigan funksionalliklar:
1. parse_git_source va compute_package_hash yordamchi funksiyalari
2. install_dependencies (lokal papka, arxiv, git mock, lockfile sha256 yaxlitligi)
3. add_dependency (zafira.json ga yozish va avtomatik o'rnatish)
4. src/interpreter.py modul qidirish tartibi:
   - Lokal fayl ustunligi (precedence)
   - zafira_modules/<pkg_name>/src/main.zf
   - zafira_modules/<pkg_name>/index.zf
   - zafira_modules/<pkg_name>/zafira.json (manifest 'entry')
   - import "pkg" as alias
5. CLI integratsiyasi: `zafira install` va `zafira add`
"""

import os
import sys
import json
import shutil
import tempfile
import unittest
import subprocess

if sys.platform == 'win32':
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
from io import StringIO
from unittest.mock import patch, MagicMock

# Loyiha ildiz papkasini sys.path ga qo'shish
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.package_manager import (
    init_project,
    run_project,
    load_manifest,
    execute_source,
    install_dependencies,
    add_dependency,
    compute_package_hash,
    parse_git_source,
)
from src.interpreter import Interpreter, ZafiraError


class TestZPMRemoteUtils(unittest.TestCase):
    """Git URL va Xesh yordamchi funksiyalari testlari"""

    def test_parse_git_source_shorthand(self):
        url, branch = parse_git_source("salomh46-rgb/zafira-utils")
        self.assertEqual(url, "https://github.com/salomh46-rgb/zafira-utils.git")
        self.assertIsNone(branch)

    def test_parse_git_source_tag(self):
        url, branch = parse_git_source("salomh46-rgb/zafira-utils@v1.2.0")
        self.assertEqual(url, "https://github.com/salomh46-rgb/zafira-utils.git")
        self.assertEqual(branch, "v1.2.0")

    def test_parse_git_source_branch_hash(self):
        url, branch = parse_git_source("https://github.com/jasper/core.git#main")
        self.assertEqual(url, "https://github.com/jasper/core.git")
        self.assertEqual(branch, "main")

    def test_parse_git_source_git_prefix(self):
        url, branch = parse_git_source("git+https://gitlab.com/team/tools.git")
        self.assertEqual(url, "https://gitlab.com/team/tools.git")
        self.assertIsNone(branch)

    def test_compute_package_hash_deterministic(self):
        temp_d = tempfile.mkdtemp(prefix="zf_hash_test_")
        try:
            f1 = os.path.join(temp_d, "a.zf")
            with open(f1, "w", encoding="utf-8") as f:
                f.write("let x = 10\n")

            hash1 = compute_package_hash(temp_d)
            hash2 = compute_package_hash(temp_d)
            self.assertEqual(hash1, hash2)
            self.assertTrue(hash1.startswith("sha256:"))

            # Fayl mazmuni o'zgarganda xesh o'zgarishi kerak
            with open(f1, "w", encoding="utf-8") as f:
                f.write("let x = 999\n")
            hash3 = compute_package_hash(temp_d)
            self.assertNotEqual(hash1, hash3)
        finally:
            shutil.rmtree(temp_d, ignore_errors=True)


class TestZPMInstallAndAdd(unittest.TestCase):
    """install_dependencies va add_dependency funksiyalari testlari"""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="zf_zpm_test_")
        self.app_dir = os.path.join(self.test_dir, "my_app")
        init_project("my_app", self.test_dir)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_install_local_folder_dependency(self):
        """Lokal papkani dependencies ga qo'shib o'rnatish va zafira.lock hosil bo'lishi"""
        # 1. Lokal paket yaratamiz
        lib_dir = os.path.join(self.test_dir, "zafira_math")
        os.makedirs(os.path.join(lib_dir, "src"), exist_ok=True)

        lib_manifest = {
            "name": "zafira_math",
            "version": "1.0.5",
            "entry": "src/main.zf"
        }
        with open(os.path.join(lib_dir, "zafira.json"), "w", encoding="utf-8") as f:
            json.dump(lib_manifest, f)

        lib_code = """
fn qosh(a, b) {
    return a + b
}
fn kopaytir(a, b) {
    return a * b
}
"""
        with open(os.path.join(lib_dir, "src", "main.zf"), "w", encoding="utf-8") as f:
            f.write(lib_code)

        # 2. my_app manifestiga dependency kiritamiz
        manifest_path = os.path.join(self.app_dir, "zafira.json")
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        manifest["dependencies"]["zafira_math"] = "../zafira_math"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f)

        # 3. install_dependencies ni chaqiramiz
        lock_data = install_dependencies(self.app_dir)

        # 4. zafira_modules/<pkg_name> mavjudligini tekshiramiz
        installed_entry = os.path.join(self.app_dir, "zafira_modules", "zafira_math", "src", "main.zf")
        self.assertTrue(os.path.isfile(installed_entry), "O'rnatilgan paket fayli topilmadi")

        # 5. zafira.lock mavjudligi va tarkibini tekshiramiz
        lock_file = os.path.join(self.app_dir, "zafira.lock")
        self.assertTrue(os.path.isfile(lock_file), "zafira.lock fayli yaratilmadi")

        self.assertIn("zafira_math", lock_data["packages"])
        pkg_lock = lock_data["packages"]["zafira_math"]
        self.assertEqual(pkg_lock["version"], "1.0.5")
        self.assertTrue(pkg_lock["integrity"].startswith("sha256:"))
        self.assertEqual(pkg_lock["source"], "../zafira_math")

    def test_add_dependency_local_command(self):
        """add_dependency buyrug'i manifestni yangilab, o'rnatishni amalga oshirishi"""
        lib_dir = os.path.join(self.test_dir, "salom_lib")
        os.makedirs(lib_dir, exist_ok=True)
        with open(os.path.join(lib_dir, "index.zf"), "w", encoding="utf-8") as f:
            f.write('fn xushkelibsiz() { return "Xush kelibsiz!" }\n')

        res = add_dependency("../salom_lib", self.app_dir)
        self.assertEqual(res["name"], "salom_lib")

        # Manifest tekshiruvi
        manifest = load_manifest(self.app_dir)
        self.assertIn("salom_lib", manifest["dependencies"])
        self.assertEqual(manifest["dependencies"]["salom_lib"], "../salom_lib")

        # zafira_modules tekshiruvi
        installed_file = os.path.join(self.app_dir, "zafira_modules", "salom_lib", "index.zf")
        self.assertTrue(os.path.isfile(installed_file))

        # zafira.lock tekshiruvi
        self.assertTrue(os.path.isfile(os.path.join(self.app_dir, "zafira.lock")))

    def test_add_dependency_with_custom_name(self):
        """pkg_name=path formatida nom berib qo'shish"""
        lib_dir = os.path.join(self.test_dir, "alohida_lib")
        os.makedirs(lib_dir, exist_ok=True)
        with open(os.path.join(lib_dir, "index.zf"), "w", encoding="utf-8") as f:
            f.write('fn test() { return 123 }\n')

        res = add_dependency("maxsus_nom=../alohida_lib", self.app_dir)
        self.assertEqual(res["name"], "maxsus_nom")

        manifest = load_manifest(self.app_dir)
        self.assertIn("maxsus_nom", manifest["dependencies"])
        self.assertTrue(os.path.isdir(os.path.join(self.app_dir, "zafira_modules", "maxsus_nom")))

    def test_install_git_dependency_with_mock(self):
        """Git clone orqali masofaviy repozitoriy o'rnatilishi (mock subprocess)"""
        manifest_path = os.path.join(self.app_dir, "zafira.json")
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        manifest["dependencies"]["zafira-remote"] = "salomh46-rgb/zafira-remote"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f)

        def mock_git_clone(cmd, *args, **kwargs):
            # cmd: ["git", "clone", "--depth", "1", "https://github.com/...", dest_dir]
            dest_dir = cmd[-1]
            os.makedirs(os.path.join(dest_dir, "src"), exist_ok=True)
            with open(os.path.join(dest_dir, "zafira.json"), "w", encoding="utf-8") as f:
                json.dump({"name": "zafira-remote", "version": "2.0.0"}, f)
            with open(os.path.join(dest_dir, "src", "main.zf"), "w", encoding="utf-8") as f:
                f.write('fn remote_fn() { return "remote ok" }\n')
            proc = MagicMock()
            proc.returncode = 0
            proc.stdout = "Cloning into..."
            proc.stderr = ""
            return proc

        with patch("subprocess.run", side_effect=mock_git_clone):
            lock_data = install_dependencies(self.app_dir)

        self.assertIn("zafira-remote", lock_data["packages"])
        self.assertEqual(lock_data["packages"]["zafira-remote"]["version"], "2.0.0")
        installed_entry = os.path.join(self.app_dir, "zafira_modules", "zafira-remote", "src", "main.zf")
        self.assertTrue(os.path.isfile(installed_entry))

    def test_install_empty_dependencies(self):
        """Bo'sh qaramliklar ro'yxatida xatosiz lockfile yaratilishi"""
        lock = install_dependencies(self.app_dir)
        self.assertIn("packages", lock)
        self.assertEqual(len(lock["packages"]), 0)


class TestZafiraModulesResolution(unittest.TestCase):
    """Interpreter modul qidirish tartibi va zafira_modules import integratsiyasi testlari"""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="zf_resolve_test_")
        self.app_dir = os.path.join(self.test_dir, "my_app")
        init_project("my_app", self.test_dir)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_import_zafira_modules_src_main(self):
        """zafira_modules/<pkg>/src/main.zf dan import qilinishi va funksiyalari chaqirilishi"""
        pkg_dir = os.path.join(self.app_dir, "zafira_modules", "matematika", "src")
        os.makedirs(pkg_dir, exist_ok=True)
        with open(os.path.join(pkg_dir, "main.zf"), "w", encoding="utf-8") as f:
            f.write("""
fn kvadrat(n) {
    return n * n
}
""")

        code = """
import "matematika"

let res = matematika.kvadrat(7)
print("NATIJA:" + str(res))
"""
        captured = StringIO()
        main_zf = os.path.join(self.app_dir, "src", "main.zf")
        with patch("sys.stdout", captured):
            execute_source(code, filename=main_zf)

        output = captured.getvalue()
        self.assertIn("NATIJA:49", output)

    def test_import_zafira_modules_index(self):
        """zafira_modules/<pkg>/index.zf dan import qilinishi"""
        pkg_dir = os.path.join(self.app_dir, "zafira_modules", "matnlar")
        os.makedirs(pkg_dir, exist_ok=True)
        with open(os.path.join(pkg_dir, "index.zf"), "w", encoding="utf-8") as f:
            f.write("""
fn salom_ber(ism) {
    return "Salom, " + ism + "!"
}
""")

        code = """
import "matnlar"

let xabar = matnlar.salom_ber("Jasper")
print(xabar)
"""
        captured = StringIO()
        main_zf = os.path.join(self.app_dir, "src", "main.zf")
        with patch("sys.stdout", captured):
            execute_source(code, filename=main_zf)

        output = captured.getvalue()
        self.assertIn("Salom, Jasper!", output)

    def test_import_zafira_modules_with_alias(self):
        """import "pkg" as alias sintaksisi ishlashi"""
        pkg_dir = os.path.join(self.app_dir, "zafira_modules", "hisob", "src")
        os.makedirs(pkg_dir, exist_ok=True)
        with open(os.path.join(pkg_dir, "main.zf"), "w", encoding="utf-8") as f:
            f.write("""
fn foiz(summa, stavka) {
    return summa * stavka / 100
}
""")

        code = """
import "hisob" as h

let daromad = h.foiz(2000, 15)
print("FOIZ:" + str(daromad))
"""
        captured = StringIO()
        main_zf = os.path.join(self.app_dir, "src", "main.zf")
        with patch("sys.stdout", captured):
            execute_source(code, filename=main_zf)

        output = captured.getvalue()
        self.assertIn("FOIZ:300", output)

    def test_import_zafira_modules_manifest_entry(self):
        """zafira.json manifestidagi 'entry' ko'rsatilgan fayl topilishi"""
        pkg_dir = os.path.join(self.app_dir, "zafira_modules", "maxsus_paket")
        os.makedirs(os.path.join(pkg_dir, "lib"), exist_ok=True)

        with open(os.path.join(pkg_dir, "zafira.json"), "w", encoding="utf-8") as f:
            json.dump({"name": "maxsus_paket", "entry": "lib/core.zf"}, f)

        with open(os.path.join(pkg_dir, "lib", "core.zf"), "w", encoding="utf-8") as f:
            f.write("""
fn core_qiymat() {
    return 777
}
""")

        code = """
import "maxsus_paket"

let q = maxsus_paket.core_qiymat()
print("CORE:" + str(q))
"""
        captured = StringIO()
        main_zf = os.path.join(self.app_dir, "src", "main.zf")
        with patch("sys.stdout", captured):
            execute_source(code, filename=main_zf)

        output = captured.getvalue()
        self.assertIn("CORE:777", output)

    def test_local_file_precedence_over_zafira_modules(self):
        """
        Muhim Qoida:
        Lokal fayl zafira_modules dagi bir xil nomli paketdan ustun turishi kerak
        """
        # 1. zafira_modules ga 'yordamchi' paketini yaratamiz
        mod_dir = os.path.join(self.app_dir, "zafira_modules", "yordamchi")
        os.makedirs(mod_dir, exist_ok=True)
        with open(os.path.join(mod_dir, "index.zf"), "w", encoding="utf-8") as f:
            f.write('fn manba() { return "MODULE" }\n')

        # 2. src/ papkasiga lokal 'yordamchi.zf' faylini yaratamiz
        src_dir = os.path.join(self.app_dir, "src")
        with open(os.path.join(src_dir, "yordamchi.zf"), "w", encoding="utf-8") as f:
            f.write('fn manba() { return "LOKAL_FAYL" }\n')

        # 3. src/main.zf dan import qilinganda LOKAL_FAYL olinishi shart
        code = """
import "yordamchi"

print("MANBA:" + yordamchi.manba())
"""
        captured = StringIO()
        main_zf = os.path.join(src_dir, "main.zf")
        with patch("sys.stdout", captured):
            execute_source(code, filename=main_zf)

        output = captured.getvalue()
        self.assertIn("MANBA:LOKAL_FAYL", output)


class TestZPMCommandLineIntegration(unittest.TestCase):
    """zafira.py CLI orqali `zafira install` va `zafira add` testlari"""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="zf_cli_test_")
        self.app_dir = os.path.join(self.test_dir, "cli_app")
        init_project("cli_app", self.test_dir)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_cli_add_and_install_end_to_end(self):
        """CLI orqali add -> install -> run siklini sinash"""
        py_cmd = sys.executable
        zafira_cli = os.path.join(PROJECT_ROOT, "zafira.py")

        # 1. Lokal paket yaratamiz
        pkg_dir = os.path.join(self.test_dir, "cli_helper")
        os.makedirs(os.path.join(pkg_dir, "src"), exist_ok=True)
        with open(os.path.join(pkg_dir, "src", "main.zf"), "w", encoding="utf-8") as f:
            f.write("""
fn salom() {
    return "CLI SALOM!"
}
""")

        # 2. zafira add cli_helper
        cmd_add = [py_cmd, zafira_cli, "add", "../cli_helper", self.app_dir]
        res_add = subprocess.run(cmd_add, capture_output=True, text=True, cwd=PROJECT_ROOT)
        self.assertEqual(res_add.returncode, 0, f"zafira add xatosi: {res_add.stderr}")
        self.assertTrue(os.path.isdir(os.path.join(self.app_dir, "zafira_modules", "cli_helper")))
        self.assertTrue(os.path.isfile(os.path.join(self.app_dir, "zafira.lock")))

        # 3. my_app src/main.zf ni yangilab paketni import qilamiz
        main_zf = os.path.join(self.app_dir, "src", "main.zf")
        with open(main_zf, "w", encoding="utf-8") as f:
            f.write("""
import "cli_helper"

let matn = cli_helper.salom()
print("NATIJA: " + matn)
""")

        # 4. zafira install
        cmd_install = [py_cmd, zafira_cli, "install", self.app_dir]
        res_install = subprocess.run(cmd_install, capture_output=True, text=True, cwd=PROJECT_ROOT)
        self.assertEqual(res_install.returncode, 0, f"zafira install xatosi: {res_install.stderr}")

        # 5. zafira run
        cmd_run = [py_cmd, zafira_cli, "run", self.app_dir]
        res_run = subprocess.run(cmd_run, capture_output=True, text=True, cwd=PROJECT_ROOT)
        self.assertEqual(res_run.returncode, 0, f"zafira run xatosi: {res_run.stderr}")
        self.assertIn("NATIJA: CLI SALOM!", res_run.stdout)


if __name__ == "__main__":
    unittest.main()
