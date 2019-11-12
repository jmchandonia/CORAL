import sys
import os
import json
import traceback
import pandas as pd
from . import services
from .workspace import EntityDataHolder, ProcessDataHolder, BrickDataHolder
from .typedef import TYPE_NAME_PROCESS, TYPE_NAME_BRICK, TYPE_CATEGORY_STATIC
from .brick import Brick


def init_system(argv=None):
    init_system_collections()
    upload_ontologies()
    upload_bricks()
    upload_core()
    upload_processes()

def init_system_collections(argv=None):
    services._init_db_connection()    
    _try_init_collection('SYS_ID',[
        {   
            'fields':['dtype'],
            'type':'hash',
            'unique': True
        }])
    _try_init_collection('SYS_ObjectTypeID',[
        {   
            'fields':['type_name', 'upk_id'],
            'type'  : 'hash',
            'unique': True
        }])
    _try_init_collection('SYS_UserProfile',[])

def _try_init_collection(collection_name, indices):
    print('Init system collection: %s' % collection_name)
    db = services.arango_service.db
    try:
        db.createCollection(name=collection_name)
    except:
        print('Can not create collection: %s' % collection_name)

    # Ensure indicies
    collection = db[collection_name]
    for ind in indices:
        if ind['type'] == 'hash':
            collection.ensureHashIndex(ind['fields'], unique=ind['unique'])
        
def upload_ontologies(argv=None):
    services.IN_ONTOLOGY_LOAD_MODE = True
    services._init_services()
    try:
        services.ontology._upload_ontologies(config_fname=services._UPLOAD_CONFIG_FILE)
    finally:
        services.IN_ONTOLOGY_LOAD_MODE = False

def _get_upload_config_doc():
    with open(services._UPLOAD_CONFIG_FILE, 'r') as f:
        doc = json.loads(f.read())
    return doc

def upload_bricks(argv=None):
    services._init_services()
    ws = services.workspace

    itd = services.indexdef.get_type_def(TYPE_NAME_BRICK)
    itd._ensure_init_index()
    
    doc = _get_upload_config_doc()
    for file_def in doc['bricks']:
        if 'ignore' in file_def: continue
        try:
            file_name = os.path.join(services._IMPORT_DIR_BRICK, file_def['file'])
            print('Doing %s: %s' % ('Brick', file_name))
            brick = Brick.read_json(None, file_name)
            data_holder = BrickDataHolder(brick)
            ws.save_data(data_holder)
        except Exception as e:
            print('Error: ', e)


def upload_core(argv=None):
    services._init_services()
    ws = services.workspace
    doc = _get_upload_config_doc()

    for file_def in doc['entities']:
        if 'ignore' in file_def: continue
        try:
            file_name = os.path.join(services._IMPORT_DIR_ENTITY, file_def['file'])
            type_name = file_def['dtype']
            index_type_def = services.indexdef.get_type_def(type_name)
            index_type_def._ensure_init_index()

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


def upload_processes(argv=None):
    services._init_services()
    ws = services.workspace
    index_type_def = services.indexdef.get_type_def(TYPE_NAME_PROCESS)
    index_type_def._ensure_init_index()

    doc = _get_upload_config_doc()

    for file_def in doc['processes']:
        if 'ignore' in file_def: continue
        try:
            process_type = file_def['ptype']
            file_name = os.path.join(services._IMPORT_DIR_PROCESS, file_def['file'])

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
                    traceback.print_exc()
        except Exception as e:
            print('Error:', e)
            traceback.print_exc()
        print('Done!')
        print()

def delete_core(argv=None):
    for type_def in services.indexdef.get_type_defs(category=TYPE_CATEGORY_STATIC):
        print('Removing %s ' % type_def.collection_name)
        try:
            services.arango_service.drop_index(type_def)
        except:
            pass


def delete_bricks(argv=None):
    type_def = services.indexdef.get_type_def(TYPE_NAME_BRICK)
    try:
        services.arango_service.drop_index(type_def)
    except:
        pass


if __name__ == '__main__':
    # print ('Hi')
    method = sys.argv[1]
    print('method = ', method)
    globals()[method](sys.argv[2:])
