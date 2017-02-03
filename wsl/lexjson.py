import wsl


def lex_json_string(x):
    assert isinstance(x, str)
    return x


def unlex_json_string(x):
    assert isinstance(x, str)
    return x


def lex_json_int(x):
    assert isinstance(x, int)
    return str(x)


def unlex_json_int(x):
    assert isinstance(x, str)
    try:
        return int(x)
    except ValueError as e:
        raise wsl.UnlexError('Unlexing token to JSON integer', x, 'Not a valid integer')


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
        jsonlex = domobj.funcs.jsonlex
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
        jsonunlex = domobj.funcs.jsonunlex
        def jsonwriter(value):
            return jsonunlex(encode(value))
        return jsonwriter
    return make_jsonwriter
