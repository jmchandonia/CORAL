import json
import os
import re
import pandas as pd
import sys
from .utils import to_var_name
from . import services


OTERM_TYPE = 'OTerm'
TYPE_CATEGORY_ONTOLOGY = ''
OTERM_COLLECTION_NAME = TYPE_CATEGORY_ONTOLOGY + OTERM_TYPE

ONTOLOGY_COLLECTION_NAME_PREFIX = 'generix-ont-'

_TERM_PATTERN = re.compile(r'(.+)<(\w+:\d+)>')
_TERM_ID_PATTERN = re.compile(r'\w+:\d+')

_TERM_ID = re.compile(r'id:\s+(\w+:\d+)')
_TERM_NAME = re.compile(r'name:\s+(.+)')
_TERM_DEF = re.compile(r'def:\s+"(.+)" \[.*?\]')
_TERM_IS_A = re.compile(r'is_a:\s+(\w+:\d+)')
_TERM_SYNONYM = re.compile(r'synonym:\s+"(.+)"')
_TERM_SCALAR_TYPE = re.compile(r'data_type\s+"(\w+)"')
_TERM_IS_MICROTYPE = re.compile(r'is_microtype\s+"true"')
_TERM_IS_DIMENSION = re.compile(r'is_valid_dimension\s+"true"')
_TERM_IS_DIMENSION_VARIABLE = re.compile(r'is_valid_dimension_variable\s+"true"')
_TERM_IS_PROPERTY = re.compile(r'is_valid_property\s+"true"')
_TERM_IS_HIDDEN = re.compile(r'is_hidden\s+"true"')
_TERM_VALID_UNITS = re.compile(r'valid_units\s+"([\w+:\d+\s*]+)"')
_TERM_VALID_UNITS_PARENT = re.compile(r'valid_units_parent\s+"([\w+:\d+\s*]+)"')
_TERM_OREF = re.compile(r'ORef:\s+(\w+:\d+)')
_TERM_REF = re.compile(r'Ref:\s+(\w+:\d+\.\w+\.\w+)')
_MICROTYPE_FK_PATTERN = re.compile(r'(\w+:\d+)\.(\w+)\.(\w+)')


class OntologyService:
    def __init__(self, arango_service):
        self.__arango_service = arango_service

    def _ensure_ontology_ready(self):
        try:
            services.arango_service.create_collection(OTERM_COLLECTION_NAME)
        except:
            print('Ontology collection is present already')
        
        # build indices
        print('Ensure ontology indices')
        collection = services.arango_service.db[OTERM_COLLECTION_NAME]
        collection.ensureFulltextIndex(['term_name'],minLength=1)
        collection.ensureFulltextIndex(['term_desc'],minLength=1)
        collection.ensureHashIndex(['term_id'], unique=True)
        collection.ensureHashIndex(['ontology'])


    def _upload_ontologies(self, config_fname):
        self._ensure_ontology_ready()
        with open(config_fname, 'r') as f:
            doc = json.loads(f.read())
            for ont in doc['ontologies']:
                print('Doing ontology: ' + ont['name'])
                if 'ignore' in ont and ont['ignore']:
                    print(' (skipping because of ignore directive)')
                    continue
                self._upload_ontology(services._IMPORT_DIR_ONTOLOGY, ont)
 
    def _upload_ontology(self, dir_name, ont):
        self._clean_ontology(ont['name'])

        terms = self._load_terms(dir_name, ont)
        self._index_terms(ont['name'], terms)

    def _index_terms(self, ont_id, terms):
        for _, term in terms.items():
            all_parent_ids = {}
            self._collect_all_parent_ids(term, all_parent_ids)             
            term_desc = term.term_def;
            if (len(term.synonyms) > 0):
                term_desc += '['+', '.join(term.synonyms)+']'
            doc = {
                'ontology_id': ont_id,
                'term_id': term.term_id,
                'term_name': term.term_name,
                'term_def': term.term_def,
                'term_desc': term_desc,
                'term_names': [term.term_name] + term.synonyms,
                'parent_term_ids': term.parent_ids,
                
                'synonyms':term.synonyms,
                'is_microtype':term.is_microtype,
                'is_dimension':term.is_dimension,
                'is_dimension_variable':term.is_dimension_variable,
                'is_property':term.is_property,
                'is_hidden':term.is_hidden,
                'microtype_value_scalar_type': term.microtype_value_scalar_type,
                'microtype_fk':term.microtype_fk,
                'microtype_valid_values_parent':term.microtype_valid_values_parent,
                'microtype_valid_units':term.microtype_valid_units,
                'microtype_valid_units_parents':term.microtype_valid_units_parents,

                'parent_path_term_ids': list(all_parent_ids.keys())
            }
            try:
                self.__arango_service.index_doc(doc, OTERM_TYPE, TYPE_CATEGORY_ONTOLOGY)
            except Exception as e:
                print('ERROR: can not index term: %s - %s' % (doc['term_id'],doc['term_name']), e )

    def _get_term(self, term_id_name):
        return Term.get_term(term_id_name)

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
        root_term = None

        with open( os.path.join(dir_name, file_name) , 'r') as f:
            for line in f:
                line = line.strip()
                if state == STATE_NONE:
                    if line.startswith('[Term]'):

                        # init term properties
                        term_id = None
                        term_name = ''
                        term_def = ''
                        term_synonyms = []

                        term_value_scalar_type = ''
                        term_is_microtype = False
                        term_is_dimension = False
                        term_is_dimension_variable = False
                        term_is_property = False
                        term_is_hidden = False
                        term_ref = ''
                        term_oref = ''
                        term_valid_units = []
                        term_valid_units_parents = []
                        term_parent_ids = []                        

                        state = STATE_TERM_FOUND

                elif state == STATE_TERM_FOUND:
                    if line.startswith('id:'):    
                        m = _TERM_ID.match(line)
                        if m is not None:                    
                            term_id = m.groups()[0]
                    elif line.startswith('name:'):
                        m = _TERM_NAME.match(line)
                        if m is not None:
                            term_name = m.groups()[0]
                    elif line.startswith('def:'):
                        m = _TERM_DEF.match(line)
                        if m is not None:
                            term_def = m.groups()[0]
                    elif line.startswith('is_a:'):
                        m = _TERM_IS_A.match(line)
                        if m is not None:
                            parent_id = m.groups()[0]                        
                            term_parent_ids.append(parent_id)
                    elif line.startswith('synonym:'):
                        m = _TERM_SYNONYM.match(line)
                        if m is not None:
                            syn = m.groups()[0]                        
                            term_synonyms.append(syn)
                    elif line.startswith('xref:'):
                        xr = line[len('xref:'):].strip()

                        m = _TERM_REF.match(xr)
                        if m is not None:
                            term_ref = m.groups()[0]

                        m = _TERM_OREF.match(xr)
                        if m is not None:
                            term_oref = m.groups()[0]

                    elif line.startswith('property_value:'):
                        pv = line[len('property_value:'):].strip()
                        if not term_is_microtype and _TERM_IS_MICROTYPE.match(pv):
                            term_is_microtype = True
                        elif not term_is_dimension and _TERM_IS_DIMENSION.match(pv):
                            term_is_dimension = True
                        elif not term_is_dimension_variable and _TERM_IS_DIMENSION_VARIABLE.match(pv):
                            term_is_dimension_variable = True
                        elif not term_is_property and _TERM_IS_PROPERTY.match(pv):
                            term_is_property = True
                        elif not term_is_hidden and _TERM_IS_HIDDEN.match(pv):
                            term_is_hidden = True

                        else:
                            m = _TERM_SCALAR_TYPE.match(pv)
                            if m is not None:
                                term_value_scalar_type = m.groups()[0]

                            m = _TERM_VALID_UNITS.match(pv)
                            if m is not None:
                                term_valid_units = m.groups()[0].split()
                            
                            m = _TERM_VALID_UNITS_PARENT.match(pv)
                            if m is not None:
                                term_valid_units_parents = m.groups()[0].split()

                    elif line == '':
                        term = Term(term_id,
                                    term_name=term_name,
                                    term_def=term_def,
                                    ontology_id=ont_id,
                                    parent_ids=term_parent_ids,
                                    
                                    synonyms=term_synonyms,
                                    is_microtype=term_is_microtype,
                                    is_dimension=term_is_dimension,
                                    is_dimension_variable=term_is_dimension_variable,
                                    is_property=term_is_property,
                                    is_hidden=term_is_hidden,
                                    microtype_value_scalar_type=term_value_scalar_type,
                                    microtype_fk=term_ref,
                                    microtype_valid_values_parent=term_oref,
                                    microtype_valid_units=term_valid_units,
                                    microtype_valid_units_parents=term_valid_units_parents                        
                                    )
                        terms[term.term_id] = term
                        if root_term is None:
                            root_term = term
                        term_id = None
                        state = STATE_NONE

        if term_id is not None:
            term = Term(term_id,
                        term_name=term_name,
                        term_def=term_def,
                        ontology_id=ont_id,
                        parent_ids=term_parent_ids,
                        synonyms=term_synonyms,
                        is_microtype=term_is_microtype,
                        is_dimension=term_is_dimension,
                        is_dimension_variable=term_is_dimension_variable,
                        is_property=term_is_property,
                        is_hidden=term_is_hidden,
                        microtype_value_scalar_type=term_value_scalar_type,
                        microtype_fk=term_ref,
                        microtype_valid_values_parent=term_oref,
                        microtype_valid_units=term_valid_units,
                        microtype_valid_units_parents=term_valid_units_parents                        
                        )

            terms[term.term_id] = term
            if root_term is None:
                root_term = term

        for _, term in terms.items():
            term._update_parents(terms)

        return terms

    def _clean_ontology(self, ont_name):
        print("Deleting terms in %s" % ont_name)
        aql = """
            FOR x IN @@collection
            FILTER x.ontology_id==@value
            REMOVE x in @@collection
        """
        aql_bind = {
            '@collection': OTERM_COLLECTION_NAME,
            'value': ont_name
        }
        self.__arango_service.db.AQLQuery(aql, bindVars=aql_bind)

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

    @property
    def dimension_microtypes(self):
        return Ontology(self.__arango_service, 'all', ontologies_all=True, 
            base_aql_filter='x.is_microtype==True and x.is_dimension==True')

    @property
    def dimension_variable_microtypes(self):
        return Ontology(self.__arango_service, 'all', ontologies_all=True, 
            base_aql_filter='x.is_microtype==True and x.is_dimension_variable==True')

    @property
    def property_microtypes(self):
        return Ontology(self.__arango_service, 'all', ontologies_all=True, 
            base_aql_filter='x.is_microtype==True and x.is_property==True')

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
    def __init__(self, arango_service, ontology_id, base_aql_filter=None, base_aql_bind=None, ontologies_all=False):        
        self.__arango_service = arango_service
        self.__ontology_id = ontology_id
        self.__base_aql_filter = base_aql_filter
        self.__base_aql_bind = base_aql_bind

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

    def __find_terms(self, aql_filter, aql_bind, aql_fulltext=None, size=1000):        
        if aql_filter is None or len(aql_filter) == 0:
            aql_filter = '1==1'

        if not self.__index_name.endswith('*'):
            aql_filter += ' and x.ontology_id == @ontology_id'
            aql_bind['ontology_id'] = self.__ontology_id
        
        if self.__base_aql_filter is not None:
            aql_filter += ' and ' + self.__base_aql_filter
        if self.__base_aql_bind is not None:
            aql_bind.update(self.__base_aql_bind)

        if aql_fulltext is None:
            aql = 'FOR x IN %s FILTER %s RETURN x' % (OTERM_COLLECTION_NAME, aql_filter )
        else:
            aql = 'FOR x IN %s FILTER %s RETURN x' % (aql_fulltext, aql_filter )
        
        # print('aql=%s' % aql)
        # print('aql_bind:', aql_bind)
        result_set =  self.__arango_service.find(aql, aql_bind, size)

        return self.__build_terms(result_set)
    
    def __build_terms(self, aql_result_set):
        terms = []
        for row in aql_result_set:
            term = Term(row['term_id'],
                        term_name=row['term_name'],
                        term_def=row['term_def'],
                        ontology_id=row['ontology_id'],
                        parent_ids=row['parent_term_ids'],
                        parent_path_ids=row['parent_path_term_ids'],
                        
                        synonyms = row['synonyms'],
                        is_microtype = row['is_microtype'],
                        is_dimension = row['is_dimension'],
                        is_dimension_variable = row['is_dimension_variable'],
                        is_property = row['is_property'],
                        is_hidden = row['is_hidden'],

                        microtype_value_scalar_type=row['microtype_value_scalar_type'],
                        microtype_fk = row['microtype_fk'],
                        microtype_valid_values_parent = row['microtype_valid_values_parent'],
                        microtype_valid_units = row['microtype_valid_units'],
                        microtype_valid_units_parents = row['microtype_valid_units_parents'],

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

    def find_root(self, size=1000):
        aql_bind = {}
        aql_filter = 'x.parent_term_ids == []'
        return TermCollection(self.__find_terms(aql_filter, aql_bind, size=size))

    def find_id(self, term_id):
        aql_bind = {'term_id': term_id}
        aql_filter = 'x.term_id == @term_id'
        try:
            return self.__find_term(aql_filter, aql_bind)
        except:
            raise ValueError('Error finding term id: %s' % term_id)

    def find_microtype_dimensions(self, size=1000):    
        aql_bind = {}
        aql_filter = 'x.is_dimension == true'
        return MicrotypeCollection(self.__find_terms(aql_filter, aql_bind, size=size))

    def find_microtype_dimension_variables(self, size=1000):    
        aql_bind = {}
        aql_filter = 'x.is_dimension_variable == true'
        return MicrotypeCollection(self.__find_terms(aql_filter, aql_bind, size=size))

    def find_microtype_data_variables(self, size=1000):    
        aql_bind = {}
        aql_filter = 'x.is_dimension_variable == true'
        return MicrotypeCollection(self.__find_terms(aql_filter, aql_bind, size=size))

    def find_microtype_properties(self, size=1000):    
        aql_bind = {}
        aql_filter = 'x.is_property == true'
        return MicrotypeCollection(self.__find_terms(aql_filter, aql_bind, size=size))

    def find_microtypes(self, size=1000):    
        aql_bind = {}
        aql_filter = 'x.is_microtype == true'
        return MicrotypeCollection(self.__find_terms(aql_filter, aql_bind, size=size))

    def find_ids(self, term_ids, size=1000):
        aql_bind = {'term_ids': term_ids}
        aql_filter = 'x.term_id in @term_ids'

        return TermCollection(self.__find_terms(aql_filter, aql_bind, size=size))

    def find_name(self, term_name):
        aql_bind = {'term_name': term_name}
        aql_filter = 'x.term_name == @term_name'
        return self.__find_term(aql_filter, aql_bind)

    def find_name_prefix(self, value, parent_term_id=None, size=1000):
        return self.find_name_pattern("prefix:" + value, parent_term_id=parent_term_id, size=size)

    def find_name_pattern(self, value, parent_term_id=None, size=1000):
        aql_bind = {
            '@collection': 'OTerm', 
            'property_name': 'term_name', 
            'property_value': value}
        aql_filter = ''
        aql_fulltext = 'FULLTEXT(@@collection, @property_name, @property_value)'

        if parent_term_id is not None and parent_term_id != '':
            aql_bind['parent_term_id'] = parent_term_id
            aql_filter = '@parent_term_id in x.parent_path_term_ids'

        return TermCollection(self.__find_terms(aql_filter, aql_bind, 
            aql_fulltext=aql_fulltext, size=size))

    def find_parent_id(self, parent_term_id, size=1000):
        aql_bind = {'parent_term_id': parent_term_id}
        aql_filter = '@parent_term_id in x.parent_term_ids'

        return TermCollection(self.__find_terms(aql_filter, aql_bind, size=size))

    def find_parent_path_id(self, parent_term_id, size=1000):
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

class MicrotypeCollection:
    def __init__(self, terms):
        self.__terms = terms
        self.__terms.sort(key=lambda term: term.term_name)
        # self.__inflate_terms()

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


    def head(self, n=5):
        return MicrotypeCollection(self.__terms[:n])

    def _repr_html_(self):
        columns = ['Term ID', 'Term Name', 'Dimension', 'Dim. Var', 'Data Var', 'Property']
        header = '<tr>%s</tr>' % ''.join(['<th>%s</th>' % x for x in columns])
        rows = []
        for term in self.terms:
            rows.append(
                '<tr>%s%s%s%s%s%s</tr>' % (
                    '<td>%s</td>' % term.term_id,
                    '<td>%s</td>' % term.term_name,
                    '<td>%s</td>' % term.is_dimension, 
                    '<td>%s</td>' % term.is_dimension_variable,
                    '<td>%s</td>' % term.is_dimension_variable,
                    '<td>%s</td>' % term.is_property
                )
            )

        table = '<table>%s%s</table>' % (header, ''.join(rows))
        return '%s <br> %s terms' % (table, len(self.terms))

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

class Term:
    '''
        Supports lazy loading
    '''

    def __init__(self, term_id, 
                term_name=None, 
                term_def=None, 
                ontology_id=None,
                parent_ids=None, 
                parent_path_ids=None, 
                synonyms=None,
                is_microtype=None,
                is_dimension=None,
                is_dimension_variable=None,
                is_property=None,
                is_hidden=None,

                microtype_value_scalar_type=None,
                microtype_fk=None,
                microtype_valid_values_parent=None,
                microtype_valid_units=None,
                microtype_valid_units_parents=None,              
                validator_name=None, 
                persisted=False, 
                refresh=False):


        self.__term_id = term_id
        self.__term_name = term_name
        self.__term_def = term_def
        self.__ontology_id = ontology_id
        self.__parent_ids = parent_ids
        self.__parent_path_ids = parent_path_ids

        self.__synonyms = synonyms
        self.__is_microtype = is_microtype
        self.__is_dimension = is_dimension
        self.__is_dimension_variable = is_dimension_variable
        self.__is_property = is_property
        self.__is_hidden = is_hidden

        self.__microtype_value_scalar_type = microtype_value_scalar_type
        self.__microtype_fk = microtype_fk
        self.__microtype_fk_term_id = None
        self.__microtype_fk_core_type = None
        self.__microtype_fk_core_prop_name = None
        self.__microtype_valid_values_parent = microtype_valid_values_parent
        self.__microtype_valid_units = microtype_valid_units
        self.__microtype_valid_units_parents = microtype_valid_units_parents 

        self.__validator_name = validator_name
        self.__update_microtype_fk()

        self.__parent_terms = []
        self.__persisted = persisted
        if refresh:
            self.refresh()

    def __init(self, term):
        self.__persisted = True

        #self.__term_id = term_id
        self.__term_name = term.term_name
        self.__term_def = term.term_def
        self.__ontology_id = term.ontology_id
        self.__parent_ids = term.parent_ids
        self.__parent_path_ids = term.parent_path_ids

        self.__synonyms = term.synonyms
        self.__is_microtype = term.is_microtype
        self.__is_dimension = term.is_dimension
        self.__is_dimension_variable = term.is_dimension_variable
        self.__is_property = term.is_property
        self.__is_hidden = term.is_hidden

        self.__microtype_value_scalar_type = term.microtype_value_scalar_type
        self.__microtype_fk = term.microtype_fk
        self.__microtype_fk_term_id = term.microtype_fk_term_id
        self.__microtype_fk_core_type = term.microtype_fk_core_type
        self.__microtype_fk_core_prop_name = term.microtype_fk_core_prop_name
        self.__microtype_valid_values_parent = term.microtype_valid_values_parent
        self.__microtype_valid_units = term.microtype_valid_units
        self.__microtype_valid_units_parents = term.microtype_valid_units_parents 

        self.__validator_name = term.validator_name

    def __update_microtype_fk(self):
        if self.__microtype_fk is not None:
            self.__microtype_fk_term_id = ''
            self.__microtype_fk_core_type = ''
            self.__microtype_fk_core_prop_name = ''
            if self.__microtype_fk != '':
                m = _MICROTYPE_FK_PATTERN.match(self.__microtype_fk)
                if m is not None:
                    vals = m.groups()
                    self.__microtype_fk_term_id = vals[0]
                    self.__microtype_fk_core_type = vals[1]
                    self.__microtype_fk_core_prop_name = vals[2].lower()
        

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

    def __safe_property(self, prop_name):
        if self.__dict__[prop_name] is None and not self.__persisted:
            self.__lazy_load()
        return self.__getattribute__(prop_name)

    def refresh(self):
        self.__lazy_load()

    def __lazy_load(self):
        term = services.ontology.all.find_id(self.term_id)
        if term is None:
            raise ValueError('Can not find term with id: %s' % self.term_id)
        self.__init(term)
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
        return self.__safe_property('_Term__ontology_id')

    @property
    def term_name(self):
        return self.__safe_property('_Term__term_name')

    @property
    def term_def(self):
        return self.__safe_property('_Term__term_def')

    # @property
    # def property_name(self):
    #     return '_'.join(self.term_name.split(' '))

    @property
    def parent_ids(self):
        return self.__safe_property('_Term__parent_ids')

    @property
    def parent_path_ids(self):
        return self.__safe_property('_Term__parent_path_ids')

    @property
    def synonyms(self):
        return self.__safe_property('_Term__synonyms')

    @property
    def is_microtype(self):
        return self.__safe_property('_Term__is_microtype')

    @property
    def is_dimension(self):
        return self.__safe_property('_Term__is_dimension')

    @property
    def is_dimension_variable(self):
        return self.__safe_property('_Term__is_dimension_variable')

    @property
    def is_property(self):
        return self.__safe_property('_Term__is_property')

    @property
    def is_hidden(self):
        return self.__safe_property('_Term__is_hidden')

    @property
    def microtype_value_scalar_type(self):
        return self.__safe_property('_Term__microtype_value_scalar_type')

    @property
    def microtype_fk(self):
        return self.__safe_property('_Term__microtype_fk')

    @property
    def microtype_fk_term_id(self):
        return self.__safe_property('_Term__microtype_fk_term_id')

    @property
    def microtype_fk_core_type(self):
        return self.__safe_property('_Term__microtype_fk_core_type')

    @property
    def microtype_fk_core_prop_name(self):
        return self.__safe_property('_Term__microtype_fk_core_prop_name')

    @property
    def microtype_valid_values_parent(self):
        return self.__safe_property('_Term__microtype_valid_values_parent')

    @property
    def microtype_valid_units(self):
        return self.__safe_property('_Term__microtype_valid_units')

    @property
    def microtype_valid_units_parents(self):
        return self.__safe_property('_Term__microtype_valid_units_parents')

    @property
    def has_units(self):
        return not not self.microtype_valid_units or not not self.microtype_valid_units_parents

    @property
    def require_mapping(self):
        return not not self.microtype_fk

    @property
    def is_fk(self):
        if self.require_mapping:
            core_type = self.microtype_fk_core_type
            type_def = services.typedef.get_type_def(core_type)
            prop_def = type_def.property_def(self.microtype_fk_core_prop_name)
            if prop_def.is_pk:
                return True
        return False

    @property
    def is_ufk(self):
        if self.require_mapping:
            core_type = self.microtype_fk_core_type
            type_def = services.typedef.get_type_def(core_type)
            prop_def = type_def.property_def(self.microtype_fk_core_prop_name)
            if prop_def.is_upk:
                return True
        return False


    def to_descriptor(self):
        return {
            'id' : self.term_id,
            'text': self.term_name,
            'definition': self.term_def,
            'has_units': self.has_units,
            'is_hidden': self.is_hidden,
            'scalar_type': self.microtype_value_scalar_type,
            'require_mapping': self.require_mapping,
            'microtype':{
                'fk': self.microtype_fk,
                'value_scalar_type': self.microtype_value_scalar_type,
                'valid_values_parent': self.microtype_valid_values_parent,
                'valid_units': self.microtype_valid_units,
                'valid_units_parents': self.microtype_valid_units_parents
            }
        }

    @property
    def validator_name(self):
        return self.__safe_property('_Term__validator_name')

    @property
    def property_name(self):
        # return re.sub('[^A-Za-z0-9]+', '_', self.term_name)
        return to_var_name('', self.term_name)

    # def validate_value(self, val):
    #     if self.validator_name is None:
    #         return True

    #     validator = services.term_value_validator.validator(
    #         self.validator_name)
    #     if validator is None:
    #         return True

    #     return validator(val)

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
            if pid in terms:
                self.__parent_terms.append(terms[pid])
            else:
                term = services.ontology.all.find_id(pid)
                if term:
                    self.__parent_terms.append(term)
                else:
                    raise ValueError('Can not find parent "%s" for term "%s"' % 
                        (pid, self.term_id))


class CachedTermProvider:
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
