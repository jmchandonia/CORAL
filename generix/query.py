from .utils import to_var_name
from .ontology import Term
from .indexdef import IndexPropertyDef
from .typedef import TYPE_NAME_BRICK, TYPE_NAME_PROCESS, TYPE_CATEGORY_DYNAMIC, TYPE_CATEGORY_STATIC
from .descriptor import DataDescriptorCollection, EntityDescriptor, BrickDescriptor, ProcessDescriptor
from . import services

FILTER_FULLTEXT = 'FULLTEXT'
FILTER_EQ = '=='
FILTER_LT = '<'
FILTER_LTE = '<='
FILTER_GT = '>'
FILTER_GTE = '>='
FILTER_IN = 'IN'
FILTER_ARR_IN = '@IN'


_OPERATIONS = {
    '=':  FILTER_EQ,
    '==': FILTER_EQ,
    'eq': FILTER_EQ,
    '>':  FILTER_GT,
    'gt': FILTER_GT,
    '<':  FILTER_LT,
    'lt': FILTER_LT,
    '>=': FILTER_LTE,
    'gte':FILTER_LTE,
    '<=': FILTER_LTE,
    'lte':FILTER_LTE,
    'fulltext': FILTER_FULLTEXT,
    'match': FILTER_FULLTEXT,
    'like': FILTER_FULLTEXT,
    'in': FILTER_IN
}

class Query:
    def __init__(self, index_type_def):

        self.__index_type_def = index_type_def
        self.__has_filters = {}
        self.__linked_up_filters = []
        self.__linked_dn_filters = []
        self.__input_of_process_filters = {}
        self.__output_of_process_filters = {}
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

                # check and polish operation
                operation = operation.lower()
                if operation not in _OPERATIONS:
                    raise ValueError('Unknown operation: %s' % operation)
                operation = _OPERATIONS[operation]

                # polish value and prop_name
                ip_def = index_type_def.get_property_def(prop_name)

                if ip_def.scalar_type in ['term', '[term]'] :
                    # build term_ids
                    term_ids = []
                    if type(value) is str:
                        if operation == FILTER_FULLTEXT:
                            tc = services.ontology.all.find_name_pattern(value)
                            if tc.size == 0:
                                raise ValueError('Can not find a term with pattern: %s' % value)
                            term_ids = tc.term_ids
                        else:
                            term_ids.append( Term.get_term(value).term_id )
                    elif type(value) is list:
                        term_ids = [t.term_id for t in Term.get_terms(value) ]
                    elif type(value) is Term:
                        term_ids.append(value.term_id)
                    else:
                        raise ValueError('Wrong type of the value for the %s property' & prop_name )                 

                    # update operation, prop_name and value
                    if ip_def.scalar_type == 'term':
                        prop_name = prop_name + '_term_id'
                        if len(term_ids) == 1:
                            operation = FILTER_EQ
                            value = term_ids[0]
                        else:
                            operation = FILTER_IN
                            value = term_ids
                    elif ip_def.scalar_type == '[term]':
                        prop_name = prop_name[:-1] + '_ids'                
                        if len(term_ids) == 1:
                            operation = FILTER_ARR_IN
                            value = term_ids[0]
                        else:
                            operation = FILTER_ARR_IN
                            value = term_ids
                else:
                    if ip_def.scalar_type.startswith('['):
                        operation = FILTER_ARR_IN

                # get operation filters
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

    def is_input_of_process(self, criterion):
        index_type_def = services.indexdef.get_type_def(TYPE_NAME_PROCESS)
        self.__add_filters(criterion, self.__input_of_process_filters, index_type_def)
        return self

    def is_output_of_process(self, criterion):
        index_type_def = services.indexdef.get_type_def(TYPE_NAME_PROCESS)
        self.__add_filters(criterion, self.__output_of_process_filters, index_type_def)
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

    def _find_upks(self, upks):        
        cname = self.__index_type_def.collection_name
        typedef = services.typedef.get_type_def(self.__index_type_def.name)
        pk = typedef.pk_property_def
        upk = typedef.upk_property_def

        aql = '''
            FOR x in %s 
            filter x.%s in @upk_ids
            return {'pk': x.%s, 'upk': x.%s}            
        ''' % (cname, upk.name, pk.name, upk.name)

        aql_bind = {'upk_ids': upks}
        rs = services.arango_service.find(aql, aql_bind, len(upks))

        pk_upks = []
        for row in rs:
            pk_upks.append({
                'pk': row['pk'],
                'upk': row['upk']
            })
        return pk_upks

    def _find_pks(self, pks):        
        cname = self.__index_type_def.collection_name
        typedef = services.typedef.get_type_def(self.__index_type_def.name)
        pk = typedef.pk_property_def

        aql = '''
            FOR x in %s 
            filter x.%s in @pk_ids
            return {'pk': x.%s }           
        ''' % (cname, pk.name, pk.names)

        aql_bind = {'pk_ids': pks}
        rs = services.arango_service.find(aql, aql_bind, len(pks))

        pks = []
        for row in rs:
            pks.append(row['pk'])
        return pks

    def find_ids(self):
        return []
        # TODO
        # es_query = services.es_search._build_query(self.__es_filters)
        # # id_field_name = 'brick_id' if self.__type_name == 'brick' else 'id'
        # # return services.es_search._find_entity_ids(self.__type_name, id_field_name, es_query)
        # return services.es_search._find_entity_ids(self.__type_name, 'id', es_query)

    def __build_aql_trio(self, filters, index_type_def, var_name):

        cname = self.__param_name('@collection')

        aql_source = index_type_def.collection_name
        aql_filter = ['1==1']
        aql_bind = {}

        for filter_type, filters in filters.items():
            if filter_type in [FILTER_EQ, FILTER_LT, FILTER_LTE, FILTER_GT, FILTER_GTE]:
                for ft in filters:
                    pname = self.__param_name()
                    aql_filter.append( '%s.%s %s @%s' %(var_name, ft['name'], filter_type, pname) )
                    aql_bind[ pname ] = ft['value']
            elif filter_type == FILTER_IN:
                for ft in filters:
                    pname = self.__param_name()
                    value = ft['value']
                    if type(value) is not list:
                        value = [value]
                    aql_filter.append( '%s.%s IN @%s' %(var_name, ft['name'], pname) )
                    aql_bind[ pname ] = value
            elif filter_type == FILTER_ARR_IN:
                for ft in filters:
                    pname = self.__param_name()
                    aql_bind[ pname ] = ft['value']
                    if type(ft['value']) is list:
                        aql_filter.append('length(intersection(%s.%s, @%s)) > 0' % (var_name, ft['name'], pname) )
                    else:
                        aql_filter.append( '@%s IN %s.%s' %(pname, var_name, ft['name']) )

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
        elif self.__index_type_def.name == TYPE_NAME_PROCESS: 
            dd = ProcessDescriptor(row)
        else:
            dd = EntityDescriptor(self.__index_type_def, row)
        return dd

    def __clean(self):
        self.__tmp_index = 0
        self.__has_filters = {}
        self.__linked_up_filters = []
        self.__linked_dn_filters = []
        self.__input_of_process_filters = {}
        self.__output_of_process_filters = {}


    def find(self, size = 1000):
        var_name = 'x'
        aql_source, aql_filter, aql_bind = self.__build_aql_trio(self.__has_filters, self.__index_type_def, var_name)
        
        process_itd = services.indexdef.get_type_def(TYPE_NAME_PROCESS)
        pr_aqls = []
        if self.__input_of_process_filters:
            pi_var_name = 'pi'
            pi_aql_source, pi_aql_filter, pi_aql_bind = self.__build_aql_trio(
                    self.__input_of_process_filters, 
                    process_itd, 
                    pi_var_name)
            pi_aql = '''
                FOR spi IN SYS_ProcessInput FILTER %s._id == spi._from
                FOR %s IN %s FILTER spi._to == %s._id and %s               
            ''' % (
                var_name, 
                pi_var_name, 
                pi_aql_source,
                pi_var_name, 
                ' and '.join(pi_aql_filter),
                )
            aql_bind.update(pi_aql_bind)
            pr_aqls.append(pi_aql)


        if self.__output_of_process_filters:
            po_var_name = 'po'
            po_aql_source, po_aql_filter, po_aql_bind = self.__build_aql_trio(
                    self.__output_of_process_filters, 
                    process_itd, 
                    po_var_name)
            po_aql = '''
                FOR spo IN SYS_ProcessOutput FILTER %s._id == spo._to
                FOR %s IN %s FILTER spo._from == %s._id and %s               
            ''' % (
                var_name, 
                po_var_name, 
                po_aql_source,
                po_var_name, 
                ' and '.join(po_aql_filter),
                )
            aql_bind.update(po_aql_bind)
            pr_aqls.append(po_aql)


        if len(self.__linked_up_filters) == 0 and len(self.__linked_dn_filters) == 0:

            aql = 'FOR %s IN %s FILTER %s %s RETURN distinct %s' % (
                var_name, 
                aql_source, 
                ' and '.join(aql_filter),
                ' '.join(pr_aqls),
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
                    %s
                    return distinct %s 
                ''' % ( 
                    u_var_name,
                    u_aql_source, 
                    ' and '.join(u_aql_filter), 
                    var_name,
                    ' and '.join(_aql_filter),
                    ' '.join(pr_aqls),
                    var_name)
                
                aql_var = self.__param_name('a')
                var_aqls.append({
                    'var_name': aql_var,
                    'aql': 'let %s = (%s) ' % (aql_var, uaql) 
                })

                aql_bind.update(u_aql_bind)

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
                    %s
                    return distinct %s
                ''' % ( 
                    d_var_name,
                    d_aql_source, 
                    ' and '.join(d_aql_filter), 
                    var_name,
                    ' and '.join(_aql_filter),
                    ' '.join(pr_aqls),
                    var_name)
                
                aql_var = self.__param_name('a')
                var_aqls.append({
                    'var_name': aql_var,
                    'aql': 'let %s = (%s) ' % (aql_var, daql) 
                })

                aql_bind.update(d_aql_bind)
            
            # build final aql

            if len(var_aqls) == 1:
                aql_return = var_aqls[0]['var_name']
            else:
                aql_return = 'intersection(%s)' % (','.join( a['var_name']  for a in var_aqls ))

            aql =  '%s FOR x IN %s RETURN x' %  (
                ' '.join( a['aql'] for a in var_aqls ),
                aql_return
            )

        
        # print('aql = ', aql)
        # print('aql_bind = ', aql_bind)

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

