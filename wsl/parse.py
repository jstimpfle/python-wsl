"""Module wsl.parse: Functionality for parsing a WSL database."""

from .domain import get_builtin_domain_parsers
from .exceptions import ParseError
from .lexwsl import lex_wsl_newline
from .lexwsl import lex_wsl_relation_name
from .lexwsl import lex_wsl_space
from .schema import Schema, SchemaDomain, SchemaTable, SchemaKey, SchemaForeignKey


def _is_lowercase(c):
    return 0x61 <= ord(c) <= 0x7a


def _is_uppercase(c):
    return 0x41 <= ord(c) <= 0x5a


def _is_digit(c):
    return 0x30 <= ord(c) <= 0x39


def _is_identifier(x):
    if not x:
        return False
    if not _is_lowercase(x[0]) and not _is_uppercase(x[0]):
        return False
    for c in x[1:]:
        if (not _is_lowercase(c) and not _is_uppercase(c)
            and not _is_digit(c) and not c == '_'):
            return False
    return True


def _is_variable(v):
    return len(v) != 0 and v[0:1].isalpha() and v.isalnum()


def parse_domain_decl(line, text, pos, domain_parsers):
    """Parse a domain declaration line.

    Args:
        line (str): Specification of the domain to parse.
        domain_parsers (dict): Maps domain parser names to domain parsers.
    Returns:
        wsl.SchemaDomain: The parsed domain object.
    Raises:
        wsl.ParseError: If the parse failed
    """
    ws = line.split(None, 1)
    if len(ws) != 2:
        raise ParseError('Domain declaration', text, 0, pos, 'Expecting name and datatype declaration')

    domainname, spec = ws
    ws = spec.split(None, 1)
    parsername = ws[0]
    param = ws[1] if len(ws) > 1 else ''
    parser = domain_parsers.get(parsername)
    if parser is None:
        raise ParseError('Domain declaration', text, 0, pos, 'Parser "%s" not available' %(parsername,))

    funcs = parser(param)
    return SchemaDomain(domainname, spec, funcs)


def parse_table_decl(line, text, pos):
    """Parse a table declaration ilne.

    Args:
        line (str): The table declaration.
    Returns:
        wsl.SchemaTable: The parsed table object.
    Raises:
        wsl.ParseError: If the parse failed.
    """
    spec = line
    ws = line.split()
    if not ws:
        raise ParseError('Table declaration', text, 0, pos, 'empty line')
    name, cols = ws[0], tuple(ws[1:])
    return SchemaTable(name, spec, cols, colnames=[])


def parse_key_decl(line, text, pos):
    """Parse a key constraint declaration.

    Args:
        line (str): The key declaration
    Returns:
        (str, list): A 2-tuple (table, variables) holding the table name on
            which the key constraint is placed, and the variables or "*"
            wildcards split into a list.
    Raises:
        wsl.ParseError: If the parse failed
    """
    ws = line.split(None, 1)
    if len(ws) != 2:
        raise ParseError('KEY declaration', text, 0, pos, 'Expected key name and specification')

    name, spec = ws[0], ws[1]
    if not _is_identifier(name):
        raise ParseError('KEY declaration', text, 0, pos, 'Invalid key name')

    ix = []
    ws = spec.split()
    table = ws[0]
    vs = ws[1:]
    for i, v in enumerate(vs):
        if v != '*' and not _is_variable(v):
            raise ParseError('KEY declaration', text, 0, pos, 'Invalid variable name "%s"' %(v,))
        elif v != '*':
            ix.append(i)

    return SchemaKey(name, spec, table, tuple(ix))


def parse_foreignkey_decl(line, text, pos, tables):
    """Parse a REFERENCE constraint declaration.

    Args:
        line (str): holds reference declaration (without the leading REFERENCE
            keyword)
    Returns:
        (str, list, str, list): a 4-tuple (table1, vars2, table2, vars2) holding
            the local and foreign table names and variable lists.
    Raises:
        wsl.ParseError: If the parse failed
    """
    ws = line.split(None, 1)
    if len(ws) < 2:
        raise ParseError('REFERENCE declaration', text, 0, pos, 'Need a name and a datatype')

    name, spec = ws
    if not _is_identifier(name):
        raise ParseError('REFERENCE declaration', text, 0, pos, 'Invalid REFERENCE name')

    parts = spec.split('=>')
    if len(parts) != 2:
        raise ParseError('REFERENCE declaration', text, 0, pos, 'Expected <local key spec> => <foreign key spec>')

    lws = parts[0].split(None, 1)
    if len(lws) != 2:
        raise ParseError('REFERENCE declaration', text, 0, pos, 'Error in left-hand side of "=>"')
    table1, vs1 = lws[0], lws[1].split()
    if table1 not in tables:
        raise ParseError('REFERENCE declaration', text, 0, pos, 'Local table "%s" is not defined' %(table1,))
    if len(vs1) != len(tables[table1].columns):
        raise ParseError('REFERENCE declaration', text, 0, pos, 'Number of columns in left-hand side of "=>" (%d) does not match number of columns of table "%s" (%d)' %(len(vs1), tables[table1].name, len(tables[table1].columns)))

    rws = parts[1].split(None, 1)
    if len(rws) != 2:
        raise ParseError('REFERENCE declaration', text, 0, pos, 'Error in right-hand side of "=>"')
    table2, vs2 = rws[0], rws[1].split()
    if table2 not in tables:
        raise ParseError('REFERENCE declaration', text, 0, pos, 'Foreign table "%s" is not defined' %(table2,))
    if len(vs2) != len(tables[table2].columns):
        raise ParseError('REFERENCE declaration', text, 0, pos, 'Number of columns in right-hand side of "=>" (%d) does not match number of columns of table "%s" (%d)' %(len(vs2), tables[table2].name, len(tables[table2].columns)))

    d1, d2 = {}, {}

    # build maps (variable -> column index) for both sides
    for (table, vs, d, side) in [(table1, vs1, d1, 'left'), (table2, vs2, d2, 'right')]:
        for i, v in enumerate(vs):
            if v == '*':
                continue
            if not _is_variable(v):
                raise ParseError('REFERENCE declaration', text, 0, pos, 'Invalid variable "%s"' %(v,))

            if v in d:
                raise ParseError('REFERENCE declaration', text, 0, pos, 'Variable "%s" used twice on %s side of "=>"' %(v, side))
            d[v] = i

    if sorted(d1.keys()) != sorted(d2.keys()):
        raise ParseError('REFERENCE declaration', text, 0, pos, 'Different variables used on both sides of "=>"')

    # use maps to pair columns
    ix1 = tuple(i for _, i in sorted(d1.items()))
    ix2 = tuple(i for _, i in sorted(d2.items()))

    return SchemaForeignKey(name, spec, table1, ix1, table2, ix2)


def parse_schema(schemastr, domain_parsers=None):
    """Parse a wsl schema (without *%* escapes)

    Args:
        schemastr (str): The schema string to parse
        domain_parsers (dict): maps parser names to parsers
    Returns:
        wsl.Schema: The parsed schema object
    Raises:
        wsl.ParseError: If the parse failed
    """
    if domain_parsers is None:
        domain_parsers = get_builtin_domain_parsers()

    text = schemastr

    domains = {}
    tables = {}
    keys = {}
    foreignkeys = {}
    colnames = {}

    domainspecs = set()
    tablespecs = set()
    keyspecs = set()
    foreignkeyspecs = set()
    colnamespecs = set()

    i = 0
    end = len(text)
    while i < end:
        if text[i] == '\n':
            i += 1
            continue

        eol = text.find('\n', i)
        if eol == -1:
            eol = len(text)

        line = text[i:eol]

        ws = line.split(None, 1)
        if len(ws) != 2:
            ws.append('')

        kw, spec = ws
        if kw == 'DOMAIN':
            domainspecs.add((spec, i))
        elif kw == 'TABLE':
            tablespecs.add((spec, i))
        elif kw == 'KEY':
            keyspecs.add((spec, i))
        elif kw == 'REFERENCE':
            foreignkeyspecs.add((spec, i))
        else:
            pass  # XXX

        i = eol

    for spec, pos in domainspecs:
        domain = parse_domain_decl(spec, text, pos, domain_parsers)
        if domain.name in domains:
            raise ParseError('Schema', text, 0, pos, 'Redeclaration of domain "%s"' %(domain.name,))
        domains[domain.name] = domain

    for spec, pos in tablespecs:
        table = parse_table_decl(spec, text, pos)
        if table.name in tables:
            raise ParseError('Schema', text, 0, pos, 'Redeclaration of table "%s"' %(table.name,))
        tables[table.name] = table

    for spec, pos in keyspecs:
        key = parse_key_decl(spec, text, pos)
        if key.name in keys:
            raise ParseError('Schema', text, 0, pos, 'Redeclaration of key "%s"' %(key.name,))
        keys[key.name] = key

    for spec, pos in foreignkeyspecs:
        fkey = parse_foreignkey_decl(spec, text, pos, tables)
        if fkey.name in foreignkeys:
            raise ParseError('Schema', text, 0, pos, 'Redeclaration of foreign key "%s"' %(fkey.name,))
        foreignkeys[fkey.name] = fkey

    return Schema(text, domains, tables, keys, foreignkeys)


def parse_tokens(text, i, lexers):
    """Parse a database tuple of tokens according to *domain_objects*, separated by single spaces.

    Args:
        text (str): holds a database tuple.
        i (int): An index into *text* where the space is supposed to be.
        lexers (list): A list of lexers corresponding to the columns of the
            database table.
    Returns:
        tuple: A tuple containing the lexed tokens.
    Raises:
        wsl.ParseError: The called lexers raise ParseErrors if lexing fails.
    """
    end = len(text)
    toks = []
    for lexer in lexers:
        i, _ = lex_wsl_space(text, i)
        i, tok = lexer(text, i)
        toks.append(tok)
    i, _ = lex_wsl_newline(text, i)
    return i, tuple(toks)


def parse_row(text, i, lexers_of_relation):
    """Parse a database row (a relation name and according tuple of tokens).

    This lexes a relation name, which is used to lookup lexers from
    *lexers_of_relation*. Then *parse_tokens()* is called with these lexers.

    Args:
        text (str): holds a database tuple.
        lexers_of_relation (dict): maps relation names to the list of the
            lexers of their according columns.
    Returns:
        (int, (str, tuple)): The index of the first unconsumed character and a
        2-tuple holding the lexed relation name and lexed tokens.
    Raises:
        wsl.ParseError: if the lex failed.
    """
    start = i
    end = len(text)
    i, relation = lex_wsl_relation_name(text, i)
    lexers = lexers_of_relation.get(relation)
    if lexers is None:
        raise ParseError('Table name', text, start, i, 'No such table: "%s"' %(relation,))
    i, tokens = parse_tokens(text, i, lexers)
    return i, (relation, tokens)


def split_schema(text, i):
    end = len(text)

    lines = []

    while i < end and text[i] == '%':
        i += 1
        while i < end and text[i] == ' ':
            i += 1
        lstart = i
        while i < end and text[i] != '\n':
            i += 1
        if not i < end:
            raise ValueError('Schema line missing newline')

        lines.append(text[lstart:i])
        i += 1

    return i, ''.join(line + '\n' for line in lines)


def parse_db(dbfilepath=None, dbstr=None, schema=None, schemastr=None, domain_parsers=None):
    """Convenience def to parse a WSL database.

    This routine parses a database given schema information.

    Zero or one of *schema* or *schemastr* must be given. If *schema* is *None*,
    the schema is parsed from a schema string. If *schemastr* is also None, the
    schema string is assumed to be inline before the database contents.

    One, and only one, of *dbfilepath* or *dbstr* should be given.

    Args:
        dbfilepath (str): Path to the file that contains the database.
        dbstr (str): A string that holds the database.
        schema (wsl.Schema): Optional schema. If not given, the schema is
            expected to be given in text form (either in *schemastr* or inline
            as part of the database).
        schemastr (str): Optional schema specification. If not given, the schema
            is expected to be given either in *schema* or inline as part of the
            database (each line prefixed with *%*).
        domain_parsers (dict): Optional domain parsers for the domains used in
            the database. If not given, the built-in parsers are used.
    Returns:
        A tuple *(schema, tables)*. *schema* is the parsed *wsl.Schema* and
            *tables* is a *dict* mapping each table name to a list of database
            rows (parsed values)
    Raises:
        wsl.ParseError: if the parse failed.
    """
    assert dbfilepath is None or isinstance(dbfilepath, str)
    assert dbstr is None or isinstance(dbstr, str)
    assert schema is None or isinstance(schema, Schema)
    assert schemastr is None or isinstance(schemastr, str)
    assert domain_parsers is None or isinstance(domain_parsers, dict)

    if len(list(x for x in [schema, schemastr] if x is not None)) > 1:
        raise ValueError('At most one of "schema" or "schemastr" arguments is allowed')

    if len(list(x for x in [dbfilepath, dbstr] if x is not None)) != 1:
        raise ValueError('Need exactly one of "dbfilepath" or "dbstr" arguments')

    if dbfilepath is not None:
        with open(dbfilepath, "r", encoding="utf-8", newline='\n') as f:
            text = f.read()

    if dbstr is not None:
        text = dbstr

    assert isinstance(text, str)

    i = 0

    if schema is None:
        if schemastr is None:
            i, schemastr = split_schema(text, i)

        schema = parse_schema(schemastr, domain_parsers)

    lexers_of_relation = {}
    decoders_of_relation = {}

    for table in schema.tables.values():
        lexers_of_relation[table.name] = tuple(schema.domains[domainname].funcs.wsllex for domainname in table.columns)
        decoders_of_relation[table.name] = tuple(schema.domains[domainname].funcs.decode for domainname in table.columns)

    tokens_of_relation = { table.name: [] for table in schema.tables.values() }

    end = len(text)
    while i < end:
        if text[i] != '\n':
            i, (table, tup) = parse_row(text, i, lexers_of_relation)
            tokens_of_relation[table].append(tup)
        else:
            i += 1

    tables = { table.name: [] for table in schema.tables.values() }

    for tablename, rows in tables.items():
        ps = decoders_of_relation[tablename]
        for toks in tokens_of_relation[tablename]:
            rows.append(tuple(f(x) for f, x in zip(ps, toks)))

    return schema, tables
