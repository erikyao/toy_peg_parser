import pytest

from src.peg_token import Token as Token, TokenType as TokenType
from src.peg_parser import ToyPEGParser

def test_program():
    # var x = 5;
    tokens = [
        Token(TokenType.VAR, 'var', 1, 1),
        Token(TokenType.IDENTIFIER, 'x', 1, 5),
        Token(TokenType.ASSIGN, '=', 1, 7),
        Token(TokenType.NUMBER, '5', 1, 9),
        Token(TokenType.SEMICOLON, ';', 1, 10),
        Token(TokenType.EOF)
    ]
    parser = ToyPEGParser(tokens)
    ast = parser.program()
    assert ast['type'] == 'program'
    assert len(ast['body']) == 1
    assert ast['body'][0]['type'] == 'var_decl'

def test_empty_program():
    tokens = [Token(TokenType.EOF)]
    parser = ToyPEGParser(tokens)
    with pytest.raises(SyntaxError):
        parser.program()

def test_var_decl():
    # var x;
    tokens = [
        Token(TokenType.VAR, 'var'),
        Token(TokenType.IDENTIFIER, 'x'),
        Token(TokenType.SEMICOLON, ';'),
        Token(TokenType.EOF)
    ]
    parser = ToyPEGParser(tokens)
    ast = parser.var_decl()
    assert ast['type'] == 'var_decl'
    assert ast['name'] == 'x'
    assert ast['init'] == {}

def test_var_decl_with_init():
    # var x = 5;
    tokens = [
        Token(TokenType.VAR, 'var'),
        Token(TokenType.IDENTIFIER, 'x'),
        Token(TokenType.ASSIGN, '='),
        Token(TokenType.NUMBER, '5'),
        Token(TokenType.SEMICOLON, ';'),
        Token(TokenType.EOF)
    ]
    parser = ToyPEGParser(tokens)
    ast = parser.var_decl()
    assert ast['type'] == 'var_decl'
    assert ast['name'] == 'x'
    assert ast['init']['type'] == 'number'
    assert ast['init']['value'] == 5.0

def test_assignment():
    # x = 5;
    tokens = [
        Token(TokenType.IDENTIFIER, 'x'),
        Token(TokenType.ASSIGN, '='),
        Token(TokenType.NUMBER, '5'),
        Token(TokenType.SEMICOLON, ';'),
        Token(TokenType.EOF)
    ]
    parser = ToyPEGParser(tokens)
    ast = parser.assignment()
    assert ast['type'] == 'assignment'
    assert ast['name'] == 'x'
    assert ast['value']['type'] == 'number'

def test_if_stmt():
    # if (x > 0) print x;
    tokens = [
        Token(TokenType.IF, 'if'),
        Token(TokenType.LPAREN, '('),
        Token(TokenType.IDENTIFIER, 'x'),
        Token(TokenType.GT, '>'),
        Token(TokenType.NUMBER, '0'),
        Token(TokenType.RPAREN, ')'),
        Token(TokenType.PRINT, 'print'),
        Token(TokenType.IDENTIFIER, 'x'),
        Token(TokenType.SEMICOLON, ';'),
        Token(TokenType.EOF)
    ]
    parser = ToyPEGParser(tokens)
    ast = parser.if_stmt()
    assert ast['type'] == 'if_stmt'
    assert ast['cond']['type'] == 'binary_expr'
    assert ast['if-body']['type'] == 'print_stmt'
    assert ast['else-body'] == {}

def test_if_else_stmt():
    # if (x > 0) print x; else print 0;
    tokens = [
        Token(TokenType.IF, 'if'),
        Token(TokenType.LPAREN, '('),
        Token(TokenType.IDENTIFIER, 'x'),
        Token(TokenType.GT, '>'),
        Token(TokenType.NUMBER, '0'),
        Token(TokenType.RPAREN, ')'),
        Token(TokenType.PRINT, 'print'),
        Token(TokenType.IDENTIFIER, 'x'),
        Token(TokenType.SEMICOLON, ';'),
        Token(TokenType.ELSE, 'else'),
        Token(TokenType.PRINT, 'print'),
        Token(TokenType.NUMBER, '0'),
        Token(TokenType.SEMICOLON, ';'),
        Token(TokenType.EOF)
    ]
    parser = ToyPEGParser(tokens)
    ast = parser.if_stmt()
    assert ast['type'] == 'if_stmt'
    assert ast['else-body']['type'] == 'print_stmt'

def test_while_loop():
    # while ( x < 10 ) {
    #   print x;
    # }
    tokens = [
        Token(TokenType.WHILE, 'while'),
        Token(TokenType.LPAREN, '('),
        Token(TokenType.IDENTIFIER, 'x'),
        Token(TokenType.LT, '<'),
        Token(TokenType.NUMBER, '10'),
        Token(TokenType.RPAREN, ')'),
        Token(TokenType.LBRACE, '{'),
        Token(TokenType.PRINT, 'print'),
        Token(TokenType.IDENTIFIER, 'x'),
        Token(TokenType.SEMICOLON, ';'),
        Token(TokenType.RBRACE, '}'),
        Token(TokenType.EOF)
    ]
    parser = ToyPEGParser(tokens)
    ast = parser.while_loop()
    assert ast['type'] == 'while_loop'
    assert ast['cond']['type'] == 'binary_expr'
    assert ast['body']['type'] == 'block'

def test_print_stmt():
    # print x;
    tokens = [
        Token(TokenType.PRINT, 'print'),
        Token(TokenType.IDENTIFIER, 'x'),
        Token(TokenType.SEMICOLON, ';'),
        Token(TokenType.EOF)
    ]
    parser = ToyPEGParser(tokens)
    ast = parser.print_stmt()
    assert ast['type'] == 'print_stmt'
    assert ast['expression']['type'] == 'identifier'

def test_block():
    # {
    #   print x;
    # }
    tokens = [
        Token(TokenType.LBRACE, '{'),
        Token(TokenType.PRINT, 'print'),
        Token(TokenType.IDENTIFIER, 'x'),
        Token(TokenType.SEMICOLON, ';'),
        Token(TokenType.RBRACE, '}'),
        Token(TokenType.EOF)
    ]
    parser = ToyPEGParser(tokens)
    ast = parser.block()
    assert ast['type'] == 'block'
    assert len(ast['body']) == 1
    assert ast['body'][0]['type'] == 'print_stmt'

def test_expression():
    # x + 5
    tokens = [
        Token(TokenType.IDENTIFIER, 'x'),
        Token(TokenType.PLUS, '+'),
        Token(TokenType.NUMBER, '5'),
        Token(TokenType.EOF)
    ]
    parser = ToyPEGParser(tokens)
    ast = parser.expression()
    assert ast['type'] == 'binary_expr'
    assert ast['op'] == '+'

def test_logical_or():
    # x || y
    tokens = [
        Token(TokenType.IDENTIFIER, 'x'),
        Token(TokenType.OR, '||'),
        Token(TokenType.IDENTIFIER, 'y'),
        Token(TokenType.EOF)
    ]
    parser = ToyPEGParser(tokens)
    ast = parser.logical_or()
    assert ast['type'] == 'binary_expr'
    assert ast['op'] == '||'

def test_logical_and():
    # x && y
    tokens = [
        Token(TokenType.IDENTIFIER, 'x'),
        Token(TokenType.AND, '&&'),
        Token(TokenType.IDENTIFIER, 'y'),
        Token(TokenType.EOF)
    ]
    parser = ToyPEGParser(tokens)
    ast = parser.logical_and()
    assert ast['type'] == 'binary_expr'
    assert ast['op'] == '&&'

def test_equality():
    # x == y
    tokens = [
        Token(TokenType.IDENTIFIER, 'x'),
        Token(TokenType.EQ, '=='),
        Token(TokenType.IDENTIFIER, 'y'),
        Token(TokenType.EOF)
    ]
    parser = ToyPEGParser(tokens)
    ast = parser.equality()
    assert ast['type'] == 'binary_expr'
    assert ast['op'] == '=='

def test_relational():
    # x < y
    tokens = [
        Token(TokenType.IDENTIFIER, 'x'),
        Token(TokenType.LT, '<'),
        Token(TokenType.IDENTIFIER, 'y'),
        Token(TokenType.EOF)
    ]
    parser = ToyPEGParser(tokens)
    ast = parser.relational()
    assert ast['type'] == 'binary_expr'
    assert ast['op'] == '<'

def test_additive():
    # x + y
    tokens = [
        Token(TokenType.IDENTIFIER, 'x'),
        Token(TokenType.PLUS, '+'),
        Token(TokenType.IDENTIFIER, 'y'),
        Token(TokenType.EOF)
    ]
    parser = ToyPEGParser(tokens)
    ast = parser.additive()
    assert ast['type'] == 'binary_expr'
    assert ast['op'] == '+'

def test_multiplicative():
    # x * y
    tokens = [
        Token(TokenType.IDENTIFIER, 'x'),
        Token(TokenType.MUL, '*'),
        Token(TokenType.IDENTIFIER, 'y'),
        Token(TokenType.EOF)
    ]
    parser = ToyPEGParser(tokens)
    ast = parser.multiplicative()
    assert ast['type'] == 'binary_expr'
    assert ast['op'] == '*'

def test_primary_number():
    # 42
    tokens = [Token(TokenType.NUMBER, '42'), Token(TokenType.EOF)]
    parser = ToyPEGParser(tokens)
    ast = parser.primary()
    assert ast['type'] == 'number'
    assert ast['value'] == 42.0

def test_primary_identifier():
    # x
    tokens = [Token(TokenType.IDENTIFIER, 'x'), Token(TokenType.EOF)]
    parser = ToyPEGParser(tokens)
    ast = parser.primary()
    assert ast['type'] == 'identifier'
    assert ast['name'] == 'x'

def test_primary_parenthesized():
    # (x)
    tokens = [
        Token(TokenType.LPAREN, '('),
        Token(TokenType.IDENTIFIER, 'x'),
        Token(TokenType.RPAREN, ')'),
        Token(TokenType.EOF)
    ]
    parser = ToyPEGParser(tokens)
    ast = parser.primary()
    assert ast['type'] == 'identifier'
    assert ast['name'] == 'x'

def test_primary_unary():
    # -5
    tokens = [
        Token(TokenType.MINUS, '-'),
        Token(TokenType.NUMBER, '5'),
        Token(TokenType.EOF)
    ]
    parser = ToyPEGParser(tokens)
    ast = parser.primary()
    assert ast['type'] == 'unary_expr'
    assert ast['op'] == '-'
    assert ast['argument']['type'] == 'number'

def test_syntax_error_missing_semicolon():
    # var x = 5
    tokens = [
        Token(TokenType.VAR, 'var'),
        Token(TokenType.IDENTIFIER, 'x'),
        Token(TokenType.ASSIGN, '='),
        Token(TokenType.NUMBER, '5'),
        Token(TokenType.EOF)
    ]
    parser = ToyPEGParser(tokens)
    with pytest.raises(SyntaxError):
        parser.var_decl()

def test_syntax_error_missing_paren():
    # if x > 0)
    tokens = [
        Token(TokenType.IF, 'if'),
        Token(TokenType.IDENTIFIER, 'x'),
        Token(TokenType.GT, '>'),
        Token(TokenType.NUMBER, '0'),
        Token(TokenType.RPAREN, ')'),
        Token(TokenType.EOF)
    ]
    parser = ToyPEGParser(tokens)
    with pytest.raises(SyntaxError):
        parser.if_stmt()