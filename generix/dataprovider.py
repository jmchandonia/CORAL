import os
from . import services
from .typedef import TYPE_NAME_BRICK, TYPE_CATEGORY_DYNAMIC, TYPE_CATEGORY_STATIC, TYPE_CATEGORY_SYSTEM
from .utils import to_var_name
from .brick import Brick, BrickProvenance
from .query import Query
from .user_profile import UserProfile

class DataProvider:
    def __init__(self):
        services._init_db_connection()
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
        super().__init__(services.indexdef.get_type_def(TYPE_NAME_BRICK) )

    @staticmethod
    def _load_brick(brick_id):
        brick = Brick.read_dict(
            brick_id,  services.workspace.get_brick_data(brick_id))
        provenance = BrickProvenance('loaded', ['id:%s' % brick.id])
        brick.session_provenance.provenance_items.append(provenance)
        return brick

    def load(self, brick_id):
        return BrickProvider._load_brick(brick_id)
