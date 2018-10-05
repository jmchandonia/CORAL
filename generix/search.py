import pandas as pd
from .brick import BrickDescriptor, BrickDescriptorCollection
from . import services
from .utils import to_es_type_name

_ES_BRICK_INDEX_NAME = 'generix-data-brick'
_ES_ENTITY_INDEX_NAME_PREFIX = 'generix-data-'


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

    def _find_entities(self, entity_type, query, size=10000):
        query['size'] = size
        entity_descriptors = []
        index_name = self._index_name(entity_type)
        result_set = self.__es_client.search(
            index=index_name, body=query)

        # print('entity_type:', entity_type)
        # print('index_name:', index_name)
        # print('Query:', query)
        # print('result_set:', result_set)

        for hit in result_set['hits']['hits']:
            data = hit["_source"]
            bd = EntityDescriptor(entity_type, data)

            entity_descriptors.append(bd)
        return entity_descriptors

    def _find_entity_ids(self, entity_type, id_field_name, query, size=100):
        query['size'] = size
        query['_source'] = [id_field_name]

        ids = []
        index_name = self._index_name(entity_type)

        # print('Doing index name:' + index_name)
        result_set = self.__es_client.search(index=index_name, body=query)

        for hit in result_set['hits']['hits']:
            ids.append(hit["_source"][id_field_name])
        return ids

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
        try:
            result_set = self.__es_client.search(
                index=_ES_BRICK_INDEX_NAME, body=query)

            # print('entity_type:', 'brick')
            # print('index_name:', _ES_BRICK_INDEX_NAME)
            # print('Query:', query)
            # print('result_set:', result_set)

            for hit in result_set['hits']['hits']:
                data = hit["_source"]
                bd = BrickDescriptor(data['brick_id'], data['name'], data['description'],
                                     data['data_type_term_id'], data['data_type_term_name'],
                                     data['n_dimensions'],
                                     data['dim_type_term_ids'], data['dim_type_term_names'], data['dim_sizes'],
                                     data['value_type_term_id'], data['value_type_term_name'])

                brick_descriptors.append(bd)
        except:
            print('Error: can not get bricks')
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

        term_ids_hash = services.ontology.all.find_ids_hash(term_ids)

        for term_stat in term_stats:
            term_id = term_stat['Term ID']
            term_stat['Term Name'] = term_ids_hash[term_id].term_name

        return pd.DataFrame(term_stats)[['Term Name', 'Term ID', 'Bricks count']]

    def _index_name(self, doc_type):
        doc_type = to_es_type_name(doc_type)
        return _ES_BRICK_INDEX_NAME if doc_type == 'brick' else _ES_ENTITY_INDEX_NAME_PREFIX + doc_type

    # def get_entity_properties(self, type_name):
    #     doc_type = type_name
    #     # index_name = 'generix-'
    #     # if doc_type != 'brick':
    #     #     index_name += 'entity-'
    #     # index_name += doc_type

    #     index_name = self._index_name(doc_type)
    #     doc = self.__es_client.indices.get_mapping(index=index_name)
    #     return list(doc[index_name]['mappings'][doc_type]['properties'].keys())

    def data_type_terms(self):
        return self.__term_stat('data_type_term_id')

    def dim_type_terms(self):
        return self.__term_stat('dim_type_term_ids')

    def value_type_terms(self):
        return self.__term_stat('value_type_term_id')


class EntityDescriptorCollection:
    def __init__(self, entity_descriptors):
        self.__entity_descriptors = entity_descriptors

    @property
    def items(self):
        return self.__entity_descriptors

    @property
    def size(self):
        return len(self.__entity_descriptors)

    def __getitem__(self, i):
        return self.__entity_descriptors[i]

    def to_df(self):
        ed_list = []
        for ed in self.__entity_descriptors:
            ed_doc = {}
            for prop in ed.properties:
                ed_doc[prop] = ed[prop]
            ed_list.append(ed_doc)
        return pd.DataFrame(ed_list)

    def _repr_html_(self):
        return self.to_df()._repr_html_()


class EntityDescriptor:
    def __init__(self, data_type, doc):
        self.__properties = []

        self.data_type = data_type
        self.__properties.append('data_type')
        for key in doc:
            self.__dict__[key] = doc[key]
            self.__properties.append(key)

    def __getitem__(self, property):
        return self.__dict__[property]

    @property
    def properties(self):
        return self.__properties

    def _repr_html_(self):
        def _row2_header(c):
            return '<tr><td colspan=2 style="text-align:left;">%s</td></tr>' % (c)

        def _row2(c1, c2):
            cell = '<td style="padding-left:20px; text-align:left">%s</td>'
            patterm = '<tr>' + ''.join([cell for i in range(2)]) + '</tr>'
            return patterm % (c1, c2)

        rows = []
        for prop in self.__dict__:
            if prop.startswith('_'):
                continue
            rows.append(_row2(prop, self.__dict__[prop]))

        return '<table>%s</table>' % ''.join(rows)

    def __str__(self):
        return self.__dict__
