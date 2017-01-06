from .datatypes import Value, Struct, Set, List, Dict, Query


class Settable():
    def __init__(self):
        self.x = None

    def __repr__(self):
        if self.x is None:
            return '?'
        else:
            return '!%s' %(self.x,)

    def set(self, x):
        self.x = x

    def get(self):
        return self.x


def add_rows(database, query, cols, rows):
    key = tuple(cols.index(v) for v in query.variables)
    table = database.setdefault(query.table, [])
    for row in rows:
        table.append(tuple(row[i].get() for i in key))


def todb_value(cols, rows, objs, spec, database):
    if spec.query is not None:
        nextcols = cols + spec.query.freshvariables
        nextrows = []
        nextobjs = []
        for row, obj in zip(rows, objs):
            if obj is not None:
                nextrows.append(row + tuple(Settable() for _ in spec.query.freshvariables))
                nextobjs.append(obj)
    else:
        nextcols = cols
        nextrows = rows
        nextobjs = objs
    idx = nextcols.index(spec.variable)
    for nextrow, nextobj in zip(nextrows, nextobjs):
        nextrow[idx].set(nextobj)
    if spec.query is not None:
        add_rows(database, spec.query, nextcols, nextrows)


def todb_struct(cols, rows, objs, spec, database):
    if spec.query is not None:
        nextcols = cols + spec.query.freshvariables
        nextrows = []
        nextobjs = { key: [] for key in spec.childs }
        for row, obj in zip(rows, objs):
            if obj is not None:
                nextrows.append(row + tuple(Settable() for _ in spec.query.freshvariables))
                for key in spec.childs:
                    nextobjs[key].append(obj[key])
    else:
        nextcols = cols
        nextrows = rows
        nextobjs = { key: [] for key in spec.childs }
        for obj in objs:
            assert obj is not None
            for key in spec.childs:
                if key not in obj:
                    raise ValueError('Expected member "%s" but got object with these keys: %s' %(key, ', '.join(str(k) for k in obj.keys())))
                nextobjs[key].append(obj[key])
    for key in spec.childs:
        todb(nextcols, nextrows, nextobjs[key], spec.childs[key], database)
    if spec.query is not None:
        add_rows(database, spec.query, nextcols, nextrows)


def todb_list(cols, rows, objs, spec, database):
    nextcols = cols + spec.query.freshvariables
    nextrows = []
    nextobjs = []
    for row, lst in zip(rows, objs):
        for item in lst:
            nextrows.append(row + tuple(Settable() for _ in spec.query.freshvariables))
            nextobjs.append(item)
    todb(nextcols, nextrows, nextobjs, spec.childs['_val_'], database)
    add_rows(database, spec.query, nextcols, nextrows)


def todb_dict(cols, rows, objs, spec, database):
    nextcols = cols + spec.query.freshvariables
    nextrows = []
    nextobjs_keys = []
    nextobjs_vals = []
    for row, dct in zip(rows, objs):
        for key, val in dct.items():
            nextrows.append(row + tuple(Settable() for _ in spec.query.freshvariables))
            nextobjs_keys.append(key)
            nextobjs_vals.append(val)
    todb(nextcols, nextrows, nextobjs_keys, spec.childs['_key_'], database)
    todb(nextcols, nextrows, nextobjs_vals, spec.childs['_val_'], database)
    add_rows(database, spec.query, nextcols, nextrows)


def todb(cols, rows, objs, spec, database):
    assert len(rows) == len(objs)
    typ = type(spec)
    if typ == Value:
        todb_value(cols, rows, objs, spec, database)
    elif typ == Struct:
        todb_struct(cols, rows, objs, spec, database)
    elif typ == List:
        todb_list(cols, rows, objs, spec, database)
    elif typ == Dict:
        todb_dict(cols, rows, objs, spec, database)
    else:
        assert False


def objects2rows(objs, spec):
    assert any(isinstance(spec, t) for t in [Value, Struct, List, Set, Dict])
    database = {}

    todb((), [()], [objs], spec, database)

    for table in database.values():
        table.sort()

    return database
