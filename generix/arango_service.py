from .brick import BrickIndexDocumnet
from .typedef import TYPE_NAME_BRICK
from .ontology import Term

class ArangoService:
    def __init__(self, connection, db_name):
        self.__connection = connection
        self.__db_name = db_name
        self.__db = self.__connection[self.__db_name]
    
    def create_brick_index(self):
        pass

    def index_brick(self, data_holder):
        bid = BrickIndexDocumnet(data_holder.brick)
        doc = vars(bid)

        bind = {'doc': doc, '@collection': data_holder.type_name}
        aql = 'INSERT @doc INTO @@collection'
        self.__db.AQLQuery(aql, bindVars=bind)


    def index_data(self, data_holder):
        type_def = data_holder.type_def

        doc = {}
        all_term_ids = set()
        all_parent_path_term_ids = set()
        for pdef in type_def.property_defs:
            pname = pdef.name
            if pname in data_holder.data:
                value = data_holder.data[pname]
                if pdef.type == 'term':
                    term = Term.parse_term(value)
                    # term.refresh()
                    doc[pname + '_term_id'] = term.term_id
                    doc[pname + '_term_name'] = term.term_name

                    all_term_ids.add(term.term_id)
                    for pid in term.parent_path_ids:
                        all_parent_path_term_ids.add(pid)
                else:
                    doc[pname] = value

        # doc['all_term_ids'] = list(all_term_ids)
        # doc['all_parent_path_term_ids'] = list(all_parent_path_term_ids)

        bind = {'doc': doc, '@collection': type_def.name}
        aql = 'INSERT @doc INTO @@collection'
        self.__db.AQLQuery(aql, bindVars=bind)

    def create_index(self, type_def):
        pass

    def drop_index(self, type_name):
        pass

    def get_type_names(self):        
        names = []
        # for name in self.__es_client.indices.get_alias(ES_INDEX_NAME_PREFIX + '*').keys():
        #     name = name[len(ES_INDEX_NAME_PREFIX):]
        #     names.append(name)
        return names

    def get_entity_properties(self, type_name):
        props = []
    #     es_type = to_es_type_name(type_name)
    #     index_name = ES_INDEX_NAME_PREFIX + es_type
    #     # print('From get_entity_properties:', es_type, index_name)

    #     try:
    #         doc = self.__es_client.indices.get_mapping(index=index_name)
    #         props = list(doc[index_name]['mappings']
    #                      [es_type]['properties'].keys())
    #     except:
    #         props = []
        return props
