import re


class TypeDefService:
    __term_pattern = re.compile('(.+)<(.+)>')

    def __init__(self, file_name):
        self.__validate_value = {
            'text': self.__validate_text,
            'float': self.__validate_float,
            'term': self.__validate_term
        }

        self.__check_value_type = {
            'text': self.__check_type_text,
            'float': self.__check_type_float,
            'term': self.__check_type_term
        }

        self.__type_defs = {}
        self.__load_type_defs(file_name)

    def __load_type_defs(self, file_name):
        pass

    def __check_type_text(self, name, value):
        if type(value) is not str:
            raise ValueError(
                'Wrong property type: the value of "%s" property is not text (%s)' % (name, value))

    def __check_type_float(self, name, value):
        if type(value) is not float:
            raise ValueError(
                'Wrong property type: the value of "%s" property is not float (%s)' % (name, value))

    def __check_type_term(self, name, value):
        if type(value) is not str or not self.parse_term(value):
            raise ValueError(
                'Wrong property type:  the value of "%s" property is not term (%s)' % (name, value))

    def parse_term(self, value):
        m = TypeDefService.__term_pattern.findall(value)
        return m is not None

    def __validate_text(self, validator, name, value):
        pass

    def __validate_float(self, validator, name, value):
        pass

    def __validate_term(self, validator, name, value):
        pass

    @property
    def types(self):
        return self.__type_defs.keys()

    def get_type_def(self, dtype):
        return self.__type_defs[dtype]

    def get_property_defs(self, dtype):
        property_defs = {}
        type_def = self.get_type_def(dtype)
        for prop in type_def['properties']:
            property_defs[prop['name']] = prop
        return property_defs

    def validate_type(self, dtype, data):
        type_def = self.get_type_def(dtype)

        # check that all properties are present
        for property_def in type_def['properties']:
            property_name = property_def['name']

            if property_def['required'] and property_name not in data:
                raise ValueError(
                    'The required property is absent: %s' % property_name)

        # check that there are no undeclared properties
        property_defs = self.get_property_defs(dtype)
        for prop_name in data:
            if prop_name not in property_defs:
                raise ValueError(
                    'The object has undeclared property: %s' % prop_name)

    def validate_values(self, dtype, data):
        type_def = self.get_type_def(dtype)
        for property_def in type_def['properties']:
            property_name = property_def['name']
            property_type = property_def['type']
            property_value = data.get(property_name)
            if property_value is None:
                if property_def['required']:
                    raise ValueError(
                        'The required property is absent: %s' % property_name)
                else:
                    continue

            # check value type
            self.__check_value_type[property_type](
                property_name, property_value)

            # apply validator if defined
            if 'validator' in property_def:
                self.__validate_value[property_type](
                    property_def['validator'], property_name, property_value)

    def validate_entity_process(self, entity_type, process_type, process_data):
        pass
