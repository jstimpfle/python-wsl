import wsl


JSONTYPE_STRING = 1
JSONTYPE_INT = 2


def jsonlex_string(x):
    assert isinstance(x, str)
    return x


def jsonunlex_string(x):
    assert isinstance(x, str)
    return x


def jsonlex_int(x):
    assert isinstance(x, int)
    return str(x)


def jsonunlex_int(x):
    assert isinstance(x, str)
    try:
        return int(x)
    except ValueError as e:
        raise wsl.FormatError('Failed to convert "%s" to JSON integer' %(x,)) from e


def make_jsonlex(jsontype, is_dict_key):
    if jsontype not in [JSONTYPE_STRING, JSONTYPE_INT]:
        raise ValueError()
    if not isinstance(is_dict_key, bool):
        raise ValueError()
    if jsontype == JSONTYPE_STRING or is_dict_key:
        return jsonlex_string
    elif jsontype == JSONTYPE_INT:
        return jsonlex_int
    assert False


def make_jsonunlex(jsontype, is_dict_key):
    if jsontype not in [JSONTYPE_STRING, JSONTYPE_INT]:
        raise ValueError()
    if not isinstance(is_dict_key, bool):
        raise ValueError()
    if jsontype == JSONTYPE_STRING or is_dict_key:
        return jsonunlex_string
    elif jsontype == JSONTYPE_INT:
        return jsonunlex_int
    assert False


def make_make_jsonreader(schema):
    if not isinstance(schema, wsl.Schema):
        raise ValueError()
    def make_jsonreader(domain, is_dict_key):
        domobj = schema.domains.get(domain)
        if domobj is None:
            return None
        if not hasattr(domobj.funcs, 'decode'):
            return None
        if not hasattr(domobj.funcs, 'jsontype'):
            return None
        decode = domobj.funcs.decode
        jsontype = domobj.funcs.jsontype
        jsonlex = make_jsonlex(jsontype, is_dict_key)
        def jsonreader(value):
            return decode(jsonlex(value))
        return jsonreader
    return make_jsonreader


def make_make_jsonwriter(schema):
    if not isinstance(schema, wsl.Schema):
        raise ValueError()
    def make_jsonwriter(domain, is_dict_key):
        domobj = schema.domains.get(domain)
        if domobj is None:
            return None
        if not hasattr(domobj.funcs, 'encode'):
            return None
        if not hasattr(domobj.funcs, 'jsontype'):
            return None
        encode = domobj.funcs.encode
        jsontype = domobj.funcs.jsontype
        jsonunlex = make_jsonunlex(jsontype, is_dict_key)
        def jsonwriter(value):
            return jsonunlex(encode(value))
        return jsonwriter
    return make_jsonwriter
