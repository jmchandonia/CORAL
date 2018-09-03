

class Neo4JService:
    def __init__(self, neo4j_client):
        self.__neo4j_client = neo4j_client

    def delete_all(self, type_name):
        with self.__neo4j_client.session() as session:
            session.run('MATCH (n : %s) DETACH DELETE n' % type_name)

    def index_entities(self, data_holder):
        type_def = data_holder.type_def
        type_name = type_def.name
        pk_property_def = type_def.pk_property_def

        id_value = data_holder.data[pk_property_def.name]
        with self.__neo4j_client.session() as session:
            session.run(
                'CREATE (n : %s{id:"%s"})' % (type_name, id_value))

    def index_processes(self, data_holder):
        pass
