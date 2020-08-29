from .utils import to_var_name
from .ontology import Term
from .indexdef import IndexPropertyDef
from .typedef import TYPE_NAME_BRICK, TYPE_NAME_PROCESS, TYPE_CATEGORY_DYNAMIC, TYPE_CATEGORY_STATIC
from .descriptor import DataDescriptorCollection, EntityDescriptor, BrickDescriptor, ProcessDescriptor
from . import services
import sys

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
        self.__immediate_parent_filters = []
        self.__input_of_process_filters = {}
        self.__output_of_process_filters = {}
        self.__search_all_down = False
        self.__search_all_up = False
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

        for prop, operation_value_pairs in criterion.items():
            prop_name = prop
            if type(prop) is IndexPropertyDef:
                prop_name = prop.name

            self.__check_property(prop_name, index_type_def)
            if type(operation_value_pairs) is not dict:
                operation_value_pairs = {
                    '==': operation_value_pairs
                }

            for operation, value in operation_value_pairs.items():

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

    def search_all_up(self, b):
        self.__search_all_up = b
        return self

    def search_all_down(self, b):
        self.__search_all_down = b
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

    def immediate_parent(self, criterion):
        # check criterion is valid; add list wrapper if necessary
        if not 'processInputs' in criterion:
            raise ValueError('Need processInputs in %s' % criterion)
        if not 'processOutputs' in criterion:
            raise ValueError('Need processOutputs in %s' % criterion)
        if type(criterion['processInputs']) is not list:
            criterion['processInputs'] = [criterion['processInputs']]
        if type(criterion['processOutputs']) is not list:
            criterion['processOutputs'] = [criterion['processOutputs']]
        if len(criterion['processInputs']) < 1:
            raise ValueError('Need at least one processInputs in %s' % criterion)
        if len(criterion['processOutputs']) < 1:
            raise ValueError('Need at least one processOutputs in %s' % criterion)
        self.__immediate_parent_filters.append(criterion)
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
                curFilterName = ''
                curFilter = False
                for ft in sorted(filters, key=lambda x: x['name']):
                    pname = self.__param_name()
                    if ft['name'] != curFilterName:
                        curFilterName = ft['name']
                        if curFilter:
                            aql_filter.append(curFilter+')')
                        curFilter = '('
                    else:
                        curFilter += ' or '
                    curFilter += ( '%s.%s %s @%s' %(var_name, ft['name'], filter_type, pname) )
                    aql_bind[ pname ] = ft['value']
                aql_filter.append(curFilter+')')
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
        self.__immediate_parent_filters = []
        self.__input_of_process_filters = {}
        self.__output_of_process_filters = {}
        self.__search_all_down = False
        self.__search_all_up = False


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

        link_aql = ''

        if self.__output_of_process_filters:
            if self.__search_all_up==False and self.__search_all_down==False:
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

            else:
                po_var_name = 'po'
                po_aql_source, po_aql_filter, po_aql_bind = self.__build_aql_trio(
                    self.__output_of_process_filters, 
                    process_itd, 
                    po_var_name)
                link_aql = '''
                  let filtered_procs = (
                    for po in SYS_Process
                    filter %s
                    return po
                  )
                ''' % (' and '.join(po_aql_filter))
                if self.__search_all_up:
                    link_aql += '''
                      let upprocs=(
                        for p1 in filtered_procs
                        for p in 0..100 inbound p1 SYS_ProcessInput, SYS_ProcessOutput
                        OPTIONS {
                          bfs: true,
                          uniqueVertices: 'global'
                        }
                        filter is_same_collection("SYS_Process",p)
                        return p
                     )
                    '''
                else:
                    link_aql += '''
                      let upprocs=[]
                    '''
                if self.__search_all_down:
                    link_aql += '''
                      let dnprocs=(
                        for p1 in filtered_procs
                        for p in 1..100 outbound p1 SYS_ProcessInput, SYS_ProcessOutput
                        OPTIONS {
                          bfs: true,
                          uniqueVertices: 'global'
                        }
                        filter is_same_collection("SYS_Process",p)
                        return p
                      )
                    '''
                else:
                    link_aql += '''
                      let dnprocs=[]
                    '''
                link_aql += '''
                  let linked_ids = unique(flatten(
                    FOR p IN unique(append(upprocs,dnprocs))
                    let oo=(
                      for spo in SYS_ProcessOutput
                      filter spo._from == p._id
                      filter IS_SAME_COLLECTION(%s, spo._to)
                      return spo._to
                    )
                    let io=(
                      for spi in SYS_ProcessInput
                      filter spi._to == p._id
                      filter IS_SAME_COLLECTION(%s, spi._from)
                      return spi._from
                    )
                    return append(io,oo)
                  ))
                ''' % (self.__index_type_def.collection_name,
                       self.__index_type_def.collection_name)
                
                aql_bind.update(po_aql_bind)
                aql_filter.append('%s._id in linked_ids' % var_name)
            
        if len(self.__linked_up_filters) == 0 and len(self.__linked_dn_filters) == 0 and len(self.__immediate_parent_filters) == 0:

            aql = link_aql+'FOR %s IN %s FILTER %s %s RETURN distinct %s' % (
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
                    FOR %s in 1..100 OUTBOUND s SYS_ProcessInput, SYS_ProcessOutput
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
                    FOR %s in 1..100 INBOUND s SYS_ProcessInput, SYS_ProcessOutput
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

            # Do immediate parent filters
            for ip_filters in self.__immediate_parent_filters:
                daql = ''
                d_var_names = []
                # calculate expected number of distinct inputs
                # and outputs:
                nInputs = 0
                nOutputs = 0
                hasDDT = False
                for pi in ip_filters['processInputs']:
                    if pi.startswith('DDT_'):
                        if not hasDDT:
                            hasDDT = True
                            nInputs+=1
                    else:
                        nInputs+=1
                hasDDT = False
                for pi in ip_filters['processOutputs']:
                    if pi.startswith('DDT_'):
                        if not hasDDT:
                            hasDDT = True
                            nOutputs+=1
                    else:
                        nOutputs+=1
                    
                for pi in ip_filters['processInputs']:
                    d_var_name = self.__param_name('pr')
                    d_var_names.append(d_var_name)
                    d_aql_bind = {}
                    f = ''
                    if pi.startswith('DDT_'):
                        f = 'FILTER s.data_type_term_name=="%s"' % pi[4:]
                        pi = 'DDT_Brick'
                    d_aql_bind[d_var_name] = pi
                    daql += '''
                      let %s = (
                         for s in %s
                         %s
                         for x in 1..1 OUTBOUND s SYS_ProcessInput
                         let io=(
                           for i in x.input_objects
                           return distinct split(i,":",1)
                         )
                         let oo=(
                           for o in x.output_objects
                           return distinct split(o,":",1)
                         )
                         filter length(io)==%d
                         filter length(oo)==%d
                         return x
                       )
                    ''' % (d_var_name, pi, f, nInputs, nOutputs)
                for po in ip_filters['processOutputs']:
                    d_var_name = self.__param_name('pr')
                    d_var_names.append(d_var_name)
                    d_aql_bind = {}
                    f = ''
                    if po.startswith('DDT_'):
                        f = 'FILTER s.data_type_term_name=="%s"' % po[4:]
                        po = 'DDT_Brick'
                    d_aql_bind[d_var_name] = po
                    daql += '''
                      let %s = (
                         for s in %s
                         %s
                         for x in 1..1 INBOUND s SYS_ProcessOutput
                         let io=(
                           for i in x.input_objects
                           return distinct split(i,":",1)
                         )
                         let oo=(
                           for o in x.output_objects
                           return distinct split(o,":",1)
                         )
                         filter length(io)==%d
                         filter length(oo)==%d
                         return x
                       )
                    ''' % (d_var_name, po, f, nInputs, nOutputs)
                name = self.__index_type_def.name
                f = ''
                if name.startswith('DDT_'):
                   f = 'FILTER s.data_type_term_name=="%s"' % name[4:]
                   name = 'DDT_Brick'
                daql+='''
                      for p in intersection(%s)
                      for %s in 1..1 OUTBOUND p SYS_ProcessOutput
                      FILTER IS_SAME_COLLECTION(%s, x._id)
                      FILTER %s %s
                      return distinct %s
                   ''' % (','.join(d_var_names),
                       var_name,
                       aql_source,
                       ' and '.join(aql_filter),
                       ' '.join(pr_aqls),
                       var_name)
                aql_var = self.__param_name('a')
                var_aqls.append({
                    'var_name': aql_var,
                    'aql': 'let %s = (%s) ' % (aql_var, daql) 
                })

            # build final aql
            if len(var_aqls) == 1:
                aql_return = var_aqls[0]['var_name']
            else:
                aql_return = 'intersection(%s)' % (','.join( a['var_name']  for a in var_aqls ))

            aql =  link_aql+'%s FOR x IN %s RETURN x' %  (
                ' '.join( a['aql'] for a in var_aqls ),
                aql_return
            )

        
        sys.stderr.write('aql = '+aql+'\n')
        sys.stderr.write('aql_bind = '+str(aql_bind)+'\n')

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

