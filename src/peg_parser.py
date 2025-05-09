from src.peg_token import Token, TokenType


class ToyPEGParser:
    def __init__(self, _tokens: list[Token]):
        self.tokens = _tokens
        self.pos = 0
        self.current_token = _tokens[0] if _tokens else Token(TokenType.EOF)

    def advance_to_next_token(self) -> Token:
        self.pos += 1
        if self.pos < len(self.tokens):
            self.current_token = self.tokens[self.pos]
        else:
            self.current_token = Token(TokenType.EOF)
        return self.current_token

    def consume_token(self, token_type, value=None) -> Token | None:
        if ((self.current_token.type == token_type) and
                (value is None or self.current_token.value == value)):
            consumed_token = self.current_token
            self.advance_to_next_token()
            return consumed_token
        return None

    def consume_token_or_fail(self, token_type, value=None, err_msg=None) -> Token:
        token = self.consume_token(token_type, value)
        if token is None:  # not actually consumed, so no need to backtrack to the last token
            expected = value if value else token_type.name
            found = self.current_token.value or self.current_token.type.name
            raise SyntaxError(
                f"{err_msg or 'Syntax error'}. Expected {expected}, found {found} "
                f"at line {self.current_token.lineno}:{self.current_token.col}"
            )
        return token

    # PEG combinators

    # We require every "symbol()" function returns a non-None result, or raise a SyntaxError
    # We require every "combinator()" function returns a list of non-None result, an empty list, or raise a SyntaxError

    def parse_sequence(self, *symbols) -> list[dict]:
        if not symbols:
            raise SyntaxError("Syntax error. Empty sequence.")

        start_pos = self.pos
        start_token = self.current_token

        results = []
        for symbol in symbols:
            try:
                result = symbol()
            except SyntaxError as se:
                # one rule fails with raising SyntaxError, the whole sequence fails, and we must roll back
                self.pos = start_pos
                self.current_token = start_token
                raise SyntaxError("Syntax error. One symbol parsing failed within sequence.") from se
            else:
                results.append(result)
        return results

    def parse_ordered_choice(self, *symbols) -> list[dict]:
        if not symbols:
            raise SyntaxError("Syntax error. Empty ordered choice.")

        start_pos = self.pos
        start_token = self.current_token

        for symbol in symbols:
            try:
                result = symbol()
            except SyntaxError:
                # rollback
                self.pos = start_pos
                self.current_token = start_token
                continue  # continue to the next symbol specified in the choice
            else:
                return [result]  # first succeed, first return
        return []

    def parse_zero_or_more(self, symbol) -> list[dict]:
        results = []
        while True:
            start_pos = self.pos
            start_token = self.current_token

            try:
                result = symbol()
            except SyntaxError:
                # rollback
                self.pos = start_pos
                self.current_token = start_token
                return results  # failure terminates the current parsing, return directly
            else:
                results.append(result)
                if start_pos == self.pos:  # Prevent infinite loops (should be rare)
                    return results

    def parse_one_or_more(self, symbol) -> list[dict]:
        start_pos = self.pos
        start_token = self.current_token

        try:
            first_result = symbol()
        except SyntaxError as se:
            self.pos = start_pos
            self.current_token = start_token
            raise SyntaxError("Syntax error. 1st symbol parsing failed in 'one_or_more'.") from se

        if not first_result:
            return []

        if isinstance(first_result, dict):
            first_result = [first_result]

        rest_results = self.parse_zero_or_more(symbol)
        if not rest_results:
            return first_result

        if isinstance(rest_results, dict):
            rest_results = [rest_results]

        return first_result + rest_results

    def parse_optional(self, symbol) -> list[dict]:
        start_pos = self.pos
        start_token = self.current_token

        try:
            result = symbol()
        except SyntaxError:
            # rollback
            self.pos = start_pos
            self.current_token = start_token
            return []
        else:
            return result

    # LHS Symbols

    def program(self) -> dict:
        """program ::= statement+"""

        stmt_results = self.parse_one_or_more(self.statement)
        if not stmt_results:
            raise SyntaxError("Empty program")
        return {'type': 'program', 'body': stmt_results}

    def statement(self) -> dict:
        """statement ::= var_decl | assignment | if_stmt | while_loop | print_stmt | block"""

        choice_results = self.parse_ordered_choice(
            self.var_decl,
            self.assignment,
            self.if_stmt,
            self.while_loop,
            self.print_stmt,
            self.block
        )

        if not choice_results:
            raise SyntaxError("Expected statement")
        return choice_results[0]

    def block(self) -> dict:
        """block ::= '{' statement* '}'"""

        self.consume_token_or_fail(TokenType.LBRACE, '{', "Expected '{' to start block")
        stmt_results = self.parse_zero_or_more(self.statement)
        self.consume_token_or_fail(TokenType.RBRACE, '}', "Expected '}' to end block")
        return {'type': 'block', 'body': stmt_results}

    def var_decl(self) -> dict:
        """var_decl ::= 'var' IDENTIFIER ('=' expression)? ';'"""

        start_pos = self.pos
        start_token = self.current_token

        self.consume_token_or_fail(TokenType.VAR, 'var')
        id_token = self.consume_token_or_fail(TokenType.IDENTIFIER, None, "Expected variable name in declaration")

        expr_result = {}  # if declaration is not initialized, this empty dict is used to represent emtpy initialization
        if self.consume_token(TokenType.ASSIGN, '='):
            try:
                expr_result = self.expression()
            except SyntaxError as se:
                self.pos = start_pos
                self.current_token = start_token
                raise SyntaxError("Expected expression after '=' in declaration") from se

        self.consume_token_or_fail(TokenType.SEMICOLON, ';', "Expected ';' after declaration")
        return {'type': 'var_decl', 'name': id_token.value, 'init': expr_result}

    def assignment(self) -> dict:
        """assignment ::= IDENTIFIER '=' expression ';'"""

        start_pos = self.pos
        start_token = self.current_token

        id_token = self.consume_token_or_fail(TokenType.IDENTIFIER, None, "Expected variable name in assignment")
        self.consume_token_or_fail(TokenType.ASSIGN, '=', "Expected '=' in assignment")

        try:
            expr_result = self.expression()
        except SyntaxError as se:
            self.pos = start_pos
            self.current_token = start_token
            raise SyntaxError("Expected expression in assignment") from se
        else:
            self.consume_token_or_fail(TokenType.SEMICOLON, ';', "Expected ';' after assignment")
            return {'type': 'assignment', 'name': id_token.value, 'value': expr_result}

    def if_stmt(self) -> dict:
        """if_stmt ::= 'if' '(' expression ')' statement ('else' statement)?"""

        start_pos = self.pos
        start_token = self.current_token

        self.consume_token_or_fail(TokenType.IF, 'if')
        self.consume_token_or_fail(TokenType.LPAREN, '(', "Expected '(' after 'if'")

        try:
            condition_result = self.expression()
        except SyntaxError as se:
            self.pos = start_pos
            self.current_token = start_token
            raise SyntaxError("Expected condition in 'if' statement") from se

        self.consume_token_or_fail(TokenType.RPAREN, ')', "Expected ')' after condition")

        try:
            if_body_result = self.statement()
        except SyntaxError as se:
            self.pos = start_pos
            self.current_token = start_token
            raise SyntaxError("Expected statement after 'if'") from se

        else_body_result = {}
        if self.consume_token(TokenType.ELSE, 'else'):
            try:
                else_body_result = self.statement()
            except SyntaxError as se:
                self.pos = start_pos
                self.current_token = start_token
                raise SyntaxError("Expected statement after 'else'") from se

        return {'type': 'if_stmt', 'cond': condition_result, 'if-body': if_body_result, 'else-body': else_body_result}

    def while_loop(self) -> dict:
        """while_loop ::= 'while' '(' expression ')' statement"""

        start_pos = self.pos
        start_token = self.current_token

        self.consume_token_or_fail(TokenType.WHILE, 'while')
        self.consume_token_or_fail(TokenType.LPAREN, '(', "Expected '(' after 'while'")

        try:
            condition_result = self.expression()
        except SyntaxError as se:
            self.pos = start_pos
            self.current_token = start_token
            raise SyntaxError("Expected condition in 'while' loop") from se

        self.consume_token_or_fail(TokenType.RPAREN, ')', "Expected ')' after condition")

        try:
            body_result = self.statement()
        except SyntaxError as se:
            self.pos = start_pos
            self.current_token = start_token
            raise SyntaxError("Expected loop body") from se

        return {'type': 'while_loop', 'cond': condition_result, 'body': body_result}

    def print_stmt(self) -> dict:
        """print_stmt ::= 'print' expression ';'"""

        start_pos = self.pos
        start_token = self.current_token

        self.consume_token_or_fail(TokenType.PRINT, 'print')

        try:
            expr_result = self.expression()
        except SyntaxError as se:
            self.pos = start_pos
            self.current_token = start_token
            raise SyntaxError("Expected expression after 'print'") from se

        self.consume_token_or_fail(TokenType.SEMICOLON, ';', "Expected ';' after print")

        return {'type': 'print_stmt', 'expression': expr_result}

    def expression(self) -> dict:
        """expression ::= logical_or"""

        try:
            return self.logical_or()
        except SyntaxError as se:
            raise SyntaxError("Failed to parse expression") from se

    def logical_or(self) -> dict:
        """logical_or ::= logical_and ('||' logical_and)*"""

        start_pos = self.pos
        start_token = self.current_token

        try:
            left = self.logical_and()
        except SyntaxError as se:
            self.pos = start_pos
            self.current_token = start_token
            raise SyntaxError("Expected expression before '||'") from se

        while self.consume_token(TokenType.OR, '||'):
            try:
                right = self.logical_and()
            except SyntaxError as se:
                self.pos = start_pos
                self.current_token = start_token
                raise SyntaxError("Expected expression after '||'") from se
            else:
                left = {'type': 'binary_expr', 'op': '||', 'left': left, 'right': right}
        return left

    def logical_and(self) -> dict:
        """logical_and ::= equality ('&&' equality)*"""

        start_pos = self.pos
        start_token = self.current_token

        try:
            left = self.equality()
        except SyntaxError as se:
            self.pos = start_pos
            self.current_token = start_token
            raise SyntaxError("Expected expression before '&&'") from se

        while self.consume_token(TokenType.AND, '&&'):
            try:
                right = self.equality()
            except SyntaxError as se:
                self.pos = start_pos
                self.current_token = start_token
                raise SyntaxError("Expected expression after '&&'") from se
            else:
                left = {'type': 'binary_expr', 'op': '&&', 'left': left, 'right': right}
        return left

    def equality(self) -> dict:
        """equality ::= relational (('==' | '!=') relational)*"""

        start_pos = self.pos
        start_token = self.current_token

        try:
            left = self.relational()
        except SyntaxError as se:
            self.pos = start_pos
            self.current_token = start_token
            raise SyntaxError("Expected expression before '==' or '!='") from se

        while True:
            if self.consume_token(TokenType.EQ, '=='):
                op = '=='
            elif self.consume_token(TokenType.NEQ, '!='):
                op = '!='
            else:
                break

            try:
                right = self.relational()
            except SyntaxError as se:
                self.pos = start_pos
                self.current_token = start_token
                raise SyntaxError(f"Expected expression after '{op}'") from se
            else:
                left = {'type': 'binary_expr', 'op': op, 'left': left, 'right': right}
        return left

    def relational(self) -> dict:
        """relational ::= additive (('<' | '>' | '<=' | '>=') additive)*"""

        start_pos = self.pos
        start_token = self.current_token

        try:
            left = self.additive()
        except SyntaxError as se:
            self.pos = start_pos
            self.current_token = start_token
            raise SyntaxError("Expected expression before '<', '>', '<=', or '>='") from se

        while True:
            if self.consume_token(TokenType.LT, '<'):
                op = '<'
            elif self.consume_token(TokenType.GT, '>'):
                op = '>'
            elif self.consume_token(TokenType.LTE, '<='):
                op = '<='
            elif self.consume_token(TokenType.GTE, '>='):
                op = '>='
            else:
                break

            try:
                right = self.additive()
            except SyntaxError as se:
                self.pos = start_pos
                self.current_token = start_token
                raise SyntaxError(f"Expected expression after '{op}'") from se
            else:
                left = {'type': 'binary_expr', 'op': op, 'left': left, 'right': right}
        return left

    def additive(self) -> dict:
        """additive ::= multiplicative (('+' | '-') multiplicative)*"""

        start_pos = self.pos
        start_token = self.current_token

        try:
            left = self.multiplicative()
        except SyntaxError as se:
            self.pos = start_pos
            self.current_token = start_token
            raise SyntaxError("Expected expression before '<', '>', '<=', or '>='") from se

        while True:
            if self.consume_token(TokenType.PLUS, '+'):
                op = '+'
            elif self.consume_token(TokenType.MINUS, '-'):
                op = '-'
            else:
                break

            try:
                right = self.multiplicative()
            except SyntaxError as se:
                self.pos = start_pos
                self.current_token = start_token
                raise SyntaxError(f"Expected expression after '{op}'") from se
            left = {'type': 'binary_expr', 'op': op, 'left': left, 'right': right}
        return left

    def multiplicative(self) -> dict:
        """multiplicative ::= primary (('*' | '/') primary)*"""

        start_pos = self.pos
        start_token = self.current_token

        try:
            left = self.primary()
        except SyntaxError as se:
            self.pos = start_pos
            self.current_token = start_token
            raise SyntaxError("Expected expression before '*' or '/'") from se

        while True:
            if self.consume_token(TokenType.MUL, '*'):
                op = '*'
            elif self.consume_token(TokenType.DIV, '/'):
                op = '/'
            else:
                break

            try:
                right = self.primary()
            except SyntaxError as se:
                self.pos = start_pos
                self.current_token = start_token
                raise SyntaxError(f"Expected expression after '{op}'") from se
            left = {'type': 'binary_expr', 'op': op, 'left': left, 'right': right}
        return left

    def primary(self) -> dict:
        """primary ::= NUMBER | IDENTIFIER | '(' expression ')' | ('+' | '-') primary"""

        # Number literal
        if num := self.consume_token(TokenType.NUMBER):
            return {'type': 'number', 'value': float(num.value)}

        # Variable reference
        if ident := self.consume_token(TokenType.IDENTIFIER):
            return {'type': 'identifier', 'name': ident.value}

        start_pos = self.pos
        start_token = self.current_token

        # Parenthesized expression
        if self.consume_token(TokenType.LPAREN, '('):
            try:
                expr_result = self.expression()
            except SyntaxError as se:
                self.pos = start_pos
                self.current_token = start_token
                raise SyntaxError("Expected expression after '('") from se
            else:
                self.consume_token_or_fail(TokenType.RPAREN, ')', "Expected ')' after expression")
                return expr_result

        # Unary plus/minus
        if op_token := self.consume_token(TokenType.PLUS, '+') or self.consume_token(TokenType.MINUS, '-'):
            op = op_token.value

            try:
                operand = self.primary()
            except SyntaxError as se:
                self.pos = start_pos
                self.current_token = start_token
                raise SyntaxError(f"Expected expression after '{op}'") from se
            else:
                return {'type': 'unary_expr', 'op': op, 'argument': operand}

        raise SyntaxError("Expected primary expression")


# Example usage
if __name__ == "__main__":
    # Example token stream (in real usage, this would come from a lexer)
    """
    var x = 5;
    while ( x < 10 ) {
        print x;
        x = x + 1;
    }
    """
    tokens = [
        Token(TokenType.VAR, 'var', 1, 1),
        Token(TokenType.IDENTIFIER, 'x', 1, 5),
        Token(TokenType.ASSIGN, '=', 1, 7),
        Token(TokenType.NUMBER, '5', 1, 9),
        Token(TokenType.SEMICOLON, ';', 1, 10),
        Token(TokenType.WHILE, 'while', 2, 1),
        Token(TokenType.LPAREN, '(', 2, 7),
        Token(TokenType.IDENTIFIER, 'x', 2, 8),
        Token(TokenType.LT, '<', 2, 10),
        Token(TokenType.NUMBER, '10', 2, 12),
        Token(TokenType.RPAREN, ')', 2, 14),
        Token(TokenType.LBRACE, '{', 2, 16),
        Token(TokenType.PRINT, 'print', 3, 5),
        Token(TokenType.IDENTIFIER, 'x', 3, 11),
        Token(TokenType.SEMICOLON, ';', 3, 12),
        Token(TokenType.IDENTIFIER, 'x', 4, 5),
        Token(TokenType.ASSIGN, '=', 4, 7),
        Token(TokenType.IDENTIFIER, 'x', 4, 9),
        Token(TokenType.PLUS, '+', 4, 11),
        Token(TokenType.NUMBER, '1', 4, 13),
        Token(TokenType.SEMICOLON, ';', 4, 14),
        Token(TokenType.RBRACE, '}', 5, 1),
        Token(TokenType.EOF)
    ]

    parser = ToyPEGParser(_tokens=tokens)
    ast = parser.program()
    import pprint

    pprint.pprint(ast, width=40)