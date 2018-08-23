import json
import numpy as np
import pandas as pn
from .ontology import Term
from . import services


def read_brick(brick_id, file_name):
    json_data = json.loads(open(file_name).read())
    return Brick(brick_id, json_data=json_data)


class BrickDimensionVariable:
    def __init__(self, json_data=None):
        term = json_data['value_type']
        self.type_term = Term(
            term['oterm_ref'], term_name=term['oterm_name'])

        # term = json_data['value_units']
        # self.units_term = Term(
        #     term['oterm_ref'], term_name=term['oterm_name'])

        term_value_type = json_data['values']['scalar_type']
        if term_value_type == 'oterm_ref':
            term_value_type = 'oterm_refs'
            self.values = []
            for term_id in json_data['values'][term_value_type]:
                self.values.append(Term(term_id))
        else:
            term_value_type += '_values'
            self.values = json_data['values'][term_value_type]

    def _collect_property_terms(self, id2terms):
        id2terms[self.type_term.term_id] = self.type_term

    def _collect_value_terms(self, id2terms):
        for val in self.values:
            if type(val) is Term:
                term = val
                id2terms[term.term_id] = term

    def _collect_all_term_values(self, term_id_2_values):
        term_id = self.type_term.term_id
        values = term_id_2_values.get(term_id)
        if values is None:
            values = set()
            term_id_2_values[term_id] = values
        for val in self.values:
            if type(val) is str:
                values.add(val)
            elif type(val) is Term:
                values.add(val.term_name)


class BrickDimension:
    def __init__(self, json_data=None):

        term = json_data['data_type']
        self.dim_type_term = Term(
            term['oterm_ref'], term_name=term['oterm_name'])
        self.dim_size = json_data['size']
        self.variables = []
        for variable in json_data['typed_values']:
            self.variables.append(BrickDimensionVariable(json_data=variable))
        self.__inflate_variables()

    def __inflate_variables(self):
        for v in self.variables:
            self.__dict__['VAR_' + v.type_term.property_name] = v

    def _collect_property_terms(self, id2terms):
        id2terms[self.dim_type_term.term_id] = self.dim_type_term
        for v in self.variables:
            v._collect_property_terms(id2terms)

    def _collect_value_terms(self, id2terms):
        for v in self.variables:
            v._collect_value_terms(id2terms)

    def _collect_all_term_values(self, term_id_2_values):
        for v in self.variables:
            v._collect_all_term_values(term_id_2_values)

    def _repr_html_(self):
        def _row(prop, value):
            return '<tr><td>%s</td><td>%s</td></tr>' % (prop, value)

        rows = [
            _row('Type', str(self.dim_type_term)),
            _row('Size', str(self.dim_size))
        ]

        for v in self.variables:
            rows.append(
                _row('Variable', str(v.type_term)),
            )

        return '<table>%s</table>' % ''.join(rows)


class BrickProperty:
    def __init__(self, json_data=None):
        term = json_data['value_type']
        self.type_term = Term(term['oterm_ref'], term_name=term['oterm_name'])

        value_type = json_data['value']['scalar_type']
        if value_type == 'oterm_ref':
            self.value = Term(json_data['value'][value_type])
        else:
            value_type += '_value'
            self.value = json_data['value'][value_type]


class BrickContext:
    def __init__(self, json_data=None):
        self.properties = []
        for prop_data in json_data:
            self.properties.append(BrickProperty(prop_data))

    def _collect_property_terms(self, id2terms):
        for prop in self.properties:
            id2terms[prop.type_term.term_id] = prop.type_term

    def _collect_value_terms(self, id2terms):
        for prop in self.properties:
            if type(prop.value) is Term:
                term = prop.value
                id2terms[term.term_id] = term

    def _collect_all_term_values(self, term_id_2_values):
        for prop in self.properties:
            term_id = prop.type_term.term_id
            values = term_id_2_values.get(term_id)
            if values is None:
                values = set()
                term_id_2_values[term_id] = values

            if type(prop.value) is str:
                values.add(prop.value)
            elif type(prop.value) is Term:
                values.add(prop.value.term_name)

    def _repr_html_(self):
        columns = ['Property', 'Units', 'Value']
        table_header = '<tr>%s</tr>' % ['<th>%s</th>' % c for c in columns]
        table_rows = []
        for prop in self.properties:
            table_rows.append('<tr>')
            table_rows.append('<td>%s</td>' % prop.type_term.term_name)
            table_rows.append('<td>%s</td>' % '')
            table_rows.append('<td>%s</td>' % prop.value)
            table_rows.append('</tr>')

        return '<table>%s%s</table>' % (table_header, ''.join(table_rows))


class Brick:
    def __init__(self, brick_id, json_data=None):
        self.id = brick_id
        self.name = json_data['name']
        self.description = json_data['description']

        term = json_data['data_type']
        self.data_type_term = Term(
            term['oterm_ref'], term_name=term['oterm_name'])

        # do context
        self.properties = BrickContext(json_data['array_context'])

        # do dimensions
        self.dimensions = []
        for dim_json in json_data['dim_context']:
            self.dimensions.append(BrickDimension(json_data=dim_json))

        term = json_data['typed_values']['value_type']
        self.value_type_term = Term(
            term['oterm_ref'], term_name=term['oterm_name'])

        if 'value_units' in json_data['typed_values']:
            term = json_data['typed_values']['value_units']
            self.value_unit_term = Term(
                term['oterm_ref'], term_name=term['oterm_name'])
        else:
            self.value_unit_term = None

        value_type = json_data['typed_values']['values']['scalar_type']
        if value_type == 'oterm_ref':
            value_type = 'oterm_refs'
        else:
            value_type += '_values'
        data = np.array(json_data['typed_values']['values'][value_type])
        self.data = data.reshape([dim.dim_size for dim in self.dimensions])

        self.__inflate_dimensions()

    def __inflate_dimensions(self):
        for d in self.dimensions:
            self.__dict__['DIM_' + d.dim_type_term.property_name] = d

    def _repr_html_(self):
        def _row(prop, value):
            return '<tr><td>%s</td><td>%s</td></tr>' % (prop, value)

        dim_names = ', '.join(
            [dim.dim_type_term.term_name for dim in self.dimensions])
        dim_sizes = [dim.dim_size for dim in self.dimensions]

        name = self.name.split('.')[0]
        name = ' '.join(name.split('_'))

        rows = [
            _row('ID', self.id),
            _row('Name', name),
            _row('Data type', self.data_type_term.term_name),
            _row('Dimensions', dim_names),
            _row('Shape', dim_sizes),
            _row('Value type', self.value_type_term.term_name),
            _row('Value units', self.value_unit_term.term_name)
        ]

        return '<table>%s</table>' % ''.join(rows)
        # lines.append('')
        # for dim_index, dim in enumerate(self.dimensions):
        #     lines.append('Dimension[%s]: %s' %
        #                  (dim_index + 1, dim.dim_type_term.term_name))
        #     for variable in dim.variables:
        #         lines.append('<span style="margin-left:10px"> %s: </span>' %
        #                      variable.type_term.term_name)

        # return '<br>'.join(lines)

    def get_all_term_ids(self):
        term_ids = set()
        for term in self.get_property_terms():
            term_ids.add(term.term_id)

        for term in self.get_value_terms():
            term_ids.add(term.term_id)

        return term_ids

    def get_property_terms(self):
        id2terms = {}
        id2terms[self.data_type_term.term_id] = self.data_type_term
        id2terms[self.value_type_term.term_id] = self.value_type_term
        if self.value_unit_term:
            id2terms[self.value_unit_term.term_id] = self.value_unit_term

        self.properties._collect_property_terms(id2terms)

        for dim in self.dimensions:
            dim._collect_property_terms(id2terms)

        return list(id2terms.values())

    def get_value_terms(self):
        id2terms = {}
        self.properties._collect_value_terms(id2terms)

        for dim in self.dimensions:
            dim._collect_value_terms(id2terms)
        return list(id2terms.values())

    def get_term_id_2_values(self):
        term_id_2_values = {}
        self.properties._collect_all_term_values(term_id_2_values)
        for d in self.dimensions:
            d._collect_all_term_values(term_id_2_values)
        return term_id_2_values

    def get_all_term_values(self):
        values = set()
        term_id_2_values = self.get_term_id_2_values()
        for term_vals in term_id_2_values.values():
            for val in term_vals:
                values.add(val)
        return values


class BrickIndexDocumnet:
    def __init__(self, brick):
        self.brick_id = brick.id
        self.name = brick.name
        self.description = brick.description
        self.n_dimensions = len(brick.dimensions)
        self.data_type_term_id = brick.data_type_term.term_id
        self.data_type_term_name = brick.data_type_term.term_name
        self.value_type_term_id = brick.value_type_term.term_id
        self.value_type_term_name = brick.value_type_term.term_name
        self.dim_type_term_ids = [
            d.dim_type_term.term_id for d in brick.dimensions]
        self.dim_type_term_names = [
            d.dim_type_term.term_name for d in brick.dimensions]
        self.dim_sizes = [
            d.dim_size for d in brick.dimensions]

        # all term ids and values
        self.all_term_ids = list(brick.get_all_term_ids())
        self.all_term_values = list(brick.get_all_term_values())

        # parent path term ids
        all_parent_path_term_ids = set()
        ont_all = services.ontology.all
        term_collection = ont_all.find_ids(self.all_term_ids)
        for term in term_collection.terms:
            for term_id in term.parent_path_ids:
                all_parent_path_term_ids.add(term_id)
        self.all_parent_path_term_ids = list(all_parent_path_term_ids)

        # values per ontology term
        term_id_2_values = brick.get_term_id_2_values()
        for term_id, values in term_id_2_values.items():
            prop = 'ont_' + '_'.join(term_id.split(':'))
            self.__dict__[prop] = list(values)


class BrickDescriptorCollection:
    def __init__(self, brick_descriptors):
        self.__brick_descriptors = brick_descriptors

    @property
    def items(self):
        return self.__brick_descriptors

    @property
    def size(self):
        return len(self.__brick_descriptors)

    def __getitem__(self, i):
        return self.__brick_descriptors[i]

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

    def _repr_html_(self):
        return self.df()._repr_html_()


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
