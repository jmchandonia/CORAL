import sys
import pandas as pd
from . import services
from .workspace import EntityDataHolder, ProcessDataHolder, BrickDataHolder
from .typedef import TYPE_NAME_PROCESS, TYPE_NAME_BRICK, TYPE_CATEGORY_STATIC
from .brick import Brick

_FILES = {
    # 'import_dir': '../../data/import/',
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
        }, {
            #	    'file': 'generic_field_data_hazen_post100ws.json'
            #	}, {
            'file': 'generic_field_insitu_hach_hazen.json'
        }, {
            'file': 'generic_field_insitu_hazen.json'
        }, {
            'file': 'generic_field_data_adams.json'
        }, {
            #	    'file': 'generic_otu_id_zhou_100ws.json'
            #	}, {
            #            'file': 'generic_otu_count_zhou_100ws.json'
            #        }, {
            'file': 'generic_otu_id_zhou_corepilot.json'
        }, {
            'file': 'generic_otu_count_zhou_corepilot_271.json'
        }, {
            'file': 'generic_otu_count_zhou_corepilot_106.json'
        }, {
            'file': 'generic_hazen_aquatroll600_300.json'
        }, {
            'file': 'generic_hazen_aquatroll600_835.json'
        }, {
            'file': 'generic_corepilot_dapi_271.json'
        }, {
            'file': 'generic_corepilot_dapi_106.json'
        }, {
            'file': 'generic_corepilot_boncat_271.json'
        }, {
            'file': 'generic_corepilot_boncat_106.json'
        }, {
            'file': 'generic_adams_corepilot_271.json'
        }, {
            'file': 'generic_adams_corepilot_106.json'
        }
    ],
    'entities': [
        {
            'file': 'wells_all.tsv',
            'dtype': 'Well'
        }, {
            'file': 'samples_all.tsv',
            'dtype': 'Sample'
        }, {
            'file': 'strains_isolates.tsv',
            'dtype': 'Strain'
        }, {
            'file': 'communities_isolates.tsv',
            'dtype': 'Community'
        }, {
            'file': 'communities_corepilot_active.tsv',
            'dtype': 'Community'
        }, {
            'file': 'taxa_zhou_100ws.tsv',
            'dtype': 'Taxon'
        }, {
            'file': 'taxa_zhou_corepilot.tsv',
            'dtype': 'Taxon'
        }, {
            'file': 'otus_zhou_100ws.tsv',
            'dtype': 'OTU'
        }, {
            'file': 'otus_zhou_corepilot.tsv',
            'dtype': 'OTU'
        }, {
            'file': 'condition_tnseq.tsv',
            'dtype': 'Condition'
        }, {
            'file': 'condition_isolates.tsv',
            'dtype': 'Condition'
        }, {
            'file': 'condition_filters.tsv',
            'dtype': 'Condition'
        }, {
            'file': 'kbase_reads_isolates.tsv',
            'dtype': 'Reads'
        }, {
            'file': 'kbase_reads_wgs.tsv',
            'dtype': 'Reads'
        }, {
            'file': 'kbase_reads_100ws.tsv',
            'dtype': 'Reads'
        }, {
            'file': 'kbase_reads_corepilot.tsv',
            'dtype': 'Reads'
        }, {
            'file': 'kbase_assemblies.tsv',
            'dtype': 'Assembly'
        }, {
            'file': 'kbase_genomes.tsv',
            'dtype': 'Genome'
        }, {
            'file': 'kbase_genes_isolates.tsv',
            'dtype': 'Gene'
        }, {
            'file': 'tnseq_library.tsv',
            'dtype': 'TnSeq_Library'
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
            'file': 'process_sequence_corepilot_16S.tsv',
            'ptype': '16S Sequencing'
        }, {
            'file': 'process_filter_100ws.tsv',
            'ptype': 'Filter'
        }, {
            'file': 'process_dapi_corepilot_271.tsv',
            'ptype': 'DAPI Enrichment'
        }, {
            'file': 'process_dapi_corepilot_106.tsv',
            'ptype': 'DAPI Enrichment'
        }, {
            'file': 'process_boncat_corepilot_271.tsv',
            'ptype': 'BONCAT Enrichment'
        }, {
            'file': 'process_boncat_corepilot_106.tsv',
            'ptype': 'BONCAT Enrichment'
        }, {
            'file': 'process_dapi_count_corepilot_271.tsv',
            'ptype': 'Assay Cell Counts'
        }, {
            'file': 'process_dapi_count_corepilot_106.tsv',
            'ptype': 'Assay Cell Counts'
        }, {
            'file': 'process_boncat_count_corepilot_271.tsv',
            'ptype': 'Assay Cell Counts'
        }, {
            'file': 'process_boncat_count_corepilot_106.tsv',
            'ptype': 'Assay Cell Counts'
        }, {
            #	    'file': 'process_otu_inference_zhou_100ws.tsv',
            #	    'ptype': 'Classify OTUs'
            #	}, {
            'file': 'process_otu_inference_zhou_corepilot.tsv',
            'ptype': 'Classify OTUs'
        }, {
            'file': 'process_hazen_aquatroll.tsv',
            'ptype': 'Assay Geochemistry'
        }, {
            'file': 'process_environmental_measurements_hazen.tsv',
            'ptype': 'Assay Environment'
        }, {
            'file': 'process_environmental_measurements_hach_hazen.tsv',
            'ptype': 'Assay Geochemistry'
        }, {
            #	    'file': 'process_environmental_measurements_hazen_post100ws.tsv',
            #	    'ptype': 'Assay Geochemistry'
            #	}, {
            'file': 'process_environmental_measurements_adams_corepilot.tsv',
            'ptype': 'Assay Environment'
        }, {
            'file': 'process_environmental_measurements_adams.tsv',
            'ptype': 'Assay Environment'
        }
    ]
}


def upload_ontologies(argv):
    pass
    # TODO
    # services.IN_ONTOLOGY_LOAD_MODE = True
    # try:
    #     services.ontology._upload_ontologies()
    # finally:
    #     services.IN_ONTOLOGY_LOAD_MODE = False


def neo_delete(argv):
    pass
    # TODO
    # if len(argv) > 0:
    #     services.neo_service.delete_all(type_name=argv[0])
    # else:
    #     services.neo_service.delete_all()


def delete_core(argv):
    for type_def in services.indexdef.get_type_defs(category=TYPE_CATEGORY_STATIC):
        print('Removing %s ' % type_def.collection_name)
        try:
            services.arango_service.drop_index(type_def)
        except:
            pass


def delete_bricks(argv):
    type_def = services.indexdef.get_type_def(TYPE_NAME_BRICK)
    try:
        services.arango_service.drop_index(type_def)
    except:
        pass


def upload_bricks(argv):
    ws = services.workspace
    try:
        services.arango_service.create_brick_index()
    except:
        print('\t Collection is present')


    for file_def in _FILES['bricks']:
        try:
            file_name = _FILES['import_dir'] + file_def['file']

            print('Doing %s: %s' % ('Brick', file_name))
            brick = Brick.read_json(None, file_name)
            data_holder = BrickDataHolder(brick)
            ws.save_data(data_holder)
        except Exception as e:
            print('Error: ', e)


def upload_core(argv):
    ws = services.workspace
    for file_def in _FILES['entities']:
        try:
            file_name =  _FILES['import_dir'] + file_def['file']
            type_name = file_def['dtype']
            type_def = services.indexdef.get_type_def(type_name)
            try:
                services.arango_service.create_index(type_def)
            except:
                print('\t Collection is present')

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
        # TODO: switch to type_def
        services.arango_service.drop_index(type_name)
    except:
        pass

    # TODO: switch to type_def
    services.arango_service.create_index(
        services.typedef.get_type_def(type_name))

    for file_def in _FILES['processes']:
        try:
            process_type = file_def['ptype']
            file_name =  _FILES['import_dir'] + file_def['file']

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


if __name__ == '__main__':
    # print ('Hi')
    method = sys.argv[1]
    print('method = ', method)
    globals()[method](sys.argv[2:])
