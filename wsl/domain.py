"""Module wsl.domain: Built-in WSL domain parsers.

Users can add their own domains by providing a parser following the example of
the built-in ones.
"""

import wsl


def split_opts(line):
    opts = []
    for word in line.split():
        if '=' in word:
            key, val = word.split('=', 1)
        else:
            key, val = word, None
        opts.append((key, val, word))
    return opts


def parse_ID_domain(line):
    """Parser for ID domain declarations.

    No special syntax is recognized. Only the bare "ID" is allowed.
    """
    if line:
        raise wsl.ParseError('Construction of ID domain does not receive any arguments')
    class IDDomain:
        wsllex = wsl.lex_identifier
        wslunlex = wsl.unlex_identifier
        decode = ID_decode
        encode = ID_encode
        jsontype = wsl.JSONTYPE_STRING
    return IDDomain


def parse_String_domain(line):
    opts = split_opts(line)
    escape = False
    for key, val, orig in opts:
        if key == 'escape' and val is None:
            escape = True
        else:
            raise wsl.ParseError('Did not understand String parameterization: %s' %(orig,))
    if escape:
        class StringDomain:
            wsllex = wsl.lex_string_with_escapes
            wslunlex = wsl.unlex_string_with_escapes
            decode = String_decode
            encode = String_encode
            jsontype = wsl.JSONTYPE_STRING
    else:
        class StringDomain:
            wsllex = wsl.lex_string_without_escapes
            wslunlex = wsl.unlex_string_without_escapes
            decode = String_decode
            encode = String_encode
            jsontype = wsl.JSONTYPE_STRING
    return StringDomain


def parse_Int_domain(line):
    if line:
        raise wsl.ParseError('Construction of Integer domain does not receive any arguments')
    class IntDomain:
        wsllex = wsl.lex_identifier
        wslunlex = wsl.unlex_identifier
        decode = Int_decode
        encode = Int_encode
        jsontype = wsl.JSONTYPE_INT
    return IntDomain


class EnumBase:
    """An enumeration type. Essentially a list of possible identifiers"""
    def __init__(self, strings):
        self.strings = list(strings)


class EnumValue:
    """An option representing a particular choice of value for a given Enum"""
    def __init__(self, base, string):
        self.base = base
        self.string = string
        self.integer = base.strings.index(string)

    def __repr__(self):
        return self.string

    def __str__(self):
        return self.string

    def __hash__(self):
        return self.integer

    def __eq__(self, other):
        return self.integer == other.integer

    def __ne__(self, other):
        return self.integer != other.integer

    def __le__(self, other):
        return self.integer <= other.integer

    def __ge__(self, other):
        return self.integer >= other.integer

    def __lt__(self, other):
        return self.integer < other.integer

    def __gt__(self, other):
        return self.integer > other.integer


def parse_Enum_domain(line):
    strings = line.split()
    base = EnumBase(strings)
    values = []
    for s in strings:
        values.append(EnumValue(base, s))
    class EnumDomain:
        wsllex = wsl.lex_identifier
        wslunlex = wsl.unlex_identifier
        decode = make_Enum_decode(values)
        encode = make_Enum_encode(values)
        jsontype = wsl.JSONTYPE_STRING
    return EnumDomain


def parse_IPv4_domain(line):
    if line.strip():
        raise wsl.ParseError('IPv4 domain doesn\'t take any arguments')
    class IPv4:
        wsllex = wsl.lex_identifier
        wslunlex = wsl.unlex_identifier
        decode = IPv4_decode
        encode = IPv4_encode
        jsontype = wsl.JSONTYPE_STRING
    return IPv4


def ID_decode(token):
    return token


def ID_encode(value):
    return value


def String_decode(token):
    return token


def String_encode(value):
    return value


def Int_decode(token):
    try:
        return int(token)
    except ValueError as e:
        raise wsl.ParseError('Failed to parse integer') from e


def Int_encode(value):
    return str(value)


def make_Enum_decode(values):
    def Enum_decode(token):
        for enumValue in EnumValues:
            if enumValue.string == token:
                return enumValue


def make_Enum_encode(values):
    def Enum_encode(value):
        if not isinstance(value, EnumValue):
            raise ValueError('Not a valid enum value: %s' %(value,))
        return value.string


def IPv4_decode(token):
    ws = token.split('.')
    if len(ws) == 4:
        try:
            ip = tuple(map(int, ws))
            for b in ip:
                if b < 0 or b >= 256:
                    raise ValueError()
            return i, ip
        except ValueError:
            pass
    raise wsl.ParseError('IPv4 address must be 4-tuple of 1 byte integers (0-255)')


def IPv4_encode(ip):
    try:
        a,b,c,d = ip
        for x in [a,b,c,d]:
            if not isinstance(x, int) or not 0 <= x < 256:
                raise ValueError()
        return '%d.%d.%d.%d' %ip
    except ValueError as e:
        raise wsl.FormatError('Not a valid ip address (need 4-tuple of integers in [0,255])')


_builtin_domain_parsers = {
    'ID': parse_ID_domain,
    'String': parse_String_domain,
    'Enum': parse_Enum_domain,
    'Int': parse_Int_domain,
    'IPv4': parse_IPv4_domain,
}


def get_builtin_domain_parsers():
    """Get a dict containing all domain parsers built-in to this library.

    The dict is freshly created, so can be modified by the caller.

    Returns:
        dict: A dictionary mapping the names of all built-in parsers to the parsers.
    """
    return dict(_builtin_domain_parsers)


if __name__ == '__main__':
    parse_ID_domain('')
    parse_String_domain('')
    parse_String_domain('escape')
    parse_IPv4_domain('')
