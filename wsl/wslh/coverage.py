from .datatypes import Value
from .datatypes import Struct
from .datatypes import Option
from .datatypes import Set
from .datatypes import List
from .datatypes import Dict


def doquery(query, bindings):
    """Add bindings according to query"""
    for v in query.freshvariables:
        if v in bindings:
            raise ValueError("Sorry, can't handle shadowed variables (%s)" %(v,))
        idx = query.variables.index(v)
        bindings[v] = query.table, idx


def checkvalue(schema, spec, bindings, coverage):
    table, idx = bindings[spec.variable]
    coverage[table][idx] += 1


def checkstruct(schema, spec, bindings, coverage):
    for child in spec.childs.values():
        checkany(schema, child, dict(bindings), coverage)


def checkoption(schema, spec, bindings, coverage):
    doquery(spec.query, bindings)
    checkany(schema, spec.childs['_val_'], bindings, coverage)


def checkset(schema, spec, bindings, coverage):
    doquery(spec.query, bindings)
    checkany(schema, spec.childs['_val_'], bindings, coverage)


def checklist(schema, spec, bindings, coverage):
    doquery(spec.query, bindings)
    checkany(schema, spec.childs['_idx_'], bindings, coverage)
    checkany(schema, spec.childs['_val_'], bindings, coverage)


def checkdict(schema, spec, bindings, coverage):
    doquery(spec.query, bindings)
    checkany(schema, spec.childs['_key_'], bindings, coverage)
    checkany(schema, spec.childs['_val_'], bindings, coverage)


def checkany(schema, spec, bindings, coverage):
    if type(spec) == Value:
        return checkvalue(schema, spec, bindings, coverage)
    if type(spec) == Struct:
        return checkstruct(schema, spec, bindings, coverage)
    if type(spec) == Option:
        return checkoption(schema, spec, bindings, coverage)
    if type(spec) == Set:
        return checkset(schema, spec, bindings, coverage)
    if type(spec) == List:
        return checklist(schema, spec, bindings, coverage)
    if type(spec) == Dict:
        return checkdict(schema, spec, bindings, coverage)

    raise TypeError('Unexpected type: %s' %(type(spec),))


def check_coverage(schema, spec):
    """Check schema coverage of a spec.

    IN DEVELOPMENT - does not work yet. We still need to recognize functional
    dependencies, at least for "Dict"s where values are often used both as key
    and in the value. Read further to understand what this means.

    Returns a dict, containing a tuple of *int* for every table name. The tuple
    contains for each column in the table the number of independent uses of this
    column, from some place in the spec.

    A spec is isomorphic if, and only if, all these tuples are all 1's: A zero
    means that the column is never used, so the spec is not an injection. Some
    number > 1 means that the column is used as a fresh variable in multiple
    places and no functional dependencies between these queries could be found.
    In other words, the spec is "denormalized" and trees that carry
    contradicting values at the according places can't be meaningfully converted
    to rows.
    """

    bindings = {}
    coverage = { table.name: [0 for column in table.columns] for table in schema.tables.values() }

    checkany(schema, spec, bindings, coverage)

    return { k: tuple(v) for k, v in coverage.items() }
