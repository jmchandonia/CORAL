import pandas as pd
from . import services
from .typedef import TYPE_NAME_BRICK, TYPE_NAME_PROCESS


class ReportBuilderService:           

    @property
    def process_types(self):
        return self.__process_term_stat_report( 'Types of processes', 'process' )

    @property
    def process_persons(self):
        return self.__process_term_stat_report( 'Persons of processes', 'person' )

    @property
    def process_campaigns(self):
        return self.__process_term_stat_report( 'Campaigns of processes', 'campaign' )

    @property
    def brick_types(self):
        return self.__brick_term_stat_report( 'Data types of bricks', 'data_type' )
        
    @property
    def brick_dim_types(self):
        return self.__brick_term_stat_report( 'Dimension types of bricks', 'dim_types' )

    @property
    def brick_data_var_types(self):
        return self.__brick_term_stat_report( 'Data value types of bricks', 'value_type' )


    @property
    def brick_full_types(self):
        report_name = 'Full types of bricks'
        # get data
        aql = '''
            let rows = (
            for x in DDT_Brick
            collect data_type_term_id = x.data_type_term_id, dim_type_term_ids = x.dim_type_term_ids
            with count into term_count
            sort data_type_term_id, term_count desc
            return {data_type_term_id, dim_type_term_ids, term_count})

            for x in rows
            collect data_type_term_id = x.data_type_term_id 
            aggregate data_type_count = SUM(x.term_count)
            into group_item
            return {
                data_type_term_id,
                group_dim_type_term_ids: group_item[*].x.dim_type_term_ids,
                group_term_counts: group_item[*].x.term_count,
                data_type_count
            }
        '''
        aql_bind = {}
        rs = services.arango_service.find(aql, aql_bind)

        # load all term ids
        term_ids = set()
        for row in rs:
            term_ids.add(row['data_type_term_id'])
            for gt_ids in row['group_dim_type_term_ids']:
                for tid in gt_ids:
                    term_ids.add(tid)
        term_ids_hash = services.ontology.all.find_ids_hash( list(term_ids) )

        # build group items
        group_items = []
        for row in rs:
            data_type_term = term_ids_hash.get(row['data_type_term_id'])
            data_type_count = row['data_type_count']

            report_items = []
            group_dim_type_term_ids = row['group_dim_type_term_ids']
            group_term_counts = row['group_term_counts']
            for i, dim_type_term_ids in enumerate(group_dim_type_term_ids):
                item_count = group_term_counts[i]
                term_names = []
                for term_id in dim_type_term_ids:
                    term = term_ids_hash.get(term_id)
                    term_names.append(term.term_name)
                report_items.append(ReportItem(
                    [ ','.join(term_names)], 
                    item_count
                ))

            group_items.append(ReportGroupItem(
                [ data_type_term.term_name, data_type_term.term_id ],
                data_type_count,
                report_items
            ))
        return GroupReport(report_name, 
            ['Data Type', 'Term ID'], 
            'Bricks count',
            ['Dimension Types'],
            'Bricks count',
            group_items)

    def __process_term_stat_report(self, report_name, term_prop_name):
        itype_def = services.indexdef.get_type_def(TYPE_NAME_PROCESS)
        return self.__term_stat_report(report_name, itype_def, term_prop_name, 'Processes count')

    def __brick_term_stat_report(self, report_name, term_prop_name):
        itype_def = services.indexdef.get_type_def(TYPE_NAME_BRICK)
        return self.__term_stat_report(report_name, itype_def, term_prop_name, 'Bricks count')

    def __term_stat_report(self, report_name, index_type_def, term_prop_name, count_name):        
        term_counts = services.ontology.term_stat( index_type_def, term_prop_name)
        report_items = []
        for term_count in term_counts:
            term = term_count[0]
            report_items.append(ReportItem( [term.term_name, term.term_id], term_count[1] ))

        return PlainReport(report_name, ['Term Name', 'Term ID'], count_name, report_items)


class PlainReport:
    def __init__(self, report_name, prop_names, prop_count_name, report_items):
        self.__report_name = report_name
        self.__prop_names = prop_names
        self.__prop_count_name = prop_count_name
        self.__report_items = report_items

    def _repr_html_(self):
        rows = []
        for item in self.__report_items:
            row = {}
            for i, prop_name in enumerate(self.__prop_names):
                row[prop_name] = item.value(i)
            row[self.__prop_count_name] = item.count
            rows.append(row)
        
        names = self.__prop_names.copy()
        names.append(self.__prop_count_name)
        html = '############################# <br> %s <br>############################# <br> %s' % (
            self.__report_name,
            pd.DataFrame(rows)[names]._repr_html_()    
        )
        return html

    def to_df(self):
        rows = []
        for item in self.__report_items:
            row = {}
            for i, prop_name in enumerate(self.__prop_names):
                row[prop_name] = item.value(i)
            row[self.__prop_count_name] = item.count
            rows.append(row)
        
        names = self.__prop_names.copy()
        names.append(self.__prop_count_name)
        return pd.DataFrame(rows)[names]


class GroupReport:
    def __init__(self, report_name, group_prop_names, group_prop_count_name, prop_names, prop_count_name, group_items):
        self.__report_name = report_name
        self.__group_prop_names = group_prop_names
        self.__group_prop_count_name = group_prop_count_name
        self.__prop_names = prop_names
        self.__prop_count_name = prop_count_name
        self.__group_items = group_items
    
    def _repr_html_(self):
        rows = [
            '#############################',
            self.__report_name, 
            '#############################', 
            '']
        
        for gitem in self.__group_items:
            rows.append(
                '''
                <b> %s </b> : %s [%s]
                ''' % ( gitem.value(0), gitem.value(1), gitem.count )
            )
            for item in gitem.sub_items:
                rows.append(
                    '.... %s [%s]' %
                    ( item.value(0), item.count)
                )
            rows.append('')

        return '<br>'.join(rows)


class ReportGroupItem:
    def __init__(self, values, count, report_items):
        self.__values = values
        self.__count = count
        self.__report_items = report_items
    
    def value(self, index):
        return self.__values[index]
    
    @property
    def count(self):
        return self.__count
    
    @property
    def sub_items(self):
        return self.__report_items

class ReportItem:
    def __init__(self, values, count):
        self.__values = values
        self.__count = count
    
    def value(self, index):
        return self.__values[index]
    
    @property
    def count(self):
        return self.__count

