from .brick import read_brick
from . import services
from .typedef import PROCESS_TYPE_NAME


class EntityDataHolder:
    def __init__(self, type_name, data, file_name=None):
        self.__type_name = type_name
        self.__type_def = services.typedef.get_type_def(type_name)
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


class Workspace:
    __ID_PATTERN = '%s%07d'

    def __init__(self):
        self.__dtype_2_id_offset = {}
        self.__id_2_file_name = {}
        self.__id_2_text_id = {}
        self.__file_name_2_id = {}
        self.__text_id_2_id = {}

    def next_id(self, dtype, text_id=None, file_name=None):
        id_offset = self.__dtype_2_id_offset.get(dtype)
        if id_offset is None:
            id_offset = 0
        id_offset += 1
        self.__dtype_2_id_offset[dtype] = id_offset

        obj_id = Workspace.__ID_PATTERN % (dtype, id_offset)

        if text_id is not None:
            self.__text_id_2_id[text_id] = obj_id
            self.__id_2_text_id[obj_id] = text_id
        if file_name is not None:
            self.__file_name_2_id[file_name] = obj_id
            self.__id_2_file_name[obj_id] = file_name

        return obj_id

    def _get_file_name(self, obj_id):
        return self.__id_2_file_name.get(obj_id)

    def _get_text_id(self, obj_id):
        return self.__id_2_text_id.get(obj_id)

    def _get_id(self, text_id=None, file_name=None):
        if text_id is not None:
            return self.__text_id_2_id.get(text_id)
        elif file_name is not None:
            return self.__file_name_2_id.get(file_name)

        return None

    def _get_ids(self, dtype):
        id_offset = self.__dtype_2_id_offset[dtype]
        return [Workspace.__ID_PATTERN % (dtype, x) for x in range(1, id_offset + 1)]

    def get_brick(self, brick_id):
        file_name = self._get_file_name(brick_id)
        return read_brick(brick_id, file_name)

    def save(self, doc):
        '''
            expected format of doc:
            {
                'entity':{
                    # required
                    'type': ...,
                    'data': {...},

                    # optional (for brick)
                    'file_name': ...

                    # will be added in this method
                    'type_def': {},
                    'guid': ...
                },
                'process':{
                    # required
                    'type': ...,
                    'data': {...},

                    # optional (for brick)
                    'file_name': ...

                    # will be added in this method
                    'type_def': {},
                    'guid': ...
                }
            }
            Either entity, or process, or both should be provided 
        '''

        try:
            entity = doc.get('entity')
            process = doc.get('process')

            # attach type definition
            if entity is not None:
                self._attach_type_def(entity)
            if process is not None:
                self._attach_type_def(process)

            # generate GUID
            if entity is not None:
                self._generate_guid(entity)
            if process is not None:
                self._generate_guid(process)

            # validate
            if entity is not None:
                if entity['type'] == 'Brick':
                    self._validate_brick(entity)
                else:
                    self._validate_entity(entity)
            if process is not None:
                self._validate_process(process)

            # store
            if entity is not None:
                if entity['type'] == 'Brick':
                    self._store_brick(entity)
                else:
                    self._store_entity(entity)

            if process is not None:
                self._store_process(process)

            # index in elastic search
            if entity is not None:
                if entity['type'] == 'Brick':
                    self._index_es_brick(entity)
                else:
                    self._index_es_entity(entity)
                self._mark_as_indexed_es(entity)

            if process is not None:
                self._index_es_process(process)
                self._mark_as_indexed_es(process)

            # index in neo4j (brick and entity are treated the same)
            if entity is not None:
                self._index_neo_entity(entity)
                self._mark_as_indexed_neo(entity)

            if process is not None:
                self._index_neo_process(process)
                self._mark_as_indexed_neo(process)

        except:
            pass

    def _attach_type_def(self, entity_or_process):
        pass

    def _generate_guid(self, entity_or_process):
        pass

    def _validate_brick(self, entity):
        pass

    def _validate_entity(self, entity):
        pass

    def _validate_process(self, process):
        pass

    def _store_brick(self, entity):
        pass

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
