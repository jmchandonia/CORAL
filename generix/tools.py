import sys
import pandas as pd
from . import services
from .workspace import EntityDataHolder, ProcessDataHolder, BrickDataHolder
from .typedef import TYPE_NAME_PROCESS, TYPE_NAME_BRICK
from .brick import Brick


_FILES = {
    'import_dir': 'data/import/',
    'bricks': [
        {
            'file': 'generic_taxonomic_abundance_fw215_02_100ws.json'
        }, {
            'file': 'generic_mt123_growth_carbon_sources.json'
        }, {
            'file': 'generic_mt94_metals_growth.json'
        }, {
            'file': 'generic_metals_pH_growth.json'
        }, {
            'file': 'generic_tnseq_N2E2.json'
        }, {
            'file': 'generic_field_data_adams.json'
        }, {
            'file': 'generic_otu_id_zhou_100ws.json'
            # }, {
            #     'file': 'generic_otu_count_zhou_100ws.json'
        }, {
            'file': 'generic_otu_id_zhou_corepilot.json'
        }, {
            'file': 'generic_otu_count_zhou_corepilot_271.json'
        }, {
            'file': 'generic_otu_count_zhou_corepilot_106.json'
        }, {
            'file': 'generic_adams_corepilot_271.json'
        }, {
            'file': 'generic_adams_corepilot_106.json'
        }
    ],
    'entities': [
        {
            'file': 'wells_all.tsv',
            'dtype': 'Well',
        },
        {
            'file': 'samples_all.tsv',
            'dtype': 'Sample',
        },
        {
            'file': 'taxa_isolates.tsv',
            'dtype': 'Taxon',
        },
        {
            'file': 'communities_isolates.tsv',
            'dtype': 'Community',
        }
    ],
    'processes': [
        {
            'file': 'process_assay_growth.tsv',
            'ptype': 'Assay Growth'
        },
        {
            'file': 'process_isolates.tsv',
            'ptype': 'Isolation'
        },
        {
            'file': 'process_sampling_all.tsv',
            'ptype': 'Sampling'
        }
    ]
}


def upload_ontologies(argv):
    services.ontology._upload_ontologies()


def neo_delete(argv):
    type_name = argv[0]
    services.neo_service.delete_all(type_name)


def upload_bricks(argv):
    ws = services.workspace
    type_name = TYPE_NAME_BRICK
    try:
        services.es_service.drop_index(type_name)
    except:
        pass
    services.es_service.create_brick_index()

    for file_def in _FILES['bricks']:
        file_name = '../' + _FILES['import_dir'] + file_def['file']

        print('Doing %s: %s' % ('Brick', file_name))
        brick = Brick.read_json(None, file_name)
        data_holder = BrickDataHolder(brick)
        ws.save(object_data_holders=[data_holder])


def upload_entities(argv):
    ws = services.workspace
    for file_def in _FILES['entities']:
        file_name = '../' + _FILES['import_dir'] + file_def['file']
        type_name = file_def['dtype']
        try:
            services.es_service.drop_index(type_name)
        except:
            pass
        services.es_service.create_index(
            services.typedef.get_type_def(type_name))

        print('Doing %s: %s' % (type_name, file_name))
        df = pd.read_csv(file_name, sep='\t')
        i = 0
        print('size=%s' % df.shape[0])
        for _, row in df.iterrows():
            i = i + 1
            if i % 10 == 0:
                print('.', end='', flush=True)
            if i % 100 == 0:
                print(i)

            data = row.to_dict()
            data_holder = EntityDataHolder(type_name, data)
            ws.save(object_data_holders=[data_holder])
        print('Done!')
        print()


def upload_processes(argv):
    ws = services.workspace
    type_name = TYPE_NAME_PROCESS
    services.es_service.drop_index(type_name)
    services.es_service.create_index(
        services.typedef.get_type_def(type_name))

    for file_def in _FILES['processes']:
        process_type = file_def['ptype']
        file_name = '../' + _FILES['import_dir'] + file_def['file']

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
