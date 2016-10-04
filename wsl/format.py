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


def format_values(tup, encoders):
    """Encode a WSL database tuple (without leading relation name)

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


def format_row(relation, tup, encoders):
    """Encode a WSL database tuple (including leading relation name).

    Args:
        relation (str): Name of the relation this tuple belongs to.
        tup (tuple): Values according to the columns of *relation*
        encoders (tuple): Encoders according to the columns of *relation*
    Returns:
        str: A single line (including the terminating newline character).
    Raises:
        wsl.FormatError: if formatting fails.
    """
    x = [relation]
    for val, encode in zip(tup, encoders):
        x.append(encode(val))
    return ' '.join(x) + '\n'


def format_db(schema, tuples_of_relation, inline_schema):
    """Convenience function for formatting a WSL database.

    Args:
        schema (wsl.Schema): The schema of the database.
        tuples_of_relation (dict): A dictionary that maps each relation name in
            *schema.relations* to a list that contains all the rows of that
            relation.
    Returns:
        An iterator yielding chunks of encoded text.
        If *inline_schema* is True, the first chunk is the textual
        representation of the schema, each line being escaped with %
        as required for WSL inline notation.
        Each following yielded chunk is the result of encoding one tuple
        of the database (as returned by *format_row()*).
    Raises:
        wsl.FormatError: if formatting fails.
    """
    if inline_schema:
        yield format_schema(schema, escape=True)
    for relation in sorted(tuples_of_relation.keys()):
        encoders = []
        for x in schema.domains_of_relation[relation]:
            encoders.append(schema.object_of_domain[x].encode)
        try:
            for tup in sorted(tuples_of_relation[relation]):
                yield format_row(relation, tup, encoders)
        except wsl.FormatError as e:
            raise wsl.FormatError('Failed to format tuple %s' % (tup,)) from e
