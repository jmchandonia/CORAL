import json
from .brick import Brick, BrickIndexDocumnet
from . import services

_IMPORT_DIR = 'data/import/'
_ES_BRICK_INDEX_NAME = 'generix-brick'
_ES_BRICK_TYPE = 'brick'


class SearchIndexerService:

    def __init__(self, es_client):
        self.__es_client = es_client

    def create_index(self):
        settings = {
            "settings": {
                "analysis": {
                    "analyzer": {
                        "keyword": {
                            "type": "custom",
                            "tokenizer": "keyword"
                        }
                    }
                }
            },
            "mappings": {
                _ES_BRICK_TYPE: {
                    "properties": {
                        "id": {
                            "type": "text",
                            "analyzer": "keyword"
                        },
                        "name": {
                            "type": "text",
                            "analyzer": "keyword"
                        },
                        "description": {
                            "type": "text",
                            "analyzer": "standard"
                        },
                        "n_dimensions": {
                            "type": "integer"
                        },
                        "data_type_term_id": {
                            "type": "text",
                            "analyzer": "keyword",
                            "fielddata": True
                        },
                        "data_type_term_name": {
                            "type": "text",
                            "analyzer": "keyword"
                        },
                        "value_type_term_id": {
                            "type": "text",
                            "analyzer": "keyword",
                            "fielddata": True
                        },
                        "value_type_term_name": {
                            "type": "text",
                            "analyzer": "keyword"
                        },
                        "dim_type_term_ids": {
                            "type": "text",
                            "analyzer": "keyword",
                            "fielddata": True
                        },
                        "dim_type_term_names": {
                            "type": "text",
                            "analyzer": "keyword"
                        },
                        "data_size": {
                            "type": "integer"
                        },
                        "dim_sizes": {
                            "type": "integer"
                        },
                        "all_term_ids": {
                            "type": "text",
                            "analyzer": "keyword"
                        },
                        "all_term_ids_with_values": {
                            "type": "text",
                            "analyzer": "keyword"
                        },
                        "all_term_values": {
                            "type": "text",
                            "analyzer": "keyword"
                        },
                        "all_parent_path_term_ids": {
                            "type": "text",
                            "analyzer": "keyword"
                        }
                    }
                }
            }
        }

        self.__es_client.indices.create(
            index=_ES_BRICK_INDEX_NAME, body=settings)

    def drop_index(self):
        try:
            self.__es_client.indices.delete(index=_ES_BRICK_INDEX_NAME)
        except:
            pass

    def index_brick(self, brick):
        bid = BrickIndexDocumnet(brick)
        doc = vars(bid)
        self.__es_client.index(
            index=_ES_BRICK_INDEX_NAME, doc_type=_ES_BRICK_TYPE, body=doc)

        # def __process_term_values(self, term_id, term_value_type, term_values,
        #                           all_term_ids, all_term_values,
        #                           term_id_2_values):
        #     all_term_ids.add(term_id)
        #     if term_value_type in ['string_value', 'string_values', 'oterm_ref', 'oterm_refs']:
        #         if term_value_type in ['oterm_ref', 'oterm_refs']:
        #             for term_value in term_values:
        #                 all_term_ids.add(term_value)

        #         for term_value in term_values:
        #             all_term_values.add(term_value)
        #         values = term_id_2_values.get(term_id)
        #         if values is None:
        #             values = set()
        #             term_id_2_values[term_id] = values
        #         for term_value in term_values:
        #             values.add(term_value)

        # def index_json_ndarray(self, obj_id, file_name):
        #     name = None
        #     description = None
        #     n_dimensions = None
        #     data_type_term_id = None
        #     data_type_term_name = None
        #     value_type_term_id = None
        #     value_type_term_name = None
        #     dim_type_term_ids = []
        #     dim_type_term_names = []
        #     dim_sizes = []
        #     data_size = None

        #     all_term_ids = set()
        #     all_term_values = set()
        #     all_term_ids_with_values = set()
        #     all_parent_term_ids = set()

        #     term_id_2_values = dict()

        #     data = None
        #     with open(file_name, 'r') as f:
        #         data = json.load(f)

        #     # basic
        #     name = data['name']
        #     description = data['description']
        #     n_dimensions = data['n_dimensions']

        #     # data type
        #     term = data['data_type']
        #     data_type_term_id = term['oterm_ref']
        #     data_type_term_name = term['oterm_name']
        #     all_term_ids.add(term['oterm_ref'])

        #     # process array context
        #     for ac in data['array_context']:
        #         term_id = ac['value_type']['oterm_ref']
        #         term_value_type = ac['value']['scalar_type']

        #         # fix bug
        #         if term_value_type == 'oterm_ref':
        #             pass
        #         else:
        #             term_value_type += '_value'

        #         if term_value_type in ac['value']:
        #             term_value = ac['value'][term_value_type]
        #             self.__process_term_values(term_id, term_value_type, [term_value],
        #                                        all_term_ids, all_term_values, term_id_2_values)

        #     # process dimensions
        #     data_size = 1
        #     for dim in data['dim_context']:
        #         term = dim['data_type']
        #         dim_type_term_ids.append(term['oterm_ref'])
        #         dim_type_term_names.append(term['oterm_name'])
        #         dim_sizes.append(dim['size'])
        #         all_term_ids.add(term['oterm_ref'])
        #         data_size *= dim['size']

        #         for tv in dim['typed_values']:
        #             term_id = tv['value_type']['oterm_ref']
        #             term_value_type = tv['values']['scalar_type']
        #             # fix bug
        #             if term_value_type == 'oterm_ref':
        #                 term_value_type = 'oterm_refs'
        #             else:
        #                 term_value_type += '_values'

        #             if term_value_type in tv['values']:
        #                 term_values = tv['values'][term_value_type]
        #                 self.__process_term_values(term_id, term_value_type, term_values,
        #                                            all_term_ids, all_term_values, term_id_2_values)

        #     # value type
        #     term = data['typed_values']['value_type']
        #     value_type_term_id = term['oterm_ref']
        #     value_type_term_name = term['oterm_name']
        #     all_term_ids.add(term['oterm_ref'])

        #     # collect parent path term ids
        #     ont_all = services.ontology.ont_all
        #     term_collection = ont_all.find_ids(list(all_term_ids))
        #     for term in term_collection.terms:
        #         for term_id in term.parent_path_ids:
        #             all_parent_term_ids.add(term_id)

        #     # build all_term_ids_with_values
        #     all_term_ids_with_values = term_id_2_values.keys()

        #     doc = {
        #         'brick_id': obj_id,
        #         'name': name,
        #         'description': description,
        #         'n_dimensions': n_dimensions,
        #         'data_type_term_id': data_type_term_id,
        #         'data_type_term_name': data_type_term_name,
        #         'value_type_term_id': value_type_term_id,
        #         'value_type_term_name': value_type_term_name,
        #         'dim_type_term_ids': dim_type_term_ids,
        #         'dim_type_term_names': dim_type_term_names,
        #         'dim_sizes': dim_sizes,
        #         'data_size': data_size,

        #         'all_term_ids': list(all_term_ids),
        #         'all_term_values': list(all_term_values),
        #         'all_term_ids_with_values': list(all_term_ids_with_values),
        #         'all_parent_term_ids': list(all_parent_term_ids)
        #     }

        #     for term_id, values in term_id_2_values.items():
        #         prop = 'ont_' + '_'.join(term_id.split(':'))
        #         doc[prop] = list(values)

        #     self.__es_client.index(
        #         index=_ES_BRICK_INDEX_NAME, doc_type=_ES_BRICK_TYPE, body=doc)
