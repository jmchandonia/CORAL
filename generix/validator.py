import pandas as pd
import re
from .ontology import Term, OntologyService
from . import services


class TermValueValidationService:
    def __init__(self):
        self.__validators = {
            'nucleotide_sequence': self.nucleotide_sequence,
            'protein_sequence': self.protein_sequence
        }

    def validator(self, name):
        return self.__validators.get(name)

    def nucleotide_sequence(self, val):
        return True

    def protein_sequence(self, val):
        print('--- check protine sequence ---', val)
        return True


class TermValidatorService:
    def __init__(self, file_name):
        self.__file_name = file_name
        self.__f = None

    def __error(self, error_type, term, expected_name=None):
        msg = '[%s] %s - %s' % (error_type, term.term_id, term.term_name)
        if expected_name is not None:
            msg += '; Expected name = %s' % expected_name
        return msg

    def open(self):
        self.__f = open(self.__file_name, 'w')

    def close(self):
        self.__f.close()

    def __write_error(self, error_type, term, expected_name=None):
        self.__f.write('%s\n' % self.__error(
            error_type, term, expected_name))

    def validate_data_table_terms(self, data_table):
        ontology = services.ontology.all
        self.__f.write('DataTable: %s \n' % data_table.name)
        (id_2_terms, bad_term_values) = data_table.get_all_terms()

        db_id_2_terms = ontology.find_ids_hash(list(id_2_terms.keys()))

        # for terms
        for term in id_2_terms.values():
            db_term = db_id_2_terms.get(term.term_id)
            if db_term is not None:
                if term.term_name != db_term.term_name:
                    self.__write_error(
                        'wrong property term name', term, expected_name=db_term.term_name)
            else:
                self.__write_error('property term not found', term)

        # for bad values
        for bad_value in bad_term_values:
            self.__f.write('[%s] %s\n' % ('can not parse term', bad_value))

        self.__f.write('\n')

    def validate_brick_terms(self, brick):
        ontology = services.ontology.all

        self.__f.write('Brick: %s \n' % brick.name)

        # do property terms
        terms = brick.get_property_terms()
        term_ids = [t.term_id for t in terms]
        id2terms = ontology.find_ids_hash(term_ids)
        for term in terms:
            if term.term_id in id2terms:
                t = id2terms[term.term_id]
                if term.term_name != t.term_name:
                    self.__write_error(
                        'wrong property term name', term, expected_name=t.term_name)
            else:
                self.__write_error('property term not found', term)

        # do value terms
        terms = brick.get_value_terms()
        term_ids = [t.term_id for t in terms]
        id2terms = ontology.find_ids_hash(term_ids)
        for term in terms:
            if term.term_id not in id2terms:
                self.__write_error('value term not found', term)

        self.__f.write('\n')
