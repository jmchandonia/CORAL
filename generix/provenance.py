import os
import pandas as pd
import numpy as np
from .validator import TermValidatorService
from .datatable import DataTable
from . import services


_DTYPES = {
    'Well': {
        'id': 'name',
        'terms': ['continent', 'country', 'biome', 'feature']
    },
    'Sample': {
        'id': 'name',
        'terms': ['material', 'env_package']
    },
    'Taxon': {
        'id': 'name',
        'terms': []
    },
    'Community': {
        'id': 'name',
        'terms': ['community_type']
    },
    'Generic': {
        'id': 'name',
        'terms': []
    },
    'Process': {
        'id': None,
        'terms': ['process', 'person', 'campaign'],
        'avoid_types': ['Condition']
    }
}


_FILES = {
    'entities': [
        {
            'file': 'data/import/wells_all.tsv',
            'dtype': 'Well',
        },
        {
            'file': 'data/import/samples_all.tsv',
            'dtype': 'Sample',
        },
        {
            'file': 'data/import/taxa_isolates.tsv',
            'dtype': 'Taxon',
        },
        {
            'file': 'data/import/communities_isolates.tsv',
            'dtype': 'Community',
        }
    ],
    'processes': [
        {
            'file': 'data/import/process_assay_growth.tsv',
            'ptype': 'Assay Growth'
        },
        {
            'file': 'data/import/process_isolates.tsv',
            'ptype': 'Isolation'
        },
        {
            'file': 'data/import/process_sampling_all.tsv',
            'ptype': 'Sampling'
        }
    ]
}


def _to_data_frame(tx, query):
    nodes = []
    for record in tx.run(query):
        items = {}
        for _, node in record.items():
            items['_id'] = node.id
            for entry in node.items():
                items[entry[0]] = entry[1]
        nodes.append(items)
    return pd.DataFrame(nodes)


class ProvenanceSearchService:
    def __init__(self, neo4j_client):
        self.__neo4j_client = neo4j_client

    def brick_ids_from_well(self, well_name):
        query = "match(g:Generic)<-[*1..20]-(w:Well{name:'%s'}) return g" % well_name
        df = self.__list_data(query)
        return list(df.id.values)

    def __list_data(self, query):
        with self.__neo4j_client.session() as session:
            df = session.read_transaction(_to_data_frame, query)
        return df


class ProvenanceIndexerService:
    def __init__(self):
        pass

    def __write_process_header(self, f, dt):
        columns = [
            ':LABEL',
            'id:ID',
            'date'
        ]
        for column in dt.term_columns:
            columns.append(column + '_term_nmae')
            columns.append(column + '_term_id')

        f.write(','.join(columns))
        f.write('\n')

    def __write_relations_row(self, process_id, f_rel_param, f_rel_res, it):
        in_objs = it.value('input objects').split(',')
        for in_obj in in_objs:
            dtype_name, obj_id = [x.strip() for x in in_obj.split(':')]
            if dtype_name not in _DTYPES['Process']['avoid_types']:
                ws_obj_id = services.workspace._get_id(text_id=obj_id)
                if ws_obj_id is not None:
                    f_rel_param.write('%s,%s\n' % (ws_obj_id, process_id))
                else:
                    print('\t %s: id not found: %s[%s]' % (
                        process_id, dtype_name, obj_id))

        out_objs = it.value('output objects').split(',')
        for out_obj in out_objs:
            dtype_name, obj_id = [x.strip() for x in out_obj.split(':')]
            if dtype_name not in _DTYPES['Process']['avoid_types']:
                ws_obj_id = services.workspace._get_id(text_id=obj_id)
                if ws_obj_id is not None:
                    f_rel_res.write('%s,%s\n' % (process_id, ws_obj_id))
                else:
                    print('\t %s: id not found: %s[%s]' % (
                        process_id, dtype_name, obj_id))

    def __write_process_row(self, f, it, dtype_name):
        values = []

        # type
        values.append(dtype_name)

        # id
        row_id = services.workspace.next_id(dtype_name)
        values.append(row_id)

        # date
        values.append(self.__to_value(it.value('date')))

        # terms
        for _, term in it.term_column_values():
            values.append(self.__to_value(term.term_name))
            values.append(self.__to_value(term.term_id))

        f.write(','.join(values))
        f.write('\n')
        return row_id

    def __write_relation_header(self, f):
        f.write(':START_ID,:END_ID')
        f.write('\n')

    def _build_process_index_files(self, dir_name):
        for fd in _FILES['processes']:
            print('Doing: ' + fd['file'])
            dtype_name = 'Process'
            dtype = _DTYPES[dtype_name]

            dt = DataTable(fd['file'], id_column=dtype['id'],
                           term_columns=dtype['terms'])

            base_file_name = os.path.basename(fd['file']).split('.')[0]
            base_file_name = os.path.join(dir_name,  base_file_name)

            try:
                f_process = open(base_file_name + '.csv', 'w')
                f_rel_param = open(base_file_name + '.rel_param.csv', 'w')
                f_rel_res = open(base_file_name + '.rel_res.csv', 'w')

                self.__write_process_header(f_process, dt)
                self.__write_relation_header(f_rel_param)
                self.__write_relation_header(f_rel_res)

                it = dt.iterator()
                while it.has_next():
                    it.next()
                    process_id = self.__write_process_row(
                        f_process, it, dtype_name)
                    self.__write_relations_row(
                        process_id, f_rel_param, f_rel_res, it)

            finally:
                f_process.close()
                f_rel_param.close()
                f_rel_res.close()

    def _build_entities_index_files(self, dir_name):

        for fd in _FILES['entities']:

            print('Doing: ' + fd['file'])
            dtype = _DTYPES[fd['dtype']]
            dt = DataTable(fd['file'], id_column=dtype['id'],
                           term_columns=dtype['terms'])

            base_file_name = os.path.basename(fd['file'])
            base_file_name = base_file_name.split('.')[0] + '.csv'
            entity_file_name = os.path.join(dir_name,  base_file_name)
            with open(entity_file_name, 'w') as f:
                # write header
                self.__write_entity_header(f, dt)

                # write rows
                it = dt.iterator()
                while it.has_next():
                    it.next()
                    self.__write_entity_row(f, it, fd['dtype'])

    def __to_value(self, value):
        value = bytes(str(value), 'utf-8').decode('utf-8', 'ignore')
        value = '\''.join(value.split('"'))
        if type(value) is str:
            return '"%s"' % value
        return value

    def __write_entity_row(self, f, it, dtype_name):
        values = []

        # type
        values.append(dtype_name)

        # id
        # name = self.__to_value(it.id_value())
        row_id = services.workspace.next_id(dtype_name, text_id=it.id_value())
        values.append(row_id)
        values.append(it.id_value())

        for _, term in it.term_column_values():
            values.append(self.__to_value(term.term_name))
            values.append(self.__to_value(term.term_id))

        for _, value in it.other_column_values():
            values.append(self.__to_value(value))
        # print(values)
        f.write(','.join(values))
        f.write('\n')

    def __write_entity_header(self, f, dt):
        columns = []

        # add type
        columns.append(':LABEL')

        # column id
        columns.append('id:ID')
        columns.append(dt.id_column)

        # term columns
        for column in dt.term_columns:
            columns.append(column + '_term_name')
            columns.append(column + '_term_id')

        # other columns
        for column in dt.other_columns:
            columns.append(column)

        f.write(','.join(columns))
        f.write('\n')

    def _build_bricks_index_files(self, dir_name, brick_ids):
        with open(os.path.join(dir_name, 'bricks.csv'), 'w') as f:
            f.write(':LABEL,id:ID\n')
            for brick_id in brick_ids:
                f.write('Generic,%s\n' % brick_id)

    def validate_data_tables(self, log_file_name):
        tvs = TermValidatorService(log_file_name)
        try:
            tvs.open()

            # do entities
            for fe in _FILES['entities']:
                print('Doing entities: ' + fe['file'])
                dtype = _DTYPES[fe['dtype']]
                dt = DataTable(fe['file'], id_column=dtype['id'],
                               term_columns=dtype['terms'])
                tvs.validate_data_table_terms(dt)

            # do processes
            dtype = _DTYPES['Process']
            for fp in _FILES['processes']:
                print('Doing processes: ' + fp['file'])
                dt = DataTable(fp['file'], id_column=None,
                               term_columns=dtype['terms'])
                tvs.validate_data_table_terms(dt)

        finally:
            tvs.close()
