import json
import numpy as np
import pandas as pd
import xarray as xr
import re
import datetime
from time import gmtime, strftime
from .ontology import Term
from .workspace import BrickDataHolder, ProcessDataHolder
from .typedef import TYPE_NAME_BRICK
from .query import Query
from . import services
from .utils import to_var_name, to_es_type_name

class NPEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.float):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return super(NPEncoder, self).default(obj)

def _collect_all_term_values(term_id_2_values, term_id, data_values):
    values = term_id_2_values.get(term_id)
    if values is None:
        values = set()
        term_id_2_values[term_id] = values
    for val in data_values:
        if type(val) is str:
            values.add(val)
        elif type(val) is Term:
            values.add(val.term_name)

    
    
DATA_EXAMPLE_SIZE = 5
    
class PropertyValue:
    def __init__(self, name=None, type_term=None, units_term=None, scalar_type='str', value=None):
        if type_term is None:
            raise ValueError('type_term can not be None')
        if type(type_term) is not Term:
            raise ValueError('type_term should be instance of Term')
        
        self.type_term = type_term
        
        if units_term is not None and type(units_term) is not Term:
            raise ValueError('units_term should be instance of Term')
        self.units_term = units_term

        #TODO validate scalar_type and the value
        self.scalar_type = scalar_type
        
        self.value = value
        self.name = name if name is not None else type_term.term_name   

    @staticmethod
    def read_json(json_data):
        term = json_data['value_type']
        type_term = services.term_provider.get_term(term['oterm_ref'])
        # type_term = Term(term['oterm_ref'], term_name=term['oterm_name'])

        value_type = json_data['value']['scalar_type']

        if value_type == 'oterm_ref':
            # value = Term(json_data['value'][value_type])
            value = services.term_provider.get_term(json_data['value'][value_type])

        else:
            value = json_data['value'][value_type + '_value']     
            
        # TODO: units    
        return PropertyValue( type_term=type_term, scalar_type=value_type, value=value )




    def _collect_property_terms(self, id2terms):
        id2terms[self.type_term.term_id] = self.type_term


    def _collect_value_terms(self, id2terms):
        if self.value is not None and type(self.value) is Term:
            id2terms[self.value.term_id] = self.value

    def _collect_all_term_values(self, term_id_2_values):
        _collect_all_term_values(term_id_2_values, self.type_term.term_id, [self.value])
 

    def __str__(self):
        name = str(self.type_term)
        if self.name != self.type_term.term_name:
            name =  '%s (%s)' % (self.name, name)  
        return '%s [%s]: %s' % (name, self.units_term, self.value)

class Brick:

    @staticmethod
    def read_json(brick_id, file_name):
        json_data = json.loads(open(file_name).read())    
        return Brick.read_dict(brick_id, json_data)


    @staticmethod
    def read_dict(brick_id, json_data):            
        ds = xr.Dataset()        
        
        # Do general properties
        # ds.attrs['__id'] = 'Brick000023'
        # ds.attrs['__type_term'] = Term('AA:145', 'Growth Data')
        # ds.attrs['__name'] = 'Object name'
        # ds.attrs['__description'] = 'Object description'    
        
        ds.attrs['__id'] = brick_id
        ds.attrs['__name'] = json_data['name']
        ds.attrs['__description'] = json_data['description']

        term = json_data['data_type']
        # ds.attrs['__type_term'] = Term(term['oterm_ref'], term_name=term['oterm_name'])
        ds.attrs['__type_term'] = services.term_provider.get_term(term['oterm_ref'])
        
        # Do context
        # ds.attrs['__attr_count'] = 2
        # ds.attrs['__attr1'] = PropertyValue( type_term=Term('AA:145', 'ENIMGA Campaign'), value=Term('AA:146', 'Metal')  )
        # ds.attrs['__attr2'] = PropertyValue( type_term=Term('AA:145', 'Genome'), value='E.coli'  )

        ds.attrs['__attr_count'] = 0
        for prop_data in json_data['array_context']:
            try:
                pv = PropertyValue.read_json(prop_data)        
                ds.attrs['__attr_count'] += 1
                attr_name = '__attr%s' % ds.attrs['__attr_count'] 
                ds.attrs[attr_name] = pv
            except Exception as e:
                print('Error: can not read property', e, prop_data)
        
        # do dimensions
        # ds.attrs['__dim_count'] = dim_count    
        ds.attrs['__dim_count'] = 0
        dim_names  = []
        dim_sizes = []
        for dim_json in json_data['dim_context']:
            ds.attrs['__dim_count'] += 1
            dim_name = '__dim%s' % ds.attrs['__dim_count']
            dim_names.append(dim_name)
            
            # ds.attrs['__dim1_term'] = dim1_term
            # ds.attrs['__dim1_var_count'] = 2
            
            term = dim_json['data_type']
            # dim_type_term = Term(term['oterm_ref'], term_name=term['oterm_name'])
            dim_type_term = services.term_provider.get_term(term['oterm_ref'])

            dim_size = dim_json['size']

            # # TODO: it is a hack... check if heterogeneous
            # if type(json_data['typed_values']) is list:
            #     dim_size = 1

            dim_sizes.append(dim_size)
            vars_json = dim_json['typed_values']
            
            ds.attrs[dim_name + '_term'] = dim_type_term        
            
            # Do variables
            ds.attrs[dim_name + '_var_count'] = 0
            for var_json in vars_json:
                ds.attrs[dim_name + '_var_count'] += 1
                            
                term = var_json['value_type']
                # vr_type_term = Term(term['oterm_ref'], term_name=term['oterm_name'])
                vr_type_term = services.term_provider.get_term(term['oterm_ref'])    
                
                if 'value_units' in var_json:
                    term = var_json['value_units']
                    # var_unit_term = Term(term['oterm_ref'], term_name=term['oterm_name'])
                    var_unit_term = services.term_provider.get_term(term['oterm_ref'])
                else:
                    var_unit_term = None
                
                var_scalar_type = var_json['values']['scalar_type']
                if var_scalar_type == 'oterm_ref':
                    var_values = []
                    for term_id in var_json['values']['oterm_refs']:
                        # var_values.append(Term(term_id))
                        var_values.append(services.term_provider.get_term(term_id))                        
                else:
                    var_values = var_json['values'][var_scalar_type + '_values']

                # da11 = xr.DataArray([i for i in range(dim1_size)], dims=dim1)
                # da11.attrs['__type_term'] = Term('AA:123', 'Time')
                # da11.attrs['__units_term'] = Term('UI:5', 'seconds')
                # da11.attrs['__name'] = 'Time0'
                # da11.attrs['__scalar_type'] = 'float'
                # da11.attrs['__attr_count'] = 0            
                
                var = xr.DataArray(var_values, dims=dim_name)
                var.attrs['__type_term'] = vr_type_term
                var.attrs['__units_term'] = var_unit_term
                var.attrs['__name'] = vr_type_term.property_name
                var.attrs['__scalar_type'] = var_scalar_type
                
                # Do attributes            
                # value_context
                # [{'value': {'oterm_ref': 'CHEBI:17632', 'scalar_type': 'oterm_ref', 'string_value': 'nitrate'}, 
                #   'value_type': {'oterm_name': 'Molecule', 'oterm_ref': 'ME:0000027', 'term_name': 'molecule'}}]            
                
                var.attrs['__attr_count'] = 0     
                if 'value_context' in var_json:
                    for attr_json in var_json['value_context']:
                        try:
                            pv = PropertyValue.read_json(attr_json)
                            var.attrs['__attr_count'] += 1
                            attr_name = '__attr%s' % var.attrs['__attr_count'] 
                            var.attrs[attr_name] = pv
                        except Exception as e:
                            print('Error: can not read property', e, attr_json)
                
                
                var_name = '%s_var%s' % (dim_name, ds.attrs[dim_name + '_var_count'])
                ds[var_name] = var

        

        # Do data
        ds.attrs['__data_var_count'] = 0

        values_jsons = json_data['typed_values']
        if type(values_jsons) is not list:
            values_jsons = [values_jsons]
        for values_json in values_jsons:
            term = values_json['value_type']
            # value_type_term = Term(term['oterm_ref'], term_name=term['oterm_name'])
            value_type_term = services.term_provider.get_term(term['oterm_ref'])

            if 'value_units' in values_json:
                term = values_json['value_units']
                # value_unit_term = Term(term['oterm_ref'], term_name=term['oterm_name'])
                value_unit_term = services.term_provider.get_term(term['oterm_ref'])                
            else:
                value_unit_term = None

            value_scalar_type = values_json['values']['scalar_type']
            if value_scalar_type == 'oterm_ref':
                value_scalar_type = 'oterm_refs'
            else:
                value_scalar_type += '_values'
            data = np.array(values_json['values'][value_scalar_type])
            data = data.reshape(dim_sizes)    
            
            # da = xr.DataArray(np.random.rand(dim1_size, dim2_size, dim3_size), dims=(dim1,dim2, dim3))
            # da.attrs['__type_term'] = Term('AA:154', 'Optical Density')
            # da.attrs['__units_term'] = None
            # da.attrs['__name'] = 'OD'
            # da.attrs['__scalar_type'] = 'float'

            # da.attrs['__attr_count'] = 2
            # da.attrs['__attr1'] = PropertyValue( type_term=Term('AA:145', 'Chemical'), value=Term('AA:146', 'Arg')  )
            # da.attrs['__attr2'] = PropertyValue( type_term=Term('AA:145', 'Chemical'), value=Term('AA:147', 'Lys')  )
            
            da = xr.DataArray(data, dims=dim_names)
            da.attrs['__type_term'] = value_type_term
            da.attrs['__units_term'] = value_unit_term
            da.attrs['__name'] = value_type_term.property_name
            da.attrs['__scalar_type'] = value_scalar_type
            da.attrs['__attr_count'] = 0
            
            if 'value_context' in values_json:
                for attr_json in values_json['value_context']:
                    try:
                        pv = PropertyValue.read_json(attr_json)

                        da.attrs['__attr_count'] += 1
                        attr_name = '__attr%s' % da.attrs['__attr_count'] 
                        da.attrs[attr_name] = pv
                    except Exception as e:
                        print('Error: can not read property', e, attr_json)

            ds.attrs['__data_var_count'] += 1
            data_var_name = '__data_var%s' % ds.attrs['__data_var_count']

            ds[data_var_name] = da
        return Brick(xds=ds)    

    
    def __inflate_data_vars(self):
        for i,var in enumerate(self.data_vars):
            self.__dict__['DATA%s_%s' %( i+1 , var.var_name)] = var

    @staticmethod
    def _xds_build_var(brick, dim, xds, xds_var_prefix, dim_names, type_term, units_term, values, scalar_type):
        var = xr.DataArray(values, dims=dim_names)
        var.attrs['__type_term'] = type_term
        var.attrs['__units_term'] = units_term
        var.attrs['__name'] = type_term.term_name
        var.attrs['__scalar_type'] = scalar_type
        var.attrs['__attr_count'] = 0

        # add variable to xds
        var_count = xds.attrs[xds_var_prefix + '_var_count']
        var_count += 1
        xds.attrs[xds_var_prefix + '_var_count'] = var_count
        var_name = '%s_var%s'  % (xds_var_prefix, var_count )
        xds[var_name] = var

        return BrickVariable(brick, dim, xds, var_name) 

    def __init__(self, xds=None, type_term=None, dim_terms=None, shape=None, id='', name='', description=''):

        if xds is None:
            xds = self.__build_xds(type_term, dim_terms, shape, id=id, name=name, description=description)

        self.__xds = xds
        self.__session_provenance = BrickProvenance('-',[])

        self.__dims = []
        for i in range( self.dim_count ):
            dim = BrickDimension(self, xds, i)
            self.__dims.append( dim )
            self.__dict__['DIM%s_%s' %(i+1, dim.name) ] = dim
            
        self.__data_vars = []
        for i in range( self.data_var_count):            
            data_var = BrickVariable(self, None, xds, '__data_var%s' % (i+1))
            self.__data_vars.append(data_var)

        self.__inflate_data_vars()
       
    def __getitem__(self, selectors):

        # check dimensions
        if self.dim_count == 1:
            if not np.isscalar(selectors):
                raise ValueError('The selector for one-dimensional array should be a scalar')
        else:
            if type(selectors) is not tuple:
                raise ValueError('The selector for multi-dimensional array should be a tuple')
            if len(selectors) !=  self.dim_count:
                raise ValueError('The selector should have %s items' % self.dim_count)

        # check variable names
        for dim_index, selector in enumerate(selectors):
            dim = self.dims[dim_index]
            if type(selector) is dict:
                for value_name in selector:
                    name_found = False
                    for var in dim.vars:
                        if value_name == var.type_term.term_name:
                            name_found = True
                            break
                    if name_found == False:
                        raise ValueError('Variable %s is not found in the %s dimension' % (value_name, dim.name))
            else: 
                if np.isscalar(selector):
                    if dim.var_count > 1:
                        raise ValueError('Selector[%s] must sepcify the name of the variable since there are more than one variables in this dimension' % dim_index)            
                else:
                    raise ValueError('Selector[%s] must be either scalar or dict' % dim_index)            

        # build selectors
        kwargs = {}
        for dim_index, selector in enumerate(selectors):
            dim = self.dims[dim_index]
            dim_prefix = '__dim%s' % (dim_index + 1)
            var_prefix = '%s_var1' % dim_prefix

            bool_array = [True]*dim.size
            if type(selector) is dict:
                for var_name in selector:
                    for var_index, var in enumerate(dim.vars):
                        if var_name == var.name:
                            var_prefix = '%s_var%s' % ( dim_prefix, var_index + 1 ) 
                            break

                    ba = self.__xds[var_prefix] == selector[var_name]
                    for i, b in enumerate(ba):
                       bool_array[i] = bool_array[i] and b 
            else:
                bool_array = self.__xds[var_prefix] == selector
            
            kwargs[dim_prefix] = bool_array

        xds = self.__xds.isel(kwargs)
        brick = Brick(xds=xds)
        
        return  brick._shrink_dims()    

    def _shrink_dims(self):
        # find dim indeces with dim size = 1
        dim_indeces = []
        for dim_index, dim in enumerate(self.dims):
            if dim.size == 1:
                dim_indeces.append(dim_index)

        # add properties from dim variables
        for dim_index in dim_indeces:
            dim = self.dims[dim_index]
            for var in dim.vars:
                self.add_attr( var.type_term, var.units_term, var.scalar_type, var.values[0] )
            
        br = self
        for i,dim_index in enumerate(dim_indeces):
            br = br.mean( br.dims[  dim_index - i  ] )

        return br

    def add_attr(self, type_term, units_term, scalar_type, value):
        pv = PropertyValue( type_term=type_term, units_term=units_term, scalar_type=scalar_type, value=value )        
        self.__xds.attrs['__attr_count'] += 1
        attr_name = '__attr%s' % self.__xds.attrs['__attr_count'] 
        self.__xds.attrs[attr_name] = pv    

    def __build_xds(self, type_term, dim_terms, shape, id='', name='', description=''):
        ds = xr.Dataset()                
        ds.attrs['__id'] = id
        ds.attrs['__name'] = name
        ds.attrs['__description'] = description
        ds.attrs['__type_term'] = type_term
        ds.attrs['__attr_count'] = 0        
        ds.attrs['__dim_count'] = len(dim_terms)
        ds.attrs['__data_var_count'] = 0        
        
        dim_names = []
        for i, term in enumerate(dim_terms):
            dim_name = '__dim%s' % (i+1)
            ds.attrs[dim_name + '_term'] = term
            ds.attrs[dim_name + '_var_count'] = 0
            dim_names.append(dim_name)



        ds['_'] = xr.DataArray(np.zeros(shape), dims=dim_names)

        return ds    

    def __get_attr(self, name):
        return self.__xds.attrs[name]
        
    @property
    def shape(self):
        sh = []
        for dim in self.dims:
            sh.append(dim.size)
        return sh
    
    @property
    def dim_count(self):
        return self.__get_attr('__dim_count')
    
    @property
    def data_var_count(self):
        return self.__get_attr('__data_var_count')

    @property
    def id(self):
        return self.__get_attr('__id')
    
    def set_id(self, id):
        self.__xds.attrs['__id'] = id

    @property
    def name(self):
        return self.__get_attr('__name')
    
    @property
    def description(self):
        return self.__get_attr('__description')
    
    @property
    def type_term(self):
        return self.__get_attr('__type_term')    
    
    @property
    def dims(self):
        return self.__dims          
        
    @property
    def dims_df(self):
        data = {
            'name' :[],
            'term_id': [],
            'size' :[],
            'var_count': []
        }
        for dim in self.dims:
            data['name'].append(dim.name)
            data['term_id'].append(dim.type_term.term_id)
            data['size'].append(dim.size)
            data['var_count'].append(dim.var_count)
        return pd.DataFrame(data)

    @property
    def data_vars(self):
        return self.__data_vars
    
    @property
    def attrs(self):
        items = []
        for i in range( self.__get_attr('__attr_count') ):
            attr_key = '__attr%s' % (i+1)
            items.append( self.__get_attr(attr_key) )
        return items       
            
    @property
    def properties_df(self):
        names = ['Id', 'Name', 'Description']
        types = ['','','']
        units = ['','','']
        values = [self.id, self.name, self.description]
                
        for attr in self.attrs:
            names.append(attr.name)
            types.append(str(attr.type_term))
            units.append(str(attr.units_term) if attr.units_term is not None else '')
            values.append(str(attr.value) if attr.value is not None else '')
        return pd.DataFrame({
            'Property': names,
            'Type': types,
            'Units': units,
            'Value': values
        })[[ 'Property', 'Value', 'Units']]                    

    @property
    def session_provenance(self):
        return self.__session_provenance
    
    @property
    def descriptor(self):        
        q = Query(services.indexdef.get_type_def(TYPE_NAME_BRICK))
        q.has({'id': self.id})
        return q.find_one()

    def to_json(self, exclude_data_values=False, typed_values_property_name=True):
        return json.dumps(
            self.to_dict(exclude_data_values=exclude_data_values,
                typed_values_property_name=typed_values_property_name ), 
            cls=NPEncoder)

    def to_dict(self, exclude_data_values=False, typed_values_property_name=True):
        data = {}

        # ds.attrs['__id'] = brick_id
        # ds.attrs['__name'] = json_data['name']
        # ds.attrs['__description'] = json_data['description']        
        data['id'] = self.id
        data['name'] = self.name
        data['description'] = self.description

        # term = json_data['data_type']
        # ds.attrs['__type_term'] = Term(term['oterm_ref'], term_name=term['oterm_name'])
        data['data_type'] = {
            'oterm_ref': self.type_term.term_id,
            'oterm_name': self.type_term.term_name
        }

        # Do context
        # ds.attrs['__attr_count'] = 0
        # for prop_data in json_data['array_context']:
        #     ds.attrs['__attr_count'] += 1
        #     attr_name = '__attr%s' % ds.attrs['__attr_count'] 
        #     ds.attrs[attr_name] = _parse_property_value(prop_data)

        # term = json_data['value_type']
        # type_term = Term(term['oterm_ref'], term_name=term['oterm_name'])

        # value_type = json_data['value']['scalar_type']
        # if value_type == 'oterm_ref':
        #     value = Term(json_data['value'][value_type])
        # else:
        #     value_type += '_value'
        #     value = json_data['value'][value_type]     
            
        # return PropertyValue( type_term=type_term, scalar_type=value_type, value=value )


        # TODO: units
        data['array_context'] = []
        for attr in self.attrs:
            value_key = ''
            value_val = ''
            if attr.value is not None and type(attr.value) is Term:
                value_key = attr.scalar_type
                value_val = attr.value.term_id
            else:
                value_key = attr.scalar_type + '_value'
                value_val = attr.value

            if not typed_values_property_name:
                value_key = 'value'

            data['array_context'].append({
                'value_type':{
                    'oterm_ref': attr.type_term.term_id,
                    'oterm_name': attr.type_term.term_name
                },
                'value':{
                    'scalar_type': attr.scalar_type,
                    value_key : value_val
                }
            })


        # do dimensions
        data['dim_context'] = []

        # term = dim_json['data_type']
        # dim_type_term = Term(term['oterm_ref'], term_name=term['oterm_name'])
        # dim_size = dim_json['size']
        # dim_sizes.append(dim_size)
        # vars_json = dim_json['typed_values']

        for dim in self.dims:
            dim_data = {}
            data['dim_context'].append(dim_data)

            dim_data['data_type'] = {
                'oterm_ref': dim.type_term.term_id,
                'oterm_name': dim.type_term.term_name
            }
            dim_data['size'] = dim.size
            dim_data['typed_values'] = []

            # # Do variables
            # ds.attrs[dim_name + '_var_count'] = 0
            # for var_json in vars_json:
            #     ds.attrs[dim_name + '_var_count'] += 1
                            
            #     term = var_json['value_type']
            #     vr_type_term = Term(
            #         term['oterm_ref'], term_name=term['oterm_name'])
                
            #     if 'value_units' in var_json:
            #         term = var_json['value_units']
            #         var_unit_term = Term(
            #             term['oterm_ref'], term_name=term['oterm_name'])
            #     else:
            #         var_unit_term = None
                
            #     var_scalar_type = var_json['values']['scalar_type']
            #     if var_scalar_type == 'oterm_ref':
            #         var_values = []
            #         for term_id in var_json['values']['oterm_refs']:
            #             var_values.append(Term(term_id))
            #     else:
            #         var_values = var_json['values'][var_scalar_type + '_values']


            for var in dim.vars:

                # Do type and values
                value_key = ''
                value_vals = []
                if var.scalar_type == 'oterm_ref':
                    value_key = 'oterm_refs'
                    value_vals = [t.term_id for t in var.values]
                else:
                    value_key = var.scalar_type + '_values'
                    value_vals = list(var.values)

                if not typed_values_property_name:
                    value_key = 'values'


                var_data = {
                    'value_type': {
                        'oterm_ref': var.type_term.term_id,
                        'oterm_name': var.type_term.term_name
                    },
                    'values': {
                        'scalar_type': var.scalar_type,
                        value_key: value_vals
                    },
                    'value_context': []
                }

                # Do units
                if var.units_term is not None:
                    var_data['value_units'] = {
                        'oterm_ref': var.units_term.term_id,
                        'oterm_name': var.units_term.term_name
                    }

                # Do attributes
                for attr in var.attrs:
                    value_key = ''
                    value_val = ''
                    if attr.value is not None and type(attr.value) is Term:
                        value_key = attr.scalar_type
                        value_val = attr.value.term_id
                    else:
                        value_key = attr.scalar_type + '_value'
                        value_val = attr.value

                    if not typed_values_property_name:
                        value_key = 'value'

                    var_data['value_context'].append({
                        'value_type':{
                            'oterm_ref': attr.type_term.term_id,
                            'oterm_name': attr.type_term.term_name
                        },
                        'value':{
                            'scalar_type': attr.scalar_type,
                            value_key : value_val
                        }
                    })
                dim_data['typed_values'].append(var_data)
            
        # do data
        data['typed_values'] = []
        for vard in self.data_vars:
            value_key = ''
            value_vals = []
            if vard.scalar_type == 'oterm_ref':
                value_key = 'oterm_refs'
                value_vals = [t.term_id for t in vard.values]
            else:
                value_key = vard.scalar_type + '_values'
                value_vals = list(vard.values)

            if not typed_values_property_name:
                value_key = 'values'

            values_data = {
                'value_type': {
                    'oterm_ref': vard.type_term.term_id,
                    'oterm_name': vard.type_term.term_name
                },                
                'value_context': []
            }
            if not exclude_data_values:
                values_data['values'] = {
                    'scalar_type': vard.scalar_type,
                    value_key: value_vals
                }

            # Do units
            if vard.units_term is not None:
                values_data['value_units'] = {
                    'oterm_ref': vard.units_term.term_id,
                    'oterm_name': vard.units_term.term_name
                }

            # Do attributes
            for attr in vard.attrs:
                value_key = ''
                value_val = ''
                if attr.value is not None and type(attr.value) is Term:
                    value_key = attr.scalar_type
                    value_val = attr.value.term_id
                else:
                    value_key = attr.scalar_type + '_value'
                    value_val = attr.value

                if not typed_values_property_name:
                    value_key = 'value'

                values_data['value_context'].append({
                    'value_type':{
                        'oterm_ref': attr.type_term.term_id,
                        'oterm_name': attr.type_term.term_name
                    },
                    'value':{
                        'scalar_type': attr.scalar_type,
                        value_key : value_val
                    }
                })

            data['typed_values'].append(values_data)
        return data

    @property
    def full_type(self):
        dim_types = [dim.type_term.term_name for dim in self.dims]
        full_type = '%s<%s>' % ( self.type_term.term_name, ', '.join(dim_types))
        return full_type


    def _repr_html_(self):
        def _row2_header(c):
            return '<tr><td bgcolor="#F5F5FF" colspan=2 style="text-align:left;">%s</td></tr>' % (c)       
        def _row2(c1, c2):
            cell = '<td bgcolor="#FFFFFF" style="padding-left:20px; text-align:left">%s</td>'
            patterm = '<tr>' + ''.join([ cell for i in range(2) ] ) + '</tr>'
            return patterm % (c1,c2)
        
        
        dim_types = [dim.type_term.term_name for dim in self.dims]
        full_type = '%s &lt; %s &gt;' % ( self.type_term.term_name, ', '.join(dim_types))
        
        rows = [
            _row2_header('<b>DataBrick: </b> %s' % full_type),
            _row2_header('<i>Properties:</i>'),               
            _row2('Id', self.id),
            _row2('Type', self.type_term),
            _row2('Shape', self.shape),
            _row2('Name', self.name)
            # _row2('Description', self.description),
        ]
        
        # Data
        rows.append(_row2_header('<i>Data:</i>'))
        for data_var in self.data_vars:
            rows.append( _row2( data_var.long_name, '' ))

        # rows.append( _row2('Type', data_var.type_term)  )
        # rows.append( _row2('Units', data_var.units_term)  )
        # rows.append( _row2('Sclar type', data_var.scalar_type)  )
                              
        # Dimensions
        rows.append(_row2_header('<i>Dimensions:</i>'))
        for i, dim in enumerate(self.dims):
            var_names = []
            for var in dim.vars:
                data_example = ', '.join( str(v) for v in var.values[:DATA_EXAMPLE_SIZE] )
                data_suffix = ' ...' if dim.size > DATA_EXAMPLE_SIZE else ''
                data = '[%s%s]' % (data_example, data_suffix)

                var_names.append(var.long_name + ':  ' + data)
            
            rows.append( _row2( '%s. %s, size=%s' % (i +1, dim.type_term.term_name, dim.size),  
                              '<i>Variables:</i><br> %s' % '<br>'.join(var_names) ))

        # Attributes
        rows.append(_row2_header('<i>Attributes:</i>'))
        for attr in self.attrs:
            val = attr.value
            if attr.units_term is not None:
                val = '%s (%s)' % (val, attr.units_term.term_name)
            rows.append( _row2(attr.type_term.term_name, val)  )
            
        return '<table>%s</table>' % ''.join(rows)   

    def _get_all_term_ids(self):
        term_ids = set()
        for term in self._get_property_terms():
            term_ids.add(term.term_id)

        for term in self._get_value_terms():
            term_ids.add(term.term_id)

        return term_ids

    def _get_property_terms(self):
        id2terms = {}
        id2terms[self.type_term.term_id] = self.type_term


        for data_var in self.data_vars:        
            id2terms[data_var.type_term.term_id] = data_var.type_term
            if data_var.units_term:
                id2terms[data_var.units_term.term_id] = data_var.units_term

        for attr in self.attrs:
            attr._collect_property_terms(id2terms)

        for dim in self.dims:
            dim._collect_property_terms(id2terms)

        return list(id2terms.values())

    def _get_value_terms(self):
        id2terms = {}
        for attr in self.attrs:
            attr._collect_value_terms(id2terms)

        for dim in self.dims:
            dim._collect_value_terms(id2terms)
        return list(id2terms.values())

    def _get_term_id_2_values(self):
        term_id_2_values = {}
        for attr in self.attrs:
            attr._collect_all_term_values(term_id_2_values)
        for d in self.dims:
            d._collect_all_term_values(term_id_2_values)
        return term_id_2_values

    def _get_all_term_values(self):
        values = set()
        term_id_2_values = self._get_term_id_2_values()
        for term_vals in term_id_2_values.values():
            for val in term_vals:
                values.add(val)
        return values        
        
    def add_data_var(self, type_term, units_term, values, scalar_type='text'):
        dim_names = [ '__dim%s'%(i+1)  for i in range(self.dim_count) ]
        var = Brick._xds_build_var(self, None, self.__xds, '__data', dim_names, 
            type_term, units_term, values, scalar_type)

        self.__data_vars.append(var)
        self.__inflate_data_vars()

    def mean(self, dim):
        dim_index = dim.dim_index
        dim_name = dim.name
        # print('Dim index = ', dim_index)

        dim_prfix = '__dim%s' % (dim_index + 1)

        # build new dim names
        new_dim_names = [ '__dim%s' %(i+1) for i in range(self.dim_count -1)  ]


        #------    
        # Build xds
        xds = xr.Dataset()

        # add all attributes 
        for attr_name in self.__xds.attrs:
            if attr_name == '__dim_count':
                xds.attrs[attr_name] = self.dim_count - 1
            elif attr_name.startswith('__dim'):
                # skip the dim data with dim_index amd decrese dim indexes
                attr_name_vals = attr_name[len('__dim'):].split('_')
                di = int(attr_name_vals[0])
                # print( 'attr_name', attr_name)
                # print('\tattr_name_vals', attr_name_vals)
                # print('\tdi', di)
                if di == dim_index + 1:
                    continue
                elif di > dim_index + 1:
                    attr_name_vals[0] = str(di - 1)
                
                new_attr_name = '__dim' +  '_'.join(attr_name_vals)
                # print('\tnew_attr_name', new_attr_name)

                xds.attrs[new_attr_name] = self.__xds.attrs[attr_name]
            else:
                xds.attrs[attr_name] = self.__xds.attrs[attr_name]


        # do dim variables
        new_dim_index = 0
        for i, dim in enumerate(self.dims):
            # skip dimvars with dim_index
            if i == dim_index:
                continue
            prev_dim_prefix = '__dim%s' % (i + 1) 
            new_dim_prefix = '__dim%s' % (new_dim_index + 1)
            new_dim_index += 1
            for var_index, var in enumerate(dim.vars):
                prev_var_prefix = '%s_var%s' % (prev_dim_prefix, var_index + 1) 
                new_var_prefix = '%s_var%s' % (new_dim_prefix, var_index + 1)
                xds[new_var_prefix] = xr.DataArray(var.values, dims=new_dim_prefix)
                for attr_name in self.__xds[prev_var_prefix].attrs:
                    xds[new_var_prefix].attrs[attr_name] = self.__xds[prev_var_prefix].attrs[attr_name]
        
        # do data vars
        for i, data_var in enumerate(self.data_vars):
            var_prefix = '__data_var%s' % (i+1)
            values = self.__xds[var_prefix].mean(dim=dim_prfix).values
            xds[var_prefix] = xr.DataArray(values, dims=new_dim_names)
            for attr_name in self.__xds[var_prefix].attrs:
                xds[var_prefix].attrs[attr_name] = self.__xds[var_prefix].attrs[attr_name]

        brick = Brick(xds=xds)
        b_prov = self.get_base_session_provenance()        
        mean_prov = BrickProvenance('mean', ['dim_index:%s' % dim_index, 'dim_name:%s' % dim_name])
        b_prov.provenance_items.append(mean_prov)
        brick.session_provenance.provenance_items.append(b_prov)

        return brick

    def get_base_session_provenance(self):
        base_prov = BrickProvenance('parent brick', ['brick:%s' % self.id])
        for prov in self.__session_provenance.provenance_items:
            base_prov.provenance_items.append(prov)
        return base_prov



    def save(self, process_term=None, person_term=None, campaign_term=None, input_obj_ids=None):

        if process_term is None:
            raise ValueError('process_term should be specified')
        
        if input_obj_ids is None:
            raise ValueError('input_obj_ids should be specified')


        # user_profile = services.user_profile
        # if person_term is None:
        #     person_term = user_profile.default_person
        
        # if campaign_term is None:
        #     campaign_term = user_profile.default_campaign

        brick_data_holder = BrickDataHolder(self)
        services.workspace.save_data(brick_data_holder)
        self.set_id(brick_data_holder.id)

        process_data = {
            'person': str(person_term),
            'process': str(process_term),
            'campaign': str(campaign_term),
            'date_start': datetime.datetime.today().strftime('%Y-%m-%d'),
            'date_end': datetime.datetime.today().strftime('%Y-%m-%d'),
            'input_objects': input_obj_ids,
            'output_objects': ['%s:%s' % ( TYPE_NAME_BRICK, brick_data_holder.id)]
        }
        services.workspace.save_process(ProcessDataHolder(process_data)) 


        
class BrickDimension:
    def __init__(self, brick,  xds, dim_index):
        self.__xds = xds
        self.__brick = brick
        self.__dim_index = dim_index
        self.__dim_prefix = '__dim%s' % (dim_index+1)
        self.__vars = []
        for i in range( self.var_count ):
            var_prefix =  '%s_var%s' % (self.__dim_prefix, i+1)
            
            bv = BrickVariable(brick, self,  xds, var_prefix) 
            self.__vars.append(bv)
        
        self.__inflate_vars()
            
    def __get_attr(self, suffix):
        return self.__xds.attrs[self.__dim_prefix + suffix]

    @property
    def dim_index(self):
        return self.__dim_index

    @property
    def var_count(self):
        return self.__get_attr('_var_count') 
        
    @property
    def type_term(self):
        return self.__get_attr('_term') 
        

    @property
    def name(self):
        return self.type_term.property_name
    
    @property
    def size(self):
        return self.__xds[self.__dim_prefix].size
    
    
    @property 
    def vars(self):
        return self.__vars
    
    @property
    def vars_df(self):
        data = {}
        for var in self.vars:
            data[var.long_name] = var.values
        return pd.DataFrame(data)    

    def where(self, dim_filter):
        kwargs = {self.__dim_prefix: dim_filter.bool_array}
        xds = self.__xds.isel(kwargs)

        b_prov = self.__brick.get_base_session_provenance()

        where_prov = BrickProvenance('where', ['dim:%s' % self.name])
        for prov in dim_filter.provenance_items:
            where_prov.provenance_items.append(prov)
        
        b_prov.provenance_items.append(where_prov)

        brick = Brick(xds=xds)
        brick.session_provenance.provenance_items.append(b_prov)

        return brick 
    

    def  __inflate_vars(self):
        for i,var in enumerate(self.vars):        
           self.__dict__['VAR%s_%s' %(i+1, var.var_name)] = var


    def add_var(self, type_term, units_term, values, scalar_type='text'):
        var = Brick._xds_build_var(self.__brick, self, self.__xds, self.__dim_prefix, self.__dim_prefix, 
            type_term, units_term, values, scalar_type)

        self.__vars.append(var)
        self.__inflate_vars()

    def add_brick_data_var(self, match_src_var, match_dst_var, data_var):
        # index dst values
        val_2_index = {}
        for i,val in enumerate(match_dst_var.values):
            val_2_index[val] = i
        
        # build values
        values = []
        for val in match_src_var.values:
            dst_index = val_2_index.get(val)
            values.append(  data_var.values[dst_index] if dst_index is not None else None  )
        
        # build variable
        var = Brick._xds_build_var(self.__brick, self, self.__xds, self.__dim_prefix, self.__dim_prefix, 
            data_var.type_term, data_var.units_term, values, data_var.scalar_type)

        self.__vars.append(var)
        self.__inflate_vars()

        return self.vars_df.head(10)




    def add_core_type_var(self, core_type, core_prop_name):
        type_def = services.typedef.get_type_def(core_type)
        if type_def is None:
            raise ValueError('Core type %s does not exist' % core_type)

        try:
            prop_def = type_def.property_def(core_prop_name)
        except:
            raise ValueError('There are no property %s in the core type %s' % (core_prop_name, core_type))

        # check if dim has variable with term id which is PK of the 
        # core type

        pk_def = None
        pk_var = None
        for var in self.vars:
            pk_prop_def = services.typedef.get_term_pk_prop_def(var.type_term.term_id)
            if pk_prop_def is not None and pk_prop_def.type_def.name == core_type:
                pk_var = var
                pk_def = pk_prop_def
                break

        if pk_def is None:
            raise ValueError('There is no variable which is PK for the core type. Please do map_to_core_type first.' % core_type)


        # build query
        values = []
        for val in pk_var.values:
            if val is not None:
                values.append(val)

        q = Query(services.indexdef.get_type_def(core_type))
        q.has({pk_def.name:{'in':values}})
        rs = q.find()

        # build data
        pk2val = {}
        for item in rs.items:
            pk_val = item[pk_def.name]
            prop_value = item[core_prop_name]
            pk2val[pk_val] = prop_value 

        data = []
        for val in pk_var.values:
            if val is None:
                data.append(None)
            else:
                data.append( pk2val.get(val) )

        # Build variable
        # type_term = Term(prop_def.term_id, refresh=True)
        type_term = services.term_provider.get_term(prop_def.term_id) 
        units_term = None
        scalar_type = prop_def.type

        var = Brick._xds_build_var(self.__brick, self, self.__xds, self.__dim_prefix, self.__dim_prefix, 
            type_term, units_term, data, scalar_type)

        self.__vars.append(var)
        self.__inflate_vars()


        prov = BrickProvenance('add_core_type_var', 
            ['core_type:%s' % core_type, 
            'core_prop_name:%s' % core_prop_name,
            'dim_index:%s' % self.dim_index,
            'dim_name:%s' % self.name])

        self.__brick.session_provenance.provenance_items.append(prov)

        return self.vars_df.head(10)

    def map_to_core_type(self, dim_var, core_type, core_prop_name):

        # build query
        values = set() 
        for val in dim_var.values:
            if val is not None:
                values.add(val)

        type_def = services.typedef.get_type_def(core_type)
        pk_prop_name =  type_def.pk_property_def.name
        q = Query(services.indexdef.get_type_def(core_type))
        q.has({core_prop_name: {'in': list(values)} })
        rs = q.find()

        # build data
        prop2pk_ids = {}
        for item in rs.items:
            prop_value = item[core_prop_name]
            pk_value = item[pk_prop_name]
            prop2pk_ids[prop_value] = pk_value 

        data = []
        for val in dim_var.values:
            if val is not None:
                pk_val = prop2pk_ids.get(val)
            else:
                pk_val = None
            data.append(pk_val)

        # Build variable
        # type_term = Term(type_def.pk_property_def.term_id, refresh=True)
        type_term = services.term_provider.get_term(type_def.pk_property_def.term_id)
        units_term = None
        scalar_type = type_def.pk_property_def.type

        var = Brick._xds_build_var(self.__brick, self, self.__xds, self.__dim_prefix, self.__dim_prefix, 
            type_term, units_term, data, scalar_type)

        self.__vars.append(var)
        self.__inflate_vars()

        prov = BrickProvenance('map_to_core_type', 
            ['core_type:%s' % core_type, 
            'core_prop_name:%s' % core_prop_name,
            'dim_index:%s' % self.dim_index,
            'dim_name:%s' % self.name,
            'var_name:%s' % dim_var.name])

        self.__brick.session_provenance.provenance_items.append(prov)

        return self.vars_df.head(10)

    def _collect_property_terms(self, id2terms):
        id2terms[self.type_term.term_id] = self.type_term
        for v in self.vars:
            v._collect_property_terms(id2terms)

    def _collect_value_terms(self, id2terms):
        for v in self.vars:
            v._collect_value_terms(id2terms)

    def _collect_all_term_values(self, term_id_2_values):
        for v in self.vars:
            v._collect_all_term_values(term_id_2_values)    

    def _repr_html_(self):
        def _row2_header(c):
            return '<tr><td colspan=2 style="text-align:left;">%s</td></tr>' % (c)       
        def _row2(c1, c2):
            cell = '<td style="padding-left:20px; text-align:left">%s</td>'
            patterm = '<tr>' + ''.join([ cell for i in range(2) ] ) + '</tr>'
            return patterm % (c1,c2)
        
        
        rows = [
            _row2_header('<b>Dimnesion</b>'),
            _row2('Name', self.name),
            _row2('Type', self.type_term),
            _row2('Size', self.size),
            _row2_header('<i>Variables:</i>')                  
        ]
                                  
        for var in self.vars:
            name = var.long_name                
            data_example = ', '.join( str(v) for v in var.values[:DATA_EXAMPLE_SIZE] )
            data_suffix = ' ...' if self.size > DATA_EXAMPLE_SIZE else ''
            data = '[%s%s]' % (data_example, data_suffix)
            rows.append(_row2(name, data))
        
        return '<table>%s</table>' % ''.join(rows)     
    
class BrickVariable:
    def __init__(self, brick, dim,  xds, var_prefix):
        self.__brick = brick
        self.__dim = dim
        self.__xds = xds
        self.__var_prefix = var_prefix
        
    def __get_attr(self, name):
        return self.__xds[self.__var_prefix].attrs[name]
            
    @property    
    def name(self):
        return self.__get_attr('__name')
        
    @property    
    def type_term(self):
        return self.__get_attr('__type_term')
        
    @property    
    def units_term(self):
        return self.__get_attr('__units_term')
    
    @property    
    def scalar_type(self):
        return self.__get_attr('__scalar_type')    
        
    @property
    def attrs(self):
        items = []
        for i in range( self.__get_attr('__attr_count') ):
            attr_key = '__attr%s' % (i+1)
            items.append( self.__get_attr(attr_key) )
        return items

    @property
    def values(self):
        return self.__xds[self.__var_prefix].data
        
    @property
    def long_name(self):
        items = []
        items.append(self.type_term.term_name)
        if self.has_attrs():
            items.append('of')
            for attr in self.attrs:
                val  = attr.value
                if type(val) is Term:
                    val = val.term_name
                items.append(val)

        if self.has_units():
            items.append( '(%s)' % self.units_term.term_name )

        return ' '.join(items)

    @property
    def var_name(self):
        items = []
        items.append(self.type_term.term_name)
        if self.has_attrs():
            items.append('of')
            for attr in self.attrs:
                val  = attr.value
                if type(val) is Term:
                    val = val.term_name
                items.append(val)

        return to_var_name('',' '.join(items))


    def map_to_core_type(self, core_type, core_prop_name):
        return self.__dim.map_to_core_type(self, core_type, core_prop_name)


    def is_none(self):
        return [  val is None for val in  self.values]

    def is_not_none(self):
        return [  val is not None for val in  self.values]

    def has_units(self):
        return self.units_term is not None

    def has_attrs(self):
        return self.__get_attr('__attr_count') > 0

    # def data_df(self):
    #     return pd.DataFrame(self.data, columns=[self.name])
        
    def __eq__(self,val):
        bool_array = (self.__xds[self.__var_prefix] == val).data
        provenance = BrickProvenance('__eq__', ['var:%s' % self.name, val])
        return DimensionFilter(self.__dim, provenance, bool_array)

    def __ne__(self,val):
        bool_array = (self.__xds[self.__var_prefix] != val).data
        provenance = BrickProvenance('__ne__', ['var:%s' % self.name, val])
        return DimensionFilter(self.__dim, provenance, bool_array)
    
    def __gt__(self,val):
        bool_array = (self.__xds[self.__var_prefix] > val).data
        provenance = BrickProvenance('__gt__', ['var:%s' % self.name, val])
        return DimensionFilter(self.__dim, provenance, bool_array)

    def __ge__(self,val):
        bool_array = (self.__xds[self.__var_prefix] >= val).data
        provenance = BrickProvenance('__ge__', ['var:%s' % self.name, val])
        return DimensionFilter(self.__dim, provenance, bool_array)
    
    def __lt__(self,val):
        bool_array = (self.__xds[self.__var_prefix] < val).data
        provenance = BrickProvenance('__lt__', ['var:%s' % self.name, val])
        return DimensionFilter(self.__dim, provenance, bool_array)
    
    def __le__(self,val):
        bool_array = (self.__xds[self.__var_prefix] <= val).data
        provenance = BrickProvenance('__le__', ['var:%s' % self.name, val])
        return DimensionFilter(self.__dim, provenance, bool_array)

    def _collect_property_terms(self, id2terms):
        id2terms[self.type_term.term_id] = self.type_term

    def _collect_value_terms(self, id2terms):
        for val in self.values:
            if type(val) is Term:
                term = val
                id2terms[term.term_id] = term

    def _collect_all_term_values(self, term_id_2_values):
        _collect_all_term_values(term_id_2_values, self.type_term.term_id, self.values)

    def _repr_html_(self):
        def _row2_header(c):
            return '<tr><td colspan=2 style="text-align:left;">%s</td></tr>' % (c)       
        def _row2(c1, c2):
            cell = '<td style="padding-left:20px; text-align:left">%s</td>'
            patterm = '<tr>' + ''.join([ cell for i in range(2) ] ) + '</tr>'
            return patterm % (c1,c2)
                        
        data_example = '<br>'.join( str(v) for v in self.values[:DATA_EXAMPLE_SIZE] )
        data_suffix = '<br> ...' if len(self.values) > DATA_EXAMPLE_SIZE else ''
        data = '%s%s' % (data_example, data_suffix)
        
        rows = [
            _row2_header('<b>Dimnesion Variable</b>'),
            _row2('Name', self.name),
            _row2('Type', self.type_term),
            _row2('Units', self.units_term),
            _row2('Size', len(self.values)),
            _row2('Values', data)          
        ]
        if len(self.attrs) > 0:
            rows.append(_row2_header('<i>Attributes:</i>'))
            for attr in self.attrs:
                name = attr.type_term.term_name
                val = attr.value
                if attr.units_term is not None:
                    val += ' (%s)' % attr.units_term.term_name
                rows.append( _row2(name, val) )        
        
        return '<table>%s</table>' % ''.join(rows) 



class BrickProvenance:
    def __init__(self, operation, args):
        self.__operation = operation
        self.__args = args
        self.__provenance_items = []
        self.__timestamp = gmtime()
    
    @property
    def operation(self):
        return self.__operation

    @property
    def args(self):
        return self.__args

    @property
    def provenance_items(self):
        return self.__provenance_items

    def _html_rows(self, level):
        rows = []

        rows.append('<div style="margin-left:20px">')
        rows.append( '%s: %s - <span style="color:gray">%s</span> ' % (self.operation, self.args, strftime("%d/%m/%Y %H:%M:%S", self.__timestamp)) )
        for prov in self.provenance_items:
            p_rows = prov._html_rows(level +1)
            for p_row in p_rows:
                rows.append(p_row)

        rows.append('</div>') 
        return rows

    def _repr_html_(self):
        return  ''.join(self._html_rows(0)) 

class DataFilter:
    def __init__(self, brick, provenance, bool_array):
        self.__brick = brick
        self.__provenance_items = [provenance]
        self.__bool_array = bool_array

    @property
    def brick(self):
        return self.__brick
    
    @property
    def provenance_items(self):
        return self.__provenance_items
    
    @property
    def bool_array(self):
        return self.__bool_array


    def __logical_trasnform(self, data_filter, trasnform_name, trasnform_method):
        if self.__brick != data_filter.brick:
            raise ValueError('Error: bricks are different')
        
        new_prov = BrickProvenance(trasnform_name,[])
        for prov in self.__provenance_items:
            new_prov.provenance_items.append(prov)

        for prov in data_filter.provenance_items:
            new_prov.provenance_items.append(prov)
        
        self.__provenance_items = [new_prov]        
        self.__bool_array = trasnform_method(self.__bool_array, data_filter.bool_array)

        return self


    def __and__(self, data_filter):
        return self.__logical_trasnform(data_filter, '__and__', np.logical_and)

    def __or__(self, data_filter):
        return self.__logical_trasnform(data_filter, '__or__', np.logical_or)




class DimensionFilter:
    def __init__(self, brick_dim, provenance, bool_array):
        self.__brick_dim = brick_dim
        self.__provenance_items = [provenance]
        self.__bool_array = bool_array
    
    @property
    def brick_dim(self):
        return self.__brick_dim
    
    @property
    def provenance_items(self):
        return self.__provenance_items
    
    @property
    def bool_array(self):
        return self.__bool_array
    
    def __logical_trasnform(self, dim_filter, trasnform_name, trasnform_method):
        if self.__brick_dim != dim_filter.brick_dim:
            raise ValueError('Error: can not operate on different dimensions')
        
        new_prov = BrickProvenance(trasnform_name,[])
        for prov in self.__provenance_items:
            new_prov.provenance_items.append(prov)

        for prov in dim_filter.provenance_items:
            new_prov.provenance_items.append(prov)
        
        self.__provenance_items = [new_prov]
        self.__bool_array = trasnform_method(self.__bool_array, dim_filter.bool_array)

        return self


    def __and__(self, data_filter):
        return self.__logical_trasnform(data_filter, '__and__', np.logical_and)

    def __or__(self, data_filter):
        return self.__logical_trasnform(data_filter, '__or__', np.logical_or)

    
