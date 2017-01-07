"""Module wsl.domain: Built-in WSL domain parsers.

Users can add their own domains by providing a parser following the example of
the built-in ones.

A parser takes a domain declaration, which is a string that must be completely
consumed. It returns a domain object with *decode* and *encode* member defs as
explained in the following paragraph.

The *decode* member of a domain object is a function that takes a string and a
start index into the string. It returns a pair *(j, val)* where *val* is the
parsed value and *j* is the position of the first unconsumed character. A
*wsl.ParseError* is raised if the decode fails.

The *encode* member of a domain object is a function that takes an object of the
type that *decode* returns, and returns a string holding the serialized value. A
*wsl.FormatError* is raised if the encode fails.
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


def hex2dec(c):
    x = ord(c)
    if 0x30 <= x <= 0x39:
        return x - 0x30
    if 0x61 <= x < 0x67:
        return x - 0x57
    raise wsl.ParseError('Not a valid hexadecimal character: %c' %(c,))


def parse_hex(chars):
    if len(chars) >= 2:
        return hex2dec(chars[0])*16 + hex2dec(chars[1])
    raise wsl.ParseError()


def parse_unicode(chars):
    if len(chars) >= 4:
        try:
            return chr(int(chars[:4]))
        except:
            raise wsl.ParseError()
    raise wsl.ParseError()


def parse_Unicode(chars):
    if len(chars) >= 8:
        try:
            return chr(int(chars[:8]))
        except:
            raise wsl.ParseError()
    raise wsl.ParseError()


def parse_ID_domain(line):
    """Parser for ID domain declarations.

    No special syntax is recognized. Only the bare "ID" is allowed.
    """
    if line:
        raise wsl.ParseError('Construction of ID domain does not receive any arguments')
    class IDDomain:
        decode = ID_decode
        encode = ID_encode
    return IDDomain


def parse_String_domain(line):
    opts = split_opts(line)
    escape = False
    for key, val, orig in opts:
        if key == 'escape' and val is None:
            escape = True
        else:
            raise wsl.ParseError('Did not understand String parameterization: %s' %(orig,))
    class StringDomain:
        decode = make_String_decode(escape)
        encode = make_String_encode(escape)
    return StringDomain


def parse_Int_domain(line):
    if line:
        raise wsl.ParseError('Construction of Integer domain does not receive any arguments')
    class IntDomain:
        decode = Int_decode
        encode = Int_encode
    return IntDomain


def parse_Enum_domain(line):
    strings = line.split()
    base = EnumBase(strings)
    values = []
    for s in strings:
        values.append(EnumValue(base, s))
    class EnumDomain:
        decode = make_Enum_decode(values)
        encode = make_Enum_encode(values)
    return EnumDomain


def parse_IPv4_domain(line):
    if line.strip():
        raise wsl.ParseError('IPv4 domain doesn\'t take any arguments')
    class IPv4:
        decode = IPv4_decode
        encode = IPv4_encode
    return IPv4


def ID_decode(line, i):
    """Value decoder for ID domain"""
    end = len(line)
    x = i
    while i < end and ord(line[i]) > 0x20 and ord(line[i]) != 0x7f:
        i += 1
    if x == i:
        raise wsl.ParseError('EOL or invalid character while expecting ID at character %d in line "%s"' %(i+1, line))
    return i, line[x:i]


def ID_encode(idval):
    """Value encoder for ID domain"""
    for c in idval:
        if ord(c) < 0x20 or ord(c) in [0x20, 0x5b, 0x5d, 0x7f]:
            raise wsl.FormatError('Disallowed character %c in ID value: %s' %(c, idval))
    return idval


def make_String_decode(escape):
    if escape:
        def String_decode(line, i):
            """Value decoder for String literals with \\xDD, \\uDDDD and \\uDDDDDDDDD escape sequences."""
            end = len(line)
            if i == end or ord(line[i]) != 0x5b:  # [
                raise wsl.ParseError('Did not find expected WSL string literal at character %d in line %s' %(i+1, line))
            i += 1
            x = i
            cs = []
            while i < end:
                c = line[i]
                d = ord(c)
                if d == 0x5d:  # ]
                    break
                if d == 0x5c:  # \\
                    if i+1 < end:
                        if line[i+1] == 'x':
                            cs.append(chr(parse_hex(line[i+2:])))
                            i += 4
                        elif line[i+1] == 'u':
                            cs.append(chr(parse_unicode(line[i+2:])))
                            i += 6
                        elif line[i+1] == 'U':
                            cs.append(chr(parse_Unicode(line[i+2:])))
                            i += 10
                        else:
                            raise wsl.ParseError('Unknown escape sequence: \\%c' %(line[i+1],))
                else:
                    if d < 0x20 or d in [0x5b, 0x7f]:
                        raise wsl.ParseError('Disallowed character %.2x in string literal at character "%d" in line "%s"' %(d, i, line))
                    cs.append(c)
                    i += 1
            if i == end:
                raise wsl.ParseError('EOL while looking for closing quote in line %s' %(line))
            return i+1, ''.join(cs)
    else:
        def String_decode(line, i):
            """Value decoder for String literals without escapes"""
            end = len(line)
            if i == end or ord(line[i]) != 0x5b:
                raise wsl.ParseError('Did not find expected WSL string literal at character %d in line %s' %(i+1, line))
            i += 1
            x = i
            while i < end:
                c = line[i]
                d = ord(c)
                if d == 0x5d:  # ]
                    break
                if d < 0x20 or d in [0x5b, 0x7f]:
                    raise wsl.ParseError('Disallowed character %.2x in string literal at character "%d" in line "%s"' %(c, i, line))
                i += 1
            if i == end:
                raise wsl.ParseError('EOL while looking for closing quote in line %s' %(line))
            return i+1, line[x:i]
    return String_decode


def make_String_encode(escape):
    if escape:
        def String_encode(string):
            frags = ['[']
            for c in string:
                code = ord(c)
                if 0x20 <= code < 0x7f and code not in (0x5b, 0x5d):
                    frags.append(c)
                elif 0 <= code < 0x20 or code in (0x5b, 0x5d) or 0x7f <= code <= 0xff:
                    frags.append('\\x%02x' %code)
                elif 256 <= code <= 9999:
                    frags.append('\\u%04d' %code)
                else:
                    frags.append('\\U%08d' %code)
            frags.append(']')
            return ''.join(frags)
    else:
        def String_encode(string):
            """Value encoder for String literals without escapes"""
            for c in string:
                if ord(c) < 0x20 or ord(c) in [0x5b, 0x5d, 0x7f]:
                    raise wsl.FormatError('Disallowed character 0x%.2x in String value: "%s"' %(ord(c), string))
            return '[' + string + ']'
    return String_encode


def Int_decode(line, i):
    """Value decoder for Int domain"""
    end = len(line)
    start = i
    while i < end and 0x30 <= ord(line[i]) <= 0x39:
        i += 1
    if i == start:
        raise wsl.ParseError('Did not find expected integer literal at character %d in line %s' %(i+1, line))
    if ord(line[start]) == 0x30 and i - start > 1:
        raise wsl.ParseError('Found integer literal (leading zero) at character %d in line %s' %(i+1, line))
    try:
        n = int(line[start:i])
    except:
        assert False
    return i, n


def Int_encode(integer):
    """Value encoder for Int domain"""
    return str(integer)


def IPv4_decode(line, i):
    end = len(line)
    x = i
    while i < end and (0x30 <= ord(line[i]) <= 0x39 or ord(line[i]) == 0x2e):
        i += 1
    token = line[x:i]
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
            if not 0 <= x < 256:
                raise ValueError()
        return '%d.%d.%d.%d' %ip
    except ValueError as e:
        raise wsl.FormatError('Not a valid ip address (need 4-tuple of integers in [0,255])')


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


def make_Enum_decode(values):
    def Enum_decode(line, i):
        """Value decoder for Enum domain"""
        end = len(line)
        x = i
        while i < end and 0x21 < ord(line[i]) and ord(line[i]) != 0x7f:
            i += 1
        if x == i:
            raise wsl.ParseError('Did not find expected token at line "%s" character %d' %(line, i))
        token = line[x:i]
        for value in values:
            if value.string == token:
                return i, value
        raise wsl.ParseError('Invalid token "%s" at line "%s" character %d; valid tokens are %s' %(token, line, i, ','.join(y for x, y in options)))
    return Enum_decode


def make_Enum_encode(options):
    def Enum_encode(value):
        """Value encoder for Enum domain"""
        return value.string
    return Enum_encode


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
