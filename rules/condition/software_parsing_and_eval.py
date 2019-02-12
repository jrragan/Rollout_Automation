import logging

logger = logging.getLogger('software_parsing_and_eval')

# Token types
# EOF (end-of-file) token is used to indicate that
# there is no more input left for lexical analysis
INTEGER, LPAREN, RPAREN, DOT, CHAR, EOF = 'INTEGER', 'LPAREN', 'RPAREN', 'DOT', 'CHAR', 'EOF'


class Token(object):
    def __init__(self, type, value):
        # token type: INTEGER, LPAREN, RPAREN, DOT, CHAR, EOF
        self.type = type
        # token value: non-negative integer value, character, parentheses, dot
        self.value = value

    def __str__(self):
        """String representation of the class instance.

        Examples:
            Token(INTEGER, 3)
            Token(PLUS '+')
        """
        return 'Token({type}, {value})'.format(
            type=self.type,
            value=repr(self.value)
        )

    def __repr__(self):
        return self.__str__()


class Interpreter(object):
    def __init__(self, text):
        # client string input
        self.text = text
        # self.pos is an index into self.text
        self.pos = 0
        # current token instance
        self.current_token = None
        if not text:
            self.error()
        self.current_char = self.text[self.pos]

    def error(self):
        raise Exception('Error parsing input')

    def advance(self):
        """Advance the 'pos' pointer and set the 'current_char' variable."""
        self.pos += 1
        if self.pos > len(self.text) - 1:
            self.current_char = None  # Indicates end of input
        else:
            self.current_char = self.text[self.pos]

    def skip_whitespace(self):
        while self.current_char is not None and self.current_char.isspace():
            self.advance()

    def integer(self):
        """Return a (multidigit) integer consumed from the input."""
        result = ''
        while self.current_char is not None and self.current_char.isdigit():
            result += self.current_char
            self.advance()
        return int(result)

    def character(self):
        """Return a multicharacter string consumed from the input."""
        result = ''
        while self.current_char is not None and self.current_char.isalpha():
            result += self.current_char
            self.advance()
        return result

    def get_next_token(self):
        """Lexical analyzer (also known as scanner or tokenizer)

        This method is responsible for breaking a sentence
        apart into tokens.
        """
        while self.current_char is not None:
            # print("current char: {}".format(self.current_char))

            if self.current_char.isspace():
                self.skip_whitespace()
                continue

            elif self.current_char.isdigit():
                yield Token(INTEGER, self.integer())

            elif self.current_char == '(':
                self.advance()
                yield Token(LPAREN, '(')

            elif self.current_char == ')':
                self.advance()
                yield Token(RPAREN, ')')

            elif self.current_char == '.':
                self.advance()
                yield Token(DOT, '.')

            elif self.current_char.isalpha:
                yield Token(CHAR, self.character())

            else:
                print(self.current_char)
                self.error()

        yield Token(EOF, None)

    def next_token_iter(self):
        self.current_token = self.get_next_token()
        yield self.current_token

    def eat(self, token_type):
        # compare the current token type with the passed token
        # type and if they match then "eat" the current token
        # and assign the next token to the self.current_token,
        # otherwise raise an exception.
        if self.current_token.type == token_type:
            self.current_token = self.get_next_token()
        else:
            self.error()


def compare_token_types(token1, token2):
    if token1.type == token2.type:
        return True
    return False


def get_operator(text):
    operators = ['==', '>=', '<=', '<', '>', '!=']
    for operator in operators:
        result = text.split(operator)
        if len(result) == 2:
            return operator, result
    return None, text


def set_not_equal_flag(operator):
    if operator != '==':
        return True
    return False


def _parser_helper(sw1, sw2, operator):
    not_equal_flag = set_not_equal_flag(operator)
    print(not_equal_flag)
    tsw1 = Interpreter(sw1)
    tsw2 = Interpreter(sw2)
    for a, b in zip(tsw1.get_next_token(), tsw2.get_next_token()):
        print("a: {}, b: {}".format(a, b))
        if (a.type != EOF and b.type != EOF) and compare_token_types(a, b):
            if a.type == INTEGER or a.type == CHAR:
                result = eval("{} {} {}".format(a.value, operator, b.value))
                print(result)
                if result and not_equal_flag:
                    return True
                elif eval("{} {} {}".format(a.value, '==', b.value)):
                    if (not tsw1.current_char or not tsw2.current_char) and not_equal_flag:
                        return False
                    elif not tsw1.current_char or not tsw2.current_char:
                        return True
                    else:
                        continue
                else:
                    return False
            else:
                continue
        else:
            return False


def parser(operator, sw1, sw2):
    if operator == ">=" or operator == "<=":
        result = False
        for op in operator:
            if op == '=':
                op2 = '=='
            else:
                op2 = op
            result = _parser_helper(sw1, sw2, op2) or result
    else:
        result = _parser_helper(sw1, sw2, operator)
    return result


def main():
    print("TESTI")
    testI = Interpreter("7.0(8)N1(1)")
    for t in testI.get_next_token():
        print(t)
    print("TESTI2")
    testI2 = Interpreter("5.1(3)N2(1)")
    for t in testI2.get_next_token():
        print(t)
    print("TESTI3")
    testI = Interpreter("7.0(8)N1(1)")
    testI2 = Interpreter("5.1(3)N2(1)")
    for t1, t2 in zip(testI.get_next_token(), testI2.get_next_token()):
        print(t1, t2)
    print("TESTI4")
    testI = Interpreter("7.0(8)N1(1)")
    testI2 = Interpreter("5.1(3)")
    for t1, t2 in zip(testI.get_next_token(), testI2.get_next_token()):
        print(t1, t2)
    print("TEST1")
    test1 = parser('>', '5.2', '5.2')
    assert test1 is False, "Test1 Failed"
    print("TEST2")
    test2 = parser('>=', '5.2', '5.2')
    assert test2 is True, "Test2 Failed"
    print("TEST3")
    test3 = parser('<', '5.2', '5.2')
    assert test3 is False, "Test3 Failed"
    print("TEST4")
    test4 = parser('<=', '5.2', '5.2')
    assert test4 is True, "Test4 Failed"
    print("TEST5")
    test5 = parser('==', '5.2', '5.2')
    assert test5 is True, "Test5 Failed"
    print("TEST6")
    test6 = parser('!=', '5.2', '5.2')
    assert test6 is False, "Test6 Failed"
    print("TEST7")
    test7 = parser('>', "7.0(8)N1(1)", "5.1(3)")
    assert test7 is True, "Test7 Failed"
    print("TEST8")
    test8 = parser('>=', "7.0(8)N1(1)", "5.1(3)")
    assert test8 is True, "Test8 Failed"
    print("TEST9")
    test9 = parser('<', "7.0(8)N1(1)", "5.1(3)")
    assert test9 is False, "Test9 Failed"
    print("TEST10")
    test10 = parser('<=', "7.0(8)N1(1)", "5.1(3)")
    assert test10 is False, "Test10 Failed"
    print("TEST11")
    test11 = parser('==', "7.0(8)N1(1)", "5.1(3)")
    assert test11 is False, "Test11 Failed"
    print("TEST12")
    test12 = parser('!=', "7.0(8)N1(1)", "5.1(3)")
    assert test12 is True, "Test12 Failed"
    print("TEST13")
    test13 = parser('>', "5.1(3)", "7.0(8)N1(1)")
    assert test13 is False, "Test13 Failed"
    print("TEST14")
    test14 = parser('>=', "5.1(3)", "7.0(8)N1(1)")
    assert test14 is False, "Test8 Failed"
    print("TEST15")
    test15 = parser('<', "5.1(3)", "7.0(8)N1(1)")
    assert test15 is True, "Test9 Failed"
    print("TEST16")
    test16 = parser('<=', "5.1(3)", "7.0(8)N1(1)")
    assert test16 is True, "Test10 Failed"
    print("TEST17")
    test17 = parser('==', "5.1(3)", "7.0(8)N1(1)")
    assert test17 is False, "Test11 Failed"
    print("TEST18")
    test18 = parser('!=', "5.1(3)", "7.0(8)N1(1)")
    assert test18 is True, "Test12 Failed"
    print("TEST19")
    try:
        test19 = parser('==', '', '')
    except:
        pass


if __name__ == '__main__':
    main()
