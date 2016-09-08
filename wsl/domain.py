"""Module wsl.domain: Built-in WSL domain parsers.

Users can add their own domains by providing a parser following the example of
the built-in ones.

A parser takes a domain declaration, which is a string that must be completely
consumed. It returns a domain object with *decode* and *encode* member defs as
explained in the following paragraph.

The *decode* member of a domain object is a function that takes a string and a
start index into the string. It returns a pair *(val, j)* where *val* is the
parsed value and *j* is the position of the first unconsumed character. A
*wsl.ParseError* is raised if the decode fails.

The *encode* member of a domain object is a function that takes an object of the
type that *decode* returns, and returns a string holding the serialized value. A
*wsl.FormatError* is raised if the encode fails.
"""

import wsl

def parse_ID_domain(line):
    """Parser for ID domain declarations.

    No special syntax is recognized. Only the bare "ID" is allowed.
    """
    if line:
        raise wsl.ParseError('Construction of ID domain does not receive any arguments')
    class IDDomain:
        decode = id_decode
        encode = id_encode
    return IDDomain

def parse_String_domain(line):
    if line:
        raise wsl.ParseError('Construction of String domain does not receive any arguments')
    class StringDomain:
        decode = string_decode
        encode = string_encode
    return StringDomain

def parse_Int_domain(line):
    if line:
        raise wsl.ParseError('Construction of Integer domain does not receive any arguments')
    class IntegerDomain:
        decode = integer_decode
        encode = integer_encode
    return IntegerDomain

def parse_Enum_domain(line):
    values = line.split()
    options = list(enumerate(values))
    class EnumDomain:
        decode = make_enum_decode(options)
        encode = make_enum_encode(options)
    return EnumDomain

def parse_ipv4_domain(line):
    if line.strip():
        raise wsl.ParseError('IPv4 domain doesn\'t take any arguments')
    class IPv4:
        decode = ipv4_decode
        encode = ipv4_encode
    return IPv4

def id_decode(line, i):
    """Value decoder for ID domain"""
    end = len(line)
    x = i
    while i < end and ord(line[i]) > 0x20 and ord(line[i]) != 0x7f:
        i += 1
    if x == i:
        raise wsl.ParseError('EOL or invalid character while expecting ID at character %d in line "%s"' %(i+1, line))
    return (line[x:i], i)

def id_encode(idval):
    """Value encoder for ID domain"""
    for c in idval:
        if ord(c) < 0x20 or ord(c) in [0x20, 0x5b, 0x5d, 0x7f]:
            raise ValueError('Disallowed character %c in ID value: %s' %(c, idval))
    return idval

def string_decode(line, i):
    """Value decoder for String domain"""
    end = len(line)
    if i == end or ord(line[i]) != 0x5b:
        raise wsl.ParseError('Did not find expected WSL string literal at character %d in line %s' %(i+1, line))
    i += 1
    x = i
    while i < end and ord(line[i]) != 0x5d:
        i += 1
    if i == end:
        raise wsl.ParseError('EOL while looking for closing quote in line %s' %(line))
    return (line[x:i], i+1)

def string_encode(string):
    """Value encoder for String domain"""
    for c in string:
        if ord(c) < 0x20 or ord(c) in [0x5b, 0x5d, 0x7f]:
            raise ValueError('Disallowed character %c in String value: %s' %(c, string))
    return '[' + string + ']'

def integer_decode(line, i):
    """Value decoder for Integer domain"""
    end = len(line)
    if i == end or not 0x30 <= ord(line[i]) < 0x40:
        raise wsl.ParseError('Did not find expected integer literal at character %d in line %s' %(i+1, line))
    if ord(line[i]) == 0x30:
        raise wsl.ParseError('Found integer literal starting with zero at character %d in line %s' %(i+1, line))
    n = ord(line[i]) - 0x30
    i += 1
    while i < end and 0x30 <= ord(line[i]) < 0x40:
        n = 10*n + ord(line[i]) - 0x30
        i += 1
    return (n, i)

def integer_encode(integer):
    """Value encoder for Integer domain"""
    return str(integer)

def make_enum_decode(options):
    def enum_decode(line, i):
        """Value decoder for Enum domain"""
        end = len(line)
        x = i
        while i < end and 0x21 < ord(line[i]) and ord(line[i]) != 0x7f:
            i += 1
        if x == i:
            raise wsl.ParseError('Did not find expected token at line "%s" character %d' %(line, i))
        token = line[x:i]
        for option in options:
            v, t = option
            if t == token:
                return (option, i)
        raise wsl.ParseError('Invalid token "%s" at line "%s" character %d; valid tokens are %s' %(token, line, i, ','.join(y for x, y in options)))
    return enum_decode

def make_enum_encode(options):
    def enum_encode(value):
        """Value encoder for Enum domain"""
        i, token = value
        return token
    return enum_encode

def ipv4_decode(line, i):
    end = len(line)
    x = i
    while i < end and (0x30 <= ord(line[i]) < 0x40 or ord(line[i]) == 0x2e):
        i += 1
    token = line[x:i]
    ws = token.split('.')
    if len(ws) == 4:
        try:
            ip = tuple(map(int, ws))
            for b in ip:
                if b < 0 or b >= 256:
                    raise ValueError()
            return (ip, i)
        except ValueError:
            pass
    raise wsl.ParseError('IPv4 address must be 4-tuple of 1 byte integers (0-255)')

def ipv4_encode(ip):
    try:
        a,b,c,d = ip
        for x in [a,b,c,d]:
            if not 0 <= x < 256:
                raise ValueError()
        return '%d.%d.%d.%d' %ip
    except ValueError as e:
        raise ValueError('Not a valid ip address (need 4-tuple of integers in [0,255])')

builtin_domain_parsers = (
    ('ID', parse_ID_domain),
    ('String', parse_String_domain),
    ('Enum', parse_Enum_domain),
    ('Int', parse_Int_domain),
    ('IPv4', parse_ipv4_domain)
)
