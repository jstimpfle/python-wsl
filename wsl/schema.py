"""Module wsl.schema: python class representing WSL database schema"""


def _is_string(x):
    return isinstance(x, str)


def _is_list_or_tuple(x):
    return isinstance(x, list) or isinstance(x, tuple)


def _is_tuple_of(tp, x):
    if not isinstance(x, tuple):
        return False
    for y in x:
        if not isinstance(y, tp):
            return False
    return True


def _is_dict_of_string_to(tp, x):
    if not isinstance(x, dict):
        return False
    for k, v in x.items():
        if not isinstance(k, str):
            return False
        if not isinstance(v, tp):
            return False
    return True


def _valid_key_indices(indices, num_columns):
    if sorted(set(indices)) != list(indices):
        return False
    for i in indices:
        if not 0 <= i < num_columns:
            return False
    return True


def _valid_foreign_key_indices(ix1, ix2, n1, n2):
    if len(ix1) != len(ix2):
        return False
    if sorted(set(ix1)) != sorted(ix1):
        return False
    if sorted(set(ix2)) != sorted(ix2):
        return False
    for i in ix1:
        if not 0 <= i < n1:
            return False
    for i in ix2:
        if not 0 <= i < n2:
            return False
    return True


class SchemaDomain:
    """Domain object

    Attributes:
        name (str): Name of the domain as used e.g. in table declarations.
        spec (str): Spec of the domain (parameterization from the definition).
        funcs: function object, holding value decoder and encoder.
    """
    def __init__(self, name, spec, funcs):
        assert _is_string(name)
        assert _is_string(spec)
        assert hasattr(funcs, 'decode')
        assert hasattr(funcs, 'encode')

        self.name = name
        self.spec = spec
        self.funcs = funcs

    def __str__(self):
        return 'DOMAIN %s %s' %(self.name, self.spec)


class SchemaTable:
    """Table object

    Attributes:
        name (str): Name of the table.
        spec (str): Spec of the table (definition string).
        columns: A tuple of domain names indicating the columns of the table.
        colnames: A list containing tuples of column names. The list may be
            empty. Each tuple must be of the same length as *column*.
            It holds a possible naming of the columns. Each name may be *None*
            in which case there is no name availble for the column in this
            naming.
            
    """
    def __init__(self, name, spec, columns, colnames):
        assert _is_string(name)
        assert _is_string(spec)
        assert _is_tuple_of(str, columns)

        self.name = name
        self.spec = spec
        self.columns = columns
        self.colnames = colnames

    def __str__(self):
        return 'TABLE %s %s' %(self.name, self.spec)


class SchemaKey:
    """Unique key object

    Attributes:
        name (str): Name of the key.
        spec (str): Spec of the key (definition string).
        table (str): Name of the table on which the unique key constraint is
            placed.
        columns: Tuple of 0-based column indices in strictly ascending order.
            These are the columns on which the table rows must be unique.
    """
    def __init__(self, name, spec, table, columns):
        assert _is_string(name)
        assert _is_string(spec)
        assert _is_string(table)
        assert _is_tuple_of(int, columns)
        
        self.name = name
        self.spec = spec
        self.table = table
        self.columns = columns

    def __str__(self):
        return 'KEY %s %s' %(self.name, self.spec)


class SchemaForeignKey:
    """Foreign key object
    Attributes:
        name (str): name of the foreign key.
        spec (str): Spec of the foreign key (definition string).
        table (str): Name of the table on which the constraint is placed.
        columns: Tuple of 0-based column indices in strictly ascending order.
            These are the columns which serve as index into the foreign table.
        reftable (str): Name of the foreign table.
        refcolumns: Tuple of 0-based column indices in strictly ascending
            order. The number and types of the columns must be identical to
            those in *columns*.
    """
    def __init__(self, name, spec, table, columns, reftable, refcolumns):
        assert _is_string(name)
        assert _is_string(spec)
        assert _is_string(table)
        assert _is_tuple_of(int, columns)
        assert _is_string(reftable)
        assert _is_tuple_of(int, refcolumns)

        self.name = name
        self.spec = spec
        self.table = table
        self.columns = columns
        self.reftable = reftable
        self.refcolumns = refcolumns

    def __str__(self):
        return 'REFERENCE %s %s' %(self.name, self.spec)


class Schema:
    """Schema information for a WSL database.

    Attributes:
        spec (str): Textual specification used to construct this schema.
        domains: A dict mapping domain names to *SchemaDomain* objects.
        tables: A dict mapping table names to *SchemaTable* objects.
        keys: A dict mapping unique key names to *SchemaKey* objects.
        foreignkeys: A dict mapping foreign key names to *SchemaForeignKey* objects.
    """
    def __init__(self, spec, domains, tables, keys, foreignkeys):
        assert _is_string(spec)
        assert _is_dict_of_string_to(SchemaDomain, domains)
        assert _is_dict_of_string_to(SchemaTable, tables)
        assert _is_dict_of_string_to(SchemaKey, keys)
        assert _is_dict_of_string_to(SchemaForeignKey, foreignkeys)

        for name, x in domains.items():
            assert name == x.name
        for name, x in tables.items():
            assert name == x.name
        for name, x in keys.items():
            assert name == x.name
        for name, x in foreignkeys.items():
            assert name == x.name

        for table in tables:
            for domain in tables[table].columns:
                if domain not in domains:
                    raise ValueError('Table "%s" has a column of domain "%s" which is not defined' %(table, domain))

        for key in keys:
            if keys[key].table not in tables:
                raise ValueError('Unique key "%s" constrains table "%s" which is not defined' %(key, keys[key].table))
            if not _valid_key_indices(keys[key].columns, len(tables[table].columns)):
                raise ValueError('Invalid column specification in key constraint "%s"' %(key,))

        for fkey in foreignkeys:
            x = foreignkeys[fkey]
            table, columns = x.table, x.columns
            reftable, refcolumns = x.reftable, x.refcolumns

            if table not in tables:
                raise ValueError('Foreign key "%s" constrains table "%s" which is not defined' %(fkey, table))
            if reftable not in tables:
                raise ValueError('Foreign key "%s" references table "%s" which is not defined' %(fkey, reftable))
            if not _valid_foreign_key_indices(
                            columns, refcolumns,
                            len(tables[table].columns),
                            len(tables[reftable].columns)):
                raise ValueError('Invalid column specification in foreign key "%s"' %(fkey,))

        self.spec = spec
        self.domains = domains
        self.tables = tables
        self.keys = keys
        self.foreignkeys = foreignkeys

    def __str__(self):
        out = []
        for x in self.domains:
            out.append(x)
        for x in self.tables:
            out.append(x)
        for x in self.keys:
            out.append(x)
        for x in self.foreignkeys:
            out.append(x)
        return ''.join(line + '\n' for line in out)
