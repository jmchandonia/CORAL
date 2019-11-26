import pandas as pd
import numpy as np
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


class ValueValidationService:

    def cast_var_values(self, values, var_term_id):
        var_term = services.ontology._get_term(var_term_id)
        scalar_type = var_term.scalar_type
        errors = []
        if scalar_type == 'int':
            errors = self.cast_values(values, int, 'int')
        elif scalar_type == 'float':
            errors = self.cast_values(values, float, 'float')
        elif scalar_type == 'string':
            errors = self.cast_values(values, str, 'string')
        elif scalar_type == 'oterm':
            errors = self.cast_oterm_values(values, var_term)

        # TODO: cast object refs
        return errors

    def __validate_values_type(self, values):
        if type(values) != np.ndarray:
            raise ValueError('Wrond type: %s'% str(type(values)))
        if values.dtype != 'object':
            raise ValueError('Type of array should be object, but it is %s'% str(values.dtype))    


    def cast_values(self, values, cast_function, cast_type):

        self.__validate_values_type(values)

        errors = []
        with np.nditer(values, op_flags=['readwrite'], flags=['multi_index', 'refs_ok']) as it:
            while not it.finished:                 
                casted_value = None
                
                value = it[0].item()
                if value:
                    try: 
                        casted_value = cast_function(value)
                    except: 
                        self.__add_error(errors, it.multi_index, value, cast_type)

                it[0] = casted_value
                it.iternext()

        return errors 

    def cast_oterm_values(self, values, var_term):
        
        self.__validate_values_type(values)

        # Get a unique set of terms 
        terms = {}
        for val in np.nditer(values, flags=['refs_ok']):
            val = val.item()
            if val is not None:
                terms[val] = {
                    'term': None,
                    'error': None
                }

        # Get terms
        ont = services.ontology
        for term_id_name in terms.keys():
            try:
                term = ont._get_term(term_id_name)
                if var_term.term_id in term.parent_path_ids:
                    terms[term_id_name]['term'] = term                
                else:
                    terms[term_id_name]['error'] = 'Term %s does not have a valid parent %s' % (str(term), str(var_term) )    
            except:
                terms[term_id_name]['error'] = 'Can not find term: %s' % term_id_name

        # cast values
        errors = []
        with np.nditer(values, op_flags=['readwrite'], flags=['multi_index', 'refs_ok']) as it:
            while not it.finished:                 
                casted_value = None
                
                value = it[0].item()
                if value:
                    term_record = terms[value]
                    casted_value = term_record['term']
                    error = term_record['error']
                    if casted_value is None and error is not None:
                        self.__add_error(errors, it.multi_index, value, 'Term', error)

                if casted_value is not None:
                    casted_value = str(casted_value)
                it[0] = casted_value
                it.iternext()
        return errors 


    def __add_error(self, errors, index, value, cast_type, err_msg = ''):
        errors.append({
            'index': index[0] if len(index) == 1 else index,
            'error_msg': 'Can not cast "%s" to type %s. %s' % (value, cast_type, err_msg)
        })
    