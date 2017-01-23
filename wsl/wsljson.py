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
