import re
from .ontology import Term
from . import services
from .brick import Brick, BrickProvenance
from .utils import to_var_name
from .typedef import TYPE_NAME_BRICK


class DataProvider:
    def __init__(self):
        self.__etities_provider = EntitiesProvider()
        self.__generics_provider = GenericsProvider()
        self.__reports = DataReports()

    @property
    def ontology(self):
        return services.ontology

    @property
    def core_types(self):
        return self.__etities_provider

    @property
    def genx_types(self):
        return self.__generics_provider

    @property
    def user_profile(self):
        return services.user_profile

    @property
    def reports(self):
        return self.__reports

    def _get_type_provider(self, type_name):
        provider = None
        if type_name == TYPE_NAME_BRICK:
            provider = BrickProvider()        
        else:
            provider = EntityProvider(type_name)
        return provider


class DataReports:
    def __init__(self):
        pass

    @property
    def brick_types(self):
        return services.ontology.data_type_terms()

    @property
    def brick_dim_types(self):
        return services.ontology.dim_type_terms()

    @property
    def brick_data_var_types(self):
        return services.ontology.value_type_terms()


class GenericsProvider:
    def __init__(self):
        self.__load_providers()

    def __load_providers(self):
        type_names = services.arango_service.get_type_names()
        for type_name in type_names:
            if type_name == TYPE_NAME_BRICK:
                self.__dict__[type_name] = BrickProvider()


class EntitiesProvider:
    def __init__(self):
        self.__load_entity_providers()

    def __load_entity_providers(self):
        type_names = services.arango_service.get_type_names()
        for type_name in type_names:
            if type_name != TYPE_NAME_BRICK:
                self.__dict__[type_name] = EntityProvider(type_name)


class EntityProvider:
    def __init__(self, type_name):
        self.__type_name = type_name
        self.__properties = self.__get_properties()
        self.__inflate_properties(self.__properties)

    def __get_properties(self):
        properties = {}
        props = services.arango_service.get_entity_properties(
            self.__type_name)
        for prop in props:
            key = to_var_name('PROPERTY_', prop)
            properties[key] = prop
        return properties

    def __inflate_properties(self, properties):
        for key in properties:
            self.__dict__[key] = properties[key]

    def find(self, criterion):
        return self.query().has(criterion).find()

    def find_one(self, criterion):
        return self.query().has(criterion).find_one()

    def query(self):
        return Query(self.__type_name, self.__properties)


class BrickProvider(EntityProvider):
    def __init__(self):
        super().__init__(TYPE_NAME_BRICK)

    def load(self, brick_id):
        brick = Brick.read_dict(
            brick_id,  services.workspace.get_brick_data(brick_id))
        provenance = BrickProvenance('loaded', ['id:%s' % brick.id])
        brick.session_provenance.provenance_items.append(provenance)
        return brick


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

    def linked_up_to(self, type_name, criterion):
        self.__neo_filters.append(
            {'dtype': type_name, 'criterion': criterion, 'direct': True})
        return self

    def linked_down_to(self, type_name, criterion):
        self.__neo_filters.append(
            {'dtype': type_name, 'criterion': criterion, 'direct': False})
        return self

    def find_ids(self):
        return []
        # TODO
        # es_query = services.es_search._build_query(self.__es_filters)
        # # id_field_name = 'brick_id' if self.__type_name == 'brick' else 'id'
        # # return services.es_search._find_entity_ids(self.__type_name, id_field_name, es_query)
        # return services.es_search._find_entity_ids(self.__type_name, 'id', es_query)

    def find(self):
        return []
        # TODO
        # neo_ids = set()

        # # collect ids based on links
        # for neo_filter in self.__neo_filters:
        #     source_type = neo_filter['dtype']
        #     source_crierion = neo_filter['criterion']
        #     direct = neo_filter['direct']
        #     q = Query(source_type, {})
        #     q.has(source_crierion)
        #     source_ids = q.find_ids()

        #     source_type = 'Brick' if source_type == 'brick' else source_type[0:1].upper(
        #     ) + source_type[1:]

        #     target_type = self.__type_name
        #     target_type = 'Brick' if target_type == 'brick' else target_type[0:1].upper(
        #     ) + target_type[1:]

        #     linked_ids = services.neo_service.find_linked_ids(
        #         source_type, 'id', source_ids, target_type, 'id', direct=direct)

        #     for linked_id in linked_ids:
        #         neo_ids.add(linked_id)

        # es_filter = {}
        # if len(self.__neo_filters) > 0:
        #     # id_filed_name = 'brick_id' if self.__type_name == 'brick' else 'id'
        #     # self._add_es_filter(es_filter, {id_filed_name: list(neo_ids)})
        #     self._add_es_filter(es_filter, {'id': list(neo_ids)})
        # for key in self.__es_filters:
        #     es_filter[key] = self.__es_filters[key]

        # es_query = services.es_search._build_query(es_filter)
        # if self.__type_name == 'brick':
        #     return DataDescriptorCollection(data_descriptors=services.es_search._find_bricks(es_query))
        # else:
        #     return DataDescriptorCollection(data_descriptors=services.es_search._find_entities(self.__type_name, es_query))

    def find_one(self):
        pass
        # TODO
        # ddc = self.find()
        # if ddc.size > 0:
        #     return ddc[0]
        # return None


class EntityProperties:
    def __init__(self, type_name):
        self.__type_name = type_name
        self.__properties = []
        self.__inflate_properties()

    def __inflate_properties(self):
        self.__properties = services.arango_service.get_entity_properties(
            self.__type_name)
        for prop in self.__properties:
            key = to_var_name('TERM_', prop)
            self.__dict__[key] = prop

    def _repr_html_(self):
        self.__properties
