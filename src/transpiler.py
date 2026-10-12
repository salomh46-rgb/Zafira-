"""
Zafira Language - C Transpiler
AST ni to'g'ridan-to'g'ri bajariladigan C kodiga aylantiradi.
Muallif: Jasper & Antigravity
"""

import json
import re
from typing import Dict, List, Optional, Any, Set

from src.parser import (
    Program, Node, NumberLiteral, StringLiteral, BoolLiteral, NullLiteral,
    Identifier, BinaryOp, UnaryOp, FunctionCall, MemberAccess, IndexAccess,
    ListLiteral, RangeExpr, LetStatement, ConstStatement, AssignStatement,
    ReturnStatement, IfStatement, WhileStatement, ForStatement, FunctionDef,
    StructDef, ImportStatement, RunBlock, ExprStatement, Block
)


# Zafira tiplari -> C tiplari mapping
TYPE_MAPPING = {
    'Int': 'int64_t',
    'Float': 'double',
    'String': 'char*',
    'Bool': 'int',
    'Any': 'ZfAny',
    'void': 'void',
    'Null': 'ZfAny',
}

C_KEYWORDS = {
    'auto', 'break', 'case', 'char', 'const', 'continue', 'default', 'do',
    'double', 'else', 'enum', 'extern', 'float', 'for', 'goto', 'if',
    'int', 'long', 'register', 'return', 'short', 'signed', 'sizeof', 'static',
    'struct', 'switch', 'typedef', 'union', 'unsigned', 'void', 'volatile', 'while'
}


class Transpiler:
    """
    Zafira AST ni C dasturlash tili kodiga aylantiruvchi transpiler.
    """

    def __init__(self):
        self.output: List[str] = []
        self.indent: int = 0
        self.functions: Dict[str, str] = {}    # fn nomi -> return_type (Zafira tipi)
        self.variables: Dict[str, str] = {}    # o'zgaruvchi nomi -> Zafira tipi
        self.structs: Set[str] = set()         # struct nomlari

    def emit(self, line: str = ""):
        """Joriy chekinish (indent) bilan C kod qatorini yozadi"""
        if line:
            self.output.append('    ' * self.indent + line)
        else:
            self.output.append("")

    def to_c_ident(self, name: str) -> str:
        """Zafira identifikatorini (masalan 'qo\'sh') C uchun xavfsiz nomga aylantiradi"""
        res = name.replace("'", "_").replace("’", "_").replace("`", "_")
        clean = []
        for ch in res:
            if ch.isalnum() or ch == '_':
                clean.append(ch)
            else:
                clean.append('_')
        out = "".join(clean)
        if not out:
            out = "_zf_anon"
        elif out[0].isdigit():
            out = "_" + out
        if out in C_KEYWORDS:
            out = f"zf_{out}"
        return out

    def map_type(self, zf_type: Optional[str]) -> str:
        """Zafira tipini C tipiga o'giradi"""
        if not zf_type:
            return 'void'
        if zf_type in TYPE_MAPPING:
            return TYPE_MAPPING[zf_type]
        if zf_type in self.structs:
            return self.to_c_ident(zf_type)
        return 'ZfAny'

    def infer_type(self, node: Optional[Node]) -> str:
        """AST tugunining Zafira tipini taxmin qiladi (type inference)"""
        if node is None:
            return 'Null'
        if isinstance(node, NumberLiteral):
            if isinstance(node.value, float) and not node.value.is_integer():
                return 'Float'
            return 'Int'
        if isinstance(node, StringLiteral):
            return 'String'
        if isinstance(node, BoolLiteral):
            return 'Bool'
        if isinstance(node, NullLiteral):
            return 'Null'
        if isinstance(node, Identifier):
            return self.variables.get(node.name, 'Any')
        if isinstance(node, FunctionCall):
            if isinstance(node.callee, Identifier):
                cname = node.callee.name
                if cname == 'String':
                    return 'String'
                if cname == 'Int':
                    return 'Int'
                if cname == 'Float':
                    return 'Float'
                if cname == 'len':
                    return 'Int'
                if cname in self.functions:
                    return self.functions[cname] or 'void'
            return 'Any'
        if isinstance(node, BinaryOp):
            lt = self.infer_type(node.left)
            rt = self.infer_type(node.right)
            if node.op == '+':
                if lt == 'String' or rt == 'String':
                    return 'String'
                if lt == 'Float' or rt == 'Float':
                    return 'Float'
                return 'Int'
            if node.op in ('-', '*', '/', '%', '**'):
                if lt == 'Float' or rt == 'Float' or node.op == '/':
                    return 'Float'
                return 'Int'
            if node.op in ('==', '!=', '<', '<=', '>', '>=', 'and', 'or'):
                return 'Bool'
        if isinstance(node, RangeExpr):
            return 'List'
        if isinstance(node, ListLiteral):
            return 'List'
        return 'Any'

    def transpile(self, program: Program) -> str:
        """
        AST dasturini to'liq C manba kodi matniga aylantiradi.
        """
        self.output = []
        self.indent = 0
        self.functions = {}
        self.variables = {}
        self.structs = set()

        # 1. Barcha struct va funksiyalarni ro'yxatga olish
        for stmt in program.body:
            if isinstance(stmt, StructDef):
                self.structs.add(stmt.name)
            elif isinstance(stmt, FunctionDef):
                if stmt.mode == 'seal':
                    self.functions[stmt.name] = stmt.return_type or 'void'
                else:
                    self.functions[stmt.name] = 'Any'

        # 2. C Header qismi
        self.emit("// ══════════════════════════════════════════════════════════════")
        self.emit("//  Zafira Dasturlash Tili - C Transpiler Chiqishi")
        self.emit("//  Generatsiya qilingan: Zafira C Transpiler")
        self.emit("// ══════════════════════════════════════════════════════════════")
        self.emit("")
        self.emit("#include <stdio.h>")
        self.emit("#include <stdlib.h>")
        self.emit("#include <string.h>")
        self.emit("#include <stdint.h>")
        self.emit("#include <math.h>")
        self.emit("")
        self.emit("// Zafira runtime")
        self.emit("typedef void* ZfAny;")
        self.emit("#define ZF_NULL NULL")
        self.emit("#define ZF_TRUE 1")
        self.emit("#define ZF_FALSE 0")
        self.emit("")
        self.emit("// Zafira yordamchi funksiyalari")
        self.emit("static inline char* zf_str_concat(const char* s1, const char* s2) {")
        self.indent += 1
        self.emit("if (!s1) s1 = \"\";")
        self.emit("if (!s2) s2 = \"\";")
        self.emit("size_t len1 = strlen(s1);")
        self.emit("size_t len2 = strlen(s2);")
        self.emit("char* res = (char*)malloc(len1 + len2 + 1);")
        self.emit("if (!res) return \"\";")
        self.emit("strcpy(res, s1);")
        self.emit("strcat(res, s2);")
        self.emit("return res;")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        self.emit("static inline char* zf_str_int(int64_t val) {")
        self.indent += 1
        self.emit("char* buf = (char*)malloc(32);")
        self.emit("snprintf(buf, 32, \"%lld\", (long long)val);")
        self.emit("return buf;")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        self.emit("static inline char* zf_str_float(double val) {")
        self.indent += 1
        self.emit("char* buf = (char*)malloc(32);")
        self.emit("snprintf(buf, 32, \"%g\", val);")
        self.emit("return buf;")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        self.emit("static inline char* zf_str_bool(int val) {")
        self.indent += 1
        self.emit("return val ? \"true\" : \"false\";")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        self.emit("static inline int64_t zf_to_int(const char* s) {")
        self.indent += 1
        self.emit("return s ? atoll(s) : 0;")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        self.emit("static inline double zf_to_float(const char* s) {")
        self.indent += 1
        self.emit("return s ? atof(s) : 0.0;")
        self.indent -= 1
        self.emit("}")
        self.emit("")

        # 3. Structlarni chiqarish
        structs = [s for s in program.body if isinstance(s, StructDef)]
        if structs:
            self.emit("// ─── Strukturalar ───")
            for st in structs:
                self.transpile_struct(st)

        # 4. Funksiyalar va top-level statementlarni ajratish
        functions = [s for s in program.body if isinstance(s, FunctionDef)]
        top_stmts = [s for s in program.body if not isinstance(s, (StructDef, FunctionDef, ImportStatement))]

        # 5. Forward declarations (prototiplar)
        if functions:
            self.emit("// ─── Funksiyalar prototiplari ───")
            for fn in functions:
                proto = self.get_function_signature(fn)
                self.emit(f"{proto};")
            self.emit("")

        # 6. Funksiyalar tanasini chiqarish
        if functions:
            self.emit("// ─── Funksiyalar ta'riflari ───")
            for fn in functions:
                self.transpile_function(fn)

        # 7. main() funksiyasi
        self.emit("// ─── Asosiy Kirish Nuqtasi (main) ───")
        self.emit("int main(int argc, char** argv) {")
        self.indent += 1

        for stmt in top_stmts:
            self.transpile_statement(stmt)

        # Agar Zafira da main() funksiyasi ta'riflangan bo'lsa, uni chaqirish
        if 'main' in self.functions:
            self.emit("main();")

        self.emit("return 0;")
        self.indent -= 1
        self.emit("}")
        self.emit("")

        return "\n".join(self.output)

    def transpile_struct(self, node: StructDef):
        """Struct ta'rifini C typedef struct ga aylantiradi"""
        c_name = self.to_c_ident(node.name)
        self.emit(f"typedef struct {c_name} {{")
        self.indent += 1
        for fname, ftype in node.fields:
            c_type = self.map_type(ftype)
            c_fname = self.to_c_ident(fname)
            self.emit(f"{c_type} {c_fname};")
        self.indent -= 1
        self.emit(f"}} {c_name};")
        self.emit("")

    def get_function_signature(self, node: FunctionDef) -> str:
        """Funksiya sarlavhasi (imzosi)ni tuzadi"""
        c_name = self.to_c_ident(node.name)
        if node.mode == 'seal':
            ret_type = self.map_type(node.return_type) if node.return_type else 'void'
            params = []
            for pname, ptype in node.params:
                c_ptype = self.map_type(ptype) if ptype else 'int64_t'
                params.append(f"{c_ptype} {self.to_c_ident(pname)}")
        else:
            # draft fn -> barcha turlar ZfAny (void*) bo'ladi
            ret_type = 'ZfAny'
            params = [f"ZfAny {self.to_c_ident(pname)}" for pname, _ in node.params]

        params_str = ", ".join(params) if params else "void"
        return f"{ret_type} {c_name}({params_str})"

    def transpile_function(self, node: FunctionDef):
        """Funksiyani C kodiga aylantiradi"""
        sig = self.get_function_signature(node)
        self.emit(f"{sig} {{")
        self.indent += 1

        # Funksiya parametrlari turlarini mahalliy ro'yxatga kiritish
        saved_vars = dict(self.variables)
        for pname, ptype in node.params:
            if node.mode == 'seal':
                self.variables[pname] = ptype or 'Int'
            else:
                self.variables[pname] = 'Any'

        for stmt in node.body:
            self.transpile_statement(stmt)

        self.variables = saved_vars
        self.indent -= 1
        self.emit("}")
        self.emit("")

    def transpile_statement(self, node: Node):
        """Operator (statement)ni C kodiga aylantiradi"""
        if isinstance(node, LetStatement):
            self.transpile_let(node)
        elif isinstance(node, ConstStatement):
            self.transpile_const(node)
        elif isinstance(node, AssignStatement):
            target = self.transpile_expr(node.target)
            val = self.transpile_expr(node.value)
            self.emit(f"{target} = {val};")
        elif isinstance(node, ReturnStatement):
            if node.value is not None:
                val = self.transpile_expr(node.value)
                self.emit(f"return {val};")
            else:
                self.emit("return;")
        elif isinstance(node, IfStatement):
            self.transpile_if(node)
        elif isinstance(node, WhileStatement):
            cond = self.transpile_expr(node.condition)
            self.emit(f"while ({cond}) {{")
            self.indent += 1
            for s in node.body:
                self.transpile_statement(s)
            self.indent -= 1
            self.emit("}")
        elif isinstance(node, ForStatement):
            self.transpile_for(node)
        elif isinstance(node, ExprStatement):
            self.transpile_expr_statement(node)
        elif isinstance(node, Block):
            self.emit("{")
            self.indent += 1
            for s in node.statements:
                self.transpile_statement(s)
            self.indent -= 1
            self.emit("}")

    def transpile_let(self, node: LetStatement):
        """LetStatement ni C o'zgaruvchisiga aylantiradi"""
        c_name = self.to_c_ident(node.name)
        zf_type = node.type_hint or self.infer_type(node.value)
        self.variables[node.name] = zf_type
        c_type = self.map_type(zf_type)

        if node.value is not None:
            val_expr = self.transpile_expr(node.value)
            self.emit(f"{c_type} {c_name} = {val_expr};")
        else:
            self.emit(f"{c_type} {c_name};")

    def transpile_const(self, node: ConstStatement):
        """ConstStatement ni const C o'zgaruvchisiga aylantiradi"""
        c_name = self.to_c_ident(node.name)
        zf_type = node.type_hint or self.infer_type(node.value)
        self.variables[node.name] = zf_type
        c_type = self.map_type(zf_type)
        val_expr = self.transpile_expr(node.value)
        self.emit(f"const {c_type} {c_name} = {val_expr};")

    def transpile_if(self, node: IfStatement):
        """IfStatement (if/else if/else) ni C shartli blokiga aylantiradi"""
        cond = self.transpile_expr(node.condition)
        self.emit(f"if ({cond}) {{")
        self.indent += 1
        for s in node.then_block:
            self.transpile_statement(s)
        self.indent -= 1

        curr = node
        while curr.else_block:
            if len(curr.else_block) == 1 and isinstance(curr.else_block[0], IfStatement):
                elif_node = curr.else_block[0]
                elif_cond = self.transpile_expr(elif_node.condition)
                self.emit(f"}} else if ({elif_cond}) {{")
                self.indent += 1
                for s in elif_node.then_block:
                    self.transpile_statement(s)
                self.indent -= 1
                curr = elif_node
            else:
                self.emit("} else {")
                self.indent += 1
                for s in curr.else_block:
                    self.transpile_statement(s)
                self.indent -= 1
                break
        self.emit("}")

    def transpile_for(self, node: ForStatement):
        """ForStatement ni C for tsikliga aylantiradi"""
        c_var = self.to_c_ident(node.var)
        self.variables[node.var] = 'Int'

        if isinstance(node.iterable, RangeExpr):
            start_c = self.transpile_expr(node.iterable.start)
            end_c = self.transpile_expr(node.iterable.end)
            self.emit(f"for (int64_t {c_var} = {start_c}; {c_var} < {end_c}; {c_var}++) {{")
        else:
            # Boshqa iteratsiyalar (masalan list)
            iter_c = self.transpile_expr(node.iterable)
            self.emit(f"for (int64_t {c_var} = 0; {c_var} < {iter_c}; {c_var}++) {{")

        self.indent += 1
        for s in node.body:
            self.transpile_statement(s)
        self.indent -= 1
        self.emit("}")

    def transpile_expr_statement(self, node: ExprStatement):
        """ExprStatement ni C qatoriga aylantiradi, print() ni printf ga o'giradi"""
        expr = node.expr

        # print(...) maxsus qoidasi: print -> C printf
        if isinstance(expr, FunctionCall) and isinstance(expr.callee, Identifier) and expr.callee.name == 'print':
            self.transpile_print_call(expr.args)
            return

        expr_c = self.transpile_expr(expr)
        self.emit(f"{expr_c};")

    def transpile_print_call(self, args: List[Node]):
        """print(...) ni C printf(...) chaqiruviga aylantiradi"""
        if not args:
            self.emit('printf("\\n");')
            return

        format_parts = []
        c_args = []

        for arg in args:
            arg_type = self.infer_type(arg)
            arg_c = self.transpile_expr(arg)

            if arg_type == 'String':
                format_parts.append("%s")
                c_args.append(arg_c)
            elif arg_type == 'Int':
                format_parts.append("%lld")
                c_args.append(f"(long long)({arg_c})")
            elif arg_type == 'Float':
                format_parts.append("%g")
                c_args.append(arg_c)
            elif arg_type == 'Bool':
                format_parts.append("%s")
                c_args.append(f"({arg_c} ? \"true\" : \"false\")")
            else:
                # Noma'lum yoki satr ifodasi
                format_parts.append("%s")
                c_args.append(arg_c)

        fmt_str = " ".join(format_parts) + "\\n"
        args_str = ", ".join(c_args)
        self.emit(f'printf("{fmt_str}", {args_str});')

    def transpile_expr(self, node: Node) -> str:
        """Iborani (Expression) C ifodasiga aylantiradi"""
        if isinstance(node, NumberLiteral):
            if isinstance(node.value, float) and not node.value.is_integer():
                return str(node.value)
            return str(int(node.value))

        if isinstance(node, StringLiteral):
            return json.dumps(node.value, ensure_ascii=False)

        if isinstance(node, BoolLiteral):
            return "ZF_TRUE" if node.value else "ZF_FALSE"

        if isinstance(node, NullLiteral):
            return "ZF_NULL"

        if isinstance(node, Identifier):
            return self.to_c_ident(node.name)

        if isinstance(node, BinaryOp):
            return self.transpile_binary_op(node)

        if isinstance(node, UnaryOp):
            operand_c = self.transpile_expr(node.operand)
            if node.op == '-':
                return f"(-{operand_c})"
            if node.op == 'not':
                return f"(!{operand_c})"
            return f"({node.op}{operand_c})"

        if isinstance(node, FunctionCall):
            return self.transpile_function_call(node)

        if isinstance(node, MemberAccess):
            obj_c = self.transpile_expr(node.obj)
            mem_c = self.to_c_ident(node.member)
            return f"{obj_c}.{mem_c}"

        if isinstance(node, IndexAccess):
            obj_c = self.transpile_expr(node.obj)
            idx_c = self.transpile_expr(node.index)
            return f"{obj_c}[{idx_c}]"

        if isinstance(node, RangeExpr):
            # Range odatda for tsiklida ishlatiladi, lekin ifoda sifatida ham qabul qilamiz
            return self.transpile_expr(node.end)

        if isinstance(node, ListLiteral):
            elements_c = [self.transpile_expr(e) for e in node.elements]
            return f"{{ {', '.join(elements_c)} }}"

        return "ZF_NULL"

    def transpile_binary_op(self, node: BinaryOp) -> str:
        """Ikkilik amal (BinaryOp)ni C ifodasiga aylantiradi"""
        left_type = self.infer_type(node.left)
        right_type = self.infer_type(node.right)

        # Satrlarni birlashtirish (+)
        if node.op == '+':
            if left_type == 'String' or right_type == 'String':
                left_c = self.transpile_expr(node.left)
                right_c = self.transpile_expr(node.right)
                # Agar tomonlardan biri satr bo'lmasa, uni satrga aylantiramiz
                if left_type != 'String':
                    left_c = self.wrap_to_string(node.left, left_c)
                if right_type != 'String':
                    right_c = self.wrap_to_string(node.right, right_c)
                return f"zf_str_concat({left_c}, {right_c})"

        left_c = self.transpile_expr(node.left)
        right_c = self.transpile_expr(node.right)

        if node.op == '**':
            return f"pow({left_c}, {right_c})"
        if node.op == 'and':
            return f"({left_c} && {right_c})"
        if node.op == 'or':
            return f"({left_c} || {right_c})"

        return f"({left_c} {node.op} {right_c})"

    def wrap_to_string(self, node: Node, expr_c: str) -> str:
        """Ifodani mos zf_str_* funksiyasi bilan o'raydi"""
        t = self.infer_type(node)
        if t == 'Int':
            return f"zf_str_int({expr_c})"
        if t == 'Float':
            return f"zf_str_float({expr_c})"
        if t == 'Bool':
            return f"zf_str_bool({expr_c})"
        return f"zf_str_int({expr_c})"

    def transpile_function_call(self, node: FunctionCall) -> str:
        """Funksiya chaqiruvini C ga aylantiradi"""
        if isinstance(node.callee, Identifier):
            name = node.callee.name

            # String(...) casting
            if name == 'String' and node.args:
                arg = node.args[0]
                arg_c = self.transpile_expr(arg)
                arg_t = self.infer_type(arg)
                if arg_t == 'Int':
                    return f"zf_str_int({arg_c})"
                if arg_t == 'Float':
                    return f"zf_str_float({arg_c})"
                if arg_t == 'Bool':
                    return f"zf_str_bool({arg_c})"
                if arg_t == 'String':
                    return arg_c
                return f"zf_str_int({arg_c})"

            # Int(...) casting
            if name == 'Int' and node.args:
                arg_c = self.transpile_expr(node.args[0])
                return f"zf_to_int({arg_c})"

            # Float(...) casting
            if name == 'Float' and node.args:
                arg_c = self.transpile_expr(node.args[0])
                return f"zf_to_float({arg_c})"

            # len(...)
            if name == 'len' and node.args:
                arg_c = self.transpile_expr(node.args[0])
                return f"((int64_t)strlen({arg_c}))"

            c_func_name = self.to_c_ident(name)
        else:
            c_func_name = self.transpile_expr(node.callee)

        args_c = [self.transpile_expr(a) for a in node.args]
        return f"{c_func_name}({', '.join(args_c)})"
