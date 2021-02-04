import re


def to_var_name(prefix, name):
    return prefix + re.sub('[^A-Za-z0-9]+', '_', name)

def to_es_type_name(type_name):
    return type_name

def to_object_type(object_id):
    res = re.search(r'([a-zA-Z_]*)(\d*)',object_id)    
    if res:
        return res.group(1)

    raise ValueError('Wrong object ID format %s' % object_id)



# def to_es_type_name(type_name):
#     chars = list(type_name)
#     es_name = []
#     for ch in chars:
#         if ch.isupper():
#             if len(es_name) > 0:
#                 es_name.append('_')
#             es_name.append(ch.lower())
#         else:
#             es_name.append(ch)
#     return ''.join(es_name)


# from .ontology import Term

# __TERM_PATTERN = re.compile('(.+)<(.+)>')


# def check_term_format(value):
#     m = __TERM_PATTERN.findall(value)
#     return m is not None


# def parse_term(value):
#     m = __TERM_PATTERN.findall(value)
#     if m:
#         term = Term(m[0][1].strip(), term_name=m[0][0].strip())
#     else:
#         raise ValueError('Can not parse term from value: %s' % value)
#     return term
