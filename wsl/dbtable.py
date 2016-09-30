"""Module wsl.dbtable: Database table instance with update operations"""

import wsl


def make_tuple_type(clsname, arity, names=None, refs=None):
    """Make a tuple class for tuples of length *arity*.

    Returns a *tuple*-like database tuple class, with convenient and
    memory-friendly property accessors and links for following foreign keys
    (references).

    It is the responsibility of the caller to make sure that the property
    names in *names* and *refs* do not clash.

    Example:

        >>> Person = make_tuple_type('Person', 2, ('givenname', 'surname'))
        >>> person = Person('John', 'Doe')
        >>> person[0], person[1]
        ('John', 'Doe')
        >>> person._1, person._2
        ('John', 'Doe')
        >>> person.givenname, person.surname
        ('John', 'Doe')

    Args:
        clsname (str): Name for the constructed class
        arity (int): length of each tuple instance.
        names: If not *None*, a list of tuples of length *arity* is expected,
            where each tuple contains alternative names for the columns of
            the table. Names can be *None* if only a subset of the columns
            have names.
        refs: If not *None*, a dict of abstract foreign keys (as used in
            the schema module). This will be used later (when the tables are
            all instanciated) to make properties to jump between tables while
            following references.

    Returns:
        A new tuple type with the configured properties (field accessors).
    """

    if names is None:
        names = []
    if refs is None:
        refs = {}

    # make sure names don't clash (the caller probably didn't intend that...)
    allnames = set()
    def addname(name):
        if name in allnames:
            raise ValueError(
                'Name clash: %s while creating database tuple type' %(name,))
        if name.startswith('_') and name[1:].isdigit():
            raise ValueError(
                'Reserved name: %s while creating database tuple type' %(name,))
        allnames.add(name)
    for namelist in names:
        for name in namelist:
            addname(name)
    for name in refs:
        addname(name)

    # class dict. We make a class from this in the end (see type() call)
    clsprops = {}
    clsprops['_refs'] = refs

    # implement single-value getters as wished, as Python properties
    def get_one(i):
        @property
        def getter(self):
            return self[i]
        return getter
    for namelist in names:
        for i, name in enumerate(namelist):
            if name is not None:
                clsprops[name] = get_one(i)
    for i in range(arity):
        def getter(self):
            return self[i]
        prop = '_%d' %(i+1)
        clsprops[prop] = get_one(i)

    # refs will be fixed up only later (with fix_refs()), when all tables
    # are created (cyclic dependencies!)
    for refname in refs:
        clsprops[refname] = None

    @classmethod
    def fix_refs(cls, tables):
        for refname, (cols_here, table_there, cols_there) in cls._refs.items():
            assert hasattr(cls, refname) and getattr(cls, refname) is None
            t = tables[table_there]
            idx = t.get_index(cols_there)
            # Take care when making closures in loops!
            def make_follow_ref(idx, cols_here):
                @property
                def follow_ref(self):
                    k = self.get_some_columns(cols_here)
                    try:
                        return idx[k]
                    except KeyError as e:
                        raise wsl.IntegrityError('Could not follow reference to table "%s". Did you call build_indices() on all relevant tables?' %(table_there)) from e
                return follow_ref
            setattr(cls, refname, make_follow_ref(idx, cols_here))

    def get_some_columns(self, columns):
        # XXX: Assuming 1-based column indices here...
        return tuple(self[c-1] for c in columns)

    clsprops['fix_refs'] = fix_refs
    clsprops['get_some_columns'] = get_some_columns

    return type(clsname, (tuple,), clsprops)



class DbTable:
    def __init__(self, tablename, arity, names=None, keys=None, refs=None):
        """
        Args:
            keys (dict): keyname -> abstract description (tuple)
            refs (dict): refname -> abstract description (tuple, tablename, tuple)
        """
        if names is None:
            names = []
        if keys is None:
            keys = {}
        if refs is None:
            refs = {}

        # there's always a key
        keys['_NODUPLICATEROWS'] = tuple(range(1, arity+1))

        for keyname, columns in keys.items():
            for i in range(1, len(columns)):
                if columns[i] <= columns[i-1]:
                    raise ValueError(
                        'Bad key %s (%s): The column indices must be ascending'
                        %(keyname, columns))

        self.tablename = tablename
        self.keys = keys
        self.tuple_type = make_tuple_type(tablename, arity, names, refs)

        # Here we append new tuples when filling the table
        self.tuples = []

        # tuple of columns -> dict mapping tuples of these columns
        # to the whole tuple
        self._indices = {}
        for columns in keys.values():
            columns = tuple(columns)
            self._indices[columns] = {}

    def get_index(self, columns):
        """Get the index for a subset of the columns"""
        columns = tuple(columns)
        idx = self._indices.get(columns)

        if idx is None:
            raise ValueError(
                'No such index for table %s: %s' %(self.tablename, columns))

        return idx

    def build_indices(self):
        for keyname, columns in self.keys.items():
            idx = self.get_index(columns)
            for tup in self.tuples:
                some = tup.get_some_columns(columns)
                idx[some] = tup

    def fix_refs(self, tables):
        """
        Args:
            tables: A dict mapping tablenames to *DbTable* instances.
        """
        self.tuple_type.fix_refs(tables)

    def insert(self, values, ignore_if_exists=False):
        self.tuples.append(self.tuple_type(values))

    def __iter__(self):
        return iter(self.tuples)


if __name__ == '__main__':
    # test
    Bikeshed = DbTable(
        'Bikeshed', 2,
        names=[('BikeshedId', 'model')],
        keys={ 'keyBikeshedId': (1,) }
    )
    Color = DbTable('Color', 1, [('ColorName',)])
    BikeshedColor = DbTable(
        'BikeshedColor', 2,
        names=[('BikeshedId','ColorName')],
        keys={ 'keyBikeshedId': (1,) },
        refs={
            'refBikeshedId': ((1,), 'Bikeshed', (1,)),
            'refColorName': ((2,), 'Color', (1,))
        }
    )

    tables = {
        'Bikeshed': Bikeshed,
        'Color': Color,
        'BikeshedColor': BikeshedColor
    }

    Bikeshed.insert(('shed1', 'HippieShed'))
    Color.insert(('green',))
    BikeshedColor.insert(('shed1', 'green'))

    Bikeshed.build_indices()
    Color.build_indices()
    BikeshedColor.build_indices()

    BikeshedColor.fix_refs(tables)

    print()
    for row in BikeshedColor:
        print('At "BikeshedColor" row: ',row)
        #print('Following "refBikeshedId"')
        print(row.refBikeshedId)
        #print('Following "refColorName"')
        print(row.refColorName)
