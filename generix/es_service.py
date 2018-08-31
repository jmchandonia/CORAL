from .utils import parse_term


ES_INDEX_NAME_PREFIX = 'generix-data-'


def to_es_type_name(type_name):
    chars = list(type_name)
    es_name = []
    for ch in chars:
        if ch.isupper():
            if len(es_name) > 0:
                es_name.append('_')
            es_name.append(ch.lower())
        else:
            es_name.append(ch)
    return ''.join(es_name)


class ElasticSearchService:
    def __init__(self, es_client):
        self.__es_client = es_client

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
                    term = parse_term(value)
                    term.refresh()
                    doc[pname + '_term_id'] = term.term_id
                    doc[pname + '_term_name'] = term.term_name
                    all_term_ids.add(term.term_id)
                    for pid in term.parent_path_ids:
                        all_parent_path_term_ids.add(pid)
                else:
                    doc[pname] = value

        doc['all_term_ids'] = list(all_term_ids)
        doc['all_parent_path_term_ids'] = list(all_parent_path_term_ids)

        self.__es_client .index(
            index=index_name, doc_type=es_type, body=doc)

    def create_index(self, type_def):
        es_type = to_es_type_name(type_def.name)
        index_name = ES_INDEX_NAME_PREFIX + es_type
        properties = {}
        for pdef in type_def.property_defs:
            pname = pdef.name
            if pdef.is_pk:
                properties[pname] = {
                    'type': 'text',
                    'analyzer': 'keyword'
                }
            elif pdef.type == 'text':
                properties[pname] = {
                    'type': 'text',
                    'analyzer': 'standard'
                }
            elif pdef.type == 'text':
                properties[pname] = {
                    'type': 'float'
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
