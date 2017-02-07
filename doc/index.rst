========================================
wsl - Python 3 library for WSL databases
========================================

This library provides an easy to use API to read and write WSL databases with
built-in and user-defined datatypes. It uses *str* for parsing and formatting
throughout.

This library is experimental. API changes are to be expected.

The wsl library in 1 minute:
============================

Read a WSL database from a file with included schema. The built-in types *ID*
and *String* are used to construct meaningful domains. These domains in turn
are used to define tables. *[Foo Bar]* is the notation for the standard WSL
string type. Its advantage is having separate opening and closing delimiters.

.. code:: text

    $ cat db.wsl
    % DOMAIN Person ID
    % DOMAIN Comment String
    % TABLE person Person Comment
    % TABLE parent Person Person
    % KEY Person person P *
    % REFERENCE Person1OfParent parent P * => person P *
    % REFERENCE Person2OfParent parent * P => person P *
    person foo [Foo Bar]
    parent foo bar

.. code:: python3

    import wsl

    dbfilepath = "db.wsl"
    schema, tables = wsl.parse_db(dbfilepath=dbfilepath)
    for person in tables['person']:
        print(person)

Read a WSL database from a python3 string. Here, the schema is given
separately.

.. code:: python3

    import wsl

    schemastr = """\
    DOMAIN Person ID
    DOMAIN Comment String
    TABLE person Person Comment
    TABLE parent Person Person
    KEY Person person P *
    REFERENCE Person1OfParent parent P * => person P *
    REFERENCE Person2OfParent parent * P => person P *
    """

    dbstr = """\
    person foo [Foo Bar]
    parent foo bar
    """

    schema, tables = wsl.parse_db(dbstr=dbstr, schemastr=schemastr)
    for person in tables['person']:
        print(person)

Given a parsed schema and a suitable tables dict, we can encode the database
back to a text string:

.. code:: python3

        include_schema = True
        text = wsl.format_db(schema, tables, include_schema)
        print(text, end='')

User-defined datatypes
======================

Custom datatypes are quite easy to add. We need a decoder and an encoder for
values in database tuples. The decoder gets an already lexed token.  It returns
the decoded value or raises *wsl.ParseError*.

The encoder is the inverse. It takes a value and returns a (*str*) token or
raises *wsl.FormatError*.

Let's make a decoder / encoder pair for base64 encoded data.

.. code:: python3

    import wsl
    import base64
    import binascii

    def Base64_decode(token):
        try:
            v = base64.b64decode(token, validate=True)
        except binascii.Error as e:
            raise wsl.ParseError('Failed to parse base64 literal at character %d, line "%s"' %(beg, line))
        return v

    def Base64_encode(x):
        return base64.b64encode(x).decode('ascii')


Furthermore we need a *domain parser*. A domain parser gets a *parameterization
string* (on a single line) and returns a *domain object*.

The parameterization string is what comes after the name of the datatype in the
DOMAIN declaration line of the database schema.

A domain object holds the decoder and encoder callables as well as a lexer and
an unlexer. The latter two can usually be taken from the wsl library.

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
            wsllex = wsl.lex_wsl_identifier
            wslunlex = wsl.unlex_wsl_identifier
            decode = Base64_decode
            encode = Base64_encode
        return Base64Datatype


Now we can parse a database using our custom parser:

.. code:: python3

    schemastr = """\
    DOMAIN Filename String
    DOMAIN Data Base64
    TABLE pic Filename Data
    """

    dbstr = """\
    pic [cat.png] bGDOgm10Dm+5ZPjfNmuP4kalHWUlqT3ZAK7WdP9QniET60y5aO4WmxDCxZUTD/IKOrC2DTSLSb/tLWkb7AyYfP1oMqdw08AFEVTdl8EEA2xldYPF4FY9WB5N+87Ymmjo7vVMpiFvcMJkZZv0zOQ6eeMpCUH2MoTPrrkTHOHx/yPA2hO32gKnOGpoCZQ7q6wUS/M1oHd6DRu1CyIMeJTAZAQjJz74oYAfr8Qt1GOWVswzLkojZlODE1WcVt8nrfm3+Kj3YNS43g2zNGwf7mb2Z7OZwzMqtQNnCuDJgXN3
    """

    dps = wsl.get_builtin_domain_parsers()
    dps['Base64'] = parse_Base64_domain
    schema, tables = wsl.parse_db(dbstr=dbstr, schemastr=schemastr, domain_parsers=dps)
    include_schema = True
    print(wsl.format_db(schema, tables, include_schema), end='')


API listing
===========

Schema
------

.. automodule:: wsl
   :members: Schema, SchemaDomain, SchemaTable, SchemaKey, SchemaForeignKey


Integrity
---------

.. automodule:: wsl
   :members: check_database_integrity


Database
--------

.. autoclass:: wsl.Database
   :members: __init__

Exceptions
----------

.. automodule:: wsl
   :members: WslValueError, LexError, UnlexError, ParseError, FormatError, IntegrityError

Lexing
------

.. automodule:: wsl
   :members: lex_json_string, lex_json_int, unlex_json_string, unlex_json_int, make_make_jsonreader, make_make_jsonwriter, lex_wsl_space, lex_wsl_newline, lex_wsl_identifier, lex_wsl_relation_name, lex_wsl_string_without_escapes, lex_wsl_string_with_escapes, lex_wsl_int, unlex_wsl_identifier, unlex_wsl_string_without_escapes, unlex_wsl_string_with_escapes, unlex_wsl_int, make_make_wslreader, make_make_wslwriter

Parsing
-------

.. automodule:: wsl
   :members: parse_db, parse_schema, parse_row, get_builtin_domain_parsers

Formatting
----------

.. automodule:: wsl
   :members: format_db, format_schema, format_row, format_values
