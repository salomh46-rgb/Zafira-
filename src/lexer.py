"""
Zafira Language - Lexer (Tokenizer)
Kodni o'qib, ma'noli tokenlarga bo'ladi.
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import List, Optional


class TokenType(Enum):
    # === LITERALS ===
    INT        = auto()   # 42
    FLOAT      = auto()   # 3.14
    STRING     = auto()   # "salom"
    BOOL       = auto()   # true / false
    NULL       = auto()   # null

    # === IDENTIFIERS & KEYWORDS ===
    IDENT      = auto()   # o'zgaruvchi nomi

    # ZAFIRA KALIT SO'ZLARI
    LET        = auto()   # let x = 5
    CONST      = auto()   # const PI = 3.14
    FN         = auto()   # fn qo'sh(a, b) { ... }
    RETURN     = auto()   # return natija
    IF         = auto()   # if shart { ... }
    ELSE       = auto()   # else { ... }
    WHILE      = auto()   # while shart { ... }
    FOR        = auto()   # for i in 0..10 { ... }
    IN         = auto()   # for i IN range
    STRUCT     = auto()   # struct Odam { ... }
    IMPORT     = auto()   # import sys.ai
    TRUE       = auto()
    FALSE      = auto()
    NULL_KW    = auto()

    # ZAFIRA O'ZIGA XOS
    SEAL       = auto()   # seal fn (qat'iy rejim)
    DRAFT      = auto()   # draft fn (erkin rejim)
    WHERE      = auto()   # where shart (invariant)
    RUN        = auto()   # run @gpu { ... }
    AT         = auto()   # @gpu, @npu, @auto
    ASYNC      = auto()   # async fn ...
    AWAIT      = auto()   # await ...

    # === OPERATORLAR ===
    PLUS       = auto()   # +
    MINUS      = auto()   # -
    STAR       = auto()   # *
    SLASH      = auto()   # /
    PERCENT    = auto()   # %
    POWER      = auto()   # **
    ASSIGN     = auto()   # =
    EQ         = auto()   # ==
    NEQ        = auto()   # !=
    LT         = auto()   # <
    GT         = auto()   # >
    LTE        = auto()   # <=
    GTE        = auto()   # >=
    AND        = auto()   # and
    OR         = auto()   # or
    NOT        = auto()   # not
    ARROW      = auto()   # ->
    DOTDOT     = auto()   # .. (range)
    DOT        = auto()   # .

    # === DELIMITERS ===
    LPAREN     = auto()   # (
    RPAREN     = auto()   # )
    LBRACE     = auto()   # {
    RBRACE     = auto()   # }
    LBRACKET   = auto()   # [
    RBRACKET   = auto()   # ]
    COMMA      = auto()   # ,
    COLON      = auto()   # :
    SEMICOLON  = auto()   # ;
    NEWLINE    = auto()   # \n

    # === MAXSUS ===
    EOF        = auto()
    UNKNOWN    = auto()


KEYWORDS = {
    'let': TokenType.LET,
    'const': TokenType.CONST,
    'fn': TokenType.FN,
    'return': TokenType.RETURN,
    'if': TokenType.IF,
    'else': TokenType.ELSE,
    'while': TokenType.WHILE,
    'for': TokenType.FOR,
    'in': TokenType.IN,
    'struct': TokenType.STRUCT,
    'import': TokenType.IMPORT,
    'true': TokenType.TRUE,
    'false': TokenType.FALSE,
    'null': TokenType.NULL_KW,
    'seal': TokenType.SEAL,
    'draft': TokenType.DRAFT,
    'where': TokenType.WHERE,
    'run': TokenType.RUN,
    'async': TokenType.ASYNC,
    'await': TokenType.AWAIT,
    'and': TokenType.AND,
    'or': TokenType.OR,
    'not': TokenType.NOT,
}


@dataclass
class Token:
    type: TokenType
    value: str
    line: int
    col: int

    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r}, L{self.line}:C{self.col})"


class LexerError(Exception):
    def __init__(self, msg: str, line: int, col: int):
        super().__init__(f"[Zafira Lexer Xatosi] {msg} (Qator: {line}, Ustun: {col})")
        self.line = line
        self.col = col


class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.col = 1
        self.tokens: List[Token] = []

    def _current(self) -> Optional[str]:
        return self.source[self.pos] if self.pos < len(self.source) else None

    def _peek(self, offset: int = 1) -> Optional[str]:
        p = self.pos + offset
        return self.source[p] if p < len(self.source) else None

    def _advance(self) -> str:
        ch = self.source[self.pos]
        self.pos += 1
        if ch == '\n':
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def _skip_whitespace(self):
        while self._current() in (' ', '\t', '\r'):
            self._advance()

    def _skip_comment(self):
        """// yoki /* */ izohlarni o'tkazib yuboradi"""
        if self._current() == '/' and self._peek() == '/':
            while self._current() and self._current() != '\n':
                self._advance()
        elif self._current() == '/' and self._peek() == '*':
            self._advance(); self._advance()
            while self._current():
                if self._current() == '*' and self._peek() == '/':
                    self._advance(); self._advance()
                    break
                self._advance()

    def _read_number(self) -> Token:
        start_col = self.col
        buf = ''
        is_float = False
        while self._current() and (self._current().isdigit() or self._current() == '_'):
            if self._current() != '_':
                buf += self._current()
            self._advance()
        if self._current() == '.' and self._peek() and self._peek().isdigit():
            is_float = True
            buf += self._advance()
            while self._current() and self._current().isdigit():
                buf += self._advance()
        tok_type = TokenType.FLOAT if is_float else TokenType.INT
        return Token(tok_type, buf, self.line, start_col)

    def _read_string(self) -> Token:
        start_col = self.col
        quote = self._advance()  # " yoki '
        buf = ''
        while self._current() and self._current() != quote:
            if self._current() == '\\':
                self._advance()
                esc = self._advance()
                buf += {'n': '\n', 't': '\t', '\\': '\\', '"': '"', "'": "'"}.get(esc, esc)
            else:
                buf += self._advance()
        if not self._current():
            raise LexerError("Tugallanmagan satr (string)", self.line, start_col)
        self._advance()  # yopuvchi quote
        return Token(TokenType.STRING, buf, self.line, start_col)

    def _read_ident(self) -> Token:
        start_col = self.col
        buf = ''
        while self._current() and (
            self._current().isalnum() or
            self._current() == '_' or
            (self._current() in ("'", "’", "`") and self._peek() and self._peek().isalpha())
        ):
            buf += self._advance()
        tok_type = KEYWORDS.get(buf, TokenType.IDENT)
        return Token(tok_type, buf, self.line, start_col)

    def tokenize(self) -> List[Token]:
        while self.pos < len(self.source):
            self._skip_whitespace()
            ch = self._current()
            if ch is None:
                break
            start_col = self.col

            # Izohlar
            if ch == '/' and (self._peek() == '/' or self._peek() == '*'):
                self._skip_comment()
                continue

            # Yangi qator
            if ch == '\n':
                self._advance()
                self.tokens.append(Token(TokenType.NEWLINE, '\\n', self.line - 1, start_col))
                continue

            # Sonlar
            if ch.isdigit():
                self.tokens.append(self._read_number())
                continue

            # Satrlar
            if ch in ('"', "'"):
                self.tokens.append(self._read_string())
                continue

            # @ (hardware direktivalar)
            if ch == '@':
                self._advance()
                buf = ''
                while self._current() and (self._current().isalnum() or self._current() == '_'):
                    buf += self._advance()
                self.tokens.append(Token(TokenType.AT, '@' + buf, self.line, start_col))
                continue

            # Identifikatorlar va kalit so'zlar
            if ch.isalpha() or ch == '_':
                self.tokens.append(self._read_ident())
                continue

            # Ko'p belgilar
            two = ch + (self._peek() or '')
            if two == '**':
                self._advance(); self._advance()
                self.tokens.append(Token(TokenType.POWER, '**', self.line, start_col))
            elif two == '==':
                self._advance(); self._advance()
                self.tokens.append(Token(TokenType.EQ, '==', self.line, start_col))
            elif two == '!=':
                self._advance(); self._advance()
                self.tokens.append(Token(TokenType.NEQ, '!=', self.line, start_col))
            elif two == '<=':
                self._advance(); self._advance()
                self.tokens.append(Token(TokenType.LTE, '<=', self.line, start_col))
            elif two == '>=':
                self._advance(); self._advance()
                self.tokens.append(Token(TokenType.GTE, '>=', self.line, start_col))
            elif two == '->':
                self._advance(); self._advance()
                self.tokens.append(Token(TokenType.ARROW, '->', self.line, start_col))
            elif two == '..':
                self._advance(); self._advance()
                self.tokens.append(Token(TokenType.DOTDOT, '..', self.line, start_col))
            # Yagona belgilar
            elif ch == '+':
                self._advance()
                self.tokens.append(Token(TokenType.PLUS, '+', self.line, start_col))
            elif ch == '-':
                self._advance()
                self.tokens.append(Token(TokenType.MINUS, '-', self.line, start_col))
            elif ch == '*':
                self._advance()
                self.tokens.append(Token(TokenType.STAR, '*', self.line, start_col))
            elif ch == '/':
                self._advance()
                self.tokens.append(Token(TokenType.SLASH, '/', self.line, start_col))
            elif ch == '%':
                self._advance()
                self.tokens.append(Token(TokenType.PERCENT, '%', self.line, start_col))
            elif ch == '=':
                self._advance()
                self.tokens.append(Token(TokenType.ASSIGN, '=', self.line, start_col))
            elif ch == '<':
                self._advance()
                self.tokens.append(Token(TokenType.LT, '<', self.line, start_col))
            elif ch == '>':
                self._advance()
                self.tokens.append(Token(TokenType.GT, '>', self.line, start_col))
            elif ch == '(':
                self._advance()
                self.tokens.append(Token(TokenType.LPAREN, '(', self.line, start_col))
            elif ch == ')':
                self._advance()
                self.tokens.append(Token(TokenType.RPAREN, ')', self.line, start_col))
            elif ch == '{':
                self._advance()
                self.tokens.append(Token(TokenType.LBRACE, '{', self.line, start_col))
            elif ch == '}':
                self._advance()
                self.tokens.append(Token(TokenType.RBRACE, '}', self.line, start_col))
            elif ch == '[':
                self._advance()
                self.tokens.append(Token(TokenType.LBRACKET, '[', self.line, start_col))
            elif ch == ']':
                self._advance()
                self.tokens.append(Token(TokenType.RBRACKET, ']', self.line, start_col))
            elif ch == ',':
                self._advance()
                self.tokens.append(Token(TokenType.COMMA, ',', self.line, start_col))
            elif ch == ':':
                self._advance()
                self.tokens.append(Token(TokenType.COLON, ':', self.line, start_col))
            elif ch == ';':
                self._advance()
                self.tokens.append(Token(TokenType.SEMICOLON, ';', self.line, start_col))
            elif ch == '.':
                self._advance()
                self.tokens.append(Token(TokenType.DOT, '.', self.line, start_col))
            else:
                raise LexerError(f"Noma'lum belgi: {ch!r}", self.line, start_col)

        self.tokens.append(Token(TokenType.EOF, '', self.line, self.col))
        return self.tokens
