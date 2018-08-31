import re
import json
from .utils import check_term_format, parse_term
from .ontology import Term


PROCESS_TYPE_NAME = 'Process'


class PropertyValidator:
    '''' abstract base validator class '''

    def __init__(self, constraint=None):
        self.__constraint = constraint

    @property
    def constraint(self):
        return self.__constraint

    @property
    def validatable(self):
        return self.__constraint is not None

    def validate(self, property_name, property_value):
        self.validate_type(property_name, property_value)
        if self.validatable:
            self.validate_value(property_name, property_value)

    def validate_type(self, property_name, property_value):
        pass

    def validate_value(self, property_name, property_value):
        pass


class PropertyTextValidator(PropertyValidator):
    def __init__(self, reg_expression_constrint):
        super().__init__(reg_expression_constrint)

        self.__pattern = None
        if self.validatable:
            self.__pattern = re.compile(reg_expression_constrint)

    def validate_type(self, property_name, property_value):
        if type(property_value) is not str:
            raise ValueError(
                'Wrong property type: the value of "%s" property is not text (%s)'
                % (property_name, property_value))

    def validate_value(self, property_name, property_value):
        if self.validatable:
            if not self.__pattern.match(property_value):
                raise ValueError(
                    'The value (%s) of the "%s" property does not follow the property constraint'
                    % (property_value, property_name))


class PropertyFloatValidator(PropertyValidator):
    def __init__(self, min_max_validator):
        super().__init__(min_max_validator)

        self.__min_value = None
        self.__max_value = None
        if self.validatable:
            self.__min_value = min_max_validator[0]
            self.__max_value = min_max_validator[1]

    def validate_type(self, property_name, property_value):
        if type(property_value) is not float and type(property_value) is not int:
            raise ValueError(
                'Wrong property type: the value of "%s" property is not float (%s)'
                % (property_name, property_value))

    def validate_value(self, property_name, property_value):
        if self.validatable:
            if property_value < self.__min_value or property_value > self.__max_value:
                raise ValueError(
                    'The value (%s) of the "%s" property is not in the rage [%s, %s]'
                    % (property_value, property_name, self.__min_value, self.__max_value))


class PropertyTermValidator(PropertyValidator):
    def __init__(self, root_term_id_validator):
        super().__init__(root_term_id_validator)

        self.__root_term = None
        if self.validatable:
            self.__root_term = Term(root_term_id_validator)
            self.__root_term.refresh()

    def validate_type(self, property_name, property_value):
        if type(property_value) is not str or not check_term_format(property_value):
            raise ValueError(
                'Wrong property type: the value of "%s" property is not term (%s)'
                % (property_name, property_value))

    def validate_value(self, property_name, property_value):
        if self.validatable:
            term = parse_term(property_value)
            term.refresh()

            root_term_id = self.__root_term.term_id
            validated = term.term_id == root_term_id
            if not validated:
                for parent_term_id in term.parent_path_ids:
                    if parent_term_id == root_term_id:
                        validated = True
                        break

            if not validated:
                raise ValueError(
                    'The term "%s" of the "%s" property is not a child term of "%s"'
                    % (str(term), property_name, str(self.__root_term)))


_PROPERTY_VALIDATORS = {
    'text': PropertyTextValidator,
    'float': PropertyFloatValidator,
    'term': PropertyTermValidator,
    '[ref]': PropertyValidator
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
        for pname, pdef in self.__property_defs.items():
            value = data.get(pname)
            if value is None or value == 'null':
                if pdef.required:
                    raise ValueError(
                        'The required property "%s" is absent' % pname)
            else:
                pdef.validate(value)

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

        self.__property_validator = _PROPERTY_VALIDATORS[self.__type](
            self.__constraint)

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

    def validate(self, value):
        self.__property_validator.validate(self.__name, value)

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
