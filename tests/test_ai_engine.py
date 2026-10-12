"""
Zafira Language - AI & Tensor Engine Unit Testlari
Silicon-Native Runtime: Tensor, std.ai, @gpu/@npu/@auto sinovlari
"""

import unittest
import math
from src.interpreter import Interpreter, Environment, ZafiraList, ZafiraError
from src.parser import Parser
from src.lexer import Lexer
from src.ai_engine import Tensor, TensorShape, get_active_device, set_active_device, silicon_context


class TestAIEngine(unittest.TestCase):
    def setUp(self):
        self.interpreter = Interpreter()
        set_active_device('cpu')

    def run_code(self, source: str):
        lexer = Lexer(source)
        parser = Parser(lexer.tokenize())
        program = parser.parse()
        return self.interpreter.run(program)

    # ─── 1. TENSOR YARATISH VA ATRIBUTLAR ───

    def test_tensor_creation_1d(self):
        t = Tensor([1.0, 2.0, 3.0])
        self.assertEqual(t.ndim, 1)
        self.assertEqual(list(t.shape), [3])
        self.assertEqual(t.shape[0], 3)
        self.assertEqual(t.data, [1.0, 2.0, 3.0])
        self.assertEqual(t.device, 'cpu')

    def test_tensor_creation_2d(self):
        t = Tensor([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])
        self.assertEqual(t.ndim, 2)
        self.assertEqual(list(t.shape), [3, 2])
        self.assertEqual(t.shape[0], 3)
        self.assertEqual(t.shape[1], 2)
        self.assertEqual(t.data[1][0], 3.0)

    def test_tensor_creation_with_zafira_list(self):
        zf_list = ZafiraList([10, 20, 30])
        t = Tensor(zf_list)
        self.assertEqual(list(t.shape), [3])
        self.assertEqual(t.data, [10.0, 20.0, 30.0])

    def test_tensor_invalid_shapes(self):
        with self.assertRaises(ZafiraError):
            Tensor([[1.0, 2.0], [3.0]])  # Noto'g'ri qator uzunligi
        with self.assertRaises(ZafiraError):
            Tensor(["not_a_number"])

    # ─── 2. DOT OPERATSIYALARI (1D, 2D, MATMUL) ───

    def test_tensor_dot_1d_1d(self):
        v1 = Tensor([1.0, 2.0, 3.0])
        v2 = Tensor([4.0, 5.0, 6.0])
        # 1*4 + 2*5 + 3*6 = 4 + 10 + 18 = 32
        res = v1.dot(v2)
        self.assertEqual(res, 32.0)

    def test_tensor_dot_2d_2d(self):
        m1 = Tensor([[1.0, 2.0], [3.0, 4.0]])
        m2 = Tensor([[5.0, 6.0], [7.0, 8.0]])
        # [[19, 22], [43, 50]]
        res = m1.dot(m2)
        self.assertEqual(list(res.shape), [2, 2])
        self.assertEqual(res.data, [[19.0, 22.0], [43.0, 50.0]])

    def test_tensor_dot_2d_1d(self):
        m = Tensor([[1.0, 2.0], [3.0, 4.0]])
        v = Tensor([5.0, 6.0])
        # [1*5 + 2*6, 3*5 + 4*6] = [17, 39]
        res = m.dot(v)
        self.assertEqual(list(res.shape), [2])
        self.assertEqual(res.data, [17.0, 39.0])

    def test_tensor_dot_1d_2d(self):
        v = Tensor([1.0, 2.0])
        m = Tensor([[5.0, 6.0, 7.0], [8.0, 9.0, 10.0]])
        # [1*5 + 2*8, 1*6 + 2*9, 1*7 + 2*10] = [21, 24, 27]
        res = v.dot(m)
        self.assertEqual(list(res.shape), [3])
        self.assertEqual(res.data, [21.0, 24.0, 27.0])

    def test_tensor_dot_dimension_mismatch(self):
        v1 = Tensor([1.0, 2.0])
        v2 = Tensor([1.0, 2.0, 3.0])
        with self.assertRaises(ZafiraError):
            v1.dot(v2)

    # ─── 3. ARIFMETIK AMALLAR (ADD, SUB, MUL) ───

    def test_tensor_add(self):
        v1 = Tensor([1.0, 2.0, 3.0])
        v2 = Tensor([4.0, 5.0, 6.0])
        res = v1.add(v2)
        self.assertEqual(res.data, [5.0, 7.0, 9.0])

        res_scalar = v1.add(10)
        self.assertEqual(res_scalar.data, [11.0, 12.0, 13.0])

    def test_tensor_sub(self):
        v1 = Tensor([10.0, 20.0, 30.0])
        v2 = Tensor([1.0, 2.0, 3.0])
        res = v1.sub(v2)
        self.assertEqual(res.data, [9.0, 18.0, 27.0])

        res_scalar = v1.sub(5)
        self.assertEqual(res_scalar.data, [5.0, 15.0, 25.0])

    def test_tensor_mul(self):
        v1 = Tensor([2.0, 3.0, 4.0])
        res_scalar = v1.mul(3)
        self.assertEqual(res_scalar.data, [6.0, 9.0, 12.0])

        v2 = Tensor([5.0, 2.0, 3.0])
        res_elemwise = v1.mul(v2)
        self.assertEqual(res_elemwise.data, [10.0, 6.0, 12.0])

    # ─── 4. STATISTIKA: SUM, MEAN ───

    def test_tensor_sum_and_mean(self):
        v = Tensor([1.0, 2.0, 3.0, 4.0])
        self.assertEqual(v.sum(), 10.0)
        self.assertEqual(v.mean(), 2.5)

        m = Tensor([[1.0, 2.0], [3.0, 4.0]])
        self.assertEqual(m.sum(), 10.0)
        self.assertEqual(m.mean(), 2.5)

    # ─── 5. KOSINUS O'XSHASHLIK ───

    def test_tensor_cosine_similarity(self):
        v1 = Tensor([1.0, 0.0, 0.0])
        v2 = Tensor([1.0, 0.0, 0.0])
        self.assertAlmostEqual(v1.cosine_similarity(v2), 1.0)

        v3 = Tensor([0.0, 1.0, 0.0])
        self.assertAlmostEqual(v1.cosine_similarity(v3), 0.0)

        v4 = Tensor([-1.0, 0.0, 0.0])
        self.assertAlmostEqual(v1.cosine_similarity(v4), -1.0)

        # Parallel vektorlar
        va = Tensor([1.0, 2.0, 3.0])
        vb = Tensor([2.0, 4.0, 6.0])
        self.assertAlmostEqual(va.cosine_similarity(vb), 1.0)

        # Nol vektor
        v_zero = Tensor([0.0, 0.0, 0.0])
        self.assertEqual(va.cosine_similarity(v_zero), 0.0)

    # ─── 6. STD.AI MODUL SINOVI (ZAFIRA TILI ORQALI) ───

    def test_zafira_std_ai_basic(self):
        code = """
        import std.ai

        let v1 = ai.tensor([1.0, 2.0, 3.0])
        let v2 = ai.tensor([4.0, 5.0, 6.0])
        let dot_res = v1.dot(v2)
        let total = v1.sum()
        let avg = v1.mean()
        let sim = ai.similarity(v1, v2)
        """
        self.run_code(code)
        env = self.interpreter.global_env
        self.assertEqual(env.get('dot_res'), 32.0)
        self.assertEqual(env.get('total'), 6.0)
        self.assertEqual(env.get('avg'), 2.0)
        self.assertGreater(env.get('sim'), 0.9)

    def test_zafira_std_ai_zeros_ones(self):
        code = """
        import std.ai

        let z1 = ai.zeros(4)
        let z2 = ai.zeros(2, 3)
        let o1 = ai.ones(3)
        let o2 = ai.ones(2, 2)

        let z1_sum = z1.sum()
        let o2_sum = o2.sum()
        """
        self.run_code(code)
        env = self.interpreter.global_env
        self.assertEqual(list(env.get('z1').shape), [4])
        self.assertEqual(list(env.get('z2').shape), [2, 3])
        self.assertEqual(list(env.get('o1').shape), [3])
        self.assertEqual(list(env.get('o2').shape), [2, 2])
        self.assertEqual(env.get('z1_sum'), 0.0)
        self.assertEqual(env.get('o2_sum'), 4.0)

    def test_zafira_std_ai_embedding_mock(self):
        code = """
        import std.ai

        let emb1 = ai.embedding_mock("sun'iy intellekt")
        let emb2 = ai.embedding_mock("sun'iy intellekt")
        let emb3 = ai.embedding_mock("avtomobil dvigateli")

        let sim_same = ai.similarity(emb1, emb2)
        let sim_diff = ai.similarity(emb1, emb3)
        let emb_len = emb1.shape[0]
        """
        self.run_code(code)
        env = self.interpreter.global_env
        self.assertEqual(env.get('emb_len'), 8)
        self.assertAlmostEqual(env.get('sim_same'), 1.0, places=5)
        # Turli matnlar uchun o'xshashlik 1.0 dan kam
        self.assertLess(env.get('sim_diff'), 0.99)

    def test_zafira_std_ai_device_and_silicon_runblocks(self):
        code = """
        import std.ai

        let initial_dev = ai.device()
        let gpu_dev = "none"
        let npu_dev = "none"

        run @gpu {
            gpu_dev = ai.device()
            let t = ai.tensor([1, 2, 3])
        }

        run @npu {
            npu_dev = ai.device()
        }

        let after_dev = ai.device()
        """
        self.run_code(code)
        env = self.interpreter.global_env
        self.assertEqual(env.get('initial_dev'), 'cpu')
        self.assertEqual(env.get('gpu_dev'), 'gpu')
        self.assertEqual(env.get('npu_dev'), 'npu')
        self.assertEqual(env.get('after_dev'), 'cpu')

    def test_zafira_tensor_operators_and_indexing(self):
        code = """
        import std.ai

        let a = ai.tensor([1.0, 2.0, 3.0])
        let b = ai.tensor([10.0, 20.0, 30.0])

        let c = a + b
        let d = b - a
        let e = a * 2.0
        let first_elem = a[0]
        """
        self.run_code(code)
        env = self.interpreter.global_env
        self.assertEqual(env.get('c').data, [11.0, 22.0, 33.0])
        self.assertEqual(env.get('d').data, [9.0, 18.0, 27.0])
        self.assertEqual(env.get('e').data, [2.0, 4.0, 6.0])
        self.assertEqual(env.get('first_elem'), 1.0)


if __name__ == '__main__':
    unittest.main()
