from . import services
from .typedef import TYPE_NAME_BRICK

class DataReports:

    @property
    def brick_types(self):
        return self.__brick_term_stat('data_type_term_id' )
        
    @property
    def brick_dim_types(self):
        return self.__brick_term_stat('dim_type_term_ids' )

    @property
    def brick_data_var_types(self):
        return self.__brick_term_stat('value_type_term_id' )

    def __brick_term_stat(self, term_id_prop_name):
        itd = services.indexdef.get_type_def(TYPE_NAME_BRICK)
        return services.ontology.term_stat( itd, term_id_prop_name)