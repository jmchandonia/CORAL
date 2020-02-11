import re
import json
from .ontology import Term

# TODO
# from . import services

TYPE_CATEGORY_STATIC   = 'SDT_'
TYPE_CATEGORY_DYNAMIC  = 'DDT_'
TYPE_CATEGORY_SYSTEM   = 'SYS_'
TYPE_CATEGORY_ONTOLOGY = 'ONT_'

TYPE_NAME_PROCESS = 'Process'
TYPE_NAME_BRICK = 'Brick'


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
                    'The value (%s) of the "%s" property is not in the range [%s, %s]'
                    % (property_value, property_name, self.__min_value, self.__max_value))


class PropertyTermValidator(PropertyValidator):
    def __init__(self, root_term_id_validator):
        super().__init__(root_term_id_validator)

        self.__root_term = None
        if self.validatable:
            self.__root_term = Term(root_term_id_validator)
            #self.__root_term.refresh()

    def validate_type(self, property_name, property_value):
        if type(property_value) is not str or not Term.check_term_format(property_value):
            raise ValueError(
                'Wrong property type: the value of "%s" property is not term (%s)'
                % (property_name, property_value))

    def validate_value(self, property_name, property_value):
        if self.validatable:
            term = Term.parse_term(property_value)
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
    'int': PropertyValidator,
    '[ref]': PropertyValidator,
    '[text]': PropertyValidator
}


class TypeDef:
    def __init__(self, type_name, category_name, type_def_doc):
        # print('Doing type:', name)

        self.__name = type_name
        self.__category = category_name
        self.__for_provenance = type_def_doc['used_for_provenance'] if 'used_for_provenance' in type_def_doc else False
        self.__property_defs = {}
        for pdoc in type_def_doc['fields']:
            self.__property_defs[pdoc['name']] = PropertyDef(self, pdoc)

        self.__pk_property_def = None
        for pdef in self.__property_defs.values():
            if pdef.is_pk:
                self.__pk_property_def = pdef
                break

        self.__upk_property_def = None
        for pdef in self.__property_defs.values():
            if pdef.is_upk:
                self.__upk_property_def = pdef
                break

        self.__fk_property_defs = []
        for pdef in self.__property_defs.values():
            if pdef.is_fk:
                self.__fk_property_defs.append(pdef)

        self.__process_type_terms = []
        if 'process_types' in type_def_doc:
            for term_id in type_def_doc['process_types']:
                term = Term(term_id)

                # TODO
                # if not services.IN_ONTOLOGY_LOAD_MODE:
                #     term.refresh()

                self.__process_type_terms.append(term)

        self.__process_input_type_names = []
        # TODO: process_inputs should be an array of arrays
        # if 'process_inputs' in type_def_doc:
        #     for type_name in type_def_doc['process_inputs']:
        #         self.__process_input_type_names.append(type_name)

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
    def category(self):
        return self.__category

    @property
    def collection_name(self):
        return self.__category + self.__name
        
    @property
    def property_names(self):
        return list(self.__property_defs.keys())

    @property
    def property_defs(self):
        return list(self.__property_defs.values())

    @property
    def pk_property_def(self):
        return self.__pk_property_def

    @property
    def upk_property_def(self):
        return self.__upk_property_def

    @property
    def fk_property_defs(self):
        return self.__fk_property_defs

    @property
    def for_provenance(self):
        return self.__for_provenance

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

        # print( len(self.__property_defs.items()) )
        for pname, pdef in self.__property_defs.items():

            value = data.get(pname)
            # print('[%s] = %s' % (pname, value) )
            # print ('QQQ')
            if value is None or value == 'null'  or value != value:
                # print ('QQQ1')
                # print('%s  is None: %s' % (pname, value))
                if pdef.required:
                    raise ValueError(
                        'The required property "%s" is absent' % pname)
                else:
                    data[pname] = None
            else:
                # print ('QQQ2')
                # print('---------Validating %s ' % pname)
                pdef.validate(value)

        # check that there are no undeclared properties
        for pname in data:
            if pname not in self.__property_defs:
                raise ValueError(
                    'The object has undeclared property: %s' % pname)


class PropertyDef:
    def __init__(self, type_def, pdef_doc):

        # print('Doing property:', pdef_doc['name'])
        self.__type_def = type_def
        self.__name = pdef_doc['name']
        self.__type = pdef_doc['scalar_type']
        self.__required = pdef_doc['required'] if 'required' in pdef_doc else False
        self.__constraint = pdef_doc.get('constraint')
        self.__comment = pdef_doc.get('comment')
        self.__pk = 'PK' in pdef_doc and pdef_doc['PK'] == True
        self.__fk = 'FK' in pdef_doc and pdef_doc['FK'] == True
        self.__upk = 'UPK' in pdef_doc and pdef_doc['UPK'] == True
        self.__term_id = pdef_doc['type_term'] if 'type_term' in pdef_doc else False

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
    def type_def(self):
        return self.__type_def

    @property
    def term_id(self):
        return self.__term_id

    def has_term_id(self):
        return self.__term_id is not None

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

    @property
    def is_upk(self):
        return self.__upk

    def validate(self, value):
        self.__property_validator.validate(self.__name, value)

    # TODO
    # validate FK format
    # validate_entity_process(self, entity_type, process_type, process_data):


class TypeDefService:

    def __init__(self, file_name):
        self.__type_defs = {}
        self.__term_2_prop_defs = {}
        self.__load_type_defs(file_name)

    def __load_type_defs(self, file_name):
        with open(file_name, 'r') as f:
            doc = json.loads(f.read())

        # Do static types
        for type_def_doc in doc['static_types']:
            type_name = type_def_doc['name']
            category_name = TYPE_CATEGORY_STATIC
            self.__type_defs[type_name] = TypeDef(type_name, category_name, type_def_doc)

        # Do system types
        for type_def_doc in doc['system_types']:
            type_name = type_def_doc['name']
            category_name = TYPE_CATEGORY_SYSTEM
            self.__type_defs[type_name] = TypeDef(type_name, category_name, type_def_doc)

        for type_def in self.__type_defs.values():
            type_def._update_process_input_type_defs(self.__type_defs)

            # update __term_2_prop_defs
            for prop_def in type_def.property_defs:
                if prop_def.has_term_id():
                    term_props = self.__term_2_prop_defs.get(prop_def.term_id)
                    if term_props is None:
                        term_props = []
                        self.__term_2_prop_defs[prop_def.term_id] = term_props
                    term_props.append(prop_def)

        # self.__type_defs[TYPE_NAME_BRICK] = None

    def get_type_names(self, category=None):
        names = []
        for name, type_def in self.__type_defs.items():
            if category is None:
                names.append(name)
            else:
                if type_def is not None and type_def.category == category:
                    names.append(name)
        return names

    def get_type_def(self, type_name):
        return self.__type_defs[type_name]

    def has_term_pk(self, term_id):
        prop_defs = self.__term_2_prop_defs.get(term_id)
        if prop_defs is None:
            return False

        for prop_def in prop_defs:
            if prop_def.is_pk:
                return True

        return False

    def get_term_pk_prop_def(self, term_id):
        prop_defs = self.__term_2_prop_defs.get(term_id)
        if prop_defs is None:
            return None

        for prop_def in prop_defs:
            if prop_def.is_pk:
                return prop_def

        return None

    def get_term_prop_defs(self, term_id):
        return self.__term_2_prop_defs.get(term_id)
