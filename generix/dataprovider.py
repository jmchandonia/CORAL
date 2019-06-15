from . import services
from .typedef import TYPE_NAME_BRICK, TYPE_CATEGORY_DYNAMIC, TYPE_CATEGORY_STATIC
from .utils import to_var_name
from .brick import Brick, BrickProvenance
from .query import Query

class DataProvider:
    def __init__(self):
        self.__etities_provider = EntitiesProvider()
        self.__generics_provider = GenericsProvider()
        self.__reports = DataReports()

    @property
    def ontology(self):
        return services.ontology

    @property
    def core_types(self):
        return self.__etities_provider

    @property
    def genx_types(self):
        return self.__generics_provider

    @property
    def user_profile(self):
        return services.user_profile

    @property
    def reports(self):
        return self.__reports

    def _get_type_provider(self, type_name):

        type_def = services.indexdef.get_type_def(type_name)
        provider = None        
        if type_name == TYPE_NAME_BRICK:
            provider = BrickProvider()        
        else:
            provider = EntityProvider(type_def)
        return provider


class DataReports:

    @property
    def brick_types(self):
        return self.__brick_term_stat('data_type_term_id' )
        
    @property
    def brick_dim_types(self):
        return self.__brick_term_stat('dim_type_term_ids' )

    @property
    def brick_data_var_types(self):
        return self.__brick_term_stat('value_type_term_id' )

    def __brick_term_stat(self, term_id_prop_name):
        itd = services.indexdef.get_type_def(TYPE_NAME_BRICK)
        return services.ontology.term_stat( itd, term_id_prop_name)

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

    def load(self, brick_id):
        brick = Brick.read_dict(
            brick_id,  services.workspace.get_brick_data(brick_id))
        provenance = BrickProvenance('loaded', ['id:%s' % brick.id])
        brick.session_provenance.provenance_items.append(provenance)
        return brick

