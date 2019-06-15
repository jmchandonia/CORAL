from .ontology import Term, TermCollection
from .typedef import TYPE_CATEGORY_SYSTEM
from . import services

_SYS_TERMS = [
    'Person', 'DefaultCampaign'
]

_SYS_TERM_COLLECTION = [
    'Units',
    'BrickTypes',
    'DimTypes',
    'VarTypes'
]
class UserProfile:
    def __init__(self, user_name):
        self.__user_name = user_name
        self.__named_term_collections = {}
        self.__named_terms = {}
        self.__load_profile()

        # add sys collections if not present
        for cname in _SYS_TERM_COLLECTION:
            if cname not in self.__named_term_collections:
                self.__named_term_collections[cname] = TermCollection([])

        # add sys terms
        for tname in _SYS_TERMS:
            if tname not in self.__named_terms:
                self.__named_terms[tname] = None

        # inflate collections and terms
        self.__dict__.update(self.__named_terms)
        self.__dict__.update(self.__named_term_collections)

    def add_term_collection(self, collection_name):
        if collection_name in self.__named_term_collections:
            print('Collection with name %s already exists' % collection_name)
            return self.__named_term_collections[collection_name]

        term_collection = TermCollection([])
        self.__named_term_collections[collection_name] = term_collection
        self.__dict__[collection_name] = term_collection
        return term_collection

    def add_term(self, term_name, term_id_name):
        term = self.__named_terms.get(term_name)
        if term is not None:
            print('Term with name %s already exists' % term_name)
            return self.__named_terms[term_name]
        
        term = Term.get_term(term_id_name)
        self.__named_terms[term_name] = term
        self.__dict__[term_name] = term
        return term

    def __load_profile(self):
        aql = 'FOR x IN SYS_UserProfile FILTER x._key == @user_name return x'
        aql_bind = {'user_name': self.__user_name}
        rs = services.arango_service.find(aql, aql_bind)
        if len(rs) == 1:
            # load terms
            terms = rs[0]['terms']
            for term_name, term_id in terms.items():
                self.__named_terms[term_name] = Term(term_id)
            
            # load term collections
            tcols = rs[0]['term_collections']
            for cname, term_ids in tcols.items():
                terms = [ Term(id) for id in term_ids ]
                self.__named_term_collections[cname] = TermCollection(terms)

    def save(self):
        terms_doc = {}
        for tname, term in self.__named_terms.items():
            if term is not None:
                terms_doc[tname] = term.term_id

        term_cl_doc = {}
        for cname, term_collection in self.__named_term_collections.items():
            term_cl_doc[cname] = term_collection.term_ids

        doc = {
            services.indexdef.PK_PROPERTY_NAME : self.__user_name,
            'terms': terms_doc,
            'term_collections': term_cl_doc
        }
        services.arango_service.upsert_doc( 
            {
                services.indexdef.PK_PROPERTY_NAME : self.__user_name
            }, doc, 'UserProfile', TYPE_CATEGORY_SYSTEM)

