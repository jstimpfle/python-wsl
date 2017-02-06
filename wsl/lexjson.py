import wsl


def _chardesc(text, i):
    if i >= len(text):
        return '(end of input)'

    return '"' + text[i] + '"'


def _whitespace(text, i):
    end = len(text)
    while i < end and ord(text[i]) in [0x09, 0x0a, 0x0d, 0x20]:
        i += 1
    return i


def lex_json_string(text, i):
    start = i
    end = len(text)

    if not (i < end and text[i] == '"'):
        raise wsl.LexError('JSON string literal', text, start, i, 'String literals must begin with quotation mark, got: "%s"' %(_chardesc(text, i)))

    i += 1
    while (i < end and text[i] != '"'):
        i += 1

    if not (i < end and text[i] == '"'):
        raise wsl.LexError('JSON string literal', text, start, i, 'String literals must end with quotation mark, got: "%s"' %(_chardesc(text, i)))

    i += 1
    return i, text[start+1:i-1]


def unlex_json_string(token):
    return '"' + token + '"'  # XXX


def lex_json_int(text, i):
    start = i
    end = len(text)

    m = re.match(r'0|-?[1-9][0-9]*', text[i:])

    if m is None:
        raise wsl.LexError('JSON integer literal', text, start, i, 'Integer literals must match /0|-?[1-9][0-9]*/')

    i += m.end()

    return i, int(text[start:i])


def unlex_json_int(token):
    assert isinstance(token, int)
    return str(token)


def lex_json_null(text, i):
    start = i

    if text[i:].startswith('null'):
        i += 4
        return i, None
    else:
        raise wsl.LexError('JSON null literal', text, i, 'Expected "null"')


def unlex_json_null(token):
    assert token is None
    return 'null'


def make_make_jsonreader(schema):
    if not isinstance(schema, wsl.Schema):
        raise TypeError()
    def make_jsonreader(domain, is_dict_key):
        domobj = schema.domains.get(domain)
        if domobj is None:
            return None
        if not hasattr(domobj.funcs, 'decode'):
            return None
        if not hasattr(domobj.funcs, 'jsonlex'):
            return None
        decode = domobj.funcs.decode
        jsonlex = lex_json_string if is_dict_key else domobj.funcs.jsonlex
        def jsonreader(value):
            return decode(jsonlex(value))
        return jsonreader
    return make_jsonreader


def make_make_jsonwriter(schema):
    if not isinstance(schema, wsl.Schema):
        raise TypeError()
    def make_jsonwriter(domain, is_dict_key):
        domobj = schema.domains.get(domain)
        if domobj is None:
            return None
        if not hasattr(domobj.funcs, 'encode'):
            return None
        if not hasattr(domobj.funcs, 'jsonunlex'):
            return None
        encode = domobj.funcs.encode
        jsonunlex = unlex_json_string if is_dict_key else domobj.funcs.jsonunlex
        def jsonwriter(value):
            return jsonunlex(encode(value))
        return jsonwriter
    return make_jsonwriter
