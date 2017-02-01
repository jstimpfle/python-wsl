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


def lex_wsl_relation_name(text, i):
    end = len(text)
    x = i
    if not 0x41 <= ord(text[i]) <= 0x5a and not 0x61 <= ord(text[i]) <= 0x7a:
        raise wsl.ParseError('Expected table name')
    while i < end and (0x41 <= ord(text[i]) <= 0x5a or 0x61 <= ord(text[i]) <= 0x7a):
        i += 1
    return i, text[x:i]


def lex_wsl_identifier(text, i):
    end = len(text)
    x = i
    while i < end and ord(text[i]) > 0x20 and ord(text[i]) != 0x7f:
        i += 1
    if x == i:
        raise wsl.ParseError('EOL or invalid character while expecting ID')
    return i, text[x:i]


def unlex_wsl_identifier(token):
    if not isinstance(token, str):
        raise ValueError('Not a string token: %s (%s)' %(token, type(token)))
    return token


def lex_wsl_string_without_escapes(text, i):
    start = i
    end = len(text)

    if not 0 <= i < end or ord(text[i]) != 0x5b:  # [
        raise wsl.ParseError('Did not find expected WSL string literal')

    i += 1
    while i < end and text[i] != ']':
        i += 1

    return i+1, text[start+1:i]


def unlex_wsl_string_without_escapes(token):
    if not isinstance(token, str):
        raise ValueError()
    if '[' in token or ']' in token:
        raise ValueError('Cannot unlex string without escaping: %s' %(token,))
    return '[' + token + ']'


def lex_wsl_string_with_escapes(text, i):
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


def unlex_wsl_string_with_escapes(token):
    return '[' + token + ']'  # XXX


def lex_wsl_space(text, i):
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


def lex_wsl_newline(text, i):
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


def make_make_wslreader(schema):
    if not isinstance(schema, wsl.Schema):
        raise ValueError()
    def make_wslreader(domain):
        domobj = schema.domains.get(domain)
        if domobj is None:
            return None
        if not hasattr(domobj.funcs, 'decode'):
            return None
        if not hasattr(domobj.funcs, 'wsllex'):
            return None
        decode = domobj.funcs.decode
        lex = domobj.funcs.wsllex
        def wslreader(text, i):
            i, token = lex(text, i)
            return i, decode(token)
        return wslreader
    return make_wslreader


def make_make_wslwriter(schema):
    if not isinstance(schema, wsl.Schema):
        raise ValueError()
    def make_wslwriter(domain):
        domobj = schema.domains.get(domain)
        if domobj is None:
            return None
        if not hasattr(domobj.funcs, 'encode'):
            return None
        if not hasattr(domobj.funcs, 'wslunlex'):
            return None
        encode = domobj.funcs.encode
        wslunlex = domobj.funcs.wslunlex
        def wslwriter(value):
            return wslunlex(encode(value))
        return wslwriter
    return make_wslwriter
