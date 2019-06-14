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
        q = self.query()
        q.has(criterion)
        return q.find()

    def find_one(self, criterion=None):
        q = self.query()
        q.has(criterion)
        return q.find_one()

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
FILTER_EQ = '=='
FILTER_LT = '<'
FILTER_LTE = '<='
FILTER_GT = '>'
FILTER_GTE = '>='


_OPERATIONS = {
    '=': '==',
    '==': '==',
    'eq': '==',
    '>': '>',
    'gt': '>',
    '<': '<',
    'lt': '<',
    '>=': '>=',
    'gte': '>=',
    '<=': '<=',
    'lte': '<=',
    'fulltext': 'FULLTEXT',
    'FULLTEXT': 'FULLTEXT'
}

class Query:
    def __init__(self, index_type_def):

        self.__index_type_def = index_type_def
        self.__has_filters = {}
        self.__linked_up_filters = []
        self.__linked_dn_filters = []
        self.__tmp_index = 0

        for index_prop_def in index_type_def.property_defs:
            key = to_var_name('PROPERTY_', index_prop_def.name)            
            self.__dict__[key] = index_prop_def

    def __check_property(self, prop_name, index_type_def):
        if not index_type_def.has_property(prop_name) :
            raise ValueError('Unknown property %s' % prop_name)

    def __add_filters(self, criterion, filters, index_type_def):
        if type(criterion) is not dict:
            print('Error: Criterion should be a dict')

        for prop, operaion_value_pairs in criterion.items():
            prop_name = prop
            if type(prop) is IndexPropertyDef:
                prop_name = prop.name

            self.__check_property(prop_name, index_type_def)
            if type(operaion_value_pairs) is not dict:
                operaion_value_pairs = {
                    '==': operaion_value_pairs
                }

            for operation, value in operaion_value_pairs.items():
                if operation not in _OPERATIONS:
                    raise ValueError('Unknown operation: %s' % operation)

                operation = _OPERATIONS[operation]
                operation_filters = filters.get(operation)
                if operation_filters is None:
                    operation_filters = []
                    filters[operation] = operation_filters
                    operation_filters.append({
                        'name': prop_name,
                        'value': value
                    })

    def has(self, criterion):
        if criterion is None:
            criterion = {}
        self.__add_filters(criterion, self.__has_filters, self.__index_type_def)
        return self

    def linked_up_to(self, type_name, criterion):
        index_type_def = services.indexdef.get_type_def(type_name)
        filters = {}
        self.__add_filters(criterion, filters, index_type_def)
        self.__linked_up_filters.append({
            'index_type_def': index_type_def,
            'filters': filters
        })
        return self

    def linked_down_to(self, type_name, criterion):
        index_type_def = services.indexdef.get_type_def(type_name)
        filters = {}
        self.__add_filters(criterion, filters, index_type_def)
        self.__linked_dn_filters.append({
            'index_type_def': index_type_def,
            'filters': filters
        })
        return self

    def find_ids(self):
        return []
        # TODO
        # es_query = services.es_search._build_query(self.__es_filters)
        # # id_field_name = 'brick_id' if self.__type_name == 'brick' else 'id'
        # # return services.es_search._find_entity_ids(self.__type_name, id_field_name, es_query)
        # return services.es_search._find_entity_ids(self.__type_name, 'id', es_query)

    def __build_aql_trio(self, filters, index_type_def, var_name):

        cname = self.__param_name('@collection')
        # aql_source = '@%s' % cname
        # aql_filter = ['1==1']
        # aql_bind = { cname: index_type_def.collection_name}

        aql_source = index_type_def.collection_name
        aql_filter = ['1==1']
        aql_bind = {}

        for filter_type, filters in filters.items():
            if filter_type in [FILTER_EQ, FILTER_LT, FILTER_LTE, FILTER_GT, FILTER_GTE]:
                for ft in filters:
                    pname = self.__param_name()
                    aql_filter.append( '%s.%s %s @%s' %(var_name, ft['name'], filter_type, pname) )
                    aql_bind[ pname ] = ft['value']
            elif filter_type == FILTER_FULLTEXT:
                for ft in filters:
                    pname = self.__param_name()
                    pval = self.__param_name()
                    aql_source = 'FULLTEXT(@%s, @%s, @%s)' %(cname, pname, pval)
                    aql_bind[ cname ] = index_type_def.collection_name
                    aql_bind[ pname ] = ft['name']
                    aql_bind[ pval  ] = ft['value']
        
        return (aql_source, aql_filter, aql_bind)

    def __param_name(self, name=None):
        if name is None:
            name = 'p'
        self.__tmp_index += 1            
        return '%s_%s' % (name, self.__tmp_index)

    def __to_descriptor(self, row):
        if self.__index_type_def.name == TYPE_NAME_BRICK:
            dd = BrickDescriptor(row)
        else:
            dd = EntityDescriptor(self.__index_type_def, row)
        return dd

    def __clean(self):
        self.__tmp_index = 0
        self.__has_filters = {}
        self.__linked_up_filters = []
        self.__linked_dn_filters = []


    def find(self, size = 100):
        var_name = 'x'
        aql_source, aql_filter, aql_bind = self.__build_aql_trio(self.__has_filters, self.__index_type_def, var_name)

        if len(self.__linked_up_filters) == 0 and len(self.__linked_dn_filters) == 0:
            aql = 'FOR %s IN %s FILTER %s RETURN %s' % (
                var_name, 
                aql_source, 
                ' and '.join(aql_filter),
                var_name)
        else:
            var_aqls = []

            # Do up filters
            for up_filters in self.__linked_up_filters:
                index_type_def = up_filters['index_type_def']
                filters = up_filters['filters']

                u_var_name = 's'
                u_aql_source, u_aql_filter, u_aql_bind = self.__build_aql_trio(
                    filters, 
                    index_type_def, 
                    u_var_name)

                _aql_filter = aql_filter.copy()
                cname = self.__index_type_def.collection_name
                _aql_filter.append('IS_SAME_COLLECTION(%s, %s._id)' % (cname,var_name))

                uaql = '''
                    FOR %s IN %s FILTER %s 
                    FOR %s in 1..10 OUTBOUND s SYS_ProcessInput, SYS_ProcessOutput
                    FILTER %s
                    return distinct %s 
                ''' % ( 
                    u_var_name,
                    u_aql_source, 
                    ' and '.join(u_aql_filter), 
                    var_name,
                    ' and '.join(_aql_filter),
                    var_name)
                
                aql_var = self.__param_name('a')
                var_aqls.append({
                    'var_name': aql_var,
                    'aql': 'let %s = (%s) ' % (aql_var, uaql) 
                })

                for key, value in u_aql_bind.items():
                    aql_bind[key] = value

            # Do dn filters
            for dn_filters in self.__linked_dn_filters:
                index_type_def = dn_filters['index_type_def']
                filters = dn_filters['filters']
                d_var_name = 's'
                d_aql_source, d_aql_filter, d_aql_bind = self.__build_aql_trio(
                    filters, 
                    index_type_def,
                    d_var_name)

                _aql_filter = aql_filter.copy()
                cname = self.__index_type_def.collection_name
                _aql_filter.append('IS_SAME_COLLECTION(%s, %s._id)' % (cname, var_name))

                daql = '''
                    FOR %s IN %s FILTER %s 
                    FOR %s in 1..10 INBOUND s SYS_ProcessInput, SYS_ProcessOutput
                    FILTER %s
                    return distinct %s
                ''' % ( 
                    d_var_name,
                    d_aql_source, 
                    ' and '.join(d_aql_filter), 
                    var_name,
                    ' and '.join(_aql_filter),
                    var_name)
                
                aql_var = self.__param_name('a')
                var_aqls.append({
                    'var_name': aql_var,
                    'aql': 'let %s = (%s) ' % (aql_var, daql) 
                })


                for key, value in d_aql_bind.items():
                    aql_bind[key] = value
            
            # build final aql

            if len(var_aqls) == 1:
                aql_return = var_aqls[0]['var_name']
            else:
                aql_return = 'intersection(%s)' % (','.join( a['var_name']  for a in var_aqls ))

            aql =  '%s FOR x IN %s RETURN x' %  (
                ' '.join( a['aql'] for a in var_aqls ),
                aql_return
            )

        
        print('aql = ', aql)
        print('aql_bind = ', aql_bind)

        data_descriptors = []
        rs = services.arango_service.find(aql, aql_bind, size)
        for row in rs:
            data_descriptors.append(self.__to_descriptor(row))
        dds = DataDescriptorCollection(data_descriptors=data_descriptors)

        self.__clean()
        return dds

    def find_one(self):
        ddc = self.find(size=1)
        if ddc.size > 0:
            return ddc[0]
        return None

