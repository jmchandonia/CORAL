import pandas as pd
from .typedef import TYPE_NAME_BRICK, TYPE_NAME_PROCESS, TYPE_CATEGORY_DYNAMIC, TYPE_CATEGORY_STATIC
from .ontology import Term
from .descriptor import DataDescriptorCollection, ProcessDescriptor, EntityDescriptor, IndexDocument, BrickIndexDocument
import sys
import pprint
from . import services


class ArangoService:
    def __init__(self, connection, db_name):
        self.__connection = connection
        self.__db_name = db_name
        self.__db = self.__connection[self.__db_name]
    
    @property
    def db(self):
        return self.__db


    def create_collection(self, collection_name):
        self.__db.createCollection(name=collection_name)

    def create_edge_collection(self, collection_name):
        self.__db.createCollection(name=collection_name, className='Edges')

    def create_brick_index(self):
        type_def = services.indexdef.get_type_def(TYPE_NAME_BRICK)
        self.create_collection(type_def.collection_name)

    def create_index(self, type_def):
        self.create_collection(type_def.collection_name)

    def drop_index(self, type_def):
        self.__db[type_def.collection_name].delete()


    def upsert_doc(self, upsert_condition, doc, type_name, category):
        aql = 'UPSERT @upsert INSERT @doc REPLACE @doc IN @@collection'
        aql_bind = {
            'doc': doc, 
            'upsert': upsert_condition,  
            '@collection': category + type_name}
        self.__db.AQLQuery(aql, bindVars=aql_bind)

    def index_doc(self, doc, type_name, category):
        bind = {'doc': doc, '@collection': category + type_name}
        aql = 'INSERT @doc INTO @@collection'
        self.__db.AQLQuery(aql, bindVars=bind)


    def index_brick(self, data_holder):
        bid = BrickIndexDocument(data_holder.brick)
        doc = vars(bid)
        self.index_doc(doc, TYPE_NAME_BRICK, TYPE_CATEGORY_DYNAMIC)

    def reindex_brick(self, data_holder):
        bid = BrickIndexDocument(data_holder.brick)
        doc = vars(bid)
        # sys.stderr.write('doc = '+str(doc)+'\n')
        self.upsert_doc(
            {
                services.indexdef.PK_PROPERTY_NAME : doc[services.indexdef.PK_PROPERTY_NAME]
            }, doc, TYPE_NAME_BRICK, TYPE_CATEGORY_DYNAMIC)

    def index_data(self, data_holder):
        type_name = data_holder.type_def.name 
        index_type_def = services.indexdef.get_type_def(type_name)
        doc = IndexDocument.build_index_doc(data_holder)
        self.index_doc(doc, index_type_def.name, index_type_def.category)

    def find_all(self, type_name, category):
        aql = 'FOR x IN @@collection RETURN x'        
        aql_bind = {'@collection': category + type_name}
        # print('aql_bind:', aql_bind )

        return self.find(aql, aql_bind, 1000)


    def find(self, aql, aql_bind, size=100):
        return self.__db.AQLQuery(aql,  bindVars=aql_bind,  rawResults=True, batchSize=size).result

    def get_up_processes(self, index_type_def, obj_id, size = 100):
        aql = '''
                FOR spo IN SYS_ProcessOutput FILTER spo._to == @id
                FOR x IN SYS_Process FILTER spo._from == x._id
                RETURN DISTINCT x
        '''
        aql_bind = {'id':  index_type_def.collection_name + '/' + obj_id}
        return self.__db.AQLQuery(aql,  bindVars=aql_bind,  rawResults=True, batchSize=size)        

    def get_dn_processes(self, index_type_def, obj_id, size = 100):
        aql = '''
                FOR spi IN SYS_ProcessInput FILTER spi._from == @id
                FOR x IN SYS_Process FILTER spi._to == x._id
                RETURN DISTINCT x
        '''
        aql_bind = {'id':  index_type_def.collection_name + '/' + obj_id}
        return self.__db.AQLQuery(aql,  bindVars=aql_bind,  rawResults=True, batchSize=size)        


    def get_up_process_docs(self, index_type_def, obj_id, size = 100):
        aql = '''
            for spo in SYS_ProcessOutput filter spo._to == @id
            for pr in SYS_Process filter pr._id == spo._from
            for pi in SYS_ProcessInput filter pi._to == pr._id
            collect process = pr into docs =  document(pi._from)
            return { "process" : process,  "docs" :  docs}
        '''
        aql_bind = {'id':  index_type_def.collection_name + '/' + obj_id}
        return self.__db.AQLQuery(aql,  bindVars=aql_bind,  rawResults=True, batchSize=size)        


    def get_dn_process_docs(self, index_type_def, obj_id, size = 100):
        aql = '''
            for pi in SYS_ProcessInput filter pi._from == @id
            for pr in SYS_Process filter pr._id == pi._to
            for po in SYS_ProcessOutput filter po._from == pr._id
            collect process = pr into docs =  document(po._to)
            return { "process" : process,  "docs" :  docs}
        '''
        aql_bind = {'id':  index_type_def.collection_name + '/' + obj_id}
        return self.__db.AQLQuery(aql,  bindVars=aql_bind,  rawResults=True, batchSize=size)        

    def get_process_inputs(self, process_id, size = 100):
        process_itd = services.indexdef.get_type_def(TYPE_NAME_PROCESS)
        aql = '''
            for pi in SYS_ProcessInput filter pi._to == @id
            return distinct document(pi._from)        
        '''
        aql_bind = {'id': process_itd.collection_name  + '/' + process_id}
        rs = self.__db.AQLQuery(aql,  bindVars=aql_bind,  rawResults=True, batchSize=size)        
        return self.__to_type2objects(rs)

    def get_process_outputs(self, process_id, size = 10000):
        process_itd = services.indexdef.get_type_def(TYPE_NAME_PROCESS)
        aql = '''
            for po in SYS_ProcessOutput filter po._from == @id
            return distinct document(po._to)        
        '''
        aql_bind = {'id': process_itd.collection_name  + '/' + process_id}

        # print('aql', aql)
        # print('aql_bind', aql_bind)
        rs = self.__db.AQLQuery(aql,  bindVars=aql_bind,  rawResults=True, batchSize=size)        
        return self.__to_type2objects(rs)


    def get_brick_type_counts(self, person_term_ids, campaign_term_ids, size = 1000):
        # TODO
        # for pr in SYS_Process filter 1==1 and pr.person_term_id in ['ENIGMA:0000032'] and pr.campaign_term_id in ["ENIGMA:0000013"]
        # for po in SYS_ProcessOutput filter po._from == pr._id
        # for b in  DDT_Brick filter po._to == b._id
        aql = '''
            for b in  DDT_Brick
            collect b_type = b.data_type_term_name with count into b_count
            return {b_type, b_count}
        '''
        aql_bind = {}
        return self.__db.AQLQuery(aql,  bindVars=aql_bind,  rawResults=True, batchSize=size)        

    def get_core_type_count(self, core_type, size=1000):
        aql = '''
            return length(%s)
        ''' % core_type
        aql_bind = {}
        try:
            return self.__db.AQLQuery(aql,  bindVars=aql_bind,  rawResults=True, batchSize=size)[0]
        except Exception as e:
            return 0

    # ignores ddt->ddt for now
    def get_process_type_count(self, filterCampaigns=False, filterPersonnel=False, size=100000):
        if filterCampaigns is not False:
            if len(filterCampaigns)==0:
                filterCampaigns = False
        if filterPersonnel is not False:
            if len(filterPersonnel)==0:
                filterPersonnel = False
        if filterCampaigns is not False or filterPersonnel is not False:
            filters = 'filter ('
            if filterCampaigns is not False:
                for f in filterCampaigns:
                    filters += 'p1.campaign_term_id=="'+f+'" or '
                filters = filters[0:-4]+')'
                if filterPersonnel is not False:
                    filters += ' and ('
            if filterPersonnel is not False:
                for f in filterPersonnel:
                    filters += 'p1.person_term_id=="'+f+'" or '
                filters = filters[0:-4]+')'
            aql = '''
               let filtered_procs = (
                 for p1 in SYS_Process
                 %s
                 return p1
               )
               let up_procs=unique(
                 for p1 in filtered_procs
                 for p in 0..100 inbound p1 SYS_ProcessInput, SYS_ProcessOutput
                 OPTIONS {
                   bfs: true,
                   uniqueVertices: 'global'
                 }
                 filter is_same_collection("SYS_Process",p)
                 return p
               )
               let dn_procs=unique(
                  for p1 in filtered_procs
                  for p in 1..100 outbound p1 SYS_ProcessInput, SYS_ProcessOutput
                  OPTIONS {
                    bfs: true,
                    uniqueVertices: 'global'
                  }
                  filter is_same_collection("SYS_Process",p)
                  return p
               )
               for p in unique(append(up_procs,dn_procs))
            ''' % filters
        else:
            aql = '''
               for p in SYS_Process
              '''
        aql += '''
            let pis = (
              for pi in SYS_ProcessInput
              filter pi._to == p._id
              filter left(pi._from,4)=="SDT_"
              return pi._from
            )
            filter length(pis) > 0
            let f = concat_separator(",",flatten(pis))
            let pos = (
              for po in SYS_ProcessOutput
              filter po._from == p._id
              return (left(po._to,4)=="DDT_" ?
                concat(po._to,"/",document(po._to).data_type_term_name) :
                po._to
              )
            )
            let t=concat_separator(",",flatten(pos))
        '''
        if filterCampaigns is not False or filterPersonnel is not False:
            aql += '''
              return {"from":f, "to":t, "pname":p.process_term_name, "in_filter":p in filtered_procs}
            '''
        else:
            aql += '''
              return {"from":f, "to":t, "pname":p.process_term_name}
            '''
        aql_bind = {}

        # sys.stderr.write('aql = '+aql+'\n')
        
        return self.__db.AQLQuery(aql, bindVars=aql_bind, rawResults=True, batchSize=size)

    def get_upstream_core_props(self, type_def, props, intermediate_pks=True):


        prop_query_fmt = ' AND '.join(['HAS(x, "%s")' % p for p in props])
        prop_key_fmt = ','.join(['"%s": x.%s' % (p, p) for p in props])
        props_query = f'''
            LET properties = UNIQUE(
                FOR x in 1..100 INBOUND t SYS_ProcessOutput, SYS_ProcessInput
                FILTER {prop_query_fmt}
                RETURN {{{prop_key_fmt}}}
            )
        '''

        if intermediate_pks:
            keys_query = '''
                LET all_vertex_ids = UNIQUE(
                    FOR x in 1..100 INBOUND t SYS_ProcessOutput, SYS_ProcessInput
                    FILTER NOT IS_SAME_COLLECTION(x, SYS_Process)
                    return x
                )
            '''

            queries = props_query + keys_query
            document = '{"keys": all_vertex_ids, "properties": properties[0]}'
        else:
            queries = props_query
            document = 'MERGE(t, properties[0])'

        queries = props_query + keys_query if intermediate_pks else props_query
        document = 'MERGE(t, properties[0], {"intermediate_keys": all_vertex_ids})'

        rs = self.__db.AQLQuery(aql, rawResults=True)
        return pd.DataFrame(list(rs))

    
    def __to_type2objects(self, aql_rs):
        type2objects = {}
        for row in aql_rs:
            _id = row['_id']
            type_name = _id.split('/')[0][4:]
        
            objs = type2objects.get(type_name)
            if objs is None:
                objs = []
                type2objects[type_name] = objs
            objs.append(row)

        return type2objects




