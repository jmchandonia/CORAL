import sys
import pandas as pd
from . import services
from .brick import read_brick
from .provenance import _FILES
from .workspace import EntityDataHolder, ProcessDataHolder


def upload_ontologies(argv):
    services.ontology._upload_ontologies()


def upload_entities(argv):
    ws = services.workspace
    for file_def in _FILES['entities']:
        file_name = '../' + file_def['file']
        type_name = file_def['dtype']
        services.es_service.drop_index(type_name)
        services.es_service.create_index(
            services.typedef.get_type_def(type_name))

        print('Doing %s: %s' % (type_name, file_name))
        df = pd.read_csv(file_name, sep='\t')
        for _, row in df.iterrows():
            data = row.to_dict()
            data_holder = EntityDataHolder(type_name, data)
            ws.save(entity_data_holders=[data_holder])


def upload_processes(argv):
    ws = services.workspace
    for file_def in _FILES['processes']:
        process_type = file_def['ptype']
        file_name = '../' + file_def['file']

        print('Doing %s: %s' % (process_type, file_name))
        df = pd.read_csv(file_name, sep='\t')
        for _, row in df.iterrows():
            data = row.to_dict()
            data_holder = ProcessDataHolder(process_type, data)
            ws.save(process_data_holder=data_holder)


def load_entity_from_neo_to_esearch(argv):
    neo_dtype = argv[0]
    es_dtype = neo_dtype.lower()
    print('from load_entity_from_neo_to_esearch:', neo_dtype)

    es_index_name = 'generix-entity-' + es_dtype

    # drop index
    es_client = services._es_client
    try:
        es_client.indices.delete(index=es_index_name)
    except:
        pass

    # get data
    df = services.neo_search._list_data('match(t:%s) return t' % neo_dtype)

    # upload data
    for _, row in df.iterrows():
        doc = row.to_dict()
        try:
            del doc['_id']
        except:
            pass
        if 'id' in doc:
            doc['entity_id'] = doc['id']
            del doc['id']

        es_client.index(
            index=es_index_name, doc_type=es_dtype, body=doc)


# def es_index_bricks():

#     services.es_indexer.drop_index()
#     services.es_indexer.create_index()

#     df = pd.read_csv('data/import/generic_index.tsv', sep='\t')
#     for file_name in df[df.is_heterogeneous == 0].filename.values:
#         file_name = 'data/import/' + file_name

#         print('doing %s' % (file_name))
#         brick = read_brick(0, file_name)
#         brick.id = services.workspace.next_id(
#             'Brick', text_id=brick.name, file_name=file_name)
#         services.es_indexer.index_brick(brick)


if __name__ == '__main__':
    method = sys.argv[1]
    print('method = ', method)
    globals()[method](sys.argv[2:])
