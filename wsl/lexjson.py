import wsl


def lex_json_string(x):
    if not isinstance(x, str):
        raise wsl.LexError('JSON string token', str(x), 0, 0, 'Buffer to lex from is not a string but %s' %(type(x),))
    return x


def unlex_json_string(x):
    if not isinstance(x, str):
        raise wsl.UnlexError('JSON string token', str(x), 'Token to unlex is not a string but %s' %(type(x),))
    return x


def lex_json_int(x):
    if not isinstance(x, int):
        raise wsl.LexError('JSON int token', str(x), 0, 0, 'Not an int but %s' %(type(x),))
    return str(x)


def unlex_json_int(x):
    if not isinstance(x, str):
        raise wsl.UnlexError('JSON int token', str(x), 'Token to unlex is not a string but %s' %(type(x),))
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
