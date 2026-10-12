"""
Zafira Type Checker - Comprehensive Unit Tests
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from src.lexer import Lexer
from src.parser import Parser
from src.type_checker import TypeChecker, TypeCheckError


def check_source(source: str):
    tokens = Lexer(source).tokenize()
    program = Parser(tokens).parse()
    checker = TypeChecker()
    checker.check(program)


def expect_type_error(source: str, expected_snippet: str = ""):
    try:
        check_source(source)
        assert False, f"TypeCheckError kutilgan edi, lekin xatosiz o'tdi: {source}"
    except TypeCheckError as e:
        msg = str(e)
        if expected_snippet:
            assert expected_snippet in msg, f"Kutilgan '{expected_snippet}' xabarda topilmadi: {msg}"
        print(f"  [OK] Xato muvaffaqiyatli ushlandi: {msg}")


def test_suite():
    print("=== 1. TO'G'RI KODLAR TESTI ===")

    # 1.1 Oddiy seal funksiya
    check_source("""
    seal fn qo'sh(a: Int, b: Int) -> Int {
        return a + b
    }
    let res = qo'sh(10, 20)
    """)
    print("  [OK] 1.1 seal fn qo'sh")

    # 1.2 Seal funksiya where invarianti bilan (to'g'ri chaqiriq)
    check_source("""
    seal fn bo'lish(a: Int, b: Int) -> Float
        where b > 0
    {
        return a / b
    }
    let res = bo'lish(10, 2)
    """)
    print("  [OK] 1.2 seal fn where invariant (to'g'ri)")

    # 1.3 Draft funksiya o'tkazib yuborilishi
    check_source("""
    fn draft_test(x) {
        return "har qanday narsa"
    }
    let d = draft_test(123)
    """)
    print("  [OK] 1.3 draft fn o'tkazib yuborish")

    # 1.4 Const o'zgaruvchilar to'g'ri ishlatilishi
    check_source("""
    const PI = 3.14
    let r = 5.0
    let yuza = PI * r * r
    """)
    print("  [OK] 1.4 const to'g'ri ishlatilishi")

    # 1.5 Struct va a'zolar
    check_source("""
    struct Talaba {
        ism: String,
        ball: Int
    }
    let t = Talaba("Ali", 100)
    """)
    print("  [OK] 1.5 struct yaratish")

    print("\n=== 2. PARAMETR TIP XATOLIKLARI ===")
    # 2.1 String o'rniga Int kutilgan
    expect_type_error("""
    seal fn bo'lish(a: Int, b: Int) -> Float {
        return a / b
    }
    bo'lish(10, "salom")
    """, "String o'rniga Int kutilgan")

    # 2.2 Argumentlar soni kamligi
    expect_type_error("""
    seal fn test(a: Int, b: Int) -> Int {
        return a + b
    }
    test(10)
    """, "2 ta argument kutadi, lekin 1 ta berildi")

    print("\n=== 3. RETURN TIP XATOLIKLARI ===")
    # 3.1 String qaytarilmoqda, Int kutilgan
    expect_type_error("""
    seal fn test(x: Int) -> Int {
        return "salom"
    }
    """, "String qaytarilyapti, Int kutilgan")

    # 3.2 Return yo'qligi
    expect_type_error("""
    seal fn test(x: Int) -> Int {
        let y = x + 1
    }
    """, "return operatori topilmadi")

    print("\n=== 4. WHERE INVARIANTI STATIK XATOLIKLARI ===")
    # 4.1 Argument statically violates where clause
    expect_type_error("""
    seal fn bo'lish(a: Int, b: Int) -> Float
        where b > 0
    {
        return a / b
    }
    bo'lish(10, 0)
    """, "where' invarianti statik tekshiruvda buzildi")

    # 4.2 Where clause doimo False
    expect_type_error("""
    seal fn test(x: Int) -> Int
        where 0 > 1
    {
        return x
    }
    """, "doimo False")

    # 4.3 Where clause'da noma'lum o'zgaruvchi
    expect_type_error("""
    seal fn test(x: Int) -> Int
        where nomalum_var > 0
    {
        return x
    }
    """, "where' shartida e'lon qilinmagan o'zgaruvchi")

    print("\n=== 5. CONST QAYTA TAYINLASH XATOLIKLARI ===")
    # 5.1 Const ga to'g'ridan-to'g'ri qayta tayinlash
    expect_type_error("""
    const PI = 3.14
    PI = 3.1415
    """, "const, uni o'zgartirib bo'lmaydi")

    # 5.2 Const ni let orqali qayta e'lon qilish
    expect_type_error("""
    const PI = 3.14
    let PI = 3.15
    """, "const, uni qayta e'lon qilib bo'lmaydi")

    print("\n=== 6. E'LON QILINMAGAN O'ZGARUVCHILAR (UNDECLARED) ===")
    # 6.1 Aniqlanmagan o'zgaruvchini ishlatish (bashorat bilan)
    expect_type_error("""
    let nomi = "Zafira"
    print(nme)
    """, "aniqlanmagan")

    # 6.2 Aniqlanmagan o'zgaruvchiga tayinlash
    expect_type_error("""
    noma_lum = 123
    """, "aniqlanmagan")

    print("\n🎉 BARCHA TESTLAR 100% MUVAFFAQIYATLI O'TDI!")


if __name__ == '__main__':
    test_suite()
