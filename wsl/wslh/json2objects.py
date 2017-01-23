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


def make_struct_parser(dct):
    def struct_parser(obj):
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
                raise wsl.ParseError('Cannot parse JSON object "%s"' %(obj[k],)) from e
        return out
    return struct_parser


def make_option_parser(parser):
    def option_parser(obj):
        if obj is None:
            return None
        else:
            return parser(obj)
    return option_parser


def make_list_parser(parser):
    def list_parser(obj):
        if not isinstance(obj, list):
            raise wsl.ParseError('Cannot parse JSON object as List: Expected JSON list but got %s' %(type(object),))
        return [ parser(v) for v in obj ]
    return list_parser


def make_dict_parser(key_parser, val_parser):
    def dict_parser(obj):
        if not isinstance(obj, dict):
            raise wsl.ParseError('Cannot parse JSON object as Dict: Expected JSON dict but got %s' %(type(object),))
        out = {}
        for k, v in obj.items():
            try:
                pk = key_parser(k)
            except wsl.ParseError as e:
                raise wsl.ParseError('Cannot parse JSON dict key "%s"' %(k,)) from e
            try:
                vk = val_parser(v)
            except wsl.ParseError as e:
                raise wsl.ParseError('Cannot parse JSON dict value "%s"' %(v,)) from e
            out[pk] = vk
        return out
    return dict_parser


def make_json_parser(parser, jsontype):
    if jsontype == wsl.JSONTYPE_STRING:
        jsonlexer = wsl.jsonlex_string
    elif jsontype == wsl.JSONTYPE_INT:
        jsonlexer = wsl.jsonlex_int
    else:
        raise ValueError('only JSONTYPE_STRING and JSONTYPE_INT are supported as jsontypes')
    def json_parser(x):
        return parser(jsonlexer(x))
    return json_parser


def make_parser_from_spec(lookup_primparser, lookup_jsontype, spec):
    typ = type(spec)

    if typ == Value:
        parser = lookup_primparser(spec.primtype)
        jsontype = lookup_jsontype(spec.primtype)
        if parser is None:
            raise ValueError('There is no decoder for datatype "%s"' %(spec.primtype,))
        if jsontype is None:
            raise ValueError('There is no jsontype for datatype "%s"' %(spec.primtype,))
        return make_json_parser(parser, jsontype)

    elif typ == Struct:
        dct = {}
        for k, v in spec.childs.items():
            dct[k] = make_parser_from_spec(lookup_primparser, lookup_jsontype, v)
        return make_struct_parser(dct)

    elif typ == Option:
        subparser = make_parser_from_spec(lookup_primparser, lookup_jsontype, spec.childs['_val_'])
        return make_option_parser(subparser)

    elif typ == List:
        subparser = make_parser_from_spec(lookup_primparser, lookup_jsontype, spec.childs['_val_'])
        return make_list_parser(subparser)

    elif typ == Dict:
        if type(spec.childs['_key_']) != Value:
            raise ValueError('JSON does not support composite dictionary keys')
        if lookup_jsontype(spec.childs['_key_'].primtype) not in [wsl.JSONTYPE_STRING, wsl.JSONTYPE_INT]:
            raise ValueError('JSON only supports string literals as dict keys')

        lookup_always_str = lambda _: wsl.JSONTYPE_STRING  # EVIL: JSON supp

        key_parser = make_parser_from_spec(lookup_primparser, lookup_always_str, spec.childs['_key_'])
        val_parser = make_parser_from_spec(lookup_primparser, lookup_jsontype, spec.childs['_val_'])
        return make_dict_parser(key_parser, val_parser)

    assert False  # missing case


def json2objects(lookup_primparser, lookup_jsontype, spec, text):
    assert isinstance(text, str)
    parser = make_parser_from_spec(lookup_primparser, lookup_jsontype, spec)
    objects = json.loads(text)
    return parser(objects)
