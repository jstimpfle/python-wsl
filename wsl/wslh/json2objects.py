import json

import wsl
from .datatypes import Value, Struct, Option, Set, List, Dict


class ParseException(Exception):
    def __init__(self, msg, lineno, charno):
        self.msg = msg
        self.lineno = lineno
        self.charno = charno

    def __str__(self):
        return 'At %d:%d: %s' %(self.lineno, self.charno, self.msg)


def make_parse_exc(msg, text, i):
    lines = text[:i].split('\n')
    lineno = len(lines)
    charno = i + 1 - sum(len(l) + 1 for l in lines[:-1])
    return ParseException(msg, lineno, charno)


def make_struct_reader(dct):
    def struct_reader(obj):
        if not isinstance(obj, dict):
            raise wsl.ParseError('Cannot parse JSON object as Struct: Expected JSON dict but got %s' %(type(obj),))
        needkeys = set(dct.keys())
        havekeys = set(obj.keys())
        if needkeys != havekeys:
            raise wsl.ParseError('Cannot parse JSON object: Need keys "%s" but got keys "%s"' %(', '.join(needkeys), ', '.join(havekeys)))

        out = {}
        for k in dct:
            try:
                out[k] = dct[k](obj[k])
            except wsl.ParseError as e:
                raise wsl.ParseError('Cannot parse JSON struct value "%s"' %(obj[k],)) from e
        return out
    return struct_reader


def make_option_reader(reader):
    def option_reader(obj):
        if obj is None:
            return None
        else:
            return reader(obj)
    return option_reader


def make_set_reader(reader):
    def set_reader(obj):
        if not isinstance(obj, list):
            raise wsl.ParseError('CAnnot parse JSON object as Set: Expected JSON list but got %s' %(type(object),))
        return set([ reader(v) for v in obj ])
    return set_reader


def make_list_reader(reader):
    def list_reader(obj):
        if not isinstance(obj, list):
            raise wsl.ParseError('Cannot parse JSON object as List: Expected JSON list but got %s' %(type(object),))
        return [ reader(v) for v in obj ]
    return list_reader


def make_dict_reader(key_reader, val_reader):
    def dict_reader(obj):
        if not isinstance(obj, dict):
            raise wsl.ParseError('Cannot parse JSON object as Dict: Expected JSON dict but got %s' %(type(object),))
        out = {}
        for k, v in obj.items():
            try:
                pk = key_reader(k)
            except wsl.ParseError as e:
                raise wsl.ParseError('Cannot parse JSON dict key "%s"' %(k,)) from e
            try:
                vk = val_reader(v)
            except wsl.ParseError as e:
                raise wsl.ParseError('Cannot parse JSON dict value "%s"' %(v,)) from e
            out[pk] = vk
        return out
    return dict_reader


def make_reader_from_spec(make_reader, spec, is_dict_key):
    typ = type(spec)

    if typ == Value:
        reader = make_reader(spec.primtype, is_dict_key)
        if reader is None:
            raise ValueError('There is no JSON reader for datatype "%s"' %(spec.primtype,))
        return reader

    elif typ == Struct:
        dct = {}
        for k, v in spec.childs.items():
            dct[k] = make_reader_from_spec(make_reader, v, False)
        return make_struct_reader(dct)

    elif typ == Option:
        subreader = make_reader_from_spec(make_reader, spec.childs['_val_'], False)
        return make_option_reader(subreader)

    elif typ == Set:
        subreader = make_reader_from_spec(make_reader, spec.childs['_val_'], False)
        return make_set_reader(subreader)

    elif typ == List:
        subreader = make_reader_from_spec(make_reader, spec.childs['_val_'], False)
        return make_list_reader(subreader)

    elif typ == Dict:
        if type(spec.childs['_key_']) != Value:
            raise ValueError('JSON does not support composite dictionary keys')

        key_reader = make_reader_from_spec(make_reader, spec.childs['_key_'], True)
        val_reader = make_reader_from_spec(make_reader, spec.childs['_val_'], False)
        return make_dict_reader(key_reader, val_reader)

    assert False  # missing case


def json2objects(schema, spec, objects):
    if not isinstance(schema, wsl.Schema):
        raise TypeError()
    reader = make_reader_from_spec(wsl.make_make_jsonreader(schema), spec, False)
    return reader(objects)
