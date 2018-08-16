from .ontology import Term
from . import services
from .brick import BrickDescriptorCollection


class DataProvider:
    def __init__(self):
        self.__load_dtypes()

    def __load_dtypes(self):
        self.__dict__['TYPE_Taxonomic_Abundance'] = DataType('DA:0000028')
        self.__dict__['TYPE_Microbial_GROWTH'] = DataType('DA:0000019')

    def find_bricks(self):
        return BrickFilter()


class PropertyCriterion:
    def __init__(self, type_name, property_name, operand, value):
        self.__type_name = type_name
        self.__property_name = property_name
        self.__operand = operand
        self.__value = value

    def __str__(self):
        return '%s.%s <%s> %s' % (self.__type_name, self.__property_name,
                                  self.__operand, self.__value)


class EntityProperty:
    def __init__(self, type_name, property_name):
        self.__type_name = type_name
        self.__property_name = property_name

    def __eq__(self, value):
        return PropertyCriterion(self.__type_name, self.__property_name, 'eq', value)


class EntityType:
    def __init__(self, type_name):
        self.__type_name = type_name
        self.__inflate_properties()

    def __inflate_properties(self):
        props = services.es_search.get_entity_properties(
            self.__type_name)
        for prop in props:
            self.__dict__[prop] = EntityProperty(self.__type_name, prop)


class BrickFilter:
    def __init__(self):
        self.__es_filters = {}
        self.__neo_filters = {}

    def has_data_term_ids(self, data_type_term_ids):
        self.__es_filters["term.data_type_term_id"] = data_type_term_ids
        return self

    def has_term_ids(self, term_ids):
        self.__es_filters['terms.all_term_ids'] = term_ids
        return self

    def from_well(self, well_name):
        self.__neo_filters['Well.name'] = well_name
        return self

    def go(self):
        if len(self.__neo_filters) > 0:
            brick_ids = services.neo_search.brick_ids_from_well(
                self.__neo_filters['Well.name'])
            self.__es_filters['terms.brick_id'] = brick_ids

        es_query = services.es_search._build_query(self.__es_filters)
        return BrickDescriptorCollection(services.es_search._find_bricks(es_query))


class DataType:
    def __init__(self, term_id):
        self.__term = Term(term_id)
        self.__load_properties()

    def __load_properties(self):
        self.__dict__['id'] = 'id'
        self.__dict__['name'] = 'name'
        self.__dict__['date'] = 'date'


class DataTypeProperty:
    def __init__(self, property_name):
        self.__property_name = property_name

    @property
    def name(self):
        return self.__property_name


# class Criterion:
#     def __init__(self, parent):
#         self.__parent = parent

#     def connected_up(self, dtype=None, props=None):
#         return CriterionConnectedUp(self, dtype, props)

# class CriterionConnectedUp(Criterion):
#     def __init__(self, parent)
