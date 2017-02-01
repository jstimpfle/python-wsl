"""Module wsl.lex: standard lexical parsers for WSL text format"""

import wsl



if __name__ == '__main__':
    i, x = lex_identifier(r' asdf ', 1)
    assert i == 5
    assert x == 'asdf'

    i, x = lex_string_without_escapes(r'[abc\]] asdf', 0)
    assert i == 6
    assert x == 'abc\\'

    i, x = lex_string_with_escapes(r'[abc\]] asdf', 0)
    assert i == 7
    assert x == r'abc]'
