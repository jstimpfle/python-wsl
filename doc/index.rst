wsl - Python 3 library for WSL databases
========================================

This library provides an easy to use API to read and write WSL databases with
built-in and user-defined datatypes. It uses *str* for parsing and formatting
throughout.

WARNING: This library is experimental. API changes are to be expected.

The wsl library in 1 minute:
----------------------------

Read a WSL database from a file with included schema. The built-in types *ID*
and *String* are used to construct meaningful domains. These domains in turn
are used to define tables. *[Foo Bar]* is the notation for the standard WSL
string type.  Its advantage is having separate opening and closing delimiters.

.. code:: text

    $ cat db.wsl
    % DOMAIN Person ID
    % DOMAIN Comment String
    % TABLE person Person Comment
    % TABLE parent Person Person
    % KEY person P *
    % REFERENCE parent P * => person P *
    % REFERENCE parent * P => person P *
    person foo [Foo Bar]
    parent foo bar

.. code:: python3

    import wsl

    filepath = "db.wsl"
    schema, tables = wsl.parse_db(dbfilepath=filepath, schemastr=None, domain_parsers=None)
    print(tables['person'])
    print(tables['parent'])
    problems = wsl.check_integrity(schema, tables)
    for x in problems:
        print(x)

Read a WSL database from a python3 string. Here, the schema is given
separately.

.. code:: python3

    import wsl

    sch = """\
    DOMAIN Person ID
    DOMAIN Comment String
    TABLE person Person Comment
    TABLE parent Person Person
    KEY person P *
    REFERENCE parent P * => person P *
    REFERENCE parent * P => person P *
    """

    db = """\
    person foo [Foo Bar]
    parent foo bar
    """

    schema, tables = wsl.parse_db(dbstr=db, schemastr=sch, domain_parsers=None)
    print(tables['person'])
    print(tables['parent'])
    problems = wsl.check_integrity(schema, tables)
    for x in problems:
        print(x)

Given a parsed schema and a suitable tables dict, we can encode the database
back to a text string:

.. code:: python3

    txt = wsl.format_db(schema, tables, inline_schema=True)
    print(txt, end='')

User-defined datatypes
----------------------

Custom datatypes are quite easy to add. We need a decoder and an encoder for
values in database tuples. The decoder gets the line and the position in that
line where a value of that datatype is supposed to begin. It returns the parsed
value and the position of the first unconsumed character (or raises
*wsl.ParseError*). The encoder just serializes any given value to a string.
Let's make a decoder / encoder pair for base64 encoded data.

.. code:: python3

    import wsl
    import base64
    import binascii

    def base64_decode(line, i):
        end = len(line)
        beg = i
        while i < end and (0x41 <= ord(line[i]) <= 0x5a or 0x61 <= ord(line[i]) <= 0x7a or 0x30 <= ord(line[i]) <= 0x39 or line[i] in ['+','/']):
            i += 1
        if beg == i:
            raise wsl.ParseError('Did not find expected base64 literal at character %d, line "%s"' %(beg, line))
        try:
            v = base64.b64decode(line[beg:i], validate=True)
        except binascii.Error as e:
            raise wsl.ParseError('Failed to parse base64 literal at character %d, line "%s"' %(beg, line))
        return v, i

    def base64_encode(x):
        return base64.b64encode(x).decode('ascii')  # dance the unicode dance :/

Furthermore we need *domain parser*. A domain parser gets a parameterization
string (on a single line) and returns a domain object (which contains a decoder
and the encoder). This is the place where the datatype can be parameterized.
For example, this parser could be made to understand a specification of a range
of valid integers, or regular expressions that specify valid string values.

In this example, we don't add any parameterizability. But later, we might want
to specify other characters instead of + and /.

.. code:: python3

    def parse_Base64_domain(line):
        """Parser for Base64 domain declarations.

        No special syntax is recognized. Only the bare "Base64" is allowed.
        # TODO: Allow other characters instead of + and /
        """
        if line:
            raise wsl.ParseError('Construction of Base64 domain does not receive any arguments')
        class Base64Datatype:
            decode = base64_decode
            encode = base64_encode
        return Base64Datatype

Now we can parse a database using our custom parser:

.. code:: python3

    sch = """\
    DOMAIN Filename String
    DOMAIN Data Base64
    TABLE pic Filename Data
    """

    db = """\
    pic [cat.png] bGDOgm10Dm+5ZPjfNmuP4kalHWUlqT3ZAK7WdP9QniET60y5aO4WmxDCxZUTD/IKOrC2DTSLSb/tLWkb7AyYfP1oMqdw08AFEVTdl8EEA2xldYPF4FY9WB5N+87Ymmjo7vVMpiFvcMJkZZv0zOQ6eeMpCUH2MoTPrrkTHOHx/yPA2hO32gKnOGpoCZQ7q6wUS/M1oHd6DRu1CyIMeJTAZAQjJz74oYAfr8Qt1GOWVswzLkojZlODE1WcVt8nrfm3+Kj3YNS43g2zNGwf7mb2Z7OZwzMqtQNnCuDJgXN3
    """

    dps = wsl.get_builtin_domain_parsers()
    dps['Base64'] = parse_Base64_domain
    schema, tables = wsl.parse_db(dbstr=db, schemastr=sch, domain_parsers=dps)
    txt = wsl.format_db(schema, tables, inline_schema=True)
    print(txt, end='')

API listing
-----------

.. automodule:: wsl
   :members: parse_db, parse_schema, parse_row, parse_values, check_integrity, Schema, format_db, format_row, format_values
