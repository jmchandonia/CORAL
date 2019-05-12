import numpy as np
import json
from . import services
from .typedef import TYPE_NAME_PROCESS, TYPE_NAME_BRICK


class DataHolder:
    def __init__(self, type_name, data):
        self.__type_name = type_name
        self.__type_def = services.typedef.get_type_def(self.__type_name)
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
        for i, input_object in enumerate(self.data[ids_prop_name].split(',')):
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

        self.data[ids_prop_name] = ','.join(obj_ids)

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
        self.brick.set_id(val)


class Workspace:
    __ID_PATTERN = '%s%07d'

    def __init__(self, mongo_client):
        self.__mongo_client = mongo_client
        self.__enigma_db = self.__mongo_client.enigma
        self.__dtype_2_id_offset = {}
        self.__init_id_offsets()
        print('Workspace initialized!')

        # self.__dtype_2_id_offset = {}
        # self.__id_2_file_name = {}
        # self.__id_2_text_id = {}
        # self.__file_name_2_id = {}
        # self.__text_id_2_id = {}

    def __init_id_offsets(self):
        registered_type_names = set()

        rows = self.__enigma_db.id.find({})
        for row in rows:
            type_name = row['dtype']
            registered_type_names.add(type_name)
            self.__dtype_2_id_offset[type_name] = row['id_offset']

        for type_name in services.typedef.get_type_names():
            if type_name not in registered_type_names:
                self.__enigma_db.id.insert_one(
                    {'dtype': type_name, 'id_offset': 0})
                self.__dtype_2_id_offset[type_name] = 0

    def next_id(self, type_name):
        id_offset = self.__dtype_2_id_offset[type_name]
        id_offset += 1
        self.__enigma_db.id.update_one(
            {"dtype": type_name},
            {"$set": {"id_offset": id_offset}}
        )
        self.__dtype_2_id_offset[type_name] = id_offset
        return Workspace.__ID_PATTERN % (type_name, id_offset)

    def get_brick_data(self, brick_id):
        return self.__enigma_db.Brick.find_one({'id': brick_id})

    def save_process(self, data_holder):
        self._generate_id(data_holder)
        self._validate_process(data_holder)
        self._store_process(data_holder)

        self._index_es_process(data_holder)
        self._index_neo_process(data_holder)

    def save_data(self, data_holder):
        self._generate_id(data_holder)
        self._validate_object(data_holder)
        self._store_object(data_holder)
        self._index_es_object(data_holder)
        self._index_neo_object(data_holder)

    # def save(self, object_data_holders=None, process_data_holder=None):

    #     # process objects
    #     if object_data_holders is not None:
    #         for data_holder in object_data_holders:
    #             self._generate_id(data_holder)
    #             self._validate_object(data_holder)
    #             self._store_object(data_holder)
    #             self._index_es_object(data_holder)
    #             self._index_neo_object(data_holder)

    #     # process processes
    #     if process_data_holder is not None:
    #         data_holder = process_data_holder
    #         self._generate_id(data_holder)
    #         self._validate_process(data_holder)
    #         self._store_process(data_holder)

    #         self._index_es_process(data_holder)
    #         self._index_neo_process(data_holder)

    def _generate_id(self, data_holder):
        # file_name = data_holder.file_name if data_holder.type_name == 'Brick' else None
        # pk_def = data_holder.type_def.pk_property_def
        # text_id = data_holder.data[pk_def.name] if pk_def is not None else None
        # id = self.next_id(data_holder.type_name,
        #                     text_id=text_id, file_name=file_name)
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

            self.__enigma_db.get_collection(
                data_holder.type_name).insert_one(data_holder.data)
        elif type(data_holder) is BrickDataHolder:
            upk_id = data_holder.brick.name
            data_json = data_holder.brick.to_json()
            data = json.loads(data_json)
            self.__enigma_db.get_collection(
                data_holder.type_name).insert_one(data)

        self._store_object_type_ids(type_name, pk_id, upk_id)

    def _get_pk_id(self, type_name, upk_id):
        res = self.__enigma_db.get_collection('object_type_ids').find_one({
            "type_name": type_name,
            "upk_id": upk_id
        })
        if res is None:
            raise ValueError('Can not find pk_id for %s: %s' %
                             (type_name, upk_id))

        return res['pk_id']

    def _store_object_type_ids(self, type_name, pk_id, upk_id):
        self.__enigma_db.get_collection('object_type_ids').insert_one({
            'type_name': type_name,
            'pk_id': pk_id,
            'upk_id': upk_id
        })

    def delete_all(self):
        for collection_name in self.__enigma_db.collection_names():
            print('drop collection %s' % collection_name)
            self.__enigma_db.drop_collection(collection_name)

    def _store_process(self, data_holder):
        self.__enigma_db.get_collection(
            data_holder.type_name).insert_one(data_holder.data)

    def _index_es_object(self, data_holder):
        if type(data_holder) is EntityDataHolder:
            services.es_service.index_data(data_holder)
        elif type(data_holder) is BrickDataHolder:
            services.es_service.index_brick(data_holder)

    def _index_es_process(self, data_holder):
        services.es_service.index_data(data_holder)

    def _mark_as_indexed_es(self, entity_or_process):
        pass

    def _index_neo_object(self, data_holder):
        if type(data_holder) is EntityDataHolder:
            if data_holder.type_def.for_provenance:
                services.neo_service.index_entity(data_holder)
        elif type(data_holder) is BrickDataHolder:
            services.neo_service.index_brick(data_holder)

    def _index_neo_process(self, data_holder):
        services.neo_service.index_processes(data_holder)

    def _mark_as_indexed_neo(self, entity_or_process):
        pass
