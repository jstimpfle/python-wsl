"""Module wsl.lex: standard lexical parsers for WSL text format"""

import wsl


def _hex2dec(c):
    x = ord(c)
    if 0x30 <= x <= 0x39:
        return x - 0x30
    if 0x61 <= x < 0x67:
        return x - 0x57
    raise wsl.ParseError('Not a valid hexadecimal character: %c' %(c,))


def _hexdecode(chars):
    if len(chars) >= 2:
        return _hex2dec(chars[0])*16 + hex2dec(chars[1])
    raise wsl.ParseError()


def lex_identifier(text, i):
    end = len(text)
    x = i
    while i < end and ord(text[i]) > 0x20 and ord(text[i]) != 0x7f:
        i += 1
    if x == i:
        raise wsl.ParseError('EOL or invalid character while expecting ID')
    return i, text[x:i]


def unlex_identifier(token):
    if not isinstance(token, str):
        raise ValueError('Not a string token: %s (%s)' %(token, type(token)))
    return token


def lex_string_without_escapes(text, i):
    start = i
    end = len(text)

    if not 0 <= i < end or ord(text[i]) != 0x5b:  # [
        raise wsl.ParseError('Did not find expected WSL string literal')

    i += 1
    while i < end and text[i] != ']':
        i += 1

    return i+1, text[start+1:i]


def unlex_string_without_escapes(token):
    if not isinstance(token, str):
        raise ValueError()
    if '[' in token or ']' in token:
        raise ValueError('Cannot unlex string without escaping: %s' %(token,))
    return '[' + token + ']'


def lex_string_with_escapes(text, i):
    start = i
    end = len(text)

    if not 0 <= i < end or ord(text[i]) != 0x5b:  # [
        raise wsl.ParseError('Did not find expected WSL string literal')

    i += 1
    cs = []
    while i < end:
        c = text[i]
        d = ord(c)
        if d == 0x5d:  # ]
           break
        if d == 0x5c:  # \\
            if i+1 < end:
                if ord(text[i+1]) in [0x5b, 0x5c, 0x5d]:
                    cs.append(text[i+1])
                    i += 2
                elif text[i+1] == 'x':
                    cs.append(chr(_hexdecode(text[i+2:])))
                    i += 4
                else:
                    raise wsl.ParseError('Unknown escape sequence: \\%c' %(c,))
        else:
            if d < 0x20 or d in [0x5b, 0x7f]:
                raise wsl.ParseError('Disallowed character %.2x in string literal' %(d,))
            cs.append(c)
            i += 1
    if i == end:
        raise wsl.ParseError('EOL while looking for closing quote')
    return i+1, ''.join(cs)


def unlex_string_with_escapes(token):
    return '[' + token + ']'  # XXX


def lex_space(text, i):
    """Lex a single space character.

    Args:
        text (str): Where to lex the space from.
        i (int): An index into *text* where the space is supposed to be.
    Returns:
        If the lex succeeds, *(i, None)* where *i* is the index of the next
        character following the space.
    Raises:
        wsl.ParseError: If no space is found.
    """
    end = len(text)
    if i == end or ord(text[i]) != 0x20:
        raise wsl.ParseError('Expected space character')
    return i+1, None


def lex_newline(text, i):
    """Lex a single newline character.

    Args:
        text (str): Where to lex the newline from.
        i (int): An index into *text* where the newline is supposed to be.
    Returns:
        If the lex succeeds, *(i, None)* where *i* is the index of the next
        character following the newline.
    Raises:
        wsl.ParseError: If no newline is found.
    """
    end = len(text)
    if i == end or ord(text[i]) != 0x0a:
        raise wsl.ParseError('Expected newline (0x0a) character')
    return i+1, None


def lex_tokens(text, i, lexers):
    """Lex a database tuple of tokens according to *domain_objects*, separated by single spaces.

    Args:
        text (str): holds a database tuple.
        i (int): An index into *text* where the space is supposed to be.
        lexers (list): A list of lexers corresponding to the columns of the
            database table.
    Returns:
        tuple: A tuple containing the lexed tokens.
    Raises:
        wsl.ParseError: The called lexers raise ParseErrors if lexing fails.
    """
    end = len(text)
    toks = []
    for lexer in lexers:
        i, _ = wsl.lex_space(text, i)
        i, tok = lexer(text, i)
        toks.append(tok)
    i, _ = lex_newline(text, i)
    return i, tuple(toks)


def lex_relation_name(text, i):
    end = len(text)
    x = i
    if not 0x41 <= ord(text[i]) <= 0x5a and not 0x61 <= ord(text[i]) <= 0x7a:
        raise wsl.ParseError('Expected table name')
    while i < end and (0x41 <= ord(text[i]) <= 0x5a or 0x61 <= ord(text[i]) <= 0x7a):
        i += 1
    return i, text[x:i]


def lex_row(text, i, lexers_of_relation):
    """Lex a database row (a relation name and according tuple of tokens).

    This def lexes a relation name, which is used to lookup a domain object
    in *objects_of_relation*. Then that object is used to call *lex_tokens()*.

    Args:
        text (str): holds a database tuple.
        lexers_of_relation (dict): maps relation names to the list of the
            lexers of their according columns.
    Returns:
        (int, (str, tuple)): The index of the first unconsumed character and a
        2-tuple holding the lexed relation name and lexed tokens.
    Raises:
        wsl.ParseError: if the lex failed.
    """
    end = len(text)
    i, relation = lex_relation_name(text, i)
    lexers = lexers_of_relation.get(relation)
    if lexers is None:
        raise wsl.ParseError('No such table: "%s"' %(relation,))
    i, tokens = lex_tokens(text, i, lexers)
    return i, (relation, tokens)


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
