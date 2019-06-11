from .typedef import TYPE_CATEGORY_STATIC, TYPE_CATEGORY_DYNAMIC, TYPE_CATEGORY_ONTOLOGY, TYPE_NAME_BRICK
from .brick import BrickIndexDocumnet
from . import services



class IndexTypeDef:
    def __init__(self, type_name, type_category, index_prop_defs):
        self.__name = type_name
        self.__category = type_category
        self.__prop_defs = index_prop_defs
    
    @property
    def name(self):
        return self.__name
    
    @property
    def category(self):
        return self.__category

    @property
    def collection_name(self):
        return self.__category + self.__name
    
    @property
    def property_defs(self):
        return self.__prop_defs
    
    @property
    def property_names(self):
        return [pd.name for pd in self.__prop_defs]

    def get_property_def(self, name):
        for pd in self.__prop_defs:
            if pd.name == name:
                return pd
        return None


class IndexPropertyDef:
    def __init__(self, prop_name, prop_scalar_type):
        self.__name = prop_name
        self.__scalar_type = prop_scalar_type

    @property
    def name(self):
        return self.__name
    
    @property
    def scalar_type(self):
        return self.__scalar_type


class IndexTypeDefService:
    def __init__(self):
        self.__type_defs = []

        # do static types
        for name in services.typedef.get_type_names(TYPE_CATEGORY_STATIC):
            type_def = services.typedef.get_type_def(name)
            index_prop_defs = []
            for prop_def in  type_def.property_defs:
                index_prop_defs.append( IndexPropertyDef(prop_def.name, prop_def.type) )
            index_type_def = IndexTypeDef(type_def.name, type_def.category, index_prop_defs)
            self.__type_defs.append(index_type_def)

        # do dynamic types: Brick
        index_prop_defs = []
        for prop_name, prop_scalar_type in BrickIndexDocumnet.properties().items():
            index_prop_defs.append( IndexPropertyDef(prop_name, prop_scalar_type) )
        index_type_def = IndexTypeDef(TYPE_NAME_BRICK, TYPE_CATEGORY_DYNAMIC, index_prop_defs)
        self.__type_defs.append(index_type_def)


    def get_type_names(self, category=None):
        names = []
        for type_def in self.__type_defs:
            if category is not None and type_def.category != category:
                continue
            
            names.append(type_def.name)
        
        return names
    
    def get_type_defs(self, category):
        type_defs = []
        for type_def in self.__type_defs:
            if category is not None and type_def.category != category:
                continue
            
            type_defs.append(type_def)
        
        return type_defs

    def get_type_def(self, type_name):
        for type_def in self.__type_defs:
            if type_def.name == type_name:
                return type_def
        return None




            


