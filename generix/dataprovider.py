import re
from .ontology import Term
from . import services
from .brick import BrickDescriptorCollection
from .search import EntityDescriptorCollection


class DataProvider:
    def __init__(self):
        pass
        # self.__load_dtypes()

    # def __load_dtypes(self):
    #     self.__dict__['TYPE_Taxonomic_Abundance'] = DataType('DA:0000028')
    #     self.__dict__['TYPE_Microbial_GROWTH'] = DataType('DA:0000019')

    @property
    def ontology(self):
        return services.ontology

    @property
    def entities(self):
        return EntitiesProvider()

    # def find_bricks(self):
    #     return BrickFilter()


class EntitiesProvider:
    def __init__(self):
        self.__load_entity_providers()

    def __load_entity_providers(self):
        self.__dict__['brick'] = EntityProvider('brick')
        self.__dict__['well'] = EntityProvider('well')
        self.__dict__['sample'] = EntityProvider('sample')


class EntityProvider:
    def __init__(self, type_name):
        self.__type_name = type_name
        self.__properties = self.__get_properties()

        self.__inflate_properties(self.__properties)
        # self.__properties = None
        # self.__load_properties()

    def __get_properties(self):
        properties = {}
        props = services.es_search.get_entity_properties(
            self.__type_name)
        for prop in props:
            key = 'PROPERTY_' + re.sub('[^A-Za-z0-9]+', '_', prop)
            properties[key] = prop
        return properties

    def __inflate_properties(self, properties):
        # if self.__type_name == 'brick':
        #     props = services.es_search.get_entity_properties(
        #         self.__type_name)
        # else:
        #     props = ['id', 'name']

        for key in properties:
            self.__dict__[key] = properties[key]

        # props = services.es_search.get_entity_properties(
        #     self.__type_name)
        # for prop in props:
        #     key = 'PROPERTY_' + re.sub('[^A-Za-z0-9]+', '_', prop)
        #     self.__dict__[key] = prop

    # def __load_properties(self):
    #     if self.__type_name == 'brick':
    #         self.__properties = EntityProperties(self.__type_name)
    #         # self.__properties = services.es_search.get_entity_properties(
    #         #     self.__type_name)
    #     else:
    #         self.__properties = ['id', 'name', 'description']

    # @property
    # def properties(self):
    #     return self.__properties

    def find(self, criterion):
        return self.query().has(criterion).find()

    def find_one(self, criterion):
        return self.query().has(criterion).find_one()

    def query(self):
        return Query(self.__type_name, self.__properties)


class Query:
    def __init__(self, type_name, properties):
        self.__type_name = type_name
        self.__es_filters = {}
        self.__neo_filters = []
        for key in properties:
            self.__dict__[key] = properties[key]

    def _add_es_filter(self, es_filters, criterion):
        if type(criterion) is dict:
            for key in criterion:
                if type(criterion[key]) is list:
                    prefix = 'terms'
                else:
                    prefix = 'term'
                es_filters[prefix + '.' + key] = criterion[key]
        else:
            print('Error: Criterion should be a dict')

    def has(self, criterion):
        self._add_es_filter(self.__es_filters, criterion)
        return self

    def linked_to(self, type_name, criterion):
        self.__neo_filters.append({'dtype': type_name, 'criterion': criterion})
        return self

    def find_ids(self):
        es_query = services.es_search._build_query(self.__es_filters)
        id_field_name = 'brick_id' if self.__type_name == 'brick' else 'entity_id'
        return services.es_search._find_entity_ids(self.__type_name, id_field_name, es_query)

    def find(self):
        neo_ids = set()

        # collect ids based on links
        for neo_filter in self.__neo_filters:
            source_type = neo_filter['dtype']
            source_crierion = neo_filter['criterion']
            q = Query(source_type, {})
            q.has(source_crierion)
            source_ids = q.find_ids()

            source_type = 'Generic' if source_type == 'brick' else source_type[0:1].upper(
            ) + source_type[1:]

            target_type = self.__type_name
            target_type = 'Generic' if target_type == 'brick' else target_type[0:1].upper(
            ) + target_type[1:]

            linked_ids = services.neo_search.find_linked_ids(
                source_type, 'id', source_ids, target_type, 'id')

            for linked_id in linked_ids:
                neo_ids.add(linked_id.lower())

        print('neo_ids', neo_ids)

        es_filter = {}
        if len(self.__neo_filters) > 0:
            id_filed_name = 'brick_id' if self.__type_name == 'brick' else 'entity_id'
            self._add_es_filter(es_filter, {id_filed_name: list(neo_ids)})
        for key in self.__es_filters:
            es_filter[key] = self.__es_filters[key]

        es_query = services.es_search._build_query(es_filter)
        if self.__type_name == 'brick':
            return BrickDescriptorCollection(services.es_search._find_bricks(es_query))
        else:
            return EntityDescriptorCollection(services.es_search._find_entities(self.__type_name, es_query))

    def find_one(self):
        pass


class EntityProperties:
    def __init__(self, type_name):
        self.__type_name = type_name
        self.__properties = []
        self.__inflate_properties()

    def __inflate_properties(self):
        self.__properties = services.es_search.get_entity_properties(
            self.__type_name)
        for prop in self.__properties:
            key = 'TERM_' + re.sub('[^A-Za-z0-9]+', '_', prop)
            self.__dict__[key] = prop

    def _repr_html_(self):
        self.__properties

        # class EntityProperty:
        #     def __init__(self, type_name, property_name):
        #         self.__type_name = type_name
        #         self.__property_name = property_name

        #     def __eq__(self, value):
        #         return PropertyCriterion(self.__type_name, self.__property_name, 'eq', value)

        # class PropertyCriterion:
        #     def __init__(self, type_name, property_name, operand, value):
        #         self.__type_name = type_name
        #         self.__property_name = property_name
        #         self.__operand = operand
        #         self.__value = value

        #     def __str__(self):
        #         return '%s.%s <%s> %s' % (self.__type_name, self.__property_name,
        #                                   self.__operand, self.__value)

        # class BrickFilter:
        #     def __init__(self):
        #         self.__es_filters = {}
        #         self.__neo_filters = {}

        #     def has_data_term_ids(self, data_type_term_ids):
        #         self.__es_filters["term.data_type_term_id"] = data_type_term_ids
        #         return self

        #     def has_term_ids(self, term_ids):
        #         self.__es_filters['terms.all_term_ids'] = term_ids
        #         return self

        #     def from_well(self, well_name):
        #         self.__neo_filters['Well.name'] = well_name
        #         return self

        #     def go(self):
        #         if len(self.__neo_filters) > 0:
        #             brick_ids = services.neo_search.brick_ids_from_well(
        #                 self.__neo_filters['Well.name'])
        #             self.__es_filters['terms.brick_id'] = brick_ids

        #         es_query = services.es_search._build_query(self.__es_filters)
        #         return BrickDescriptorCollection(services.es_search._find_bricks(es_query))

        # class DataType:
        #     def __init__(self, term_id):
        #         self.__term = Term(term_id)
        #         self.__load_properties()

        #     def __load_properties(self):
        #         self.__dict__['id'] = 'id'
        #         self.__dict__['name'] = 'name'
        #         self.__dict__['date'] = 'date'

        # class DataTypeProperty:
        #     def __init__(self, property_name):
        #         self.__property_name = property_name

        #     @property
        #     def name(self):
        #         return self.__property_name

        # class Criterion:
        #     def __init__(self, parent):
        #         self.__parent = parent

        #     def connected_up(self, dtype=None, props=None):
        #         return CriterionConnectedUp(self, dtype, props)

        # class CriterionConnectedUp(Criterion):
        #     def __init__(self, parent)
