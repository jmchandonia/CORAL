import numpy as np
import json
import dumper
import sys
from . import services
from .typedef import TYPE_NAME_PROCESS, TYPE_NAME_BRICK, TYPE_CATEGORY_SYSTEM

_COLLECTION_ID = 'ID'
_COLLECTION_OBJECT_TYPE_ID = 'ObjectTypeID'

class DataHolder:
    def __init__(self, type_name, data):
        self.__type_name = type_name
        self.__type_def = None 
        if self.__type_name not in [TYPE_NAME_BRICK]:
            try:
                self.__type_def = services.typedef.get_type_def(self.__type_name)
            except:
                print ('No typedef for %s' % type_name)
        self.__data = data
        self.__id = None

    @property
    def type_name(self):
        return self.__type_name

    @property
    def type_def(self):
        return self.__type_def

    @property
    def data(self):
        return self.__data

    @property
    def id(self):
        return self.__id

    def set_id(self, val):
        self.__id = val
        self._set_data_id(val)

    def _set_data_id(self, val):
        self.__data['id'] = val


class EntityDataHolder(DataHolder):
    def __init__(self, type_name, data, file_name=None):
        super().__init__(type_name, data)
        self.__file_name = file_name

    @property
    def file_name(self):
        return self.__file_name

    def update_fk_ids(self):
        pass


class ProcessDataHolder(DataHolder):
    def __init__(self, data):
        super().__init__(TYPE_NAME_PROCESS, data)

    def __update_object_ids(self, ids_prop_name):
        obj_ids = []

        for _, input_object in enumerate(self.data[ids_prop_name].split(',')):
            type_name, upk_id = input_object.split(':')
            type_name = type_name.strip()
            upk_id = upk_id.strip()
            # TODO hack
            if type_name == 'Condition':
                continue
            if type_name == 'Generic':
                type_name = 'Brick'

            pk_id = services.workspace._get_pk_id(type_name, upk_id)
            obj_ids.append('%s:%s' % (type_name, pk_id))

        self.data[ids_prop_name] = obj_ids

    def update_object_ids(self):
        self.__update_object_ids('input_objects')
        self.__update_object_ids('output_objects')


class BrickDataHolder(DataHolder):
    def __init__(self, brick):
        super().__init__(TYPE_NAME_BRICK, brick)

    @property
    def brick(self):
        return self.data

    def _set_data_id(self, val):
        self.brick._set_id(val)


class Workspace:
    __ID_PATTERN = '%s%07d'

    def __init__(self, arango_service):
        self.__arango_service = arango_service
        self.__dtype_2_id_offset = {}
        self.__init_id_offsets()
        # print('Workspace initialized!')


        # self.__dtype_2_id_offset = {}
        # self.__id_2_file_name = {}
        # self.__id_2_text_id = {}
        # self.__file_name_2_id = {}
        # self.__text_id_2_id = {}

    def __init_id_offsets(self):
        registered_type_names = set()

        rows = self.__arango_service.find_all(_COLLECTION_ID, TYPE_CATEGORY_SYSTEM)

        for row in rows:
            type_name = row['dtype']
            registered_type_names.add(type_name)
            self.__dtype_2_id_offset[type_name] = row['id_offset']

        for type_name in services.indexdef.get_type_names():
            if type_name not in registered_type_names:
                self.__arango_service.index_doc(
                    {'dtype': type_name, 'id_offset': 0},
                    _COLLECTION_ID, 
                    TYPE_CATEGORY_SYSTEM)
                self.__dtype_2_id_offset[type_name] = 0

    def next_id(self, type_name):
        id_offset = self.__dtype_2_id_offset[type_name]
        id_offset += 1

        aql = """
            FOR x IN @@collection
            FILTER x.dtype == @dtype
            UPDATE x WITH @doc IN @@collection
        """
        aql_bind = {
            '@collection': TYPE_CATEGORY_SYSTEM + _COLLECTION_ID,
            'doc': {'id_offset':id_offset},
            'dtype':  type_name}
        self.__arango_service.db.AQLQuery(aql, bindVars=aql_bind)
        self.__dtype_2_id_offset[type_name] = id_offset
        return Workspace.__ID_PATTERN % (type_name, id_offset)


    def get_brick_data(self, brick_id):
        file_name = services._DATA_DIR + brick_id
        with open(file_name, 'r') as f:
            doc = json.loads(f.read())
        return doc

    def save_process(self, data_holder):
        self._generate_id(data_holder)
        self._validate_process(data_holder)
        self._store_process(data_holder)
        self._index_process(data_holder)

    def save_data_if_not_exists(self, data_holder):
        upk_prop_name = data_holder.type_def.upk_property_def.name
        upk_id = data_holder.data[upk_prop_name]
        try:
            current_pk_id = self._get_pk_id(data_holder.type_name, upk_id)
        except:
            current_pk_id = None
        if current_pk_id is None:
            self.save_data(data_holder)
        else:
            print('skipping %s due to older object' % upk_id)
            # check for consistency
            # for now throw an error, although we may want to upsert instead
            # data_holder_2 = EntityDataHolder(data_holder.type_name,
            # data_holder.data)
            # data_holder_2.set_id(current_pk_id)
            # self._load_object(data_holder_2)
            # print("new data")
            # dumper.dump(data_holder)
            # print("old data")
            # dumper.dump(data_holder_2)

    def save_data(self, data_holder):
        self._generate_id(data_holder)
        self._validate_object(data_holder)
        self._store_object(data_holder)
        self._index_object(data_holder)

    def _generate_id(self, data_holder):
        id = self.next_id(data_holder.type_name)
        data_holder.set_id(id)

    def _validate_object(self, data_holder):
        if type(data_holder) is EntityDataHolder:
            data_holder.type_def.validate_data(data_holder.data)
        elif type(data_holder) is BrickDataHolder:
            pass

    def _validate_process(self, data_holder):
        # data_holder.type_def.validate_data(data_holder.data)

        # Check for NaN
        for key, value in data_holder.data.items():
            if value != value:
                data_holder.data[key] = None

    def _store_object(self, data_holder):
        type_name = data_holder.type_name
        pk_id = data_holder.id
        upk_id = None

        if type(data_holder) is EntityDataHolder:
            upk_prop_name = data_holder.type_def.upk_property_def.name
            upk_id = data_holder.data[upk_prop_name]

            # self.__enigma_db.get_collection(
            #     data_holder.type_name).insert_one(data_holder.data)
        elif type(data_holder) is BrickDataHolder:
            upk_id = data_holder.brick.name
            brick_id = data_holder.brick.id
            data_json = data_holder.brick.to_json()
            data = json.loads(data_json)

            file_name = services._DATA_DIR + brick_id
            with open(file_name, 'w') as outfile:  
                json.dump(data, outfile)

        self._store_object_type_ids(type_name, pk_id, upk_id)

    def _load_object(self, data_holder):
        pk_id = data_holder.id
        aql = 'RETURN DOCUMENT(@@collection/@pk_id)'
        aql_bind = {
            '@collection': TYPE_CATEGORY_SYSTEM + _COLLECTION_OBJECT_TYPE_ID,
            'pk_id': pk_id
        }
        res = self.__arango_service.find(aql,aql_bind)
        type2objects = {}
        for row in res:
            _id = row['_id']
            type_name = _id.split('/')[0][4:]
        
            objs = type2objects.get(type_name)
            if objs is None:
                objs = []
                type2objects[type_name] = objs
            objs.append(row)
        # dumper.dump(type2objects)

    def _get_pk_id(self, type_name, upk_id):

        aql = 'FOR x IN @@collection FILTER x.type_name == @type_name and x.upk_id == @upk_id return x'
        aql_bind = {
            '@collection': TYPE_CATEGORY_SYSTEM + _COLLECTION_OBJECT_TYPE_ID,
            'type_name': type_name,
            'upk_id': upk_id
        }
        # print(str(aql_bind))

        res = self.__arango_service.find(aql,aql_bind)
        if len(res) == 0:
            raise ValueError('Can not find pk_id for %s: %s' %
                             (type_name, upk_id))
        if len(res) > 1:
            raise ValueError('There is more than one pk_id for %s: %s' %
                             (type_name, upk_id))

        res = res[0]
        return res['pk_id']

    def _store_object_type_ids(self, type_name, pk_id, upk_id):
        self.__arango_service.index_doc(
            {
            'type_name': type_name,
            'pk_id': pk_id,
            'upk_id': upk_id
            },
            _COLLECTION_OBJECT_TYPE_ID,
            TYPE_CATEGORY_SYSTEM
        )

    def _store_process(self, data_holder):
        pass
        # TODO
        # self.__enigma_db.get_collection(
        #     data_holder.type_name).insert_one(data_holder.data)

    def _index_object(self, data_holder):
        if type(data_holder) is EntityDataHolder:
            services.arango_service.index_data(data_holder)
        elif type(data_holder) is BrickDataHolder:
            services.arango_service.index_brick(data_holder)

    def _index_process(self, data_holder):
        
        # create a record in the SYS_Process table
        self.__arango_service.index_data(data_holder)

        process = data_holder.data
        process_db_id = '%s/%s' % (data_holder.type_def.collection_name, data_holder.id) 
        # sys.stderr.write('process_dbid = '+str(process_db_id)+'\n')
        
        # Do input objects
        for input_object in process['input_objects']:
            type_name, obj_id = input_object.split(':')
            type_def = services.indexdef.get_type_def(type_name)
            # sys.stderr.write('from = '+str(type_def.collection_name+':'+type_name+'/'+obj_id)+'\n')

            self.__arango_service.index_doc(
                {
                    '_from': '%s/%s' % (type_def.collection_name, obj_id),
                    '_to': process_db_id
                }, 'ProcessInput', TYPE_CATEGORY_SYSTEM
            )      

        # Do output objects
        for output_object in process['output_objects']:
            type_name, obj_id = output_object.split(':')
            type_def = services.indexdef.get_type_def(type_name)
            # sys.stderr.write('to = '+str(type_def.collection_name+':'+type_name+'/'+obj_id)+'\n')

            self.__arango_service.index_doc(
                {
                    '_from': process_db_id,
                    '_to': '%s/%s' % (type_def.collection_name, obj_id) 
                }, 'ProcessOutput', TYPE_CATEGORY_SYSTEM
            )      
