import collections
import io

from .datatypes import Value, Struct, Option, Set, List, Dict


INDENTSPACES = 4


def make_primvalue_writer(primwriter):
    def write_primvalue(writer, data):
        writer.write(' ')
        writer.write(primwriter(data))
        writer.write('\n')
    return write_primvalue


def newline_and_then(valuewriter):
    def write_newline_and_then(writer, data):
        writer.write('\n')
        valuewriter(writer, data)
    return write_newline_and_then


def make_keyvalue_writer(keywriter, valuewriter, indent):
    def write_keyvalue(writer, data):
        k, v = data
        writer.write(' ')
        keywriter(writer, k)
        writer.write('\n')
        valuewriter(writer, v)
    return write_keyvalue


def make_struct_writer(dct, indent):
    indentstr = ' ' * indent
    def write_struct(writer, data):
        for key, write_cld in dct.items():
            writer.write('%s%s' %(indentstr, key))
            if key not in data:
                raise ValueError('Missing field "%s"\n' %(key,))
            val = data[key]
            write_cld(writer, val)
            if indent == 0:
                writer.write('\n')  # special quirk
    return write_struct


def make_option_writer(write_val):
    def write_option(writer, data):
        if data is None:
            writer.write(' ?\n')
        else:
            writer.write(' !\n')
            write_val(writer, data)
    return write_option


def make_list_writer(write_value, indent):
    indentstr = ' ' * indent
    def write_list(writer, data):
        if not isinstance(data, list):
            raise ValueError('list expected')
        writer.write('\n')
        for value in data:
            writer.write(indentstr)
            write_value(writer, value)
    return write_list


def make_dict_writer(write_key, write_value, indent):
    indentstr = ' ' * indent
    def write_dict(writer, data):
        for key, value in sorted(data.items()):
            writer.write('\n')
            writer.write(indentstr)
            writer.write('value')
            write_key(writer, key)
            write_value(writer, value)
    return write_dict


def make_writer_from_spec(lookup_primwriter, spec, indent):
    nextindent = indent + INDENTSPACES
    typ = type(spec)

    if typ == Value:
        primwriter = lookup_primwriter(spec.primtype)
        if primwriter is None:
            raise ValueError('There is no primwriter for datatype "%s"' %(spec.primtype,))
        return make_primvalue_writer(primwriter)

    elif typ == Struct:
        dct = collections.OrderedDict()
        for k, v in spec.childs.items():
            dct[k] = make_writer_from_spec(lookup_primwriter, v, nextindent)

        return make_struct_writer(dct, indent)


    elif typ == Option:
        val_writer = make_writer_from_spec(lookup_primwriter, spec.childs['_val_'], indent)
        return make_option_writer(val_writer)

    elif typ == List:
        val_writer = make_writer_from_spec(lookup_primwriter, spec.childs['_val_'], nextindent)
        return make_list_writer(val_writer, indent)

    elif typ == Dict:
        key_writer = make_writer_from_spec(lookup_primwriter, spec.childs['_key_'], nextindent)
        val_writer = make_writer_from_spec(lookup_primwriter, spec.childs['_val_'], nextindent)
        return make_dict_writer(key_writer, val_writer, indent)

    assert False  # missing case


def objects2text(lookup_primwriter, spec, obj):
    sio = io.StringIO()
    writer = make_writer_from_spec(lookup_primwriter, spec, 0)
    writer(sio, obj)

    return sio.getvalue()
