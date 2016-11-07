"""Module wsl.format: Functionality for serialization of WSL databases"""

import wsl


def format_schema(schema, escape=False):
    """Encode a schema object as a WSL schema string.

    Args:
        schema (wsl.Schema): The schema object
        escape (bool): Whether the resulting string should be escaped for
            inline schema notation.
    Returns:
        str: The textual representation of the schema. Currently, this is just
        the *spec* attribute of the schema object. If *escape=True*, each line
        is prepended with *%*, so the schema string can be used
        inline in a text file.
    """
    if escape:
        return ''.join('% ' + line + '\n' for line in schema.spec.splitlines())
    else:
        return schema.spec


def format_values(row, encoders):
    """Encode a WSL database row (without leading table name)

    Args:
        tup (tuple): Some values to encode
        encoders: Encoders according to the values in *tup*.
    Returns:
        str: A single line (including the terminating newline character).
    Raises:
        wsl.FormatError: if formatting fails.
    """
    x = []
    for val, encode in zip(tup, encoders):
        x.append(encode(val))
    return ' '.join(x) + '\n'


def format_row(table, row, encoders):
    """Encode a WSL database row (including leading table name).

    Args:
        table (str): Name of the table this row belongs to.
        row (tuple): Values according to the columns of *table*
        encoders (tuple): Encoders according to the columns of *table*
    Returns:
        str: A single line (including the terminating newline character).
    Raises:
        wsl.FormatError: if formatting fails.
    """
    x = [table]
    for val, encode in zip(row, encoders):
        x.append(encode(val))
    return ' '.join(x) + '\n'


def format_db(db, inline_schema):
    """Convenience function for formatting a WSL database.

    Args:
        db (wsl.Database): The database to format.
        inline_schema (bool): Whether to include the schema (in escaped form).
    Returns:
        An iterator yielding chunks of encoded text.
        If *inline_schema* is True, the first chunk is the textual
        representation of the schema, each line being escaped with %
        as required for WSL inline notation.
        Each following yielded chunk is the result of encoding one row of the
        database (as returned by *format_row()*).
    Raises:
        wsl.FormatError: if formatting fails.
    """
    if inline_schema:
        yield format_schema(db.schema, escape=True)
    for table in sorted(db.tables):
        encoders = []
        for x in db.schema.tables[table].columns:
            encoders.append(db.schema.domains[x].funcs.encode)
        try:
            for row in sorted(db.tables[table]):
                yield format_row(table, row, encoders)
        except wsl.FormatError as e:
            raise wsl.FormatError('Failed to format database row %s' % (row,)) from e
