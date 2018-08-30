import re
import json
from .utils import check_term_format, parse_term
from .ontology import Term


def _text_type_validate(property_name, property_value):
    if type(property_value) is not str:
        raise ValueError(
            'Wrong property type: the value of "%s" property is not text (%s)'
            % (property_name, property_value))


def _float_type_validate(property_name, property_value):
    if type(property_value) is not float:
        raise ValueError(
            'Wrong property type: the value of "%s" property is not float (%s)'
            % (property_name, property_value))


def _term_type_validate(property_name, property_value):
    if type(property_value) is not str or not check_term_format(property_value):
        raise ValueError(
            'Wrong property type: the value of "%s" property is not term (%s)'
            % (property_name, property_value))


def _text_value_validate(property_name, property_value, constraint):
    ''' we expect that the constraint is the regular expression '''
    pattern = re.compile(constraint)
    if not pattern.match(property_value):
        raise ValueError(
            'The value (%s) of the "%s" property does not follow the property constraint'
            % (property_value, property_name))


def _float_value_validate(property_name, property_value, constraint):
    ''' we expect that the constraint is an array of min and max values '''
    if property_value < constraint[0] or property_value > constraint[1]:
        raise ValueError(
            'The value (%s) of the "%s" property does not follow the property constraint'
            % (property_value, property_name))


def _term_value_validate(property_name, property_value, constraint):
    ''' we expect that the value constraint is an array of root terms '''
    term = parse_term(property_value)
    term.refresh()

    validated = False
    for cterm_str in constraint:
        cterm = parse_term(cterm_str)
        for p_id in term.parent_path_ids:
            if p_id == cterm.term_id:
                validated = True
                break
        if validated:
            break

    if not validated:
        raise ValueError(
            'The value (%s) of the "%s" property does not follow the property constraint'
            % (property_value, property_name))


_PROPERTY_TYPE_VALIDATORS = {
    "text": _text_type_validate,
    "float": _float_type_validate,
    "term": _term_type_validate,
    "[ref]": None
}

_PROPERTY_VALUE_VALIDATORS = {
    "text": _text_value_validate,
    "float": _float_value_validate,
    "term": _term_value_validate,
    "[ref]": None
}


class TypeDef:
    def __init__(self, name, type_def_doc):
        self.__name = name
        self.__property_defs = {}
        for pdoc in type_def_doc['fields']:
            self.__property_defs[pdoc['name']] = PropertyDef(pdoc)

        self.__process_type_terms = []
        if 'process_types' in type_def_doc:
            for term_id in type_def_doc['process_types']:
                term = Term(term_id)
                term.refresh()
                self.__process_type_terms.append(term)

        self.__process_input_type_names = []
        if 'process_inputs' in type_def_doc:
            for type_name in type_def_doc['process_inputs']:
                self.__process_input_type_names.append(type_name)

        self.__process_input_type_defs = []

    def _repr_html_(self):
        rows = ['<b>' + self.__name + '</b>']
        for pdef in self.__property_defs.values():
            rows.append('* ' + str(pdef))
        return '<br>'.join(rows)

    def _update_process_input_type_defs(self, all_type_defs):
        for type_name in self.__process_input_type_names:
            self.__process_input_type_defs.append(all_type_defs[type_name])

    @property
    def name(self):
        return self.__name

    @property
    def property_names(self):
        return list(self.__property_defs.keys())

    def property_def(self, property_name):
        return self.__property_defs[property_name]

    @property
    def process_type_terms(self):
        return self.__process_type_terms

    @property
    def process_input_type_defs(self):
        return self.__process_input_type_defs

    def validate_data(self, data):
        # check property values
        for pname, pdef in self.__property_defs:
            value = data.get(pname)
            if value is None:
                if pdef.required:
                    raise ValueError(
                        'The required property "%s" is absent' % pname)
            else:
                pdef.validate_type(value)
                pdef.validate_value(value)

        # check that there are no undeclared properties
        for pname in data:
            if pname not in self.__property_defs:
                raise ValueError(
                    'The object has undeclared property: %s' % pname)


class PropertyDef:
    def __init__(self, pdef_doc):
        self.__name = pdef_doc['name']
        self.__type = pdef_doc['type']
        self.__required = pdef_doc['required'] if 'required' in pdef_doc else False
        self.__constraint = pdef_doc.get('constraint')
        self.__comment = pdef_doc.get('comment')
        self.__pk = 'PK' in pdef_doc and pdef_doc['PK'] == True
        self.__fk = 'FK' in pdef_doc and pdef_doc['FK'] == True

        self.__type_validator = _PROPERTY_TYPE_VALIDATORS[self.__type]
        self.__value_validator = _PROPERTY_VALUE_VALIDATORS[
            self.__type] if self.__constraint else None

    def _repr_html_(self):
        return str(self)

    def __str__(self):
        return self.__name \
            + ' ' + self.__type \
            + (' required' if self.__required else '') \
            + (' constraint="' + str(self.__constraint) + '"' if self.__constraint else '') \
            + (' comment="' + self.__comment + '"' if self.__comment else '') \
            + (' PK' if self.__pk else '') \
            + (' FK' if self.__fk else '')

    @property
    def name(self):
        return self.__name

    @property
    def type(self):
        return self.__type

    @property
    def required(self):
        return self.__required

    @property
    def constraint(self):
        return self.__constraint

    @property
    def comment(self):
        return self.__comment

    @property
    def is_pk(self):
        return self.__pk

    @property
    def is_fk(self):
        return self.__fk

    def validate_type(self, value):
        self.__type_validator(self.__name, value)

    def validate_value(self, value):
        if self.__value_validator is not None:
            self.__value_validator(self.__name, value, self.__constraint)

    # TODO
    # validate FK format
    # validate_entity_process(self, entity_type, process_type, process_data):


class TypeDefService:

    def __init__(self, file_name):
        self.__type_defs = {}
        self.__load_type_defs(file_name)

    def __load_type_defs(self, file_name):
        with open(file_name, 'r') as f:
            doc = json.loads(f.read())
        for type_name, type_def_doc in doc.items():
            self.__type_defs[type_name] = TypeDef(type_name, type_def_doc)

        for type_def in self.__type_defs.values():
            type_def._update_process_input_type_defs(self.__type_defs)

    def get_type_names(self):
        return list(self.__type_defs.keys())

    def get_type_def(self, type_name):
        return self.__type_defs[type_name]
