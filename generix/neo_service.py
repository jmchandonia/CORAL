
import pandas as pd
from . import services


def _to_data_frame(tx, query):
    nodes = []
    for record in tx.run(query):
        items = {}
        for _, node in record.items():
            items['_id'] = node.id
            for entry in node.items():
                items[entry[0]] = entry[1]
        nodes.append(items)
    return pd.DataFrame(nodes)


def _to_target_ids(tx, query, source_ids):
    target_ids = []
    # print('source_ids = ', source_ids)
    for record in tx.run(query, source_ids=source_ids):
        for _, node in record.items():
            target_ids.append(node)
    return target_ids


class Neo4JService:
    def __init__(self, neo4j_client):
        self.__neo4j_client = neo4j_client

    def delete_all(self, type_name=None):
        if type_name is None:
            with self.__neo4j_client.session() as session:
                session.run('MATCH (n) DETACH DELETE n')
        else:
            with self.__neo4j_client.session() as session:
                session.run('MATCH (n : %s) DETACH DELETE n' % type_name)

    @staticmethod
    def _get_type_ids(tx, query, process_id):
        items = {}
        for record in tx.run(query, process_id=process_id):
            for _, node in record.items():
                for dtype in node.labels:
                    ids = items.get(dtype)
                    if ids is None:
                        ids = []
                        items[dtype] = ids
                    ids.append(node.properties['id'])
        return items

    def get_input_type_ids(self, process_id):
        query = 'match(p)-[:PARAM_IN]-(t) where p.id = {process_id}  return t'
        with self.__neo4j_client.session() as session:
            type_items = session.read_transaction(
                Neo4JService._get_type_ids, query, process_id)
        return type_items

    def get_output_type_ids(self, process_id):
        query = 'match(p)-[:HAS_OUTPUT]-(t) where p.id = {process_id}  return t'
        with self.__neo4j_client.session() as session:
            type_items = session.read_transaction(
                Neo4JService._get_type_ids, query, process_id)
        return type_items

    def get_up_process_ids(self, entity_id):
        query = 'match(t)-[:HAS_OUTPUT]-(p) where t.id in {source_ids} return p.id'
        with self.__neo4j_client.session() as session:
            target_ids = session.read_transaction(
                _to_target_ids, query, [entity_id])
        return target_ids

    def get_down_process_ids(self, entity_id):
        query = 'match(t)-[:PARAM_IN]-(p) where t.id in {source_ids} return p.id'
        with self.__neo4j_client.session() as session:
            target_ids = session.read_transaction(
                _to_target_ids, query, [entity_id])
        return target_ids

    def find_linked_ids(self, source_type_name, source_id_field_name,
                        source_ids, target_type_name, target_id_field_name,
                        directed_link=True,
                        direct=True, steps=20):
        link = '-[*1..%s]-' % steps
        if directed_link:
            if direct:
                link = link + '>'
            else:
                link = '<' + link

        query = "match(s:%s)%s(t:%s) where s.%s in {source_ids} return t.%s" % \
            (source_type_name, link, target_type_name,
             source_id_field_name, target_id_field_name)
        # print(query)
        with self.__neo4j_client.session() as session:
            target_ids = session.read_transaction(
                _to_target_ids, query, source_ids)
        return target_ids

    def index_entity(self, data_holder):
        type_def = data_holder.type_def
        type_name = type_def.name
        pk_property_def = type_def.pk_property_def

        id_value = data_holder.data[pk_property_def.name]
        with self.__neo4j_client.session() as session:
            session.run(
                'CREATE (n : %s{id:"%s"})' % (type_name, id_value))

    def index_brick(self, data_holder):
        type_name = data_holder.type_name
        id_value = data_holder.brick.id
        with self.__neo4j_client.session() as session:
            session.run(
                'CREATE (n : %s{id:"%s"})' % (type_name, id_value))

    def index_processes(self, data_holder):
        match_query_items = []
        create_query_items = []

        # create process
        create_query_items.append('(p:Process{id:"%s"})' % (data_holder.id))

        # match input objects
        for i, input_object in enumerate(data_holder.data['input_objects'].split(',')):
            # type_name, upk_id = input_object.split(':')
            # type_name = type_name.strip()
            # upk_id = upk_id.strip()
            # # TODO hack
            # if type_name == 'Condition':
            #     continue
            # if type_name == 'Generic':
            #     type_name = 'Brick'

            # pk_id = services.workspace._get_pk_id(type_name, upk_id)

            type_name, pk_id = input_object.split(':')
            match_query_items.append(
                '(s%s: %s{id:"%s"})' % (i, type_name, pk_id))
            create_query_items.append(
                '(p)<-[:PARAM_IN]-(s%s)' % i)

        # match ouput objects
        for i, output_object in enumerate(data_holder.data['output_objects'].split(',')):
            # type_name, upk_id = output_object.split(':')
            # type_name = type_name.strip()
            # upk_id = upk_id.strip()

            # # TODO hack
            # if type_name == 'Condition':
            #     continue
            # if type_name == 'Generic':
            #     type_name = 'Brick'

            # pk_id = services.workspace._get_pk_id(type_name, upk_id)

            type_name, pk_id = output_object.split(':')
            match_query_items.append(
                '(r%s: %s{id:"%s"})' % (i, type_name, pk_id))
            create_query_items.append(
                '(p)-[:HAS_OUTPUT]->(r%s)' % i)

        query = 'match %s create %s ' % (
            ','.join(match_query_items), ','.join(create_query_items))

        # print('--- Query --')
        # print(query)
        with self.__neo4j_client.session() as session:
            session.run(query)


# match
# 	(t1:Well{id:'Well0003186'}),
# 	(t2:Well{id:'Well0003190'}),
#     (s1:Sample{id:'Sample0006577'})
# create
# 	(p:Process{id:'Process000001',name:'QQQ'}),
#     (p)<-[:PARAM_IN]-(t1),
#     (p)<-[:PARAM_IN]-(t2),
#     (p)-[:PRODUCED]->(s1)
