from enum import Enum, auto


class TokenType(Enum):
    # Keywords
    VAR = auto()
    IF = auto()
    ELSE = auto()
    WHILE = auto()
    PRINT = auto()

    # Identifiers and literals
    IDENTIFIER = auto()
    NUMBER = auto()

    # Operators
    PLUS = auto()
    MINUS = auto()
    MUL = auto()
    DIV = auto()
    ASSIGN = auto()
    EQ = auto()  # ==
    NEQ = auto()  # !=
    LT = auto()  # <
    GT = auto()  # >
    LTE = auto()  # <=
    GTE = auto()  # >=
    AND = auto()  # &&
    OR = auto()  # ||

    # Punctuation
    SEMICOLON = auto()
    LPAREN = auto()  # (
    RPAREN = auto()  # )
    LBRACE = auto()  # {
    RBRACE = auto()  # }

    # End of input
    EOF = auto()


class Token:
    def __init__(self, type: TokenType, value: str = None, lineno: int = None, col: int = None):
        self.type = type
        self.value = value
        self.lineno = lineno
        self.col = col

    def __repr__(self):
        return f"Token({self.type.name}, {repr(self.value)})"