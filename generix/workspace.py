from .brick import read_brick
from . import services
from .typedef import PROCESS_TYPE_NAME


class EntityDataHolder:
    def __init__(self, type_name, data, file_name=None):
        self.__type_name = type_name
        self.__type_def = services.typedef.get_type_def(self.__type_name)
        self.__data = data
        self.__file_name = file_name
        self.__guid = None

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
    def file_name(self):
        return self.__file_name

    @property
    def guid(self):
        return self.__guid

    def set_guid(self, val):
        self.__guid = val


class ProcessDataHolder:
    def __init__(self, process_type_name, data):
        self.__type_name = PROCESS_TYPE_NAME
        self.__process_type_name = process_type_name
        self.__type_def = services.typedef.get_type_def(self.__type_name)
        self.__data = data
        self.__guid = None

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
    def process_type_name(self):
        return self.__process_type_name

    @property
    def guid(self):
        return self.__guid

    def set_guid(self, val):
        self.__guid = val


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

        rows = self.__enigma_db.guid.find({})
        for row in rows:
            type_name = row['dtype']
            registered_type_names.add(type_name)
            self.__dtype_2_id_offset[type_name] = row['id_offset']

        for type_name in services.typedef.get_type_names():
            if type_name not in registered_type_names:
                self.__enigma_db.guid.insert_one(
                    {'dtype': type_name, 'id_offset': 0})
                self.__dtype_2_id_offset[type_name] = 0

    def next_guid(self, type_name):
        id_offset = self.__dtype_2_id_offset[type_name]
        id_offset += 1
        self.__enigma_db.guid.update_one(
            {"dtype": type_name},
            {"$set": {"id_offset": id_offset}}
        )
        self.__dtype_2_id_offset[type_name] = id_offset
        return Workspace.__ID_PATTERN % (type_name, id_offset)

    # def next_id(self, dtype, text_id=None, file_name=None):
    #     id_offset = self.__dtype_2_id_offset.get(dtype)
    #     if id_offset is None:
    #         id_offset = 0
    #     id_offset += 1
    #     self.__dtype_2_id_offset[dtype] = id_offset

    #     obj_id = Workspace.__ID_PATTERN % (dtype, id_offset)

    #     # if text_id is not None:
    #     #     self.__text_id_2_id[text_id] = obj_id
    #     #     self.__id_2_text_id[obj_id] = text_id
    #     # if file_name is not None:
    #     #     self.__file_name_2_id[file_name] = obj_id
    #     #     self.__id_2_file_name[obj_id] = file_name

    #     # return obj_id

    # def _get_file_name(self, obj_id):
    #     return self.__id_2_file_name.get(obj_id)

    # def _get_text_id(self, obj_id):
    #     return self.__id_2_text_id.get(obj_id)

    # def _get_id(self, text_id=None, file_name=None):
    #     if text_id is not None:
    #         return self.__text_id_2_id.get(text_id)
    #     elif file_name is not None:
    #         return self.__file_name_2_id.get(file_name)

    #     return None

    # def _get_ids(self, dtype):
    #     id_offset = self.__dtype_2_id_offset[dtype]
    #     return [Workspace.__ID_PATTERN % (dtype, x) for x in range(1, id_offset + 1)]

    # def get_brick(self, brick_id):
    #     file_name = self._get_file_name(brick_id)
    #     return read_brick(brick_id, file_name)

    def save(self, entity_data_holders=None, process_data_holder=None):

        # process entities
        if entity_data_holders is not None:
            for data_holder in entity_data_holders:

                self._generate_guid(data_holder)
                self._validate_entity(data_holder)
                self._store_entity(data_holder)

                self._index_es_entity(data_holder)
                self._index_neo_entity(data_holder)

        # process processes
        if process_data_holder is not None:
            data_holder = process_data_holder
            self._generate_guid(data_holder)
            self._validate_process(data_holder)
            self._store_process(data_holder)

            self._index_es_process(data_holder)
            self._index_neo_process(data_holder)

    def _generate_guid(self, data_holder):
        # file_name = data_holder.file_name if data_holder.type_name == 'Brick' else None
        # pk_def = data_holder.type_def.pk_property_def
        # text_id = data_holder.data[pk_def.name] if pk_def is not None else None
        # guid = self.next_id(data_holder.type_name,
        #                     text_id=text_id, file_name=file_name)
        guid = self.next_guid(data_holder.type_name)
        data_holder.set_guid(guid)

    # def _validate_brick(self, entity):
    #     pass

    def _validate_entity(self, data_holder):
        data_holder.type_def.validate_data(data_holder.data)

    def _validate_process(self, data_holder):
        data_holder.type_def.validate_data(data_holder.data)

    # def _store_brick(self, entity):
    #     pass

    def _store_entity(self, entity):
        pass

    def _store_process(self, process):
        pass

    def _index_es_brick(self, entity):
        pass

    def _index_es_entity(self, entity):
        pass

    def _index_es_process(self, process):
        pass

    def _mark_as_indexed_es(self, entity_or_process):
        pass

    def _index_neo_entity(self, entity):
        pass

    def _index_neo_process(self, process):
        pass

    def _mark_as_indexed_neo(self, entity_or_process):
        pass
