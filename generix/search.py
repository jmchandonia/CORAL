import pandas as pd
from .brick import BrickDescriptor, BrickDescriptorCollection
from . import services

_ES_BRICK_INDEX_NAME = 'generix-brick'


class SearchService:
    def __init__(self, es_client):
        self.__es_client = es_client

    def _build_query(self, key_values):
        items = []
        for key, value in key_values.items():
            tt, filed_name = key.split('.')
            items.append({
                tt: {filed_name: value}
            })

        query = {
            'query': {
                'constant_score': {
                    'filter': {
                        'bool': {
                            'must': items
                        }
                    }
                }
            }
        }
        return query

    def _find_bricks(self, query, size=100):
        query['size'] = size
        query['_source'] = [
            'brick_id',
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

        brick_descriptors = []
        result_set = self.__es_client.search(
            index=_ES_BRICK_INDEX_NAME, body=query)
        for hit in result_set['hits']['hits']:
            data = hit["_source"]
            bd = BrickDescriptor(data['brick_id'], data['name'], data['description'],
                                 data['data_type_term_id'], data['data_type_term_name'],
                                 data['n_dimensions'],
                                 data['dim_type_term_ids'], data['dim_type_term_names'], data['dim_sizes'],
                                 data['value_type_term_id'], data['value_type_term_name'])

            brick_descriptors.append(bd)
        return brick_descriptors

    def find_ids(self, brick_ids):
        query = {
            "query": {
                "terms": {
                    "brick_id": brick_ids
                }
            }
        }
        return BrickDescriptorCollection(self._find_bricks(query))

    def find_parent_term_ids(self, parent_term_ids):
        query = {
            "query": {
                "terms": {
                    "all_parent_path_term_ids": parent_term_ids
                }
            }
        }
        return BrickDescriptorCollection(self._find_bricks(query))

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
        return BrickDescriptorCollection(self._find_bricks(query))

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
        return BrickDescriptorCollection(self._find_bricks(query))

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
        return BrickDescriptorCollection(self._find_bricks(query))

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
        return BrickDescriptorCollection(self._find_bricks(query))

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
        return BrickDescriptorCollection(self._find_bricks(query))

    def find_term_values(self, term, values):
        return self.find_term_id_values(term.term_id, values)

    def __term_stat(self, term_field_name):
        query = {
            "aggs": {
                "term_stat": {
                    "terms": {"field": term_field_name, "size": 10000}
                }
            },
            "size": 0
        }

        term_ids = []
        term_stats = []
        result_set = self.__es_client.search(
            index=_ES_BRICK_INDEX_NAME, body=query)
        for hit in result_set['aggregations']['term_stat']['buckets']:
            term_id = hit['key']
            doc_count = hit['doc_count']
            term_stats.append({
                'Term ID': term_id,
                'Bricks count': doc_count
            })
            term_ids.append(term_id)

        term_ids_hash = services.ontology.ont_all.find_ids_hash(term_ids)

        for term_stat in term_stats:
            term_id = term_stat['Term ID']
            term_stat['Term Name'] = term_ids_hash[term_id].term_name

        return pd.DataFrame(term_stats)[['Term Name', 'Term ID', 'Bricks count']]

    def get_entity_properties(self, type_name):
        index_name = 'generix-' + type_name
        doc_type = 'brick'
        doc = self.__es_client.indices.get_mapping(index=index_name)
        return list(doc[index_name]['mappings'][doc_type]['properties'].keys())

    def data_type_terms(self):
        return self.__term_stat('data_type_term_id')

    def dim_type_terms(self):
        return self.__term_stat('dim_type_term_ids')

    def value_type_terms(self):
        return self.__term_stat('value_type_term_id')
