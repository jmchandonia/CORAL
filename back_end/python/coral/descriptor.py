import pandas as pd 
from .ontology import Term
from .typedef import TYPE_NAME_BRICK
from . import dataprovider
from . import services

class DataDescriptorCollection:
    def __init__(self, data_descriptors=[]):
        self.__data_descriptors = []
        self.__data_descriptors.extend(data_descriptors)

    @property
    def items(self):
        return self.__data_descriptors

    @property
    def size(self):
        return len(self.__data_descriptors)

    def add_data_descriptor(self, dd):
        self.__data_descriptors.append(dd)

    def add_data_descriptors(self, dds):
        self.__data_descriptors.extend(dds)

    def head(self, count=5):
        return DataDescriptorCollection(data_descriptors=self.__data_descriptors[:count])

    def __getitem__(self, i):
        return self.__data_descriptors[i]

    def to_df(self):
        dd_list = []
        for dd in self.__data_descriptors:
            dd_doc = {}
            for prop in dd.table_view_properties():
                dd_doc[prop] = dd[prop]
            dd_list.append(dd_doc)
        df = pd.DataFrame(dd_list)
        if len(dd_list) > 0:
            df = df[dd.table_view_properties()]
        return df

    def _repr_html_(self):
        return self.to_df()._repr_html_()


class DataDescriptor:
    def __init__(self, index_type_def, doc):
        self.__properties = []

        self.__index_type_def = index_type_def
        for key in doc:

            self.__dict__[key] = doc[key]
            self.__properties.append(key)

    def __getitem__(self, property_name):
        return self.__dict__[property_name]

    def table_view_properties(self):
        props = []
        if 'id' in self.__dict__:
            props.append('id')

        for prop in self.__dict__.keys():
            if prop.startswith('_') or prop == 'id':
                continue
            props.append(prop)
        return props

    @property
    def index_type_def(self):
        return self.__index_type_def

    @property
    def properties(self):
        return self.__properties

    def _repr_html_(self):
        def _row2_header(c):
            return '<tr><td colspan=2 style="text-align:left;">%s</td></tr>' % (c)

        def _row2(c1, c2):
            cell = '<td style="padding-left:20px; text-align:left">%s</td>'
            patterm = '<tr>' + ''.join([cell for i in range(2)]) + '</tr>'
            return patterm % (c1, c2)

        rows = []
        for prop in self.__dict__:
            if prop.startswith('_'):
                continue
            rows.append(_row2(prop, self.__dict__[prop]))

        return '<table>%s</table>' % ''.join(rows)

    def __str__(self):
        return str(self.__dict__)

class EntityDescriptor(DataDescriptor):
    def __init__(self, index_type_def, doc):
        super().__init__(index_type_def, doc)
        self.__provenance = DataDescriptorProvenance(self)

    def get_up_process(self):
        entity_id = self['id']
        docs = services.arango_service.get_up_processes(self.index_type_def, entity_id)

        dds = []
        for doc in docs:
            dds.append( ProcessDescriptor(doc) )
        return DataDescriptorCollection(dds)

    def get_down_processes(self):
        entity_id = self['id']
        docs = services.arango_service.get_dn_processes(self.index_type_def, entity_id)

        dds = []
        for doc in docs:
            dds.append( ProcessDescriptor(doc) )
        return DataDescriptorCollection(dds)

    def provenance(self):
        return self.__provenance

    @property
    def formatted_properties(self):
        # merge terms in descriptor into "term_name <term_id>" format
        # used for displaying search results and downloading bricks in appropriate TSV format
        items = {}
        for key, val in self.__dict__.items():
            if key.startswith('_'):
                continue
            elif key.endswith('_term_id'):
                prop_name = key.split('_term_id')[0]
                if prop_name + '_term_name' in self.__dict__:
                    items[prop_name] = '%s <%s>' % (self.__dict__[prop_name + '_term_name'], val)
                else:
                    items[key] = val

            elif key.endswith('_term_name'):
                prop_name = key.split('_term_name')[0]
                if prop_name + '_term_id' not in self.__dict__:
                    items[key] = val

            else:
                items[key] = val
        return items


class DataDescriptorProvenance:
    def __init__(self, data_descriptor):
        self.__data_descriptor = data_descriptor

    @staticmethod
    def _provenance_rows(data_descriptor):
        rows = []
        for pd in data_descriptor.get_up_processes():
            rows.append('<div style="margin-left:20px">')
            rows.append('&uarr;')
            rows.append('<div>')
            rows.append('Created by: %s - %s: [%s, %s]' %
                        (pd.id, pd.process_term_name,
                         pd.campaign_term_name, pd.person_term_name))
            rows.append('</div>')
            for dd in pd.get_input_data_descriptors().items:
                rows.append('<div>')
                rows.append('From object: %s' % (dd.id))
                rows.extend(DataDescriptorProvenance._provenance_rows(dd))
                rows.append('</div>')
            rows.append('</div>')

        return rows

    def _repr_html_(self):
        prov_html = ''.join(
            DataDescriptorProvenance._provenance_rows(self.__data_descriptor))
        return 'Provenance for %s %s ' % (self.__data_descriptor.id, prov_html)


class ProcessDescriptor(DataDescriptor):
    def __init__(self, doc):
        super().__init__('Process', doc)

    def get_input_data_descriptors(self):
        process_id = self['id']
        type2docs = services.arango_service.get_process_inputs(process_id)
        return self.__to_type2descriptors(type2docs)

    def get_output_data_descriptors(self):
        process_id = self['id']
        type2docs = services.arango_service.get_process_outputs(process_id)
        return self.__to_type2descriptors(type2docs)

    def __to_type2descriptors(self, type2docs):
        type2descriptors = {}
        for type_name, docs in type2docs.items():
            itd = services.indexdef.get_type_def(type_name)
            if type_name == TYPE_NAME_BRICK:
                dds = [ BrickDescriptor(doc) for doc in docs ]
            else:
                dds = [ EntityDescriptor(itd, doc) for doc in docs ]
            
            type2descriptors[type_name] = DataDescriptorCollection(dds)
        return type2descriptors


class BrickDescriptor(EntityDescriptor):
    def __init__(self, data):
        data['brick_id'] = data[services.indexdef.PK_PROPERTY_NAME]
        data['brick_name'] = data['name']
        data['brick_type'] = data['data_type_term_name']
        data['dim_types'] = data['dim_type_term_names']
        if 'value_type_term_names' in data:
            data['value_types'] = data['value_type_term_names']
        elif 'value_type_term_name' in data:
            data['value_type'] = data['value_type_term_name']
        data['shape'] = data['dim_sizes']

        super().__init__( services.indexdef.get_type_def(TYPE_NAME_BRICK), data)

    def table_view_properties(self):
        return ['brick_id', 'brick_type', 'shape',
                'dim_types', 'value_types', 'brick_name']

    @property
    def full_type(self):
        return '%s<%s>' % (self['data_type_term_name'], ','.join(self['dim_type_term_names']))

    def load(self):
        return dataprovider.BrickProvider._load_brick(self['brick_id'])

    def __str__(self):
        return 'Name: %s;  Type: %s; Shape: %s' % (self['name'], self.full_type, self['shape'])



class IndexDocument:
    @staticmethod
    def build_index_doc(data_holder):
        type_def = data_holder.type_def

        doc = {}

        doc[services.indexdef.PK_PROPERTY_NAME] = data_holder.id
        all_term_ids = set()
        all_parent_path_term_ids = set()
        for pdef in type_def.property_defs:
            pname = pdef.name
            if pname in data_holder.data:
                value = data_holder.data[pname]
                if pdef.type == 'term':
                    term = Term.parse_term(value)
                    # term.refresh()
                    doc[pname + '_term_id'] = term.term_id
                    doc[pname + '_term_name'] = term.term_name

                    all_term_ids.add(term.term_id)
                    for pid in term.parent_path_ids:
                        all_parent_path_term_ids.add(pid)
                else:
                    doc[pname] = value

        # doc['all_term_ids'] = list(all_term_ids)
        # doc['all_parent_path_term_ids'] = list(all_parent_path_term_ids)

        return doc

class BrickIndexDocument:
    @staticmethod
    def properties():
        return { 
            'id': 'text',
            'name': 'text',
            'description': 'text',
            'n_dimensions': 'int',
            'data_type': 'term',
            'value_types': '[term]',
            'dim_types': '[term]',
            'dim_sizes': '[int]',
            'all_terms': '[term]',
            'all_term_values': '[text]',
            'all_parent_path_terms': '[term]'
        }

    def __init__(self, brick):
        # ArangoDB primary key
        self.__dict__[services.indexdef.PK_PROPERTY_NAME] = brick.id

        # self.id = brick.id
        self.name = brick.name
        self.description = brick.description
        self.n_dimensions = len(brick.dims)
        self.data_type_term_id = brick.type_term.term_id
        self.data_type_term_name = brick.type_term.term_name

        self.value_type_term_ids = [
            d.type_term.term_id for d in brick.data_vars]
        self.value_type_term_names = [
            d.type_term.term_name for d in brick.data_vars]
        self.dim_type_term_ids = [
            d.type_term.term_id for d in brick.dims]
        self.dim_type_term_names = [
            d.type_term.term_name for d in brick.dims]
        self.dim_sizes = [d.size for d in brick.dims]

        # TODO: all term ids and values
        self.all_term_ids = list(brick._get_all_term_ids())
        self.all_term_values = list(brick._get_all_term_values())

        # parent path term ids
        all_parent_path_term_ids = set()
        ont_all = services.ontology.all
        term_collection = ont_all.find_ids(self.all_term_ids)
        for term in term_collection.terms:
            for term_id in term.parent_path_ids:
                all_parent_path_term_ids.add(term_id)
        self.all_parent_path_term_ids = list(all_parent_path_term_ids)

        # values per ontology term
        term_id_2_values = brick._get_term_id_2_values()
        for term_id, values in term_id_2_values.items():
            prop = 'ont_' + '_'.join(term_id.split(':'))
            self.__dict__[prop] = list(values)
