"""
Zafira Language - ZPM Package Manager & CLI Suite Unit Testlari
tests/test_package_manager.py
"""

import unittest
import os
import sys
import shutil
import tempfile
import json
import subprocess
from io import StringIO
from unittest.mock import patch

# Ensure project root in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.package_manager import (
    init_project,
    run_project,
    test_project,
    build_project,
    load_manifest,
    execute_source,
)
import zafira


class TestPackageManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="zafira_pm_test_")

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    # ─── 1. INIT_PROJECT TESTLARI ───

    def test_init_project_structure(self):
        """init_project to'g'ri fayl strukturasi va manifest yaratishini tekshirish"""
        proj_name = "salom_dunyo"
        proj_path = init_project(proj_name, self.test_dir)

        self.assertTrue(os.path.isdir(proj_path))
        manifest_file = os.path.join(proj_path, "zafira.json")
        main_file = os.path.join(proj_path, "src", "main.zf")
        test_file = os.path.join(proj_path, "tests", "test_main.zf")

        self.assertTrue(os.path.exists(manifest_file), "zafira.json mavjud bo'lishi kerak")
        self.assertTrue(os.path.exists(main_file), "src/main.zf mavjud bo'lishi kerak")
        self.assertTrue(os.path.exists(test_file), "tests/test_main.zf mavjud bo'lishi kerak")

        with open(manifest_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data["name"], proj_name)
        self.assertEqual(data["version"], "0.1.0")
        self.assertEqual(data["author"], "Jasper")
        self.assertEqual(data["entry"], "src/main.zf")
        self.assertEqual(data["dependencies"], {})

    def test_init_project_empty_name_error(self):
        """Loyiha nomi bo'sh bo'lganda xatolik berishi kerak"""
        with self.assertRaises(ValueError):
            init_project("", self.test_dir)

    def test_load_manifest(self):
        """load_manifest to'g'ri o'qishi va xatolarni ushlashi"""
        proj_name = "manifest_test"
        proj_path = init_project(proj_name, self.test_dir)

        manifest = load_manifest(proj_path)
        self.assertEqual(manifest["name"], proj_name)

        # zafira.json fayli yo'q bo'lsa xato berishi kerak
        empty_dir = os.path.join(self.test_dir, "empty")
        os.makedirs(empty_dir, exist_ok=True)
        with self.assertRaises(FileNotFoundError):
            load_manifest(empty_dir)

    # ─── 2. RUN_PROJECT TESTLARI ───

    def test_run_project_success(self):
        """Yaratilgan loyiha run_project orqali muvaffaqiyatli bajarilishi kerak"""
        proj_name = "run_app"
        proj_path = init_project(proj_name, self.test_dir)

        # Standart main.zf ni ishga tushirish
        # execute_source chiqishini tekshirish
        captured_output = StringIO()
        with patch("sys.stdout", captured_output):
            run_project(proj_path)

        output = captured_output.getvalue()
        self.assertIn("Salom, Zafira!", output)

    def test_run_project_missing_manifest(self):
        """Manifest bo'lmasa FileNotFoundError berishi kerak"""
        with self.assertRaises(FileNotFoundError):
            run_project(self.test_dir)

    def test_run_project_missing_entry(self):
        """Entry fayli o'chirilgan bo'lsa FileNotFoundError berishi kerak"""
        proj_name = "missing_entry"
        proj_path = init_project(proj_name, self.test_dir)
        os.remove(os.path.join(proj_path, "src", "main.zf"))

        with self.assertRaises(FileNotFoundError):
            run_project(proj_path)

    # ─── 3. BUILD_PROJECT TESTLARI ───

    def test_build_project_success(self):
        """build_project C faylini hosil qilishi kerak"""
        proj_name = "build_app"
        proj_path = init_project(proj_name, self.test_dir)

        c_file = build_project(proj_path)
        self.assertTrue(os.path.exists(c_file), "C fayli yaratilishi kerak")
        self.assertTrue(c_file.endswith(".c"))

        with open(c_file, "r", encoding="utf-8") as f:
            c_content = f.read()

        self.assertIn("#include <stdio.h>", c_content)
        self.assertIn("main(", c_content)

    # ─── 4. TEST_PROJECT TESTLARI ───

    def test_test_project_default_passes(self):
        """Yangi loyihaning standart tests/test_main.zf testi PASSED bo'lishi kerak"""
        proj_name = "test_pass_app"
        proj_path = init_project(proj_name, self.test_dir)

        res = test_project(proj_path)
        self.assertEqual(res["total"], 1)
        self.assertEqual(res["passed"], 1)
        self.assertEqual(res["failed"], 0)
        self.assertEqual(res["results"]["test_main.zf"], "PASSED")

    def test_test_project_with_failing_test(self):
        """Xato test fayli FAILED natija berishi kerak"""
        proj_name = "test_fail_app"
        proj_path = init_project(proj_name, self.test_dir)

        # Xato test fayli qo'shamiz (nolga bo'lish)
        fail_test_path = os.path.join(proj_path, "tests", "test_fail.zf")
        with open(fail_test_path, "w", encoding="utf-8") as f:
            f.write("// Xato test\nlet x = 1 / 0\n")

        res = test_project(proj_path)
        self.assertEqual(res["total"], 2)
        self.assertEqual(res["passed"], 1)
        self.assertEqual(res["failed"], 1)
        self.assertEqual(res["results"]["test_main.zf"], "PASSED")
        self.assertTrue("FAILED" in res["results"]["test_fail.zf"])

    def test_test_project_empty_tests_dir(self):
        """tests/ papkasi bo'sh bo'lsa total=0 bo'lishi kerak"""
        proj_name = "test_empty_app"
        proj_path = init_project(proj_name, self.test_dir)
        os.remove(os.path.join(proj_path, "tests", "test_main.zf"))

        res = test_project(proj_path)
        self.assertEqual(res["total"], 0)
        self.assertEqual(res["passed"], 0)
        self.assertEqual(res["failed"], 0)

    # ─── 5. CLI BUYRUQLARI INTEGRATSIYASI ───

    def test_cli_init_run_test_build(self):
        """zafira.py CLI orqali init, run, test va build buyruqlarini tekshirish"""
        proj_name = "cli_demo"
        target_dir = os.path.join(self.test_dir, "cli_workspace")
        os.makedirs(target_dir, exist_ok=True)

        py_cmd = sys.executable

        # 1. zafira.py init
        cmd_init = [py_cmd, os.path.join(PROJECT_ROOT, "zafira.py"), "init", proj_name, target_dir]
        res = subprocess.run(cmd_init, capture_output=True, text=True, cwd=PROJECT_ROOT)
        self.assertEqual(res.returncode, 0, f"zafira init xatosi: {res.stderr}")

        proj_path = os.path.join(target_dir, proj_name)
        self.assertTrue(os.path.exists(os.path.join(proj_path, "zafira.json")))

        # 2. zafira.py test
        cmd_test = [py_cmd, os.path.join(PROJECT_ROOT, "zafira.py"), "test", proj_path]
        res = subprocess.run(cmd_test, capture_output=True, text=True, cwd=PROJECT_ROOT)
        self.assertEqual(res.returncode, 0, f"zafira test xatosi: {res.stderr}")
        self.assertIn("PASSED", res.stdout)

        # 3. zafira.py run
        cmd_run = [py_cmd, os.path.join(PROJECT_ROOT, "zafira.py"), "run", proj_path]
        res = subprocess.run(cmd_run, capture_output=True, text=True, cwd=PROJECT_ROOT)
        self.assertEqual(res.returncode, 0, f"zafira run xatosi: {res.stderr}")
        self.assertIn("Salom, Zafira!", res.stdout)

        # 4. zafira.py build
        cmd_build = [py_cmd, os.path.join(PROJECT_ROOT, "zafira.py"), "build", proj_path]
        res = subprocess.run(cmd_build, capture_output=True, text=True, cwd=PROJECT_ROOT)
        self.assertEqual(res.returncode, 0, f"zafira build xatosi: {res.stderr}")
        self.assertTrue(os.path.exists(os.path.join(proj_path, "src", "main.c")))


if __name__ == "__main__":
    unittest.main()
