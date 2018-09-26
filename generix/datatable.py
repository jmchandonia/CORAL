import re
import pandas as pd
from .ontology import Term


class _DataTableIterator:
    def __init__(self, data_table):
        self.__row_index = -1
        self.__data_table = data_table

    def has_next(self):
        return self.__row_index < self.__data_table.size - 1

    def next(self):
        self.__row_index += 1

    def id_value(self):
        return self.__data_table.value(self.__row_index, self.__data_table.id_column)

    def term_column_values(self):
        column_value_pairs = []
        row = self.__data_table.row(self.__row_index)
        for column in self.__data_table.term_columns:
            val = row[column]
            column_value_pairs.append(
                (column, self.__data_table.parse_term(val)))

        return column_value_pairs

    def value(self, column):
        return self.__data_table.value(self.__row_index, column)

    def other_column_values(self):
        column_value_pairs = []
        row = self.__data_table.row(self.__row_index)
        for column in self.__data_table.other_columns:
            column_value_pairs.append((column, row[column]))

        return column_value_pairs


class DataTable:

    __term_pattern = re.compile('(.+)<(.+)>')

    def __init__(self, file_name, id_column='name', term_columns=[], avoid_types=[]):
        self.name = file_name
        self.id_column = id_column
        self.term_columns = term_columns
        self.other_columns = []
        self.__df = pd.read_csv(file_name, sep='\t')
        for column in self.__df.columns.values:
            if column != self.id_column and column not in self.term_columns:
                self.other_columns.append(column)

    @property
    def size(self):
        return self.__df.shape[0]

    def row(self, row_index):
        return self.__df.iloc[row_index]

    def value(self, row_index, column):
        val = self.__df.iloc[row_index][column]
        if type(val) is str:
            val = val.strip()
        return val

    def column_type(self, column):
        val = self.__df.iloc[0][column]
        return type(val)

    def iterator(self):
        return _DataTableIterator(self)

    def get_all_terms(self):
        id_2_terms = {}
        bad_terms = set()
        for i in range(self.size):
            row = self.row(i)
            for column in self.term_columns:
                val = row[column]
                term = Term.parse_term(val)
                if term is not None:
                    id_2_terms[term.term_id] = term
                else:
                    bad_terms.add(val.strip())
        return (id_2_terms, bad_terms)
