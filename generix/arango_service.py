import pandas as pd
from .typedef import TYPE_NAME_BRICK, TYPE_NAME_PROCESS, TYPE_CATEGORY_DYNAMIC, TYPE_CATEGORY_STATIC
from .ontology import Term
from .descriptor import DataDescriptorCollection, ProcessDescriptor, EntityDescriptor, IndexDocument, BrickIndexDocumnet
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
        bid = BrickIndexDocumnet(data_holder.brick)
        doc = vars(bid)
        self.index_doc(doc, TYPE_NAME_BRICK, TYPE_CATEGORY_DYNAMIC)


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
        return self.__db.AQLQuery(aql,  bindVars=aql_bind,  rawResults=True, batchSize=size)        

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

        print('aql', aql)
        print('aql_bind', aql_bind)
        rs = self.__db.AQLQuery(aql,  bindVars=aql_bind,  rawResults=True, batchSize=size)        
        return self.__to_type2objects(rs)

    
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




