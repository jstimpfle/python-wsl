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
