import re
from .ontology import Term
from . import services
from .brick import Brick, BrickProvenance
from .utils import to_var_name
from .descriptor import DataDescriptorCollection, EntityDescriptor, BrickDescriptor
from .typedef import TYPE_NAME_BRICK, TYPE_CATEGORY_DYNAMIC, TYPE_CATEGORY_STATIC
from .indexdef import IndexPropertyDef


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

        type_def = services.indexdef.get_type_def(type_name)
        provider = None        
        if type_name == TYPE_NAME_BRICK:
            provider = BrickProvider()        
        else:
            provider = EntityProvider(type_def)
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
        index_type_defs = services.indexdef.get_type_defs(category=TYPE_CATEGORY_DYNAMIC)
        for index_type_def in index_type_defs:
            if index_type_def.name == TYPE_NAME_BRICK:
                self.__dict__[TYPE_NAME_BRICK] = BrickProvider()


class EntitiesProvider:
    def __init__(self):
        self.__load_entity_providers()

    def __load_entity_providers(self):
        index_type_defs = services.indexdef.get_type_defs(category=TYPE_CATEGORY_STATIC)
        for index_type_def in index_type_defs:
            self.__dict__[index_type_def.name] = EntityProvider(index_type_def)


class EntityProvider:
    def __init__(self, index_type_def):
        self.__index_type_def = index_type_def
        self.__inflate_properties()

    def __inflate_properties(self):
        for index_prop_def in self.__index_type_def.property_defs:
            key = to_var_name('PROPERTY_', index_prop_def.name)
            self.__dict__[key] = index_prop_def

    def find(self, criterion=None):
        return self.query().has(criterion).find()

    def find_one(self, criterion=None):
        return self.query().has(criterion).find_one()

    def query(self):
        return Query(self.__index_type_def)


class BrickProvider(EntityProvider):
    def __init__(self):
        super().__init__(services.indexdef.get_type_def(TYPE_NAME_BRICK) )

    def load(self, brick_id):
        brick = Brick.read_dict(
            brick_id,  services.workspace.get_brick_data(brick_id))
        provenance = BrickProvenance('loaded', ['id:%s' % brick.id])
        brick.session_provenance.provenance_items.append(provenance)
        return brick

FILTER_FULLTEXT = 'FULLTEXT'
FILTER_EQ = ' == '
FILTER_LT = ' < '
FILTER_LE = ' <= '
FILTER_MT = ' > '
FILTER_ME = ' >= '

class Query:
    def __init__(self, index_type_def):

        self.__index_type_def = index_type_def
        self.__filters = {}

        for index_prop_def in index_type_def.property_defs:
            key = to_var_name('PROPERTY_', index_prop_def.name)            
            self.__dict__[key] = index_prop_def

    def _check_property(self, prop_name):
        key = to_var_name('PROPERTY_', prop_name)
        if key not in self.__dict__:
            raise ValueError('Unknown property %s' % prop_name)

    def _add_filters(self, criterion, filter_type):
        if type(criterion) is dict:
            for prop in criterion:
                prop_name = prop
                if type(prop) is IndexPropertyDef:
                    prop_name = prop.name

                self._check_property(prop_name)
                filters = self.__filters.get(filter_type)
                if filters is None:
                    filters = []
                    self.__filters[filter_type] = filters
                    filters.append({
                        'name': prop_name,
                        'value': criterion[prop]
                    })
        else:
            print('Error: Criterion should be a dict')


    # def _add_es_filter(self, es_filters, criterion):
    #     if type(criterion) is dict:
    #         for key in criterion:
    #             if type(criterion[key]) is list:
    #                 prefix = 'terms'
    #             else:
    #                 prefix = 'term'
    #             es_filters[prefix + '.' + key] = criterion[key]
    #     else:
    #         print('Error: Criterion should be a dict')

    def eq(self, criterion):
        self._add_filters(criterion, FILTER_EQ)
        return self

    def lt(self, criterion):
        self._add_filters(criterion, FILTER_LT)
        return self

    def le(self, criterion):
        self._add_filters(criterion, FILTER_LE)
        return self

    def mt(self, criterion):
        self._add_filters(criterion, FILTER_MT)
        return self

    def me(self, criterion):
        self._add_filters(criterion, FILTER_ME)
        return self

    def fulltext(self, criterion):
        self._add_filters(criterion, FILTER_FULLTEXT)
        return self

    def has(self, criterion):
        if criterion is None:
            criterion = {}
        self._add_filters(criterion, FILTER_EQ)
        return self

    def linked_up_to(self, type_name, criterion):
        pass
        # TODO
        # self.__neo_filters.append(
        #     {'dtype': type_name, 'criterion': criterion, 'direct': True})
        # return self

    def linked_down_to(self, type_name, criterion):
        pass
        # TODO
        # self.__neo_filters.append(
        #     {'dtype': type_name, 'criterion': criterion, 'direct': False})
        # return self

    def find_ids(self):
        return []
        # TODO
        # es_query = services.es_search._build_query(self.__es_filters)
        # # id_field_name = 'brick_id' if self.__type_name == 'brick' else 'id'
        # # return services.es_search._find_entity_ids(self.__type_name, id_field_name, es_query)
        # return services.es_search._find_entity_ids(self.__type_name, 'id', es_query)

    def find(self):

        aql_source = '@@collection'
        aql_filter = ['1==1']
        aql_bind = { '@collection': self.__index_type_def.collection_name}

        i = 0
        for filter_type, filters in self.__filters.items():
            if filter_type in [FILTER_EQ, FILTER_LT, FILTER_LE, FILTER_MT, FILTER_ME]:
                for ft in filters:
                    i += 1
                    aql_filter.append( 'x.%s %s @_p%s' %(ft['name'], filter_type, i) )
                    aql_bind[ '_p%s' % i ] = ft['value']
            elif filter_type == FILTER_FULLTEXT:
                for ft in filters:
                    aql_source = 'FULLTEXT(@@collection, @ft_prop_name, @ft_prop_value)'
                    aql_bind[ 'ft_prop_name' ] = ft['name']
                    aql_bind[ 'ft_prop_value' ] = ft['value']

        
        aql = 'FOR x IN %s FILTER %s RETURN x' % (aql_source, ' and '.join(aql_filter) )

        print('aql = ', aql)
        print('aql_bind = ', aql_bind)

        data_descriptors = []
        rs = services.arango_service.find(aql, aql_bind)
        for row in rs:
            if self.__index_type_def.name == TYPE_NAME_BRICK:
                dd = BrickDescriptor(row)
            else:
                dd = EntityDescriptor(self.__index_type_def, row)
            data_descriptors.append(dd)

        return DataDescriptorCollection(data_descriptors=data_descriptors)
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

