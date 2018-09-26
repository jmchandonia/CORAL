import json
import numpy as np
import pandas as pd
import xarray as xr
import re
from .ontology import Term
from . import services
from .utils import to_var_name


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
        type_term = Term(term['oterm_ref'], term_name=term['oterm_name'])

        value_type = json_data['value']['scalar_type']
        if value_type == 'oterm_ref':
            value = Term(json_data['value'][value_type])
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
        ds.attrs['__type_term'] = Term(term['oterm_ref'], term_name=term['oterm_name'])

        # Do context
        # ds.attrs['__attr_count'] = 2
        # ds.attrs['__attr1'] = PropertyValue( type_term=Term('AA:145', 'ENIMGA Campaign'), value=Term('AA:146', 'Metal')  )
        # ds.attrs['__attr2'] = PropertyValue( type_term=Term('AA:145', 'Genome'), value='E.coli'  )

        ds.attrs['__attr_count'] = 0
        for prop_data in json_data['array_context']:
            ds.attrs['__attr_count'] += 1
            attr_name = '__attr%s' % ds.attrs['__attr_count'] 
            ds.attrs[attr_name] = PropertyValue.read_json(prop_data)        
        
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
            dim_type_term = Term(term['oterm_ref'], term_name=term['oterm_name'])
            dim_size = dim_json['size']
            dim_sizes.append(dim_size)
            vars_json = dim_json['typed_values']
            
            ds.attrs[dim_name + '_term'] = dim_type_term        
            
            # Do variables
            ds.attrs[dim_name + '_var_count'] = 0
            for var_json in vars_json:
                ds.attrs[dim_name + '_var_count'] += 1
                            
                term = var_json['value_type']
                vr_type_term = Term(
                    term['oterm_ref'], term_name=term['oterm_name'])
                
                if 'value_units' in var_json:
                    term = var_json['value_units']
                    var_unit_term = Term(
                        term['oterm_ref'], term_name=term['oterm_name'])
                else:
                    var_unit_term = None
                
                var_scalar_type = var_json['values']['scalar_type']
                if var_scalar_type == 'oterm_ref':
                    var_values = []
                    for term_id in var_json['values']['oterm_refs']:
                        var_values.append(Term(term_id))
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
                        var.attrs['__attr_count'] += 1
                        attr_name = '__attr%s' % var.attrs['__attr_count'] 
                        var.attrs[attr_name] = PropertyValue.read_json(attr_json)
                
                
                var_name = '%s_var%s' % (dim_name, ds.attrs[dim_name + '_var_count'])
                ds[var_name] = var

        

        # Do data
        values_json = json_data['typed_values']
        term = values_json['value_type']
        value_type_term = Term(term['oterm_ref'], term_name=term['oterm_name'])

        if 'value_units' in values_json:
            term = values_json['value_units']
            value_unit_term = Term(
                term['oterm_ref'], term_name=term['oterm_name'])
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
                da.attrs['__attr_count'] += 1
                attr_name = '__attr%s' % da.attrs['__attr_count'] 
                da.attrs[attr_name] = PropertyValue.read_json(attr_json)
        
        ds['__data_var'] = da
        return Brick(ds)    



    def __init__(self, xds):
        self.__xds = xds
        self.__dims = []
        for i in range( self.dim_count ):
            dim = BrickDimension(xds, i)
            self.__dims.append( dim )
            self.__dict__['DIM%s_%s' %(i+1, dim.name) ] = dim
            
        self.__data_var = BrickVariable(xds, '__data_var')
        self.__dict__['DATA1_%s' % self.__data_var.var_name] = self.__data_var
       
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
        return [self.__data_var]
    
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

    def to_json(self):
        return json.dumps(self.to_dict(), cls=NPEncoder)

    def to_dict(self):
        data = {}

        # ds.attrs['__id'] = brick_id
        # ds.attrs['__name'] = json_data['name']
        # ds.attrs['__description'] = json_data['description']        
        data['brick_id'] = self.id
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
        vard = self.data_vars[0]
        value_key = ''
        value_vals = []
        if vard.scalar_type == 'oterm_ref':
            value_key = 'oterm_refs'
            value_vals = [t.term_id for t in vard.values]
        else:
            value_key = vard.scalar_type + '_values'
            value_vals = list(vard.values)

        values_data = {
            'value_type': {
                'oterm_ref': vard.type_term.term_id,
                'oterm_name': vard.type_term.term_name
            },
            'values': {
                'scalar_type': vard.scalar_type,
                value_key: value_vals
            },
            'value_context': []
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

        data['typed_values'] = values_data
        return data

    @property
    def type(self):
        dim_types = [dim.type_term.term_name for dim in self.dims]
        full_type = '%s<%s>' % ( self.type_term.term_name, ', '.join(dim_types))
        return full_type


    def _repr_html_(self):
        def _row2_header(c):
            return '<tr><td colspan=2 style="text-align:left;">%s</td></tr>' % (c)       
        def _row2(c1, c2):
            cell = '<td style="padding-left:20px; text-align:left">%s</td>'
            patterm = '<tr>' + ''.join([ cell for i in range(2) ] ) + '</tr>'
            return patterm % (c1,c2)
        
        
        dim_types = [dim.type_term.term_name for dim in self.dims]
        full_type = '%s &lt; %s &gt;' % ( self.type_term.term_name, ', '.join(dim_types))
        
        rows = [
            _row2_header('<b>DataBrick: </b> %s' % full_type),
            _row2_header('<i>Properties:</i>'),               
            _row2('Id', self.id),
            _row2('Name', self.name),
            _row2('Description', self.description),
            _row2('Type', self.type_term),
            _row2('Shape', self.shape)
        ]
        
        # Data
        data_var = self.data_vars[0]
        rows.append(_row2_header('<i>Data:</i>'))
        rows.append( _row2('Type', data_var.type_term)  )
        rows.append( _row2('Units', data_var.units_term)  )
        rows.append( _row2('Sclar type', data_var.scalar_type)  )
                              
        # Dimensions
        rows.append(_row2_header('<i>Dimensions:</i>'))
        for i, dim in enumerate(self.dims):
            var_names = []
            for var in dim.vars:
                data_example = ', '.join( str(v) for v in var.values[:DATA_EXAMPLE_SIZE] )
                data_suffix = ' ...' if dim.size > DATA_EXAMPLE_SIZE else ''
                data = '[%s%s]' % (data_example, data_suffix)

                var_names.append(var.long_name + ':  ' + data)
            
            rows.append( _row2( '%s. %s: %s' % (i +1, dim.type_term.term_name, dim.size),  
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

        data_var = self.data_vars[0]        
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
        
        
class BrickDimension:
    def __init__(self, xds, dim_index):
        self.__xds = xds
        self.__dim_index = dim_index
        self.__dim_prefix = '__dim%s' % (dim_index+1)
        self.__vars = []
        for i in range( self.var_count ):
            var_prefix =  '%s_var%s' % (self.__dim_prefix, i+1)
            
            bv = BrickVariable(xds, var_prefix) 
            self.__vars.append(bv)
            self.__dict__['VAR%s_%s' %(i+1, bv.var_name)] = bv
            
    def __get_attr(self, suffix):
        return self.__xds.attrs[self.__dim_prefix + suffix]
            
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
    
    def where(self, bool_array):
        kwargs = {self.__dim_prefix: bool_array}
        xds = self.__xds.isel(kwargs)
        return Brick(xds)    
    
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
    def __init__(self, xds, var_prefix):
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

    def has_units(self):
        return self.units_term is not None

    def has_attrs(self):
        return self.__get_attr('__attr_count') > 0

    # def data_df(self):
    #     return pd.DataFrame(self.data, columns=[self.name])
        
    def __eq__(self,val):
        return (self.__xds[self.__var_prefix] == val).data
    
    def __ne__(self,val):
        return (self.__xds[self.__var_prefix] != val).data
    
    def __gt__(self,val):
        return (self.__xds[self.__var_prefix] > val).data

    def __ge__(self,val):
        return (self.__xds[self.__var_prefix] >= val).data
    
    def __lt__(self,val):
        return (self.__xds[self.__var_prefix] < val).data
    
    def __le__(self,val):
        return (self.__xds[self.__var_prefix] <= val).data

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


# def read_brick(brick_id, file_name):
#     json_data = json.loads(open(file_name).read())
#     return Brick(brick_id, json_data=json_data)


# class BrickDimensionVariable:
#     def __init__(self, json_data=None):
#         term = json_data['value_type']
#         self.type_term = Term(
#             term['oterm_ref'], term_name=term['oterm_name'])

#         # term = json_data['value_units']
#         # self.units_term = Term(
#         #     term['oterm_ref'], term_name=term['oterm_name'])

#         term_value_type = json_data['values']['scalar_type']
#         if term_value_type == 'oterm_ref':
#             term_value_type = 'oterm_refs'
#             self.values = []
#             for term_id in json_data['values'][term_value_type]:
#                 self.values.append(Term(term_id))
#         else:
#             term_value_type += '_values'
#             self.values = json_data['values'][term_value_type]

#     def _collect_property_terms(self, id2terms):
#         id2terms[self.type_term.term_id] = self.type_term

#     def _collect_value_terms(self, id2terms):
#         for val in self.values:
#             if type(val) is Term:
#                 term = val
#                 id2terms[term.term_id] = term

#     def _collect_all_term_values(self, term_id_2_values):
#         term_id = self.type_term.term_id
#         values = term_id_2_values.get(term_id)
#         if values is None:
#             values = set()
#             term_id_2_values[term_id] = values
#         for val in self.values:
#             if type(val) is str:
#                 values.add(val)
#             elif type(val) is Term:
#                 values.add(val.term_name)


# class BrickDimension:
#     def __init__(self, json_data=None):

#         term = json_data['data_type']
#         self.dim_type_term = Term(
#             term['oterm_ref'], term_name=term['oterm_name'])
#         self.dim_size = json_data['size']
#         self.variables = []
#         for variable in json_data['typed_values']:
#             self.variables.append(BrickDimensionVariable(json_data=variable))
#         self.__inflate_variables()

#     def __inflate_variables(self):
#         for v in self.variables:
#             self.__dict__['VAR_' + v.type_term.property_name] = v

#     def _collect_property_terms(self, id2terms):
#         id2terms[self.dim_type_term.term_id] = self.dim_type_term
#         for v in self.variables:
#             v._collect_property_terms(id2terms)

#     def _collect_value_terms(self, id2terms):
#         for v in self.variables:
#             v._collect_value_terms(id2terms)

#     def _collect_all_term_values(self, term_id_2_values):
#         for v in self.variables:
#             v._collect_all_term_values(term_id_2_values)

#     def _repr_html_(self):
#         def _row(prop, value):
#             return '<tr><td>%s</td><td>%s</td></tr>' % (prop, value)

#         rows = [
#             _row('Type', str(self.dim_type_term)),
#             _row('Size', str(self.dim_size))
#         ]

#         for v in self.variables:
#             rows.append(
#                 _row('Variable', str(v.type_term)),
#             )

#         return '<table>%s</table>' % ''.join(rows)


# class BrickProperty:
#     def __init__(self, json_data=None):
#         term = json_data['value_type']
#         self.type_term = Term(term['oterm_ref'], term_name=term['oterm_name'])

#         value_type = json_data['value']['scalar_type']
#         if value_type == 'oterm_ref':
#             self.value = Term(json_data['value'][value_type])
#         else:
#             value_type += '_value'
#             self.value = json_data['value'][value_type]


# class BrickContext:
#     def __init__(self, json_data=None):
#         self.properties = []
#         for prop_data in json_data:
#             self.properties.append(BrickProperty(prop_data))

#     def _collect_property_terms(self, id2terms):
#         for prop in self.properties:
#             id2terms[prop.type_term.term_id] = prop.type_term

#     def _collect_value_terms(self, id2terms):
#         for prop in self.properties:
#             if type(prop.value) is Term:
#                 term = prop.value
#                 id2terms[term.term_id] = term

#     def _collect_all_term_values(self, term_id_2_values):
#         for prop in self.properties:
#             term_id = prop.type_term.term_id
#             values = term_id_2_values.get(term_id)
#             if values is None:
#                 values = set()
#                 term_id_2_values[term_id] = values

#             if type(prop.value) is str:
#                 values.add(prop.value)
#             elif type(prop.value) is Term:
#                 values.add(prop.value.term_name)

#     def _repr_html_(self):
#         columns = ['Property', 'Units', 'Value']
#         table_header = '<tr>%s</tr>' % ['<th>%s</th>' % c for c in columns]
#         table_rows = []
#         for prop in self.properties:
#             table_rows.append('<tr>')
#             table_rows.append('<td>%s</td>' % prop.type_term.term_name)
#             table_rows.append('<td>%s</td>' % '')
#             table_rows.append('<td>%s</td>' % prop.value)
#             table_rows.append('</tr>')

#         return '<table>%s%s</table>' % (table_header, ''.join(table_rows))


# class Brick:
#     def __init__(self, brick_id, json_data=None):
#         self.id = brick_id
#         self.name = json_data['name']
#         self.description = json_data['description']

#         term = json_data['data_type']
#         self.data_type_term = Term(
#             term['oterm_ref'], term_name=term['oterm_name'])

#         # do context
#         self.properties = BrickContext(json_data['array_context'])

#         # do dimensions
#         self.dimensions = []
#         for dim_json in json_data['dim_context']:
#             self.dimensions.append(BrickDimension(json_data=dim_json))

#         term = json_data['typed_values']['value_type']
#         self.value_type_term = Term(
#             term['oterm_ref'], term_name=term['oterm_name'])

#         if 'value_units' in json_data['typed_values']:
#             term = json_data['typed_values']['value_units']
#             self.value_unit_term = Term(
#                 term['oterm_ref'], term_name=term['oterm_name'])
#         else:
#             self.value_unit_term = None

#         value_type = json_data['typed_values']['values']['scalar_type']
#         if value_type == 'oterm_ref':
#             value_type = 'oterm_refs'
#         else:
#             value_type += '_values'
#         data = np.array(json_data['typed_values']['values'][value_type])
#         self.data = data.reshape([dim.dim_size for dim in self.dimensions])

#         self.__inflate_dimensions()

#     def __inflate_dimensions(self):
#         for d in self.dimensions:
#             self.__dict__['DIM_' + d.dim_type_term.property_name] = d

#     def _repr_html_(self):
#         def _row(prop, value):
#             return '<tr><td>%s</td><td>%s</td></tr>' % (prop, value)

#         dim_names = ', '.join(
#             [dim.dim_type_term.term_name for dim in self.dimensions])
#         dim_sizes = [dim.dim_size for dim in self.dimensions]

#         name = self.name.split('.')[0]
#         name = ' '.join(name.split('_'))

#         rows = [
#             _row('ID', self.id),
#             _row('Name', name),
#             _row('Data type', self.data_type_term.term_name),
#             _row('Dimensions', dim_names),
#             _row('Shape', dim_sizes),
#             _row('Value type', self.value_type_term.term_name),
#             _row('Value units', self.value_unit_term.term_name)
#         ]

#         return '<table>%s</table>' % ''.join(rows)
#         # lines.append('')
#         # for dim_index, dim in enumerate(self.dimensions):
#         #     lines.append('Dimension[%s]: %s' %
#         #                  (dim_index + 1, dim.dim_type_term.term_name))
#         #     for variable in dim.variables:
#         #         lines.append('<span style="margin-left:10px"> %s: </span>' %
#         #                      variable.type_term.term_name)

#         # return '<br>'.join(lines)

#     def get_all_term_ids(self):
#         term_ids = set()
#         for term in self.get_property_terms():
#             term_ids.add(term.term_id)

#         for term in self.get_value_terms():
#             term_ids.add(term.term_id)

#         return term_ids

#     def get_property_terms(self):
#         id2terms = {}
#         id2terms[self.data_type_term.term_id] = self.data_type_term
#         id2terms[self.value_type_term.term_id] = self.value_type_term
#         if self.value_unit_term:
#             id2terms[self.value_unit_term.term_id] = self.value_unit_term

#         self.properties._collect_property_terms(id2terms)

#         for dim in self.dimensions:
#             dim._collect_property_terms(id2terms)

#         return list(id2terms.values())

#     def get_value_terms(self):
#         id2terms = {}
#         self.properties._collect_value_terms(id2terms)

#         for dim in self.dimensions:
#             dim._collect_value_terms(id2terms)
#         return list(id2terms.values())

#     def get_term_id_2_values(self):
#         term_id_2_values = {}
#         self.properties._collect_all_term_values(term_id_2_values)
#         for d in self.dimensions:
#             d._collect_all_term_values(term_id_2_values)
#         return term_id_2_values

#     def get_all_term_values(self):
#         values = set()
#         term_id_2_values = self.get_term_id_2_values()
#         for term_vals in term_id_2_values.values():
#             for val in term_vals:
#                 values.add(val)
#         return values


class BrickIndexDocumnet:
    def __init__(self, brick):
        self.brick_id = brick.id
        self.name = brick.name
        self.description = brick.description
        self.n_dimensions = len(brick.dims)
        self.data_type_term_id = brick.type_term.term_id
        self.data_type_term_name = brick.type_term.term_name

        data_var = brick.data_vars[0]
        self.value_type_term_id = data_var.type_term.term_id
        self.value_type_term_name = data_var.type_term.term_name

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
        return pd.DataFrame(bd_list)

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

    def load(self):
        return services.workspace.get_brick(self.brick_id)

    def __str__(self):
        return 'Name: %s;  Type: %s; Shape: %s' % (self.name, self.data_type, self.shape)
