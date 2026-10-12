"""
Zafira Language - Fayllar Tizimi (std.fs) Testlari
std.fs modulining barcha funksiyalari va xatolik holatlarini 100% to'liq sinovdan o'tkazish.
"""

import os
import shutil
import tempfile
import unittest

from src.interpreter import Interpreter, ZafiraError, ZafiraList, Environment
from src.lexer import Lexer
from src.parser import Parser
from src.stdlib import load_stdlib_module, STDLIB_MODULES
from src.std_fs import (
    _fs_read_text,
    _fs_write_text,
    _fs_append_text,
    _fs_exists,
    _fs_is_file,
    _fs_is_dir,
    _fs_list_dir,
    _fs_make_dir,
    _fs_remove,
    _fs_remove_dir,
    _fs_file_size,
    _fs_copy,
    create_fs_module,
)
from src.type_checker import TypeChecker, TypeCheckError


class TestStdFsUnit(unittest.TestCase):
    """std.fs Python funksiyalarining birlik testlari."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="zafira_fs_test_")

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_read_and_write_text(self):
        file_path = os.path.join(self.temp_dir, "test.txt")
        _fs_write_text(file_path, "Salom Zafira!\n")
        self.assertTrue(os.path.exists(file_path))
        content = _fs_read_text(file_path)
        self.assertEqual(content, "Salom Zafira!\n")

    def test_append_text(self):
        file_path = os.path.join(self.temp_dir, "append.txt")
        _fs_write_text(file_path, "Qator 1\n")
        _fs_append_text(file_path, "Qator 2\n")
        content = _fs_read_text(file_path)
        self.assertEqual(content, "Qator 1\nQator 2\n")

    def test_exists_and_is_file_and_is_dir(self):
        file_path = os.path.join(self.temp_dir, "exists_test.txt")
        sub_dir = os.path.join(self.temp_dir, "sub_folder")

        self.assertFalse(_fs_exists(file_path))
        self.assertFalse(_fs_is_file(file_path))
        self.assertFalse(_fs_is_dir(file_path))

        _fs_write_text(file_path, "Test")
        _fs_make_dir(sub_dir)

        self.assertTrue(_fs_exists(file_path))
        self.assertTrue(_fs_is_file(file_path))
        self.assertFalse(_fs_is_dir(file_path))

        self.assertTrue(_fs_exists(sub_dir))
        self.assertFalse(_fs_is_file(sub_dir))
        self.assertTrue(_fs_is_dir(sub_dir))

    def test_list_dir(self):
        sub_dir = os.path.join(self.temp_dir, "list_folder")
        _fs_make_dir(sub_dir)
        _fs_write_text(os.path.join(sub_dir, "a.txt"), "A")
        _fs_write_text(os.path.join(sub_dir, "b.txt"), "B")

        res = _fs_list_dir(sub_dir)
        self.assertIsInstance(res, ZafiraList)
        self.assertIn("a.txt", res.items)
        self.assertIn("b.txt", res.items)
        self.assertEqual(len(res.items), 2)

    def test_make_dir_recursive_and_single(self):
        deep_dir = os.path.join(self.temp_dir, "level1", "level2", "level3")
        _fs_make_dir(deep_dir, recursive=True)
        self.assertTrue(os.path.isdir(deep_dir))

        single_dir = os.path.join(self.temp_dir, "single_dir")
        _fs_make_dir(single_dir, recursive=False)
        self.assertTrue(os.path.isdir(single_dir))

    def test_remove_file(self):
        file_path = os.path.join(self.temp_dir, "delete_me.txt")
        _fs_write_text(file_path, "Yo'q bo'l")
        self.assertTrue(os.path.exists(file_path))
        _fs_remove(file_path)
        self.assertFalse(os.path.exists(file_path))

    def test_remove_dir_empty_and_recursive(self):
        # Bo'sh papkani oddiy o'chirish
        empty_dir = os.path.join(self.temp_dir, "empty")
        _fs_make_dir(empty_dir)
        _fs_remove_dir(empty_dir, recursive=False)
        self.assertFalse(os.path.exists(empty_dir))

        # Ichida fayli bor papkani recursive=True bilan o'chirish
        nested_dir = os.path.join(self.temp_dir, "nested")
        _fs_make_dir(nested_dir)
        _fs_write_text(os.path.join(nested_dir, "child.txt"), "bola")
        _fs_remove_dir(nested_dir, recursive=True)
        self.assertFalse(os.path.exists(nested_dir))

    def test_file_size(self):
        file_path = os.path.join(self.temp_dir, "size.txt")
        sample_data = "1234567890"  # 10 bayt
        _fs_write_text(file_path, sample_data)
        size = _fs_file_size(file_path)
        self.assertEqual(size, 10)

    def test_copy(self):
        src_path = os.path.join(self.temp_dir, "source.txt")
        dst_path = os.path.join(self.temp_dir, "target.txt")
        _fs_write_text(src_path, "Nusxa olinadigan matn")
        _fs_copy(src_path, dst_path)

        self.assertTrue(os.path.exists(dst_path))
        self.assertEqual(_fs_read_text(dst_path), "Nusxa olinadigan matn")

    # ─── XATOLIKLAR VA CHEKKA HOLATLAR ───

    def test_error_read_nonexistent(self):
        missing = os.path.join(self.temp_dir, "yoq.txt")
        with self.assertRaises(ZafiraError):
            _fs_read_text(missing)

    def test_error_read_directory(self):
        with self.assertRaises(ZafiraError):
            _fs_read_text(self.temp_dir)

    def test_error_remove_nonexistent(self):
        missing = os.path.join(self.temp_dir, "yoq.txt")
        with self.assertRaises(ZafiraError):
            _fs_remove(missing)

    def test_error_remove_dir_with_remove(self):
        # Papkani remove() bilan o'chirmoqchi bo'lsa ZafiraError bo'lishi kerak
        with self.assertRaises(ZafiraError):
            _fs_remove(self.temp_dir)

    def test_error_remove_dir_nonempty_without_recursive(self):
        busy_dir = os.path.join(self.temp_dir, "busy")
        _fs_make_dir(busy_dir)
        _fs_write_text(os.path.join(busy_dir, "file.txt"), "fayl")
        with self.assertRaises(ZafiraError):
            _fs_remove_dir(busy_dir, recursive=False)

    def test_error_list_dir_on_file(self):
        file_path = os.path.join(self.temp_dir, "file.txt")
        _fs_write_text(file_path, "Oddiy fayl")
        with self.assertRaises(ZafiraError):
            _fs_list_dir(file_path)

    def test_error_copy_missing_source(self):
        missing = os.path.join(self.temp_dir, "missing.txt")
        dst = os.path.join(self.temp_dir, "dst.txt")
        with self.assertRaises(ZafiraError):
            _fs_copy(missing, dst)

    def test_error_null_path(self):
        with self.assertRaises(ZafiraError):
            _fs_read_text(None)


class TestStdFsIntegration(unittest.TestCase):
    """Zafira tili kodi orqali std.fs integratsiya testlari."""

    def setUp(self):
        self.interpreter = Interpreter()
        self.temp_dir = tempfile.mkdtemp(prefix="zafira_zf_test_")

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def run_code(self, source: str):
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        program = parser.parse()
        checker = TypeChecker()
        checker.check(program)
        return self.interpreter.run(program)

    def test_module_registered_in_stdlib(self):
        self.assertIn('fs', STDLIB_MODULES)
        env = Environment()
        load_stdlib_module('std.fs', env)
        self.assertIsNotNone(env.get('fs'))

    def test_zafira_fs_lifecycle(self):
        norm_dir = self.temp_dir.replace('\\', '/')
        code = f"""
        import std.fs

        let fayl = "{norm_dir}/test_zf.txt"
        fs.write_text(fayl, "Zafira tili go'zaldir!")
        let bor = fs.exists(fayl)
        let matn = fs.read_text(fayl)
        let hajm = fs.file_size(fayl)
        let is_f = fs.is_file(fayl)
        let is_d = fs.is_dir(fayl)

        fs.append_text(fayl, " Qo'shimcha.")
        let yangi_matn = fs.read_text(fayl)

        let nusxa = "{norm_dir}/nusxa_zf.txt"
        fs.copy(fayl, nusxa)
        let nusxa_bor = fs.exists(nusxa)

        fs.remove(fayl)
        let ochirildi = fs.exists(fayl)
        fs.remove(nusxa)
        """
        self.run_code(code)
        env = self.interpreter.global_env
        self.assertTrue(env.get('bor'))
        self.assertEqual(env.get('matn'), "Zafira tili go'zaldir!")
        self.assertEqual(env.get('hajm'), len("Zafira tili go'zaldir!".encode('utf-8')))
        self.assertTrue(env.get('is_f'))
        self.assertFalse(env.get('is_d'))
        self.assertEqual(env.get('yangi_matn'), "Zafira tili go'zaldir! Qo'shimcha.")
        self.assertTrue(env.get('nusxa_bor'))
        self.assertFalse(env.get('ochirildi'))

    def test_zafira_fs_folders(self):
        norm_dir = self.temp_dir.replace('\\', '/')
        code = f"""
        import std.fs

        let papka = "{norm_dir}/papka_zf"
        fs.make_dir(papka, true)
        let papka_bor = fs.exists(papka)
        let is_d = fs.is_dir(papka)

        let ichki = "{norm_dir}/papka_zf/doc.txt"
        fs.write_text(ichki, "Ichki hujjat")

        let royxat = fs.list_dir(papka)
        let fayl_soni = royxat.len

        fs.remove_dir(papka, true)
        let keyin_bor = fs.exists(papka)
        """
        self.run_code(code)
        env = self.interpreter.global_env
        self.assertTrue(env.get('papka_bor'))
        self.assertTrue(env.get('is_d'))
        self.assertEqual(env.get('fayl_soni'), 1)
        self.assertFalse(env.get('keyin_bor'))

    def test_type_checker_fs_validation(self):
        norm_dir = self.temp_dir.replace('\\', '/')
        # To'g'ri tiplar bilan seal funksiya
        code = f"""
        import std.fs

        seal fn tekshir() -> Bool {{
            let path = "{norm_dir}/check.txt"
            fs.write_text(path, "ok")
            let mavjud: Bool = fs.exists(path)
            fs.remove(path)
            return mavjud
        }}
        let res = tekshir()
        """
        self.run_code(code)
        env = self.interpreter.global_env
        self.assertTrue(env.get('res'))

    def test_zafira_fs_alias(self):
        norm_dir = self.temp_dir.replace('\\', '/')
        code = f"""
        import std.fs as files

        let fayl = "{norm_dir}/alias_test.txt"
        files.write_text(fayl, "Alias ishladi!")
        let oqildi = files.read_text(fayl)
        files.remove(fayl)
        """
        self.run_code(code)
        env = self.interpreter.global_env
        self.assertEqual(env.get('oqildi'), "Alias ishladi!")

    def test_type_checker_fs_unknown_method(self):
        # Mavjud bo'lmagan metod TypeCheckError berishi kerak
        code = """
        import std.fs
        fs.noma_lum_metod("test")
        """
        lexer = Lexer(code)
        parser = Parser(lexer.tokenize())
        prog = parser.parse()
        checker = TypeChecker()
        with self.assertRaises(TypeCheckError):
            checker.check(prog)


if __name__ == '__main__':
    unittest.main()
