import json
import os
import re
import pandas as pd
from .utils import to_var_name
from . import services

OTERM_TYPE = 'OTerm'
ONTOLOGY_COLLECTION_NAME_PREFIX = 'generix-ont-'

class OntologyService:
    def __init__(self, arango_service):
        self.__arango_service = arango_service

    def _upload_ontologies(self, config_fname):
        with open(config_fname, 'r') as f:
            doc = json.loads(f.read())
            for ont in doc['ontologies']:
                print('Doing ontology: ' + ont['name'])
                self._upload_ontology(doc['source_dir'], ont)
 
    def _upload_ontology(self, dir_name, ont):
        self._clean_ontology(ont['name'])

        terms = self._load_terms(dir_name, ont)
        self._index_terms(ont['name'], terms)

    def _index_terms(self, ont_id, terms):
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
            self.__arango_service.index_doc(doc, OTERM_TYPE)


    def _collect_all_parent_ids(self, term, all_parent_ids):
        for pt in term._parent_terms:
            all_parent_ids[pt.term_id] = pt
            self._collect_all_parent_ids(pt, all_parent_ids)

    def _load_terms(self, dir_name, ont):
        ont_id = ont['name']
        file_name = ont['file_name']

        STATE_NONE = 0
        STATE_TERM_FOUND = 1

        state = STATE_NONE
        terms = {}

        term_id = None
        term_name = None
        term_aliases = []
        term_parent_ids = []

        root_term = None
        with open(dir_name + file_name, 'r') as f:
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
                        term_id = None
                        state = STATE_NONE

        if term_id is not None:
            term = Term(term_id, term_name=term_name,
                        ontology_id=ont_id,
                        parent_ids=term_parent_ids)
            terms[term.term_id] = term
            if root_term is None:
                root_term = term

        for _, term in terms.items():
            term._update_parents(terms)

        return terms

    def _clean_ontology(self, ont_name):
        pass

    # def _drop_index(self, index_name):
    #     try:
    #         self.__es_client.indices.delete(index=index_name)
    #     except:
    #         pass

    # def _create_index(self, index_name):
    #     settings = {
    #         "settings": {
    #             "analysis": {
    #                 "analyzer": {
    #                     "keyword": {
    #                         "type": "custom",
    #                         "tokenizer": "keyword"
    #                     }
    #                 }
    #             }
    #         },
    #         "mappings": {
    #             _ES_OTERM_TYPE: {
    #                 "properties": {
    #                     "term_id": {
    #                         "type": "text",
    #                         "analyzer": "keyword"
    #                     },
    #                     "parent_term_ids": {
    #                         "type": "text",
    #                         "analyzer": "keyword"
    #                     },
    #                     "parent_path_term_ids": {
    #                         "type": "text",
    #                         "analyzer": "keyword"
    #                     },
    #                     "term_name": {
    #                         "type": "text",
    #                         "analyzer": "keyword"
    #                     },
    #                     "term_name_prefix": {
    #                         "type": "text",
    #                         "analyzer": "standard"
    #                     }
    #                 }
    #             }
    #         }
    #     }

    #     self.__es_client.indices.create(index=index_name, body=settings)


    # def __find(self, aql_filter, aql_bind):
    #     aql = 'FOR x IN %s FILTER %s RETURN x' % (OTERM_TYPE, aql_filter )
    #     return self.__arango_service.find(aql, aql_bind)


    @property
    def units(self):
        return Ontology(self.__arango_service, 'units')

    @property
    def data_types(self):
        return Ontology(self.__arango_service, 'dtype')

    @property
    def enigma(self):
        return Ontology(self.__arango_service, 'enigma')

    @property
    def all(self):
        return Ontology(self.__arango_service, 'all', ontologies_all=True)

    def term_stat(self, index_type_def, term_prop_name):
        index_prop_def = index_type_def.get_property_def(term_prop_name)

        aql_collect = ''
        if index_prop_def.scalar_type.startswith('['):
            aql_collect = '''
                FOR terms IN x.%s
                COLLECT term_id = terms 
            ''' % (index_prop_def.name[:-1] + '_term_ids')
        else:
            aql_collect = 'COLLECT term_id = x.%s ' % (index_prop_def.name + '_term_id')

        aql = '''
            FOR x IN @@collection
            %s
            WITH COUNT INTO term_count
            SORT term_count DESC
            RETURN {term_id, term_count}
        ''' % aql_collect
        aql_bind = {'@collection': index_type_def.collection_name}

        rs = services.arango_service.find(aql,aql_bind)

        term_ids = [row['term_id'] for row in rs]
        term_ids_hash = services.ontology.all.find_ids_hash(term_ids)
        return [  ( term_ids_hash.get(row['term_id']), row['term_count'] ) 
            for row in rs  ]    

class Ontology:
    def __init__(self, arango_service, ontology_id, ontologies_all=False):        
        self.__arango_service = arango_service
        self.__ontology_id = ontology_id

        self.__index_name = ONTOLOGY_COLLECTION_NAME_PREFIX
        if ontologies_all:
            self.__index_name += '*'
        else:
            self.__index_name += ontology_id
        self.__inflate_root_terms()


    def __inflate_root_terms(self):
        pass
        # TODO
        # for term in self.find_root():
        #     name = 'ROOT_' + term.property_name
        #     self.__dict__[name] = term

    def __find_terms(self, aql_filter, aql_bind, aql_fulltext=None, size=100):
        
        if aql_filter is None or len(aql_filter) == 0:
            aql_filter = '1==1'

        if not self.__index_name.endswith('*'):
            aql_filter += ' and x.ontology_id == @ontology_id'
            aql_bind['ontology_id'] = self.__ontology_id

        if aql_fulltext is None:
            aql = 'FOR x IN %s FILTER %s RETURN x' % (OTERM_TYPE, aql_filter )
        else:
            aql = 'FOR x IN %s FILTER %s RETURN x' % (aql_fulltext, aql_filter )

        result_set =  self.__arango_service.find(aql, aql_bind, size)

        return self.__build_terms(result_set)
    
    def __build_terms(self, aql_result_set):
        terms = []
        for row in aql_result_set:
            term = Term(row['term_id'], term_name=row['term_name'],
                        ontology_id=row['ontology_id'],
                        parent_ids=row['parent_term_ids'],
                        parent_path_ids=row['parent_path_term_ids'],
                        persisted=True)     
            terms.append(term)       
        return terms


    def __find_term(self, aql_filter, aql_bind):
        terms = self.__find_terms(aql_filter, aql_bind)
        return terms[0] if len(terms) > 0 else None

    def __find_terms_hash(self, aql_filter, aql_bind):
        terms_hash = {}
        terms = self.__find_terms(aql_filter, aql_bind)
        for term in terms:
            terms_hash[term.term_id] = term
        return terms_hash

    def find_root(self, size=100):
        aql_bind = {}
        aql_filter = 'x.parent_term_ids == []'
        return TermCollection(self.__find_terms(aql_filter, aql_bind, size=size))

    def find_id(self, term_id):
        aql_bind = {'term_id': term_id}
        aql_filter = 'x.term_id == @term_id'
        return self.__find_term(aql_filter, aql_bind)

    def find_ids(self, term_ids, size=100):
        aql_bind = {'term_ids': term_ids}
        aql_filter = 'x.term_id in @term_ids'

        return TermCollection(self.__find_terms(aql_filter, aql_bind, size=size))

    def find_name(self, term_name):
        aql_bind = {'term_name': term_name}
        aql_filter = 'x.term_name == @term_name'
        return self.__find_term(aql_filter, aql_bind)

    def find_name_pattern(self, term_name_prefix, size=100):
        aql_bind = {'@collection': 'OTerm', 'property_name': 'term_name_prefix', 'property_value': term_name_prefix}
        aql_filter = ''
        aql_fulltext = 'FULLTEXT(@@collection, @property_name, @property_value)'
        return TermCollection(self.__find_terms(aql_filter, aql_bind, 
            aql_fulltext=aql_fulltext, size=size))

    def find_parent_id(self, parent_term_id, size=100):
        aql_bind = {'parent_term_id': parent_term_id}
        aql_filter = '@parent_term_id in x.parent_term_ids'

        return TermCollection(self.__find_terms(aql_filter, aql_bind, size=size))

    def find_parent_path_id(self, parent_term_id, size=100):
        aql_bind = {'parent_term_id': parent_term_id}
        aql_filter = '@parent_term_id in x.parent_path_term_ids'

        return TermCollection(self.__find_terms(aql_filter, aql_bind, size=size))

    def find_ids_hash(self, term_ids):
        aql_bind = {'term_ids': term_ids}
        aql_filter = 'x.term_id in @term_ids'

        return self.__find_terms_hash(aql_filter, aql_bind)

    def find_names_hash(self, term_names):
        aql_bind = {'term_names': term_names}
        aql_filter = 'x.term_name in @term_names'
        return self.__find_terms_hash(aql_filter, aql_bind)


class TermCollection:
    def __init__(self, terms):
        self.__terms = terms
        self.__inflate_terms()

    def __inflate_terms(self):
        for term in self.__terms:
            name = to_var_name('TERM_', term.term_name)
            self.__dict__[name] = term

    def __getitem__(self, i):
        return self.__terms[i]

    @property
    def term_ids(self):
        return [t.term_id for t in self.__terms]

    @property
    def terms(self):
        return self.__terms

    @property
    def size(self):
        return len(self.__terms)

    '''
        term_id_name can be one of:
        . instance of Term
        . term_id in the format QQQ:1234234
        . exact term name
    '''
    def add_term(self, term_id_name):
        term = Term.get_term(term_id_name)
        
        self.__terms.append(term)
        name = to_var_name('TERM_', term.term_name)
        self.__dict__[name] = term

    def head(self, n=5):
        return TermCollection(self.__terms[:n])

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


_TERM_PATTERN = re.compile('(.+)<(\w+:\d+)>')
_TERM_ID_PATTERN = re.compile('\w+:\d+')


class Term:
    '''
        Supports lazzy loading
    '''

    def __init__(self, term_id, term_name=None, ontology_id=None,
                 parent_ids=None, parent_path_ids=None, validator_name=None, persisted=False, refresh=False):
        self.__persisted = persisted
        self.__term_id = term_id
        self.__term_name = term_name
        self.__ontology_id = ontology_id
        self.__parent_ids = parent_ids
        self.__parent_path_ids = parent_path_ids
        self.__validator_name = validator_name
        self.__parent_terms = []
        if refresh:
            self.refresh()

    '''
        term_id_names is an array. The elements of this array can be one of:
        . instance of Term
        . term_id in the format QQQ:1234234
        . exact term name
    '''
    @staticmethod
    def get_terms(term_id_names):
        terms = []
        for term_id_name in term_id_names:
            terms.append( Term.get_term(term_id_name) )
        return terms

    '''
        term_id_name can be one of:
        . instance of Term
        . term_id in the format QQQ:1234234
        . exact term name
    '''
    @staticmethod
    def get_term(term_id_name):
        term = None
        if type(term_id_name) is Term:
            term = term_id_name
        elif type(term_id_name) is str:
            if _TERM_ID_PATTERN.match(term_id_name) is not None:
                try:
                    term = Term(term_id_name)
                    term.refresh()
                except:
                    raise ValueError('Wrong term id: %s' % term_id_name)
            else:
                term = services.ontology.all.find_name(term_id_name)
                if term is None:
                    raise ValueError('Wrong term name: %s' % term_id_name)
        else:
            raise ValueError('Wrong term value: %s' % term_id_name)
        return term

    @staticmethod
    def check_term_format(value):
        m = _TERM_PATTERN.findall(value)
        return m is not None

    @staticmethod
    def parse_term(value):
        m = _TERM_PATTERN.findall(value)
        if m:
            # term = Term(m[0][1].strip(), term_name=m[0][0].strip())
            term = services.term_provider.get_term(m[0][1].strip())
        else:
            raise ValueError('Can not parse term from value: %s' % value)
        return term

    def __str__(self):
        return '%s <%s>' % (self.term_name, self.term_id)

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

    def __eq__(self, value):
        if type(value) is Term:
            return self.term_id == value.term_id

        if type(value) is str:
            value = value.strip()
            return value == self.term_id or value.lower() == self.term_name.lower().strip()

        return False

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
        ont = Ontology(services.arango_service, self.__ontology_id)
        return ont.find_ids(self.__parent_ids)

    @property
    def parent_path(self):
        ont = Ontology(services.arango_service, self.__ontology_id)
        id2term = ont.find_ids_hash(self.__parent_path_ids)
        terms = [id2term[term_id] for term_id in self.__parent_path_ids]
        return TermCollection(terms)

    @property
    def children(self):
        ont = Ontology(services.arango_service, self.__ontology_id)
        return ont.find_parent_id(self.term_id)

    @property
    def _parent_terms(self):
        return self.__parent_terms

    def _update_parents(self, terms):
        self.__parent_terms = []
        for pid in self.__parent_ids:
            term = terms[pid]
            self.__parent_terms.append(term)


class CashedTermProvider:
    def __init__(self):
        self.__id_2_term = {}

    def get_term(self, term_id):
        term = self.__id_2_term.get(term_id)
        if term is None:
            term = services.ontology.all.find_id(term_id)
            if term is None:
                raise ValueError(
                    'Can not find a term with id: %s' % term_id)

            self.__id_2_term[term_id] = term

        return term
