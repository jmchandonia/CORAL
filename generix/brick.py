import pandas as pn


class Brick:
    def __init__(self):
        pass


class BrickDescriptorCollection:
    def __init__(self, brick_descriptors):
        self.__brick_descriptors = brick_descriptors

    @property
    def items(self):
        return self.__brick_descriptors

    @property
    def size(self):
        return len(self.__brick_descriptors)

    def df(self):
        bd_list = []
        for bd in self.__brick_descriptors:
            bd_list.append({
                'brick_id': bd.brick_id,
                'brick_name': bd.name,
                'data_type': bd.data_type,
                'value_type': bd.value_type,
                'n_dimensions': bd.n_dimensions,
                'shape': bd.shape,
                'data_size': bd.data_size
            })
        return pn.DataFrame(bd_list)


class BrickDescriptor:
    def __init__(self, brick_id, name, description,
                 data_type_term_id, data_type_term_name,
                 n_dimensions, dim_type_term_ids, dim_type_term_names, dim_sizes,
                 value_type_term_id, value_type_term_name):
        self.brick_id = brick_id
        self.name = name
        self.description = description
        self.data_type_term_id = data_type_term_id
        self.data_type_term_name = data_type_term_name
        self.n_dimensions = n_dimensions
        self.dim_type_term_ids = dim_type_term_ids
        self.dim_type_term_names = dim_type_term_names
        self.dim_sizes = dim_sizes
        self.value_type_term_id = value_type_term_id
        self.value_type_term_name = value_type_term_name

        self.data_size = 1
        for ds in self.dim_sizes:
            self.data_size *= ds

    @property
    def data_type(self):
        return '%s<%s>' % (self.data_type_term_name, ','.join(self.dim_type_term_names))

    @property
    def value_type(self):
        return self.value_type_term_name

    @property
    def shape(self):
        return self.dim_sizes

    def __str__(self):
        return 'Name: %s;  Type: %s; Shape: %s' % (self.name, self.data_type, self.shape)
