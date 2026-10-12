"""
Zafira Language - Parser
Tokenlar oqimidan AST (Abstract Syntax Tree) daraxti yasaydi.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Any
from src.lexer import Token, TokenType


# ─────────────────────── AST TUGUNLARI ───────────────────────

@dataclass
class Node:
    """Barcha AST tugunlarining asosi"""
    pass

# --- Iboralar (Expressions) ---
@dataclass
class NumberLiteral(Node):
    value: float

@dataclass
class StringLiteral(Node):
    value: str

@dataclass
class BoolLiteral(Node):
    value: bool

@dataclass
class NullLiteral(Node):
    pass

@dataclass
class Identifier(Node):
    name: str

@dataclass
class BinaryOp(Node):
    left: Node
    op: str
    right: Node

@dataclass
class UnaryOp(Node):
    op: str
    operand: Node

@dataclass
class FunctionCall(Node):
    callee: Node         # Identifier yoki MemberAccess
    args: List[Node]

@dataclass
class MemberAccess(Node):
    obj: Node
    member: str

@dataclass
class IndexAccess(Node):
    obj: Node
    index: Node

@dataclass
class ListLiteral(Node):
    elements: List[Node]

@dataclass
class RangeExpr(Node):
    start: Node
    end: Node

# --- Operatorlar (Statements) ---
@dataclass
class LetStatement(Node):
    name: str
    type_hint: Optional[str]
    value: Optional[Node]

@dataclass
class ConstStatement(Node):
    name: str
    type_hint: Optional[str]
    value: Node

@dataclass
class AssignStatement(Node):
    target: Node
    value: Node

@dataclass
class ReturnStatement(Node):
    value: Optional[Node]

@dataclass
class IfStatement(Node):
    condition: Node
    then_block: List[Node]
    else_block: Optional[List[Node]]

@dataclass
class WhileStatement(Node):
    condition: Node
    body: List[Node]

@dataclass
class ForStatement(Node):
    var: str
    iterable: Node
    body: List[Node]

@dataclass
class Block(Node):
    statements: List[Node]

@dataclass
class FunctionDef(Node):
    name: str
    params: List[tuple]        # (ism, tip_maslahat)
    return_type: Optional[str]
    body: List[Node]
    mode: str                  # 'draft' | 'seal'
    where_clause: Optional[Node]

@dataclass
class StructDef(Node):
    name: str
    fields: List[tuple]        # (ism, tip)

@dataclass
class ImportStatement(Node):
    path: str                  # 'sys.ai' | 'py.torch'

@dataclass
class RunBlock(Node):
    target: str                # '@gpu' | '@npu' | '@auto'
    body: List[Node]

@dataclass
class ExprStatement(Node):
    expr: Node

@dataclass
class Program(Node):
    body: List[Node]


# ─────────────────────── PARSER ───────────────────────

class ParseError(Exception):
    def __init__(self, msg: str, token: Token):
        super().__init__(f"[Zafira Parser Xatosi] {msg} (Qator: {token.line}, Ustun: {token.col})")
        self.token = token


class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = [t for t in tokens if t.type != TokenType.NEWLINE]
        self.pos = 0

    def _current(self) -> Token:
        return self.tokens[self.pos]

    def _peek(self, offset: int = 1) -> Token:
        p = self.pos + offset
        return self.tokens[p] if p < len(self.tokens) else self.tokens[-1]

    def _advance(self) -> Token:
        t = self.tokens[self.pos]
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
        return t

    def _expect(self, tok_type: TokenType) -> Token:
        t = self._current()
        if t.type != tok_type:
            raise ParseError(f"'{tok_type.name}' kutilgan edi, lekin '{t.type.name}' ({t.value!r}) topildi", t)
        return self._advance()

    def _match(self, *types: TokenType) -> bool:
        return self._current().type in types

    def _skip_newlines(self):
        while self._match(TokenType.NEWLINE, TokenType.SEMICOLON):
            self._advance()

    # ─── TOP-LEVEL ───

    def parse(self) -> Program:
        stmts = []
        while not self._match(TokenType.EOF):
            self._skip_newlines()
            if self._match(TokenType.EOF):
                break
            stmts.append(self._parse_statement())
        return Program(body=stmts)

    # ─── STATEMENTS ───

    def _parse_statement(self) -> Node:
        t = self._current()

        if t.type == TokenType.LET:
            return self._parse_let()
        if t.type == TokenType.CONST:
            return self._parse_const()
        if t.type == TokenType.RETURN:
            return self._parse_return()
        if t.type == TokenType.IF:
            return self._parse_if()
        if t.type == TokenType.WHILE:
            return self._parse_while()
        if t.type == TokenType.FOR:
            return self._parse_for()
        if t.type == TokenType.IMPORT:
            return self._parse_import()
        if t.type == TokenType.RUN:
            return self._parse_run()
        if t.type == TokenType.STRUCT:
            return self._parse_struct()
        if t.type in (TokenType.FN, TokenType.SEAL, TokenType.DRAFT):
            return self._parse_function()
        if t.type == TokenType.SEMICOLON:
            self._advance()
            return ExprStatement(NullLiteral())

        # Tayinlash yoki ifoda-operator
        return self._parse_expr_or_assign()

    def _parse_let(self) -> LetStatement:
        self._advance()  # let
        name = self._expect(TokenType.IDENT).value
        type_hint = None
        if self._match(TokenType.COLON):
            self._advance()
            type_hint = self._expect(TokenType.IDENT).value
        value = None
        if self._match(TokenType.ASSIGN):
            self._advance()
            value = self._parse_expr()
        return LetStatement(name=name, type_hint=type_hint, value=value)

    def _parse_const(self) -> ConstStatement:
        self._advance()  # const
        name = self._expect(TokenType.IDENT).value
        type_hint = None
        if self._match(TokenType.COLON):
            self._advance()
            type_hint = self._expect(TokenType.IDENT).value
        self._expect(TokenType.ASSIGN)
        value = self._parse_expr()
        return ConstStatement(name=name, type_hint=type_hint, value=value)

    def _parse_return(self) -> ReturnStatement:
        self._advance()  # return
        value = None
        if not self._match(TokenType.EOF, TokenType.RBRACE, TokenType.NEWLINE, TokenType.SEMICOLON):
            value = self._parse_expr()
        return ReturnStatement(value=value)

    def _parse_if(self) -> IfStatement:
        self._advance()  # if
        condition = self._parse_expr()
        then_block = self._parse_block()
        else_block = None
        if self._match(TokenType.ELSE):
            self._advance()
            if self._match(TokenType.IF):
                else_block = [self._parse_if()]
            else:
                else_block = self._parse_block()
        return IfStatement(condition=condition, then_block=then_block, else_block=else_block)

    def _parse_while(self) -> WhileStatement:
        self._advance()  # while
        condition = self._parse_expr()
        body = self._parse_block()
        return WhileStatement(condition=condition, body=body)

    def _parse_for(self) -> ForStatement:
        self._advance()  # for
        var = self._expect(TokenType.IDENT).value
        self._expect(TokenType.IN)
        iterable = self._parse_expr()
        body = self._parse_block()
        return ForStatement(var=var, iterable=iterable, body=body)

    def _parse_import(self) -> ImportStatement:
        self._advance()  # import
        path = self._expect(TokenType.IDENT).value
        while self._match(TokenType.DOT):
            self._advance()
            path += '.' + self._expect(TokenType.IDENT).value
        return ImportStatement(path=path)

    def _parse_run(self) -> RunBlock:
        self._advance()  # run
        target = self._expect(TokenType.AT).value
        body = self._parse_block()
        return RunBlock(target=target, body=body)

    def _parse_struct(self) -> StructDef:
        self._advance()  # struct
        name = self._expect(TokenType.IDENT).value
        self._expect(TokenType.LBRACE)
        fields = []
        while not self._match(TokenType.RBRACE, TokenType.EOF):
            self._skip_newlines()
            if self._match(TokenType.RBRACE):
                break
            fname = self._expect(TokenType.IDENT).value
            self._expect(TokenType.COLON)
            ftype = self._expect(TokenType.IDENT).value
            fields.append((fname, ftype))
            if self._match(TokenType.COMMA):
                self._advance()
        self._expect(TokenType.RBRACE)
        return StructDef(name=name, fields=fields)

    def _parse_function(self) -> FunctionDef:
        mode = 'draft'
        if self._match(TokenType.SEAL):
            mode = 'seal'; self._advance()
        elif self._match(TokenType.DRAFT):
            mode = 'draft'; self._advance()
        self._expect(TokenType.FN)
        name = self._expect(TokenType.IDENT).value
        self._expect(TokenType.LPAREN)
        params = []
        while not self._match(TokenType.RPAREN, TokenType.EOF):
            pname = self._expect(TokenType.IDENT).value
            ptype = None
            if self._match(TokenType.COLON):
                self._advance()
                ptype = self._expect(TokenType.IDENT).value
            params.append((pname, ptype))
            if self._match(TokenType.COMMA):
                self._advance()
        self._expect(TokenType.RPAREN)
        return_type = None
        if self._match(TokenType.ARROW):
            self._advance()
            return_type = self._expect(TokenType.IDENT).value
        where_clause = None
        if self._match(TokenType.WHERE):
            self._advance()
            where_clause = self._parse_expr()
        body = self._parse_block()
        return FunctionDef(name=name, params=params, return_type=return_type,
                           body=body, mode=mode, where_clause=where_clause)

    def _parse_block(self) -> List[Node]:
        self._expect(TokenType.LBRACE)
        stmts = []
        self._skip_newlines()
        while not self._match(TokenType.RBRACE, TokenType.EOF):
            self._skip_newlines()
            if self._match(TokenType.RBRACE):
                break
            stmts.append(self._parse_statement())
            self._skip_newlines()
        self._expect(TokenType.RBRACE)
        return stmts

    def _parse_expr_or_assign(self) -> Node:
        expr = self._parse_expr()
        if self._match(TokenType.ASSIGN):
            self._advance()
            value = self._parse_expr()
            return AssignStatement(target=expr, value=value)
        return ExprStatement(expr=expr)

    # ─── EXPRESSIONS (Pratt Parsing) ───

    def _parse_expr(self) -> Node:
        return self._parse_or()

    def _parse_or(self) -> Node:
        left = self._parse_and()
        while self._match(TokenType.OR):
            op = self._advance().value
            right = self._parse_and()
            left = BinaryOp(left=left, op=op, right=right)
        return left

    def _parse_and(self) -> Node:
        left = self._parse_comparison()
        while self._match(TokenType.AND):
            op = self._advance().value
            right = self._parse_comparison()
            left = BinaryOp(left=left, op=op, right=right)
        return left

    def _parse_comparison(self) -> Node:
        left = self._parse_additive()
        while self._match(TokenType.EQ, TokenType.NEQ, TokenType.LT,
                           TokenType.GT, TokenType.LTE, TokenType.GTE):
            op = self._advance().value
            right = self._parse_additive()
            left = BinaryOp(left=left, op=op, right=right)
        return left

    def _parse_additive(self) -> Node:
        left = self._parse_multiplicative()
        while self._match(TokenType.PLUS, TokenType.MINUS):
            op = self._advance().value
            right = self._parse_multiplicative()
            left = BinaryOp(left=left, op=op, right=right)
        return left

    def _parse_multiplicative(self) -> Node:
        left = self._parse_power()
        while self._match(TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            op = self._advance().value
            right = self._parse_power()
            left = BinaryOp(left=left, op=op, right=right)
        return left

    def _parse_power(self) -> Node:
        left = self._parse_unary()
        if self._match(TokenType.POWER):
            op = self._advance().value
            right = self._parse_power()  # o'ngdan assotsiatsiya
            return BinaryOp(left=left, op=op, right=right)
        return left

    def _parse_unary(self) -> Node:
        if self._match(TokenType.MINUS):
            op = self._advance().value
            return UnaryOp(op=op, operand=self._parse_unary())
        if self._match(TokenType.NOT):
            op = self._advance().value
            return UnaryOp(op=op, operand=self._parse_unary())
        return self._parse_postfix()

    def _parse_postfix(self) -> Node:
        node = self._parse_primary()
        while True:
            if self._match(TokenType.DOT):
                self._advance()
                member = self._expect(TokenType.IDENT).value
                node = MemberAccess(obj=node, member=member)
            elif self._match(TokenType.LPAREN):
                self._advance()
                args = []
                while not self._match(TokenType.RPAREN, TokenType.EOF):
                    args.append(self._parse_expr())
                    if self._match(TokenType.COMMA):
                        self._advance()
                self._expect(TokenType.RPAREN)
                node = FunctionCall(callee=node, args=args)
            elif self._match(TokenType.LBRACKET):
                self._advance()
                index = self._parse_expr()
                self._expect(TokenType.RBRACKET)
                node = IndexAccess(obj=node, index=index)
            else:
                break
        return node

    def _parse_primary(self) -> Node:
        t = self._current()

        if t.type == TokenType.INT:
            self._advance()
            num = NumberLiteral(value=int(t.value))
            if self._match(TokenType.DOTDOT):
                self._advance()
                end = self._parse_primary()
                return RangeExpr(start=num, end=end)
            return num

        if t.type == TokenType.FLOAT:
            self._advance()
            return NumberLiteral(value=float(t.value))

        if t.type == TokenType.STRING:
            self._advance()
            return StringLiteral(value=t.value)

        if t.type == TokenType.TRUE:
            self._advance()
            return BoolLiteral(value=True)

        if t.type == TokenType.FALSE:
            self._advance()
            return BoolLiteral(value=False)

        if t.type == TokenType.NULL_KW:
            self._advance()
            return NullLiteral()

        if t.type == TokenType.IDENT:
            self._advance()
            ident = Identifier(name=t.value)
            if self._match(TokenType.DOTDOT):
                self._advance()
                end = self._parse_primary()
                return RangeExpr(start=ident, end=end)
            return ident

        if t.type == TokenType.LPAREN:
            self._advance()
            expr = self._parse_expr()
            self._expect(TokenType.RPAREN)
            return expr

        if t.type == TokenType.LBRACKET:
            self._advance()
            elements = []
            while not self._match(TokenType.RBRACKET, TokenType.EOF):
                elements.append(self._parse_expr())
                if self._match(TokenType.COMMA):
                    self._advance()
            self._expect(TokenType.RBRACKET)
            return ListLiteral(elements=elements)

        raise ParseError(f"Kutilmagan token: '{t.value}' ({t.type.name})", t)
