```
program        ::= statement+
statement      ::= var_decl | assignment | if_stmt | while_loop | print_stmt | block
block          ::= '{' statement* '}'

var_decl       ::= 'var' IDENTIFIER ('=' expression)? ';'
assignment     ::= IDENTIFIER '=' expression ';'
if_stmt        ::= 'if' '(' expression ')' statement ('else' statement)?
while_loop     ::= 'while' '(' expression ')' statement
print_stmt     ::= 'print' expression ';'

expression     ::= logical_or
logical_or     ::= logical_and ('||' logical_and)*
logical_and    ::= equality ('&&' equality)*
equality       ::= relational (('==' | '!=') relational)*
relational     ::= additive (('<' | '>' | '<=' | '>=') additive)*
additive       ::= multiplicative (('+' | '-') multiplicative)*
multiplicative ::= primary (('*' | '/') primary)*
primary        ::= NUMBER | IDENTIFIER | '(' expression ')' | ('+' | '-') primary

NUMBER         ::= ...
IDENTIFIER     ::= ...
```
