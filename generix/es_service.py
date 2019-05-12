# from .utils import parse_term
from .brick import BrickIndexDocumnet
from .typedef import TYPE_NAME_BRICK
from .ontology import Term
from .utils import to_es_type_name


ES_INDEX_NAME_PREFIX = 'generix-data-'


class ElasticSearchService:
    def __init__(self, es_client):
        self.__es_client = es_client

    def create_brick_index(self):
        es_type = to_es_type_name(TYPE_NAME_BRICK)
        index_name = ES_INDEX_NAME_PREFIX + es_type

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
                es_type: {
                    "properties": {
                        "id": {
                            "type": "text",
                            "analyzer": "keyword",
                            "fielddata": True
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
                            "analyzer": "keyword",
                            "fielddata": True
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
            index=index_name, body=settings)

    def index_brick(self, data_holder):
        es_type = to_es_type_name(data_holder.type_name)
        index_name = ES_INDEX_NAME_PREFIX + es_type
        bid = BrickIndexDocumnet(data_holder.brick)
        doc = vars(bid)
        self.__es_client.index(
            index=index_name, doc_type=es_type, body=doc)

    def index_data(self, data_holder):
        type_def = data_holder.type_def
        es_type = to_es_type_name(type_def.name)
        index_name = ES_INDEX_NAME_PREFIX + es_type

        doc = {}
        all_term_ids = set()
        all_parent_path_term_ids = set()
        for pdef in type_def.property_defs:
            pname = pdef.name
            if pname in data_holder.data:
                value = data_holder.data[pname]
                if pdef.type == 'term':
                    term = Term.parse_term(value)
                    # term.refresh()
                    doc[pname + '_term_id'] = term.term_id
                    doc[pname + '_term_name'] = term.term_name

                    all_term_ids.add(term.term_id)
                    for pid in term.parent_path_ids:
                        all_parent_path_term_ids.add(pid)
                else:
                    doc[pname] = value

        # doc['all_term_ids'] = list(all_term_ids)
        # doc['all_parent_path_term_ids'] = list(all_parent_path_term_ids)

        self.__es_client .index(
            index=index_name, doc_type=es_type, body=doc)

    def create_index(self, type_def):
        es_type = to_es_type_name(type_def.name)
        index_name = ES_INDEX_NAME_PREFIX + es_type
        properties = {}
        for pdef in type_def.property_defs:
            pname = pdef.name
            if pdef.is_pk or pdef.is_upk or pdef.is_fk:
                properties[pname] = {
                    'type': 'text',
                    'analyzer': 'keyword'
                }
            elif pdef.type == 'text':
                properties[pname] = {
                    'type': 'text',
                    'analyzer': 'standard'
                }
            elif pdef.type == 'float':
                # TODO: why float does not work...?
                properties[pname] = {
                    'type': 'text'
                }
            elif pdef.type == 'term':
                properties[pname + '_term_id'] = {
                    'type': 'text',
                    'analyzer': 'keyword',
                    'fielddata': True
                }
                properties[pname + '_term_name'] = {
                    'type': 'text',
                    'analyzer': 'keyword'
                }
            else:
                properties[pname] = {
                    'type': 'text',
                    'analyzer': 'standard'
                }

        properties['all_term_ids'] = {
            'type': 'text',
            'analyzer': 'keyword'
        }
        properties['all_parent_path_term_ids'] = {
            'type': 'text',
            'analyzer': 'keyword'
        }
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
                es_type: {
                    "properties": properties
                }
            }
        }
        self.__es_client.indices.create(
            index=index_name, body=settings)

    def drop_index(self, type_name):
        es_type = to_es_type_name(type_name)
        index_name = ES_INDEX_NAME_PREFIX + es_type
        try:
            self.__es_client.indices.delete(index=index_name)
        except:
            raise ValueError('Can not drop index %s' % index_name)

    def get_type_names(self):
        names = []
        for name in self.__es_client.indices.get_alias(ES_INDEX_NAME_PREFIX + '*').keys():
            name = name[len(ES_INDEX_NAME_PREFIX):]
            names.append(name)
        return names

    def get_entity_properties(self, type_name):
        es_type = to_es_type_name(type_name)
        index_name = ES_INDEX_NAME_PREFIX + es_type
        # print('From get_entity_properties:', es_type, index_name)

        try:
            doc = self.__es_client.indices.get_mapping(index=index_name)
            props = list(doc[index_name]['mappings']
                         [es_type]['properties'].keys())
        except:
            props = []
        return props
