import pandas as pd
from .typedef import TYPE_NAME_BRICK, TYPE_CATEGORY_DYNAMIC, TYPE_CATEGORY_STATIC
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

    def create_brick_index(self):
        type_def = services.indexdef.get_type_def(TYPE_NAME_BRICK)
        self.__db.createCollection(name=type_def.collection_name)

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
        print('aql_bind:', aql_bind )

        return self.find(aql, aql_bind, 1000)


    def find(self, aql, aql_bind, size=100):
        return self.__db.AQLQuery(aql,  bindVars=aql_bind,  rawResults=True, batchSize=size)        

    def create_index(self, type_def):
        self.__db.createCollection(name=type_def.collection_name)

    def drop_index(self, type_def):
        self.__db[type_def.collection_name].delete()

    # def _build_query(self, key_values):
    #     items = []
    #     for key, value in key_values.items():
    #         tt, filed_name = key.split('.')
    #         items.append({
    #             tt: {filed_name: value}
    #         })

    #     query = {
    #         'query': {
    #             'constant_score': {
    #                 'filter': {
    #                     'bool': {
    #                         'must': items
    #                     }
    #                 }
    #             }
    #         }
    #     }
    #     return query

    # TODO
    # def _find_entities(self, entity_type, query, size=10000):
    #     query['size'] = size
    #     entity_descriptors = []
    #     index_name = self._index_name(entity_type)

    #     result_set = self.__es_client.search(
    #         index=index_name, body=query)

    #     for hit in result_set['hits']['hits']:
    #         data = hit["_source"]
    #         bd = ProcessDescriptor(
    #             data) if entity_type == 'process' else EntityDescriptor(entity_type, data)

    #         entity_descriptors.append(bd)
    #     return entity_descriptors


    # TODO
    # def _find_entity_ids(self, entity_type, id_field_name, query, size=100):
    #     query['size'] = size
    #     query['_source'] = [id_field_name]

    #     ids = []
    #     index_name = self._index_name(entity_type)

    #     # print('Doing index name:' + index_name)
    #     result_set = self.__es_client.search(index=index_name, body=query)

    #     for hit in result_set['hits']['hits']:
    #         ids.append(hit["_source"][id_field_name])
    #     return ids

    def _find_bricks(self, query, size=1000):
        query['size'] = size
        query['_source'] = [
            'id',
            'name',
            'description',
            'data_type_term_id',
            'data_type_term_name',
            'dim_sizes',
            'n_dimensions',
            'dim_type_term_ids',
            'dim_type_term_names',
            'value_type_term_id',
            'value_type_term_name'
        ]
        query['sort'] = ['data_type_term_name', 'id']

        brick_descriptors = []
        try:
            result_set = self.__es_client.search(
                index=_ES_BRICK_INDEX_NAME, body=query)

            # print('entity_type:', 'brick')
            # print('index_name:', _ES_BRICK_INDEX_NAME)
            # print('Query:', query)
            # print('result_set:', result_set)

            for hit in result_set['hits']['hits']:
                data = hit["_source"]
                bd = BrickDescriptor(data)
                brick_descriptors.append(bd)
        except:
            print('Error: can not get bricks')
        return brick_descriptors

    def find_ids(self, brick_ids):
        query = {
            "query": {
                "terms": {
                    "id": brick_ids
                }
            }
        }
        return DataDescriptorCollection(data_descriptors=self._find_bricks(query))

    def find_parent_term_ids(self, parent_term_ids):
        query = {
            "query": {
                "terms": {
                    "all_parent_path_term_ids": parent_term_ids
                }
            }
        }
        return DataDescriptorCollection(data_descriptors=self._find_bricks(query))

    def find_parent_terms(self, parent_terms):
        term_ids = [t.term_id for t in parent_terms]
        return self.find_parent_term_ids(term_ids)

    def find_data_type_term_ids(self, data_type_term_ids):
        query = {
            "query": {
                "terms": {
                    "data_type_term_id": data_type_term_ids
                }
            }
        }
        return DataDescriptorCollection(data_descriptors=self._find_bricks(query))

    def find_data_type_terms(self, data_type_terms):
        term_ids = [t.term_id for t in data_type_terms]
        return self.find_data_type_term_ids(term_ids)

    def find_value_type_term_ids(self, value_type_term_ids):
        query = {
            "query": {
                "terms": {
                    "value_type_term_id": value_type_term_ids
                }
            }
        }
        return DataDescriptorCollection(data_descriptors=self._find_bricks(query))

    def find_value_type_terms(self, value_type_terms):
        term_ids = [t.term_id for t in value_type_terms]
        return self.find_value_type_term_ids(term_ids)

    def find_dim_type_term_ids(self, dim_type_term_ids):
        query = {
            "query": {
                "terms": {
                    "dim_type_term_ids": dim_type_term_ids
                }
            }
        }
        return DataDescriptorCollection(data_descriptors=self._find_bricks(query))

    def find_dim_type_terms(self, dim_type_terms):
        term_ids = [t.term_id for t in dim_type_terms]
        return self.find_dim_type_term_ids(term_ids)

    def find_term_ids(self, term_ids):
        query = {
            "query": {
                "terms": {
                    "all_term_ids": term_ids
                }
            }
        }
        return DataDescriptorCollection(data_descriptors=self._find_bricks(query))

    def find_terms(self, terms):
        term_ids = [t.term_id for t in terms]
        return self.find_term_ids(term_ids)

    def find_term_id_values(self, term_id, values):
        property = 'ont_' + '_'.join(term_id.split(':'))
        query = {
            "query": {
                "terms": {
                    property: values
                }
            }
        }
        return DataDescriptorCollection(data_descriptors=self._find_bricks(query))

    def find_term_values(self, term, values):
        return self.find_term_id_values(term.term_id, values)


    # TODO
    # def _index_name(self, doc_type):
    #     doc_type = to_es_type_name(doc_type)
    #     return _ES_BRICK_INDEX_NAME if doc_type == 'brick' else _ES_ENTITY_INDEX_NAME_PREFIX + doc_type

    # def get_entity_properties(self, type_name):
    #     doc_type = type_name
    #     # index_name = 'generix-'
    #     # if doc_type != 'brick':
    #     #     index_name += 'entity-'
    #     # index_name += doc_type

    #     index_name = self._index_name(doc_type)
    #     doc = self.__es_client.indices.get_mapping(index=index_name)
    #     return list(doc[index_name]['mappings'][doc_type]['properties'].keys())



