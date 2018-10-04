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
            'file': 'generic_isolates_16S.json'
        }, {
            'file': 'generic_mt123_growth_carbon_sources.json'
        }, {
            'file': 'generic_mt94_metals_growth.json'
        }, {
            'file': 'generic_metals_pH_growth.json'
        }, {
            'file': 'generic_tnseq_N2E2.json'
            # }, {
            #KeyError: 'oterm_ref'
            #     'file': 'generic_field_data_hazen_post100ws.json'
        }, {
            'file': 'generic_field_data_adams.json'
        }, {
            'file': 'generic_otu_id_zhou_100ws.json'
        }, {
            #            'file': 'generic_otu_count_zhou_100ws.json'
            #        }, {
            #	    'file': 'generic_otu_id_zhou_corepilot.json'
            #	}, {
            #	    'file': 'generic_otu_count_zhou_corepilot_271.json'
            #	}, {
            #	    'file': 'generic_otu_count_zhou_corepilot_106.json'
            #	}, {

            # ValueError: cannot reshape array of size 5910 into shape (6,5910)
            'file': 'generic_hazen_aquatroll600_300.json'
        }, {

            # ValueError: cannot reshape array of size 3475 into shape (6,3475)
            'file': 'generic_hazen_aquatroll600_835.json'
        }, {
            'file': 'generic_adams_corepilot_271.json'
        }, {
            'file': 'generic_adams_corepilot_106.json'
        }
    ],
    'entities': [
        {
            #     'file': 'wells_all.tsv',
            #     'dtype': 'Well'
            # }, {
            #     'file': 'samples_all.tsv',
            #     'dtype': 'Sample'
            # }, {
            #     'file': 'strains_isolates.tsv',
            #     'dtype': 'Strain'
            # }, {
            #     'file': 'communities_isolates.tsv',
            #     'dtype': 'Community'
            # }, {
            #     'file': 'taxa_zhou_100ws.tsv',
            #     'dtype': 'Taxon'
            # }, {
            #     'file': 'taxa_zhou_corepilot.tsv',
            #     'dtype': 'Taxon'
            # }, {
            #     'file': 'otus_zhou_100ws.tsv',
            #     'dtype': 'OTU'
            # }, {
            'file': 'otu_zhou_corepilot.tsv',
            'dtype': 'OTU'
            # }, {
            #     'file': 'condition_tnseq.tsv',
            #     'dtype': 'Condition'
            # }, {
            #     'file': 'condition_isolates.tsv',
            #     'dtype': 'Condition'
            # }, {
            #     'file': 'condition_filters.tsv',
            #     'dtype': 'Condition'
            # }, {
            #     'file': 'kbase_reads_isolates.tsv',
            #     'dtype': 'KBase_Reads'
            # }, {
            #     'file': 'kbase_reads_wgs.tsv',
            #     'dtype': 'KBase_Reads'
            # }, {
            #     'file': 'kbase_reads_100ws.tsv',
            #     'dtype': 'KBase_Reads'
            # }, {
            #     'file': 'kbase_assemblies.tsv',
            #     'dtype': 'KBase_Assembly'
            # }, {
            #     'file': 'kbase_genomes.tsv',
            #     'dtype': 'KBase_Genome'
            # }, {
            #     'file': 'kbase_genes_isolates.tsv',
            #     'dtype': 'KBase_Gene'
            # }, {
            #     'file': 'tnseq_library.tsv',
            #     'dtype': 'TnSeq_Library'
        }
    ],
    'processes': [
        {
            'file': 'process_assay_growth.tsv',
            'ptype': 'Assay Growth'
        }, {
            'file': 'process_isolates.tsv',
            'ptype': 'Isolation'
        }, {
            'file': 'process_sampling_all.tsv',
            'ptype': 'Sampling'
        }, {
            'file': 'process_annotate_isolates.tsv',
            'ptype': 'Genome Annotation'
        }, {
            'file': 'process_assemble_isolates.tsv',
            'ptype': 'Genome Assembly'
        }, {
            'file': 'process_assay_tnseq.tsv',
            'ptype': 'Assay Fitness'
        }, {
            'file': 'process_otu_inference.tsv',
            'ptype': 'Taxonomic Inference'
        }, {
            'file': 'process_sequencing_16S_isolates.tsv',
            'ptype': '16S Sequencing'
        }, {
            'file': 'process_sequencing_shotgun.tsv',
            'ptype': 'Shotgun Sequencing'
        }, {
            'file': 'process_tnseq.tsv',
            'ptype': 'Build TnSeq Library'
        }, {
            'file': 'process_assay_tnseq.tsv',
            'ptype': 'Assay Fitness'
        }, {
            'file': 'process_sequence_100ws_16S.tsv',
            'ptype': '16S Sequencing'
        }, {
            'file': 'process_filter_100ws.tsv',
            'ptype': 'Filter'
        }, {
            'file': 'process_otu_inference_zhou_100ws.tsv',
            'ptype': 'Classify OTUs'
        }, {
            'file': 'process_hazen_aquatroll.tsv',
            'ptype': 'Assay Geochemistry'
        }, {
            'file': 'process_environmental_measurements_hazen_post100ws.tsv',
            'ptype': 'Assay Geochemistry'
        }, {
            'file': 'process_environmental_measurements_adams_corepilot.tsv',
            'ptype': 'Assay Environment'
        }, {
            'file': 'process_environmental_measurements_adams.tsv',
            'ptype': 'Assay Environment'
        }
    ]
}


# _FILES = {
#     'import_dir': 'data/import/',
#     'bricks': [
#         {
#             'file': 'generic_taxonomic_abundance_fw215_02_100ws.json'
#         }, {
#             'file': 'generic_mt123_growth_carbon_sources.json'
#         }, {
#             'file': 'generic_mt94_metals_growth.json'
#         }, {
#             'file': 'generic_metals_pH_growth.json'
#         }, {
#             'file': 'generic_tnseq_N2E2.json'
#         }, {
#             'file': 'generic_field_data_adams.json'
#         }, {
#             'file': 'generic_otu_id_zhou_100ws.json'
#             # }, {
#             #     'file': 'generic_otu_count_zhou_100ws.json'
#         }, {
#             'file': 'generic_otu_id_zhou_corepilot.json'
#         }, {
#             'file': 'generic_otu_count_zhou_corepilot_271.json'
#         }, {
#             'file': 'generic_otu_count_zhou_corepilot_106.json'
#         }, {
#             'file': 'generic_adams_corepilot_271.json'
#         }, {
#             'file': 'generic_adams_corepilot_106.json'
#         }
#     ],
#     'entities': [
#         {
#             'file': 'wells_all.tsv',
#             'dtype': 'Well',
#         }, {
#             'file': 'samples_all.tsv',
#             'dtype': 'Sample',
#         }, {
#             'file': 'strains_isolates.tsv',
#             'dtype': 'Strain',
#         }, {
#             'file': 'communities_isolates.tsv',
#             'dtype': 'Community',
#         }
#     ],
#     'processes': [
#         {
#             'file': 'process_assay_growth.tsv',
#             'ptype': 'Assay Growth'
#         }, {
#             'file': 'process_isolates.tsv',
#             'ptype': 'Isolation'
#         }, {
#             'file': 'process_sampling_all.tsv',
#             'ptype': 'Sampling'
#         }, {
#             'file': 'process_environmental_measurements_adams.tsv',
#             'ptype': 'Environmental Measurements'
#         }
#     ]
# }


def upload_ontologies(argv):
    services.IN_ONTOLOGY_LOAD_MODE = True
    try:
        services.ontology._upload_ontologies()
    finally:
        services.IN_ONTOLOGY_LOAD_MODE = False


def neo_delete(argv):
    if len(argv) > 0:
        services.neo_service.delete_all(type_name=argv[0])
    else:
        services.neo_service.delete_all()


def mongo_delete(argv):
    services.workspace.delete_all()


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
        ws.save_data(data_holder)


def upload_entities(argv):
    ws = services.workspace
    for file_def in _FILES['entities']:
        try:
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
                try:
                    i = i + 1
                    if i % 50 == 0:
                        print('.', end='', flush=True)
                    if i % 500 == 0:
                        print(i)

                    data = row.to_dict()
                    data_holder = EntityDataHolder(type_name, data)
                    ws.save_data(data_holder)
                except Exception as e:
                    print('Error:', e)
        except Exception as e:
            print('Error:', e)

        print('Done!')
        print()


def upload_processes(argv):
    ws = services.workspace
    type_name = TYPE_NAME_PROCESS
    try:
        services.es_service.drop_index(type_name)
    except:
        pass
    services.es_service.create_index(
        services.typedef.get_type_def(type_name))

    for file_def in _FILES['processes']:
        try:
            process_type = file_def['ptype']
            file_name = '../' + _FILES['import_dir'] + file_def['file']

            print('Doing %s: %s' % (process_type, file_name))
            df = pd.read_csv(file_name, sep='\t')
            i = 0
            for _, row in df.iterrows():
                try:
                    i = i + 1
                    if i % 50 == 0:
                        print('.', end='', flush=True)
                    if i % 500 == 0:
                        print(i)

                    data = row.to_dict()
                    data_holder = ProcessDataHolder(data)
                    data_holder.update_object_ids()
                    ws.save_process(data_holder)
                except Exception as e:
                    print('Error:', e)
        except Exception as e:
            print('Error:', e)
        print('Done!')
        print()


# def load_entity_from_neo_to_esearch(argv):
#     neo_dtype = argv[0]
#     es_dtype = neo_dtype.lower()
#     print('from load_entity_from_neo_to_esearch:', neo_dtype)

#     es_index_name = 'generix-entity-' + es_dtype

#     # drop index
#     es_client = services._es_client
#     try:
#         es_client.indices.delete(index=es_index_name)
#     except:
#         pass

#     # get data
#     df = services.neo_search._list_data('match(t:%s) return t' % neo_dtype)

#     # upload data
#     for _, row in df.iterrows():
#         doc = row.to_dict()
#         try:
#             del doc['_id']
#         except:
#             pass
#         if 'id' in doc:
#             doc['entity_id'] = doc['id']
#             del doc['id']

#         es_client.index(
#             index=es_index_name, doc_type=es_dtype, body=doc)


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
