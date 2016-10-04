"""Module wsl.parse: Functionality for parsing a WSL database."""

import wsl


def _is_lowercase(c):
    return 0x61 <= ord(c) <= 0x7a


def _is_uppercase(c):
    return 0x41 <= ord(c) <= 0x5a


def _is_digit(c):
    return 0x30 <= ord(c) <= 0x39


def _is_identifier(x):
    return (x and (_is_lowercase(x[0]) or _is_uppercase(x[0]))
             and all(_is_lowercase(c) or _is_uppercase(c) or c == '_' for c in x[1:]))


def _is_variable(v):
    return len(v) != 0 and v[0:1].isalpha() and v.isalnum()


def parse_domain_decl(line, domain_parsers):
    """Parse a domain declaration line.

    Args:
        line (str): contains specification of the domain to parse.
        domain_parsers (dict): dict mapping domain parser names to domain parsers.
    Returns:
        wsl.SchemaDomain: The parsed domain object.
    Raises:
        wsl.ParseError: If the parse failed
    """
    ws = line.split(None, 1)
    if len(ws) != 2:
        raise wsl.ParseError('Failed to parse domain: expecting name and datatype declaration in line: %s' %(line,))

    domainname, spec = ws
    ws = spec.split(None, 1)
    parsername = ws[0]
    param = ws[1] if len(ws) > 1 else ''
    parser = domain_parsers.get(parsername)
    if parser is None:
        raise wsl.ParseError('Parser "%s" not available while parsing DOMAIN declaration' %(parser_name,))

    funcs = parser(param)
    return wsl.SchemaDomain(domainname, spec, funcs)


def parse_table_decl(line):
    """Parse a domain declaraation ilne.

    Args:
        line (str): The table declaration.
    Returns:
        wsl.SchemaTable: The parsed table object.
    Raises:
        wsl.ParseError: If the parse failed.
    """
    ws = line.split()
    if not ws:
        raise wsl.ParseError('Failed to parse table declaration: %s' %(line,))
    name, cols = ws[0], tuple(ws[1:])
    spec = line

    return wsl.SchemaTable(name, spec, cols, colnames=[])


def parse_logic_tuple(line):
    ws = line.split()
    return name, tuple(cols)


def parse_key_decl(line):
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
        raise wsl.ParseError('Failed to parse schema key: Expected name and specification in line %s' %(line,))

    name, spec = ws[0], ws[1]
    if not _is_identifier(name):
        raise wsl.ParseError('Bad KEY name: "%s": Must be an identifier, in line "%s"' %(name, line))

    ix = []
    ws = spec.split()
    table = ws[0]
    vs = ws[1:]
    for i, v in enumerate(vs):
        if v != '*' and not _is_variable(v):
            raise wsl.ParseError('Invalid variable name "%s" while parsing key declaration "%s"' %(v, line))
        elif v != '*':
            ix.append(i)

    return wsl.SchemaKey(name, spec, table, tuple(ix))


def parse_foreignkey_decl(line, tables):
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
        raise wsl.ParseError('Failed to parse REFERENCE declaration "%s": Need a name and a datatype' %(line,))

    name, spec = ws
    if not _is_identifier(name):
        raise wsl.ParseError('Bad REFERENCE name: "%s": Must be an identifier, in line "%s"' %(name, line))

    parts = spec.split('=>')
    if len(parts) != 2:
        raise wsl.ParseError('Could not parse "%s" as REFERENCE constraint' %(line,))

    lws = parts[0].split(None, 1)
    if len(lws) != 2:
        raise wsl.ParseError('Could not parse left-hand side of REFERENCE constraint "%s"' %(line,))
    table1, vs1 = lws[0], lws[1].split()
    if table1 not in tables:
        raise wsl.ParseError('Undefined table "%s" in REFERENCE constraint "%s"' %(table1, line))
    if len(vs1) != len(tables[table1].columns):
        raise wsl.ParseError('Wrong number of columns on left-hand side of REFERENCE constraint "%s"' %(line,))

    rws = parts[1].split(None, 1)
    if len(rws) != 2:
        raise wsl.ParseError('Could not parse right-hand side of REFERENCE constraint "%s"' %(line,))
    table2, vs2 = rws[0], rws[1].split()
    if table2 not in tables:
        raise wsl.ParseError('Undefined table "%s" in REFERENCE constraint "%s"' %(table1, line))
    if len(vs2) != len(tables[table2].columns):
        raise wsl.ParseError('Wrong number of columns on right-hand side of REFERENCE constraint "%s"' %(line,))

    d1, d2 = {}, {}

    # build maps (variable -> column index) for both sides
    for (table, vs, d) in [(table1, vs1, d1), (table2, vs2, d2)]:
        if len(vs) != len(tables[table].columns):
            raise wsl.ParseError('Arity mismatch for table "%s" while parsing KEY constraint "%s %s"' %(table, name, spec))

        for i, v in enumerate(vs):
            if v == '*':
                continue
            if not _is_variable(v):
                raise wsl.ParseError('Invalid variable "%s" while parsing REFERENCE constraint "%s %s"' %(v, name, spec))

            if v in d:
                raise wsl.ParseError('Variable "%s" used twice on the same side while parsing REFERENCE constraint "%s %s"' %(v, name, name))
            d[v] = i

    if sorted(d1.keys()) != sorted(d2.keys()):
        raise wsl.ParseError('Different variables used on both sides of "=>" while parsing REFERENCE constraint "%s %s"' %(name, spec))

    # use maps to pair columns
    ix1 = tuple(i for _, i in sorted(d1.items()))
    ix2 = tuple(i for _, i in sorted(d2.items()))

    return wsl.SchemaForeignKey(name, spec, table1, ix1, table2, ix2)


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
        domain_parsers = wsl.get_builtin_domain_parsers()

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

    for line in schemastr.splitlines():
        line = line.strip()
        if not line:
            continue

        ws = line.split(None, 1)
        if len(ws) != 2:
            raise wsl.ParseError('Failed to parse line: %s' %(line,))

        kw, spec = ws
        if kw == 'DOMAIN':
            domainspecs.add(spec)
        elif kw == 'TABLE':
            tablespecs.add(spec)
        elif kw == 'KEY':
            keyspecs.add(spec)
        elif kw == 'REFERENCE':
            foreignkeyspecs.add(spec)
        else:
            pass  # XXX

    for spec in domainspecs:
        domain = parse_domain_decl(spec, domain_parsers)
        if domain.name in domains:
            raise ParseError('Redeclaration of domain "%s" in line: %s' %(domain.name, line))
        domains[domain.name] = domain

    for spec in tablespecs:
        table = parse_table_decl(spec)
        if table.name in tables:
            raise wsl.ParseError('Redeclaration of table "%s" in line: %s' %(table.name, line))
        tables[table.name] = table

    for spec in keyspecs:
        key = parse_key_decl(spec)
        if key.name in keys:
            raise wsl.ParseError('Redeclaration of key "%s" in line: %s' %(key.name, line))
        keys[key.name] = key

    for spec in foreignkeyspecs:
        fkey = parse_foreignkey_decl(spec, tables)
        if fkey.name in foreignkeys:
            raise wsl.ParseError('Redeclaration of foreign key "%s" in line: "%s"' %(fkey.name, line))
        foreignkeys[fkey.name] = fkey

    return wsl.Schema(schemastr, domains, tables, keys, foreignkeys)


def parse_relation_name(line, i):
    end = len(line)
    if not 0x41 <= ord(line[i]) <= 0x5a and not 0x61 <= ord(line[i]) <= 0x7a:
        raise wsl.ParseError('Expected table name at character %d in line "%s"' %(i+1, line))
    x = i
    while i < end and (0x41 <= ord(line[i]) <= 0x5a or 0x61 <= ord(line[i]) <= 0x7a):
        i += 1
    return line[x:i], i


def parse_space(line, i):
    """Parse a space that separates two tokens in a database tuple line.

    This function parses expects precisely one space character, and throws an
    exception if the space is not found.

    Args:
        line (str) : holds a database tuple.
        i (int): An index into the line where the space is supposed to be.

    Returns:
        int: If the parse succeeds, the index of the next character following the space.

    Raises:
        wsl.ParseError: If no space is found.
    """
    end = len(line)
    if i == end or ord(line[i]) != 0x20:
        raise wsl.ParseError('Expected space character in line %s at position %d' %(line, i))
    return i+1


def parse_values(line, i, domain_objects):
    """Parse values from line according to *domain_objects*, separated by single spaces.

    Args:
        line (str): holds a database tuple.
        i (int): An index into the line where the space is supposed to be.
        domain_objects (dict): dict mapping the name of each domain that is expected in this line to its domain object.

    Returns:
        tuple: A tuple containing the parsed values.

    Raises:
        wsl.ParseError: The called parsers raise ParseErrors if parsing fails.
    """
    end = len(line)
    vs = []
    for do in domain_objects:
        i = parse_space(line, i)
        val, i = do.decode(line, i)
        vs.append(val)
    if i != end:
        raise wsl.ParseError('Expected EOL at character %d in line %s' %(i+1, line))
    return tuple(vs)


def parse_row(line, objects_of_relation):
    """Parse a database tuple (a relation name and according values).

    This def parses a relation name, which is used to lookup a domain object
    in *objects_of_relation*. Then that object is used to call *parse_values()*.

    Args:
        line (str): holds a database tuple.
        objects_of_relation (dict): maps relation names to the list of the
            domain objects of their according columns.

    Returns:
        (str, tuple): A 2-tuple (relation, values), i.e. the relation name and a tuple containing the parsed values.

    Raises:
        wsl.ParseError: if the parse failed.
    """
    end = len(line)
    relation, i = parse_relation_name(line, 0)
    dos = objects_of_relation.get(relation)
    if dos is None:
        raise wsl.ParseError('No such table: "%s" while parsing line: %s' %(relation, line))
    values = parse_values(line, i, dos)
    return relation, values


def parse_db(dbfilepath=None, dblines=None, dbstr=None, schemastr=None, domain_parsers=None):
    """Convenience def to parse a WSL database.

    One, and only one, of *dbfilepath*, *dblines* or *dbstr* should be given.

    This parses the schema (from *schemastr* if given, or else as inline schema
    from the database), and then calls *parse_row()* for each line in *lines*.

    Args:
        dbfilepath (str or bytes): Path to the file that contains the database.
        dblines (iter): An iterable over the (str) lines of the database.
            This works for all TextIOBase objects, like *sys.stdin* or
            open()ed files.
        dbstr (str): A string that holds the database.
        schemastr (str): Optional extern schema specification. If *None* is
            given, the schema is expected to be given inline as part of the
            database (each line prefixed with *%*)
        domain_parsers (list): Optional domain parsers for the domains used in
            the database. If not given, the built-in parsers are used.

    Returns:
        (wsl.Schema, dict): A 2-tuple *(schema, tuples_of_relation)* consisting
        of the parsed schema and a dict mapping each relation name (in
        *schema.relations*) to a list of database tuples.

    Raises:
        wsl.ParseError: if the parse failed.
    """
    if int(dbfilepath is not None) + int(dblines is not None) + int(dbstr is not None) != 1:
        raise ValueError('parse_db() needs exactly one of dbfilepath, dblines or dbstr')

    if dbfilepath is not None:
        lines = open(dbfilepath, "r", encoding="utf-8", newline='\n')
    if dblines is not None:
        lines = dblines
    if dbstr is not None:
        lines = dbstr.split('\n')

    if schemastr is None:
        schemalines = []
        for line in lines:
            if not line.startswith('%'):
                break
            schemalines.append(line.lstrip('% '))
        schemastr = ''.join(line + '\n' for line in schemalines)
    else:
        # read the first line of input. This is because the other branch
        # has to read one line of input as well (to recognize the end of
        # the schema header
        for line in lines:
            break
    schema = parse_schema(schemastr, domain_parsers)

    tables = {}
    for tablename in schema.tables:
        arity = len(schema.tables[tablename].columns)
        keys = {}
        for key in schema.keys.values():
            if key.table == tablename:
                keys[key.name] = key.columns
        refs = {}
        for fkey in schema.foreignkeys.values():
            if fkey.table == tablename:
                refs[fkey.table] = fkey.columns, fkey.reftable, fkey.refcolumns
        tables[tablename] = wsl.DbTable(tablename, arity, keys=keys, refs=refs)
    for t in tables.values():
        t.fix_refs(tables)

    objects_of_relation = {}
    for table in schema.tables.values():
        objs = []
        for domainname in table.columns:
            objs.append(schema.domains[domainname].funcs)
        objects_of_relation[table.name] = tuple(objs)

    while line is not None:
        line = line.strip()
        if line:
            r, tup = parse_row(line, objects_of_relation)
            tables[r].insert(tup)
        try:
            line = next(lines)
        except StopIteration:
            line = None

    return schema, tables


if __name__ == '__main__':
    from schema import SchemaTable
    parse_db(dbfilepath='/tmp/test.wsl')
