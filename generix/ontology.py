from elasticsearch import Elasticsearch
import os
import re
from .utils import to_var_name
from . import services

_IMPORT_DIR = '../data/import/'
_ES_OTERM_INDEX_PREFIX = 'generix-ont-'
_ES_OTERM_TYPE = 'oterm'

_ONTOLOGY_CONFIG = {
    'version': 1,
    'ontologies': {

        # 'chebi': {
        #     'name': 'chebi',
        #     'file_name': 'chebi.obo'
        # },
        'context_measurement': {
            'name': 'context_measurement',
            'file_name': 'context_measurement_ontology.obo'
        },
        'continent': {
            'name': 'continent',
            'file_name': 'continent.obo'
        },
        'country': {
            'name': 'country',
            'file_name': 'country.obo'
        },
        'dtype': {
            'name': 'Data types',
            'file_name': 'data_type_ontology.obo'
        },
        'dimension': {
            'name': 'dimension',
            'file_name': 'dimension_type_ontology.obo'
        },
        'enigma': {
            'name': 'ENIGMA metadata',
            'file_name': 'enigma_specific_ontology.obo'
        },
        'env': {
            'name': 'ENV',
            'file_name': 'env.obo'
        },
        'mixs': {
            'name': 'mixs',
            'file_name': 'mixs.obo'
        },
        'process': {
            'name': 'process_ontology',
            'file_name': 'process_ontology.obo'
        },
        'units': {
            'name': 'Units',
            'file_name': 'unit_standalone.obo'
        }

        # data/import/ncbitaxon.obo
    }
}


class OntologyService:
    def __init__(self, es_client):
        self.__es_client = es_client

    def _upload_ontologies(self):
        for ont_id, ont in _ONTOLOGY_CONFIG['ontologies'].items():
            print('Doing ontology: ' + ont_id)
            self._upload_ontology(ont_id, ont)

    def _upload_ontology(self, ont_id, ont):
        index_name = self._index_name(ont_id)
        self._drop_index(index_name)
        self._create_index(index_name)

        terms = self._load_terms(ont_id, ont['file_name'])
        self._index_terms(ont_id, terms)

    def _index_name(self, ont_id):
        return _ES_OTERM_INDEX_PREFIX + ont_id

    def _index_terms(self, ont_id, terms):
        index_name = self._index_name(ont_id)
        for _, term in terms.items():
            all_parent_ids = {}
            self._collect_all_parent_ids(term, all_parent_ids)
            doc = {
                'ontology_id': ont_id,
                'term_id': term.term_id,
                'term_name': term.term_name,
                'term_name_prefix': term.term_name,
                'parent_term_ids': term.parent_ids,
                'parent_path_term_ids': list(all_parent_ids.keys())
            }
            self.__es_client.index(
                index=index_name, doc_type=_ES_OTERM_TYPE, body=doc)

    def _collect_all_parent_ids(self, term, all_parent_ids):
        for pt in term._parent_terms:
            all_parent_ids[pt.term_id] = pt
            self._collect_all_parent_ids(pt, all_parent_ids)

    def _load_terms(self, ont_id, file_name):
        STATE_NONE = 0
        STATE_TERM_FOUND = 1

        state = STATE_NONE
        terms = {}

        term_id = None
        term_name = None
        term_aliases = []
        term_parent_ids = []

        root_term = None
        with open(_IMPORT_DIR + file_name, 'r') as f:
            for line in f:
                line = line.strip()
                if state == STATE_NONE:
                    if line.startswith('[Term]'):
                        term_id = None
                        term_name = None
                        term_aliases = []
                        term_parent_ids = []
                        state = STATE_TERM_FOUND

                elif state == STATE_TERM_FOUND:
                    if line.startswith('id:'):
                        term_id = line[len('id:'):].strip()
                    elif line.startswith('name:'):
                        term_name = line[len('name:'):].strip()
                    elif line.startswith('is_a:'):
                        parent_id = line[len('is_a:'):].strip().split(' ')[
                            0].strip()
                        term_parent_ids.append(parent_id)
                    elif line == '':
                        term = Term(term_id, term_name=term_name,
                                    ontology_id=ont_id,
                                    parent_ids=term_parent_ids)
                        terms[term.term_id] = term
                        if root_term is None:
                            root_term = term
                        state = STATE_NONE

        for _, term in terms.items():
            term._update_parents(terms)

        return terms

    def _drop_index(self, index_name):
        try:
            self.__es_client.indices.delete(index=index_name)
        except:
            pass

    def _create_index(self, index_name):
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
                _ES_OTERM_TYPE: {
                    "properties": {
                        "term_id": {
                            "type": "text",
                            "analyzer": "keyword"
                        },
                        "parent_term_ids": {
                            "type": "text",
                            "analyzer": "keyword"
                        },
                        "parent_path_term_ids": {
                            "type": "text",
                            "analyzer": "keyword"
                        },
                        "term_name": {
                            "type": "text",
                            "analyzer": "keyword"
                        },
                        "term_name_prefix": {
                            "type": "text",
                            "analyzer": "standard"
                        }
                    }
                }
            }
        }

        self.__es_client.indices.create(index=index_name, body=settings)

    def _search(self, index_name, query):
        return self.__es_client.search(index=index_name, body=query)

    @property
    def units(self):
        return Ontology(self, 'units')

    @property
    def data_types(self):
        return Ontology(self, 'dtype')

    @property
    def enigma(self):
        return Ontology(self, 'enigma')

    @property
    def all(self):
        return Ontology(self, 'all', ontologies_all=True)


class Ontology:
    def __init__(self, ontology_service, ontology_id, ontologies_all=False):
        self.__ontology_service = ontology_service
        self.__index_name = _ES_OTERM_INDEX_PREFIX
        if ontologies_all:
            self.__index_name += '*'
        else:
            self.__index_name += ontology_id
        self.__inflate_root_terms()

    def __inflate_root_terms(self):
        for term in self.find_root():
            name = 'ROOT_' + term.property_name
            self.__dict__[name] = term

    def _find_terms(self, query, size=100):
        query['size'] = size

        terms = []
        result_set = self.__ontology_service._search(self.__index_name, query)
        for hit in result_set['hits']['hits']:
            data = hit["_source"]
            term = Term(data['term_id'], term_name=data['term_name'],
                        ontology_id=data['ontology_id'],
                        parent_ids=data['parent_term_ids'],
                        parent_path_ids=data['parent_path_term_ids'],
                        persisted=True)

            terms.append(term)
        return terms

    def _find_term(self, query):
        terms = self._find_terms(query)
        return terms[0] if len(terms) > 0 else None

    def _find_terms_hash(self, query):
        terms_hash = {}
        terms = self._find_terms(query)
        for term in terms:
            terms_hash[term.term_id] = term
        return terms_hash

    def find_root(self, size=100):
        query = {
            "query": {
                "bool": {
                    "must_not": {
                        "exists": {
                            "field": "parent_term_ids"
                        }
                    }
                }
            }
        }
        return TermCollection(self._find_terms(query, size))

    def find_id(self, term_id):
        query = {
            "query": {
                "terms": {
                    "term_id": [
                        term_id
                    ]
                }
            }
        }
        return self._find_term(query)

    def find_ids(self, term_ids, size=100):
        query = {
            "query": {
                "terms": {
                    "term_id": term_ids
                }
            }
        }
        return TermCollection(self._find_terms(query, size))

    def find_name(self, term_name):
        query = {
            "query": {
                "terms": {
                    "term_name": [
                        term_name
                    ]
                }
            }
        }
        return self._find_term(query)

    def find_name_prefix(self, term_name_prefix):
        query = {
            "query": {
                "prefix": {
                    "term_name_prefix": term_name_prefix.lower()
                }
            }
        }
        return TermCollection(self._find_terms(query))

    def find_parent_ids(self, parent_term_ids, size=100):
        query = {
            "query": {
                "terms": {
                    "parent_term_ids": parent_term_ids
                }
            }
        }
        return TermCollection(self._find_terms(query, size))

    def find_parent_path_ids(self, parent_term_ids, size=100):
        query = {
            "query": {
                "terms": {
                    "parent_path_term_ids": parent_term_ids
                }
            }
        }
        return TermCollection(self._find_terms(query, size))

    def find_ids_hash(self, term_ids):
        query = {
            "query": {
                "terms": {
                    "term_id": term_ids
                }
            }
        }
        return self._find_terms_hash(query)

    def find_names_hash(self, term_names):
        query = {
            "query": {
                "terms": {
                    "term_name": term_names
                }
            }
        }
        return self._find_terms_hash(query)


class TermCollection:
    def __init__(self, terms):
        self.__terms = terms
        self.__inflate_terms()

    def __inflate_terms(self):
        for term in self.__terms:
            name = to_var_name('TERM_', term.term_name)
            # name = 'TERM_' + re.sub('[^A-Za-z0-9]+', '_', term.term_name)
            self.__dict__[name] = term

    def __getitem__(self, i):
        return self.__terms[i]

    @property
    def terms(self):
        return self.__terms

    @property
    def size(self):
        return len(self.__terms)

    def _repr_html_(self):
        columns = ['Term ID', 'Term Name', 'Ontology', 'Parents']
        header = '<tr>%s</tr>' % ''.join(['<th>%s</th>' % x for x in columns])
        rows = []
        for term in self.terms:
            rows.append(
                '<tr>%s%s%s%s</tr>' % (
                    '<td>%s</td>' % term.term_id,
                    '<td>%s</td>' % term.term_name,
                    '<td>%s</td>' % term.ontology_id,
                    '<td>%s</td>' % term.parent_ids,
                )
            )

        table = '<table>%s%s</table>' % (header, ''.join(rows))
        return '%s <br> %s terms' % (table, len(self.terms))


__TERM_PATTERN = re.compile('(.+)<(.+)>')


class Term:
    '''
        Supports lazzy loading
    '''

    def __init__(self, term_id, term_name=None, ontology_id=None,
                 parent_ids=None, parent_path_ids=None, validator_name=None, persisted=False):
        self.__persisted = persisted
        self.__term_id = term_id
        self.__term_name = term_name
        self.__ontology_id = ontology_id
        self.__parent_ids = parent_ids
        self.__parent_path_ids = parent_path_ids
        self.__validator_name = validator_name
        self.__parent_terms = []

    @staticmethod
    def check_term_format(value):
        m = __TERM_PATTERN.findall(value)
        return m is not None

    @staticmethod
    def parse_term(value):
        m = __TERM_PATTERN.findall(value)
        if m:
            term = Term(m[0][1].strip(), term_name=m[0][0].strip())
        else:
            raise ValueError('Can not parse term from value: %s' % value)
        return term

    def __str__(self):
        return '%s [%s]' % (self.term_name, self.term_id)

    def _repr_html_(self):
        return '%s [%s] <pre>Ontology: %s</pre><pre>Parents: %s</pre>' \
            % (self.term_name, self.term_id, self.ontology_id, self.parent_ids)

    def __safe_proeprty(self, prop_name):
        if self.__dict__[prop_name] is None and not self.__persisted:
            self.__lazzy_load()
        return self.__getattribute__(prop_name)

    def refresh(self):
        self.__lazzy_load()

    def __lazzy_load(self):
        term = services.ontology.all.find_id(self.term_id)
        if term is None:
            raise ValueError('Can not find term with id: %s' % self.term_id)
        self.__term_name = term.term_name
        self.__ontology_id = term.ontology_id
        self.__parent_ids = term.parent_ids
        self.__parent_path_ids = term.parent_path_ids
        self.__validator_name = term.validator_name
        self.__persisted = True

    @property
    def term_id(self):
        return self.__term_id

    @property
    def ontology_id(self):
        return self.__safe_proeprty('_Term__ontology_id')

    @property
    def term_name(self):
        return self.__safe_proeprty('_Term__term_name')

    # @property
    # def property_name(self):
    #     return '_'.join(self.term_name.split(' '))

    @property
    def parent_ids(self):
        return self.__safe_proeprty('_Term__parent_ids')

    @property
    def parent_path_ids(self):
        return self.__safe_proeprty('_Term__parent_path_ids')

    @property
    def validator_name(self):
        return self.__safe_proeprty('_Term__validator_name')

    @property
    def property_name(self):
        # return re.sub('[^A-Za-z0-9]+', '_', self.term_name)
        return to_var_name('', self.term_name)

    def validate_value(self, val):
        if self.validator_name is None:
            return True

        validator = services.term_value_validator.validator(
            self.validator_name)
        if validator is None:
            return True

        return validator(val)

    @property
    def parents(self):
        ont = Ontology(services.ontology, self.__ontology_id)
        return ont.find_ids(self.__parent_ids)

    @property
    def parent_path(self):
        ont = Ontology(services.ontology, self.__ontology_id)
        id2term = ont.find_ids_hash(self.__parent_path_ids)
        terms = [id2term[term_id] for term_id in self.__parent_path_ids]
        return TermCollection(terms)

    @property
    def children(self):
        ont = Ontology(services.ontology, self.__ontology_id)
        return ont.find_parent_ids([self.term_id])

    @property
    def _parent_terms(self):
        return self.__parent_terms

    def _update_parents(self, terms):
        self.__parent_terms = []
        for pid in self.__parent_ids:
            term = terms[pid]
            self.__parent_terms.append(term)
