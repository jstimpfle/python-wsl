"""Module wsl.schema: python class representing WSL database schema"""

class Schema:
    """Schema information for a WSL database.

    Attributes:
        spec: string containing the textual representation of the schema.
            This is normally the string that the schema object was parsed from.

        domains: set object, holding the identifiying names of all the domains
            used in this schema.
        relations: set object, holding the identifiying names of all the
            relations used in this schema.
        keys: set object, holding the identifying names of all the keys used
            in this schema.
        references: set object, holding the identifying names of all the
            references used in this schema.

        spec_of_domain: dict object, mapping each domain name from the
            *domains* attribute to a textual specification of that domain. It
            is guaranteed to be a single line (including the terminating
            newline character).
        spec_of_relation: dict object, mapping each relation name from the
            *relations* attribute to a textual specification of that relation.
            It is guaranteed to be a single line (including the terminating
            newline character).
        spec_of_key: dict object, mapping each key name from the *keys*
            attribute to a textual representation of that key. It is guaranteed
            to be a single line (including the terminating newline character).
        spec_of_reference: dict object, mapping each reference name from the
            *references* attribute to a textual representation of that
            reference. It is guaranteed to be a single line (including the
            terminating newline character).
        object_of_domain: dict object, mapping each domain name from the
            *domains* attribute to its corresponding domain object.
        domains_of_relation: dict object, mapping each relation name from the
            *relations* attribute to a tuple of the names of the columns of
            that relation (in order).
        tuple_of_key: dict object, mapping each key name from the *keys*
            attribute to a tuple *(relation name, 1-based column indices)*.
            This represents the specification of the key.
        tuple_of_reference: dict object, mapping each reference name from the
            *reference* attribute to a tuple *(relation name, column indices,
            relation name, column indices)*. This represents the reference
            constraint as (compatible) keys in the local and foreign relation.

        objects_of_relation: dict object, mapping each relation name from the
            *relations* attribute to a tuple of the domain objects corresponding
            to the columns of that relation. This attribute is for convenience;
            it is created in the constructor from the input arguments.
        
    """
    def __init__(self, spec,
            domains, relations, keys, references,
            spec_of_domain, spec_of_relation, spec_of_key, spec_of_reference,
            object_of_domain, domains_of_relation, tuple_of_key, tuple_of_reference):

        def is_list_or_tuple(x):
            return isinstance(x, list) or isinstance(x, tuple)

        def map_set(func, set_):
            return set(func(x) for x in set_)

        def map_dict(kfunc, vfunc, dict_):
            return dict({ kfunc(k): vfunc(v) for k, v in dict_.items() })

        assert isinstance(domains, set)
        assert isinstance(relations, set)
        assert isinstance(keys, set)
        assert isinstance(references, set)
        assert isinstance(spec_of_domain, dict)
        assert isinstance(spec_of_relation, dict)
        assert isinstance(spec_of_key, dict)
        assert isinstance(spec_of_reference, dict)
        assert isinstance(object_of_domain, dict)
        assert isinstance(domains_of_relation, dict)
        assert isinstance(tuple_of_key, dict)
        assert isinstance(tuple_of_reference, dict)

        assert set(domains) == set(spec_of_domain) == set(object_of_domain)
        assert set(relations) == set(spec_of_relation) == set(domains_of_relation)
        assert set(keys) == set(spec_of_key) == set(tuple_of_key)
        assert set(references) == set(spec_of_reference) == set(tuple_of_reference)

        for x in domains: assert isinstance(x, str)
        for x in relations: assert isinstance(x, str)
        for x in keys: assert isinstance(x, str)
        for x in references: assert isinstance(x, str)
        for x in spec_of_domain.values(): assert isinstance(x, str)
        for x in spec_of_relation.values(): assert isinstance(x, str)
        for x in spec_of_key.values(): assert isinstance(x, str)
        for x in spec_of_reference.values(): assert isinstance(x, str)
        for x in object_of_domain.values(): pass  # ??
        for x in domains_of_relation.values(): assert is_list_or_tuple(x)
        for x in tuple_of_key.values(): assert is_list_or_tuple(x)
        for x in tuple_of_reference.values(): assert is_list_or_tuple(x)

        self.spec = str(spec)
        self.domains = map_set(str, domains)
        self.relations = map_set(str, relations)
        self.keys = map_set(str, keys)
        self.references = map_set(str, references)
        self.spec_of_relation = map_dict(str, str, spec_of_relation)
        self.spec_of_domain = map_dict(str, str, spec_of_domain)
        self.spec_of_key = map_dict(str, str, spec_of_key)
        self.spec_of_reference = map_dict(str, str, spec_of_reference)
        self.object_of_domain = map_dict(str, lambda x: x, object_of_domain)
        self.domains_of_relation = map_dict(str, lambda v: tuple(str(x) for x in v), domains_of_relation)
        self.tuple_of_key = map_dict(str, tuple, tuple_of_key)
        self.tuple_of_reference = map_dict(str, tuple, tuple_of_reference)

        for rel in self.relations:
            for d in self.domains_of_relation[rel]:
                print(d)
        self.objects_of_relation = dict((rel, tuple(self.object_of_domain[d] for d in self.domains_of_relation[rel])) for rel in self.relations)

    def _debug_str(self):
        return """
            domains: %s
            relations: %s
            keys: %s
            references: %s
            spec_of_relation: %s
            spec_of_domain: %s
            spec_of_key: %s
            spec_of_reference: %s
            object_of_domain: %s
            domains_of_relation: %s
            tuple_of_key: %s
            tuple_of_reference: %s
        """ %(
        self.domains,
        self.relations,
        self.keys,
        self.references,
        self.spec_of_relation,
        self.spec_of_domain,
        self.spec_of_key,
        self.spec_of_reference,
        self.object_of_domain,
        self.domains_of_relation,
        self.tuple_of_key,
        self.tuple_of_reference)
