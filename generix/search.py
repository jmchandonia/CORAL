from .brick import BrickDescriptor, BrickDescriptorCollection

_ES_BRICK_INDEX_NAME = 'generix-brick'


class SearchService:
    def __init__(self, es_client):
        self.__es_client = es_client

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
                    "all_parent_term_ids": parent_term_ids
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
