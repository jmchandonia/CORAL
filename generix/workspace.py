from .brick import read_brick


class Workspace:
    ID_PATTERN = '%s%07d'

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

        obj_id = Workspace.ID_PATTERN % (dtype, id_offset)

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
        return [Workspace.ID_PATTERN % (dtype, x) for x in range(1, id_offset + 1)]

    def get_brick(self, brick_id):
        file_name = self._get_file_name(brick_id)
        return read_brick(brick_id, file_name)
