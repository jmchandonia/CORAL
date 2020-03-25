import os
from . import services
from .typedef import TYPE_NAME_BRICK, TYPE_CATEGORY_DYNAMIC, TYPE_CATEGORY_STATIC, TYPE_CATEGORY_SYSTEM
from .utils import to_var_name
from .brick import Brick, BrickProvenance
from .query import Query
from .user_profile import UserProfile

class DataProvider:
    def __init__(self):
        services._init_services()

        self.__user_name = 'default'
        if 'USER' in os.environ:
            self.__user_name = os.environ['USER']

        self.__dict__['core_types'] = EntitiesProvider()
        self.__dict__['genx_types'] = GenericsProvider()
        self.__dict__['help_types'] = SystemsProvider()        
        self.__dict__['ontology'] = services.ontology
        self.__dict__['reports'] = services.reports
        self.__dict__['user_profile'] = UserProfile(self.__user_name)

    def _get_type_provider(self, type_name):

        type_def = services.indexdef.get_type_def(type_name)
        provider = None        
        if type_name == TYPE_NAME_BRICK:
            provider = BrickProvider()        
        else:
            provider = EntityProvider(type_def)
        return provider

    def _get_services(self):
        return {
            'ontology': services.ontology,
            'reports' : services.reports,
            'indexdef': services.indexdef,
            'typedef' : services.typedef,
            'arango_service': services.arango_service,
            'workspace': services.workspace,
            'brick_template_provider': services.brick_template_provider,
            'value_validator': services.value_validator,
            'term_provider': services.term_provider
        }
    def _get_constants(self):
        return {
            '_BRICK_TYPE_TEMPLATES_FILE' : services._BRICK_TYPE_TEMPLATES_FILE,
            '_WEB_SERVICE': services._WEB_SERVICE,
            '_PLOT_TYPES_FILE': services._PLOT_TYPES_FILE,
            '_DATA_DIR': services._DATA_DIR
        }

class GenericsProvider:
    def __init__(self):
        self.__load_providers()

    def __load_providers(self):
        index_type_defs = services.indexdef.get_type_defs(category=TYPE_CATEGORY_DYNAMIC)
        for index_type_def in index_type_defs:
            if index_type_def.name == TYPE_NAME_BRICK:
                self.__dict__[TYPE_NAME_BRICK] = BrickProvider()


class EntitiesProvider:
    def __init__(self):
        self.__load_entity_providers()

    def __getitem__(self, core_type):
        return self.__dict__[core_type]

    def __load_entity_providers(self):
        index_type_defs = services.indexdef.get_type_defs(category=TYPE_CATEGORY_STATIC)
        for index_type_def in index_type_defs:
            self.__dict__[index_type_def.name] = EntityProvider(index_type_def)

class SystemsProvider:
    def __init__(self):
        self.__load_providers()

    def __load_providers(self):
        index_type_defs = services.indexdef.get_type_defs(category=TYPE_CATEGORY_SYSTEM)
        for index_type_def in index_type_defs:
            self.__dict__[index_type_def.name] = EntityProvider(index_type_def)



class EntityProvider:
    def __init__(self, index_type_def):
        self.__index_type_def = index_type_def
        self.__inflate_properties()

        # TODO: hack
        index_type_def._register_data_provider(self)

    def __inflate_properties(self):
        for index_prop_def in self.__index_type_def.property_defs:
            key = to_var_name('PROPERTY_', index_prop_def.name)
            self.__dict__[key] = index_prop_def

    def find(self, criterion=None):
        q = self.query()
        q.has(criterion)
        return q.find()

    def find_one(self, criterion=None):
        q = self.query()
        q.has(criterion)
        return q.find_one()

    def query(self):
        return Query(self.__index_type_def)


class BrickProvider(EntityProvider):
    def __init__(self):
        index_type_def = services.indexdef.get_type_def(TYPE_NAME_BRICK) 
        super().__init__(index_type_def)

        # TODO: hack
        index_type_def._register_data_provider(self)


    @staticmethod
    def _load_brick(brick_id):
        brick = Brick.read_dict(
            brick_id,  services.workspace.get_brick_data(brick_id))
        provenance = BrickProvenance('loaded', ['id:%s' % brick.id])
        brick.session_provenance.provenance_items.append(provenance)
        return brick

    def create_brick(self,type_term=None, dim_terms=None, shape=None, name=None, description=None):
        return Brick(type_term = type_term, 
                     dim_terms = dim_terms, 
                     shape = shape,
                     name = name,
                     description = description)

    def load(self, brick_id):
        return BrickProvider._load_brick(brick_id)

    def type_names(self):
        names = []
        itype_def = services.indexdef.get_type_def(TYPE_NAME_BRICK)        
        term_counts = services.ontology.term_stat( itype_def, 'data_type')        
        for term_count in term_counts:
            term = term_count[0]
            names.append(term.term_name)
        names.sort()
        return names
