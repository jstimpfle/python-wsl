import json

import wsl
from .datatypes import Value, Struct, Option, Set, List, Dict


def value2json(look, spec, is_dict_key):
    fmter = look(spec.primtype, is_dict_key)
    if fmter is None:
        raise ValueError('No primvalue formatter for type "%s"' %(spec,))
    return fmter


def struct2json(look, spec):
    items = []
    for key, sub_spec in sorted(spec.childs.items()):
        convert_sub = any2json(look, sub_spec, False)
        items.append((key, convert_sub))
    def convert_struct(data):
        out = {}
        for key, convert_sub in items:
            out[key] = convert_sub(data[key])
        return out
    return convert_struct


def option2json(look, spec):
    sub_spec = spec.childs['_val_']
    convert_sub = any2json(look, sub_spec, False)
    def convert_option(data):
        if data is None:
            return None
        return convert_sub(data)
    return convert_option


def set2json(look, spec):
    sub_spec = spec.childs['_val_']
    convert_sub = any2json(look, sub_spec, False)
    def convert_set(data):
        out = []
        for item in sorted(data):
            out.append(convert_sub(item))
        return out
    return convert_set


def list2json(look, spec):
    sub_spec = spec.childs['_val_']
    convert_sub = any2json(look, sub_spec, False)
    def convert_list(data):
        out = []
        for item in data:
            out.append(convert_sub(item))
        return out
    return convert_list


def dict2json(look, spec):
    key_spec = spec.childs['_key_']
    val_spec = spec.childs['_val_']
    assert type(key_spec) == Value
    convert_key = any2json(look, key_spec, True)
    convert_val = any2json(look, val_spec, False)
    def convert_dict(data):
        out = {}
        for key, val in sorted(data.items()):
            out[convert_key(key)] = convert_val(val)
        return out
    return convert_dict


def any2json(look, spec, is_dict_key):
    typ = type(spec)
    if typ == Value:
        return value2json(look, spec, is_dict_key)
    elif typ == Struct:
        return struct2json(look, spec)
    elif typ == Option:
        return option2json(look, spec)
    elif typ == Set:
        return set2json(look, spec)
    elif typ == List:
        return list2json(look, spec)
    elif typ == Dict:
        return dict2json(look, spec)
    else:
        assert False


def objects2json(lookup_primformatter, spec, data):
    convert = any2json(lookup_primformatter, spec, False)
    return convert(data)
