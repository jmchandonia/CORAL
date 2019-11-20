from flask import Flask, request, json, send_file
from flask import Response
from flask import request
from flask_cors import CORS
import pandas as pd
import numpy as np
import re
import random 
from simplepam import authenticate
import jwt
import datetime
import uuid 
import os


# from . import services
# from .brick import Brick

from .dataprovider import DataProvider
from .typedef import TYPE_CATEGORY_STATIC, TYPE_CATEGORY_DYNAMIC
from .utils import to_object_type
from . import template 

app = Flask(__name__)
CORS(app)
dp = DataProvider()
svs = dp._get_services()
cns = dp._get_constants()

TMP_DIR =  os.path.join(cns['_DATA_DIR'], 'tmp')  
_PERSONNEL_PARENT_TERM_ID = 'ENIGMA:0000029'
_CAMPAIGN_PARENT_TERM_ID = 'ENIGMA:0000002'
_PROCESS_PARENT_TERM_ID = 'PROCESS:0000001'

_UPLOAD_TEMPLAT_PREFIX = 'utp_'
_UPLOAD_DATA_STRUCTURE_PREFIX = 'uds_'
_UPLOAD_DATA_FILE_PREFIX = 'udf_'
_UPLOAD_PROCESSED_DATA_PREFIX = 'udp_'
_UPLOAD_VALIDATED_DATA_PREFIX = 'uvd_'
_UPLOAD_VALIDATION_REPORT_PREFIX = 'uvr_'


@app.route("/")
def hello():
    return "Welcome!"


@app.route("/generix/search_dimension_microtypes/<value>", methods=['GET'])
def search_dimension_microtypes(value):
    return _search_microtypes(svs['ontology'].dimension_microtypes, value)

@app.route("/generix/search_dimension_variable_microtypes/<value>", methods=['GET'])
def search_dimension_variable_microtypes(value):
    return _search_microtypes(svs['ontology'].dimension_variable_microtypes, value)

@app.route("/generix/search_data_variable_microtypes/<value>", methods=['GET'])
def search_data_variable_microtypes(value):
    # TODO: do we need a special OTerm porperty to select data variable - specific terms
    return _search_microtypes(svs['ontology'].dimension_variable_microtypes, value)


@app.route("/generix/search_property_microtypes/<value>", methods=['GET'])
def search_property_microtypes(value):
    return _search_microtypes(svs['ontology'].property_microtypes, value)

def _search_microtypes(ontology, value):
    if value is None:
        value = '*'
    res = []

    term_collection = ontology.find_name_prefix(value)
    for term in term_collection.terms:
        res.append(term.to_descriptor())
    return  json.dumps({
        'results': res
    })

@app.route("/generix/search_property_value_oterms", methods=['POST'])
def search_property_values():
    query = request.json
    value = query['value']
    parent_term_id = query['microtype']['valid_values_parent']
    return _search_oterms(svs['ontology'].all, value, parent_term_id=parent_term_id)

def _search_oterms(ontology, value, parent_term_id=None):
    if value is None:
        value = '*'
    res = []

    if parent_term_id == '':
        parent_term_id = None
    term_collection = ontology.find_name_prefix(value, parent_term_id=parent_term_id)
    for term in term_collection.terms:
        res.append({
            'id' : term.term_id,
            'text': term.term_name
        })
    return  json.dumps({
        'results': res
    })

@app.route("/generix/get_property_units_oterms", methods=['POST'])
def get_property_units_oterms():
    query = request.json
    parent_term_ids = query['microtype']['valid_units_parents']
    term_ids = query['microtype']['valid_units'] 
    return _get_oterms(svs['ontology'].units, term_ids=term_ids,  parent_term_ids=parent_term_ids)

@app.route("/generix/get_personnel_oterms", methods=['GET'])
def get_personnel_oterms():
    return _get_oterms(svs['ontology'].all,parent_term_ids=[_PERSONNEL_PARENT_TERM_ID])

@app.route("/generix/get_campaign_oterms", methods=['GET'])
def get_campaign_oterms():
    return _get_oterms(svs['ontology'].all,parent_term_ids=[_CAMPAIGN_PARENT_TERM_ID])

@app.route("/generix/get_process_oterms", methods=['GET'])
def get_process_oterms():
    return _get_oterms(svs['ontology'].all,parent_term_ids=[_PROCESS_PARENT_TERM_ID])

def _get_oterms(ontology, term_ids=None,  parent_term_ids=None):
    res = {}

    if term_ids is not None:
        for term in ontology.find_ids(term_ids).terms:
            res[term.term_id] = {
                'id' : term.term_id,
                'text': term.term_name
            }

    if parent_term_ids is not None:
        for parent_term_id in parent_term_ids:
            for term in ontology.find_parent_path_id(parent_term_id).terms:
                res[term.term_id] = {
                    'id' : term.term_id,
                    'text': term.term_name
                }
    res = list(res.values())
    res.sort(key=lambda x: x['text'])
    return  json.dumps({
        'results': res
    })    


# @app.route("/generix/search_ont_dtypes/<value>", methods=['GET'])
# def search_ont_dtypes(value):
#     # value = request.args.get('term')
#     return _search_oterms(svs['ontology'].data_types, value)

# @app.route("/generix/search_ont_all/<value>", methods=['GET'])
# def search_ont_all(value):
#     # value = request.args.get('term')
#     return _search_oterms(svs['ontology'].all, value)

# @app.route("/generix/search_ont_units/<value>", methods=['GET'])
# def search_ont_units(value):
#     # value = request.args.get('term')
#     return _search_oterms(svs['ontology'].units, value)

@app.route("/generix/brick_type_templates", methods=['GET'])
def brick_type_templates():
    templates = svs['brick_template_provider'].templates
    return  json.dumps( {
        'results': templates['types']
    }  )

@app.route("/generix/core_types", methods=['GET'])
def core_types():
    res = []
    
    # ctypes = []
    # for ctype in services.indexdef.get_type_names(category=TYPE_CATEGORY_STATIC):
    #     cType = []
    #     wordStart = True
    #     for c in ctype:
    #         if c == '_':
    #             wordStart = True
    #             continue
            
    #         if wordStart:
    #             c = c.upper()
    #             wordStart = False
    #         cType.append(c)
    #     ctypes.append( ''.join(cType) )

    # ctypes.sort()
    # for ctype in ctypes:
    #     props = services.arango_service.get_entity_properties(ctype)        
    #     res.append( { 'type' :ctype, 'props': props} )


    type_defs = svs['indexdef'].get_type_defs(category=TYPE_CATEGORY_DYNAMIC)
    for td in type_defs:
        res.append({'type': td.name, 'props': td.property_names})

    type_defs = svs['indexdef'].get_type_defs(category=TYPE_CATEGORY_STATIC)
    # res = [ {'type': td.name, 'props': td.property_names} for td in type_defs]
    for td in type_defs:
        res.append({'type': td.name, 'props': td.property_names})

    return  json.dumps({
        'results': res
    })


@app.route('/generix/map_dim_variable', methods=['GET', 'POST'])
def map_dim_variable():
    if request.method == 'POST':
        brick_data = json.loads(request.form['brick'])
        br = _create_brick(brick_data)

        dimIndex = int(request.form['dimIndex'])
        dimVarIndex = int(request.form['dimVarIndex'])
        mapCoreType = request.form['mapCoreType']
        mapCoreProp = request.form['mapCoreProp']      

        br.dims[dimIndex].vars[dimVarIndex].map_to_core_type(mapCoreType, mapCoreProp)
        idVar = br.dims[dimIndex].vars[-1]

        totalCount = 0
        mappedCount = 0
        for val in idVar.values:
            totalCount += 1
            if val is not None:
                mappedCount += 1
        
        res = {
            'totalCount': totalCount,
            'mappedCount': mappedCount,
            'dimIndex': dimIndex,
            'dimVarIndex': dimVarIndex,
            'type_term': { 
                'id': idVar.type_term.term_id, 
                'name': idVar.type_term.term_name},
            'values': list(idVar.values)
        }

    return  json.dumps({
        'results': res
    })


@app.route('/generix/do_search', methods=['GET', 'POST'])
def do_search():
    if request.method == 'POST':
        search_data = json.loads(request.form['searchBuilder'])

        print('Searching data')
        print(search_data)

        # dp = DataProvider()
        provider = dp._get_type_provider(search_data['dataType'])
        q = provider.query()
        for criterion in search_data['criteriaHas']:
            # print('criterion = ', criterion)
            if 'property' not in criterion:
                continue

            prop_name = criterion['property']
            value = criterion['value']

            # update value
            itype_def = svs['indexdef'].get_type_def(search_data['dataType'])
            iprop_def = itype_def.get_property_def(prop_name)
            if iprop_def.scalar_type == 'int':
                value = int(value)
            if iprop_def.scalar_type == 'float':
                value = float(value)            

            q.has({prop_name: {criterion['operation']: value}})

        for criterion in search_data['criteriaProcessOutput']:
            prop_name = criterion['property']
            value = criterion['value']
            q.is_output_of_process({prop_name: {criterion['operation']: value}})

        res = q.find().to_df().head(n=100).to_json(orient="table", index=False)
        print(res)
        

        # print(br._repr_html_())

        # process_term = _get_term({'id':'PROCESS:0000031'})
        # person_term = _get_term({'id':'ENIGMA:0000090'})
        # campaign_term = _get_term({'id':'ENIGMA:0000021'})
        # input_obj_ids = 'Well:Well0000000'


        # br.save(process_term=process_term, 
        #     person_term=person_term, 
        #     campaign_term=campaign_term,
        #     input_obj_ids=input_obj_ids)


    return  json.dumps( {
            'status': 'success',
            'res': res
    } )

@app.route("/generix/brick/<brick_id>", methods=['GET'])
def get_brick(brick_id):
    bp = dp._get_type_provider('Brick')
    br = bp.load(brick_id)
    
    return json.dumps( {
            'status': 'success',
            'res': br.to_dict()
    } )

@app.route("/generix/do_report/<value>", methods=['GET'])
def do_report(value):
    report = getattr(svs['reports'], value)
    # res = df.head(n=100).to_json(orient="table", index=False)
    res = report.to_df().head(n=100).to_json(orient="table", index=False)
    # res = df._repr_html_()

    return  json.dumps( {
            'status': 'success',
            'res': res
    } )


@app.route('/generix/create_brick', methods=['POST'])
def create_brick():
    brick_data = json.loads(request.form['brick'])
    print(json.dumps(brick_data, 
        sort_keys=True, 
        indent=4, separators=(',', ': ') ) )
        
    brick_id = svs['workspace'].next_id('Brick')

    # br = _create_brick(brick_data)

    # print('Brick created')
    # print(br.data_vars[0].values)
    # print(br._repr_html_())

    # process_term = _get_term({'id':'PROCESS:0000031'})
    # person_term = _get_term({'id':'ENIGMA:0000090'})
    # campaign_term = _get_term({'id':'ENIGMA:0000021'})
    # input_obj_ids = 'Well:Well0000000'


    # br.save(process_term=process_term, 
    #     person_term=person_term, 
    #     campaign_term=campaign_term,
    #     input_obj_ids=input_obj_ids)


    return  _ok_response(brick_id)

@app.route('/generix/validate_upload', methods=['POST'])
def validate_upload():
    try:
        query = request.json
        data_id = query['data_id']
        file_name = os.path.join(TMP_DIR,_UPLOAD_PROCESSED_DATA_PREFIX 
            + data_id)
        data = json.loads(open(file_name).read())

        res = {
            'dims':[],
            'data_vars': []
        }

        for dim in data['dims']:
            res_dim_vars = []
            res['dims'].append({
                'dim_vars': res_dim_vars
            })
            for dim_var in dim['dim_vars']:
                size = len(dim_var['values'])
                res_dim_vars.append({
                    'total_count': size,
                    'valid_count': size,
                    'invalid_count': 0
                })

        for data_var in data['data_vars']:
            size = 1
            for dim_size in np.array(data_var['values']).shape:
                size *= dim_size 
            res['data_vars'].append({
                'total_count': size,
                'valid_count': size,
                'invalid_count': 0
            })

        return _ok_response(res) 

    except Exception as e:
        return _err_response(e)



@app.route('/generix/upload', methods=['POST'])
def upload_file():
    try:
        data_id = uuid.uuid4().hex

        brick_ds = json.loads(request.form['brick'])

        # Save birck data structure
        uds_file_name = os.path.join(TMP_DIR, _UPLOAD_DATA_STRUCTURE_PREFIX + data_id )
        with open(uds_file_name, 'w') as f:
            json.dump(brick_ds, f, sort_keys=True, indent=4)
        
        # Save data file
        f = request.files['files']
        udf_file_name = os.path.join(TMP_DIR, _UPLOAD_DATA_FILE_PREFIX 
            + data_id + '_' + f.filename)
        f.save( udf_file_name )

        # Parse brick data    
        brick_data = {}

        dim_count = len(brick_ds['dimensions'])
        if dim_count == 1:
            brick_data = template.parse_brick_F1DM_data(brick_ds, udf_file_name)
        elif dim_count == 2:
            brick_data = template.parse_brick_F2DT_data(brick_ds, udf_file_name)
        else:
            raise ValueError('Brick with %s dimensions is not supported yet' % dim_count)

        # Save brick processed data
        upd_file_name = os.path.join(TMP_DIR, _UPLOAD_PROCESSED_DATA_PREFIX + data_id )
        with open(upd_file_name, 'w') as f:
            json.dump(brick_data, f, sort_keys=True, indent=4)


        # Build output (examples of values for dim vars and data vars)
        dims = []
        data_vars = []

        for dim_data in brick_data['dims']:
            dim = {
                'size' : dim_data['size'],
                'dim_vars': []
            }
            dims.append(dim)

            for dim_var_data in dim_data['dim_vars']:
                dim['dim_vars'].append({
                    'value_example': _dim_var_example(dim_var_data['values'])
                })

        for data_var_data in brick_data['data_vars']:
            data_vars.append({
                'value_example': _data_var_example(data_var_data['values'])
            })

        return  _ok_response({
                    'dims': dims,
                    'data_vars': data_vars,
                    'data_id': data_id
                })

    except Exception as e:
        return _err_response(e)

def _save_brick_proto(brick, file_name):
    data_json = brick.to_json()
    data = json.loads(data_json)
    with open(file_name, 'w') as outfile:  
        json.dump(data, outfile)    


def _data_var_example(vals, max_items=5):
    return '%s%s' % ( 
        ','.join(str(val) for val in vals[0:max_items]), 
        '...' if len(vals) > max_items else '' ) 

def _dim_var_example(vals, max_items=5):
    return '%s%s' % ( 
        ','.join(str(val) for val in vals[0:max_items]), 
        '...' if len(vals) > max_items else '' ) 

def _create_brick(brick_ui, brick_data):
    dims_data = brick_ui['dimensions']

    dim_type_terms = []
    dim_shapes = []
    for dim_data in dims_data:
        dim_type_term = _get_term(dim_data['type'])
        dim_type_terms.append( dim_type_term )
        for var_data in dim_data['variables']:
            dim_size = len(var_data['values']) 
        dim_shapes.append( dim_size )
        print('Dim type = %s' % (str(dim_type_term)))
        print('Dim size = %s' % dim_size)
        
    #TODO: get type term 
    brick_type_term = svs['ontology'].data_types.find_id('DA:0000028')
    brick_name = brick_data['name'] if "name" in brick_data else ""
    br = Brick(type_term=brick_type_term, 
        dim_terms = dim_type_terms, 
        shape=dim_shapes,
        name=brick_name)

    # add dim variables
    for dim_index, dim_data in enumerate(dims_data):
        print('dim_index = %s, shape = %s' %(dim_index, br.dims[dim_index].size) )
        for var_data in dim_data['variables']:
            print('\tdim_inde = %s, values_size = %s' %(dim_index, len(var_data['values']) ) )
            var_type_term = _get_term(var_data['type'])
            var_units_term = _get_term(var_data['units'])
            br.dims[dim_index].add_var(var_type_term, var_units_term, var_data['values'])

    # add brick properties
    for prop_data in brick_data['properties']:
        var_type_term = _get_term(prop_data['type'])
        var_units_term = _get_term(prop_data['units'])
        br.add_attr(var_type_term, var_units_term, 'text', prop_data['value'])

    # add data
    df = pd.read_csv(brick_data['data_file_name'], sep='\t') 
    offset = len(dims_data[0]['variables'])
    df = df[df.columns[offset:].values]

    # TODO: switch to real value
    data_type_term = _get_term({'id':'ME:0000126'})
    data_units_term = None
    br.add_data_var(data_type_term, data_units_term, df.values)        

    return br

def _get_term(term_data):
    return svs['ontology'].all.find_id( term_data['id'] ) if term_data['id'] != '' else None


########################################################################################
## NEW VERSION
##########################################################################################

@app.route("/generix/user_login", methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return json.dumps({ 'message': 'testing login route handler' })
    
    login = request.json
    auth = authenticate(login['username'], login['password'])
    if not auth:
        return json.dumps({'success': False, 'message': 'Incorrect username/password'})
    else:
        try:
            payload = {
		        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=0, seconds=0, microseconds=0, milliseconds=0, minutes=10),
		        'iat': datetime.datetime.utcnow(),
		        'sub': login['username']
	        }
            new_jwt = jwt.encode(payload, 'test', algorithm='HS256')
            return json.dumps({'success': True, 'token': new_jwt.decode('utf-8')})
        except Exception as e:
            print(e)
            return json.dumps({'success': False, 'message': 'Something went wrong'})  


@app.route("/generix/data_types", methods=['GET'])
def generix_data_types():
    res = []
    
    # Core types
    type_defs = svs['indexdef'].get_type_defs(category=TYPE_CATEGORY_STATIC)
    for td in type_defs:
        res.append({
            'dataType': td.name, 
            'dataModel': td.name,
            'category': TYPE_CATEGORY_STATIC
            })

    # Dynamic types
    bp = dp._get_type_provider('Brick')
    for dt_name in bp.type_names():
        res.append({
            'dataType': dt_name, 
            'dataModel': 'Brick',
            'category': TYPE_CATEGORY_DYNAMIC
        })

    # Add NDArray as a dataype
    res.append({
        'dataType': 'NDArray', 
        'dataModel': 'Brick',
        'category': TYPE_CATEGORY_DYNAMIC
    })
    res.sort(key=lambda x: x['dataType']) 
    return  json.dumps({'results': res})

@app.route("/generix/data_models", methods=['GET'])
def generix_data_models():
    res = {}

    type_defs = svs['indexdef'].get_type_defs()
    for td in type_defs:

        pdefs = []
        for pdef in td.property_defs:
            pdefs.append( {'name': pdef.name, 'scalar_type': pdef.scalar_type} )

        res[td.name] = {
            'dataModel': td.name,
            'category': td.category,
            'properties': pdefs
        }

    return  json.dumps({'results': res})

@app.route('/generix/brick_dimension/<brick_id>/<dim_index>', methods=['GET'])
def generix_brick_dimension(brick_id, dim_index):
    MAX_ROW_COUNT = 100
    res = {}
    try:
        bp = dp._get_type_provider('Brick')
        br = bp.load(brick_id)
        dim = br.dims[int(dim_index)]
        res = {
            'type':{
                'id': dim.type_term.term_id,
                'text': dim.type_term.term_name
            },
            'size': dim.size,
            'max_row_count': MAX_ROW_COUNT,
            'dim_var_count': dim.var_count,
            'dim_vars':[]
        }
        for dim_var in dim.vars:
            context = []
            for attr in dim_var.attrs:
                context.append({
                    'type':{
                        'id': attr.type_term.term_id,
                        'text': attr.type_term.term_name
                    },
                    'units':{
                        'id': attr.units_term.term_id if attr.units_term else '',
                        'text': attr.units_term.term_name if attr.units_term else ''
                    },
                    'value': str(attr.value)
                })            

            res['dim_vars'].append({
                'type':{
                    'id': dim_var.type_term.term_id,
                    'text': dim_var.type_term.term_name
                },
                'units':{
                    'id': dim_var.units_term.term_id if dim_var.units_term else '',
                    'text': dim_var.units_term.term_name if dim_var.units_term else ''
                },
                'values': list([ str(val) for val in dim_var.values][:MAX_ROW_COUNT]),
                'context': context
            })
    except Exception as e:
        return _err_response(e)

    return _ok_response(res)

@app.route('/generix/brick_metadata/<brick_id>', methods=['GET'])
def generix_brick_metadata(brick_id):
    bp = dp._get_type_provider('Brick')
    br = bp.load(brick_id)
    
    return br.to_json(exclude_data_values=True, typed_values_property_name=False)


def _get_plot_data(query):
    ''' We will currently support 1D and 2D and only the first data variable '''

    bp = dp._get_type_provider('Brick')
    brick_id = query['objectId']
    try:
        br = bp.load(brick_id)  
    except:
        raise ValueError('Can not load brick: %s' % brick_id)

    # support mean
    if 'constraints' in query:
        for dimIndex, cst in query['constraints'].items():
            dimIndex = int(dimIndex)
            if cst == 'mean':
                br = br.mean(br.dims[dimIndex])

    if br.dim_count > 2:
        raise ValueError('The current version can support only 1D and 2D objects')

    # Get all axes
    axes = list(query['data'].keys())
    if len(axes) != br.dim_count + 1:
        raise ValueError('#axes should equal to #dimensions -1')

    # Dimension indeces to axes
    dim_index2axis = {}
    for axis in axes:
        dim_index = query['data'][axis]
        dim_index2axis[dim_index] = axis

    res = {}

    for axis in axes:
        dim_index = query['data'][axis]
        if type(dim_index) is int:
            label_pattern = query['config'][axis]['label_pattern']
            res[axis] = _build_dim_labels(br.dims[dim_index],label_pattern)
        else:
            if br.dim_count == 1:
                res[axis] = br.data_vars[0].values.tolist()
            elif br.dim_count == 2:
                if dim_index2axis[dim_index] == 'x':
                    res[axis] = br.data_vars[0].values.tolist()
                else:
                    res[axis] = br.data_vars[0].values.T.tolist()

    return res

@app.route('/generix/plotly_data', methods=['POST'])
def generix_plotly_data():
    query = request.json
    try:
        rs = _get_plot_data(query)

        # Build layout
        layout = {
            'width': 800,
            'height': 600,
            'title': query['config']['title'],
            **query['plotly_layout']
        }
        if 'x' in query['config']:
            if query['config']['x']['show_title']:
                layout['xaxis'] = {
                'title': query['config']['x']['title']  
                }

        if 'y' in query['config']:
            if query['config']['y']['show_title']:
                layout['yaxis'] = {
                'title': query['config']['y']['title']  
                }

        # Build layout
        data = []
        plot_type = query['plotly_trace'].get('type')
        if plot_type == 'heatmap':
            trace = {
                'x': rs['x'],
                'y': rs['y'],
                'z': rs['z'],
                **query['plotly_trace']             
            }        
            data.append(trace)        
        else:
            if 'z' in rs:
                for zindex, zval in enumerate(rs['z']):
                    trace = {
                        'x': rs['x'][zindex] if query['data']['x'] == 'D' else rs['x'],
                        'y': rs['y'][zindex] if query['data']['y'] == 'D' else rs['y'],
                        'name': zval,
                        **query['plotly_trace']            
                    }
                    data.append(trace)
            else:
                trace = {
                    'x': rs['x'],
                    'y': rs['y'],
                    **query['plotly_trace']             
                }        
                data.append(trace)

        return _ok_response({
                'layout': layout,
                'data': data
            })

    except Exception as e:
        return _err_response(e)

@app.route('/generix/plot_data', methods=['POST'])
def generix_plot_data():
    try:
        res = _get_plot_data(request.json)
        return _ok_response(res)
    except Exception as e:
        return _err_response(e)

def _build_dim_labels(dim, pattern):
    labels = []
    for i in range(dim.size):
        label = pattern
        for vi, dvar in enumerate(dim.vars):
            vi += 1
            label = re.sub(r'#V%s'%vi, str(dvar.values[i]), label )
        labels.append(label)
    return labels



@app.route('/generix/plot_data_test', methods=['POST'])
def generix_plot_data_test():
    query = request.json
    bp = dp._get_type_provider('Brick')
    # brick_id = query['objectId']
    # br = bp.load(brick_id)  
    br = bp.load('Brick0000003')  
    # br = bp.load('Brick0000023')  
    br.mean(br.dims[2])     

    res = {}
    # axes = list(query['data'].keys())
    # for axis in axes:
    #     dimIndex = query['data'][axis]
    #     if type(dimIndex) is int:

    x = br.dims[0].vars[0].values.tolist()
    y = br.data_vars[0].values.tolist()
    z = []  
    for i in range(br.dims[1].size):
        label = ''
        for dvar in br.dims[1].vars:
            label = label + str(dvar.values[i]) + '; ' 
        z.append(
            label
        )

    res = {
        'x' : x,
        'y': y,
        'z' : z
    }
    return  json.dumps({'results': res})


def _extract_criterion_props(criterion):
    prop_name = criterion['attribute']
    prop_value = criterion['keyword']
    scalar_type = criterion['scalarType']
    operation = criterion['matchType']

    # update value
    if scalar_type == 'int':
        prop_value = int(prop_value)
    elif scalar_type == 'float':
        prop_value = float(prop_value)   
    return (prop_name, prop_value, operation)           


@app.route('/generix/search', methods=['GET','POST'])
def generix_search():
    search_data = request.json

    # Do queryMatch
    query_match = search_data['queryMatch']
    provider = dp._get_type_provider(query_match['dataModel'])
    q = provider.query()

    if query_match['dataModel'] == 'Brick' and query_match['dataType'] != 'NDArray':
        q.has({'data_type': {'=': query_match['dataType']}})

    for criterion in query_match['params']:
        (prop_name, prop_value, operation) = _extract_criterion_props(criterion)
        q.has({prop_name: {operation: prop_value}})

    # Do processesUp
    if 'processesUp' in search_data:
        for criterion in search_data['processesUp']:
            (prop_name, prop_value, operation) = _extract_criterion_props(criterion)
            q.is_output_of_process({prop_name: {operation: prop_value}})

    # Do processesDown
    if 'processesDown' in search_data:
        for criterion in search_data['processesDown']:
            (prop_name, prop_value, operation) = _extract_criterion_props(criterion)
            q.is_input_of_process({prop_name: {operation: prop_value}})

    # Do connectsUpTo
    if 'connectsUpTo' in search_data:
        connects_up_to = search_data['connectsUpTo']
        params = {}
        for criterion in connects_up_to['params']:
            (prop_name, prop_value, operation) = _extract_criterion_props(criterion)
            params['prop_name'] = {operation: prop_value}

        q.linked_up_to(connects_up_to['dataModel'],  params )

    # Do connectsDownTo
    if 'connectsDownTo' in search_data:
        connects_down_to = search_data['connectsDownTo']
        params = {}
        for criterion in connects_down_to['params']:
            (prop_name, prop_value, operation) = _extract_criterion_props(criterion)
            params['prop_name'] = {operation: prop_value}

        q.linked_down_to(connects_down_to['dataModel'],  params )

    res = q.find().to_df().head(n=100).to_json(orient="table", index=False)
    # return  json.dumps( {'res': res} )
    return res




@app.route("/generix/search_operations", methods=['GET'])
def generix_search_operations():
    # '=':  FILTER_EQ,
    # '==': FILTER_EQ,
    # 'eq': FILTER_EQ,
    # '>':  FILTER_GT,
    # 'gt': FILTER_GT,
    # '<':  FILTER_LT,
    # 'lt': FILTER_LT,
    # '>=': FILTER_LTE,
    # 'gte':FILTER_LTE,
    # '<=': FILTER_LTE,
    # 'lte':FILTER_LTE,
    # 'fulltext': FILTER_FULLTEXT,
    # 'match': FILTER_FULLTEXT,
    # 'like': FILTER_FULLTEXT,
    # 'in': FILTER_IN    

    res = ['=','>','<','>=','<=','like']
    return  json.dumps({'results': res})

@app.route("/generix/plot_types", methods=['GET'])
def generix_plot_types():
    fname = cns['_PLOT_TYPES_FILE']
    try:
        plot_types = json.loads(open(fname).read())['plot_types']
    except Exception as e:
        return _err_response(e)
        
    return _ok_response(plot_types)

@app.route("/generix/reports", methods=['GET'])
def generix_reports():

    reports = [
        {
            'name': 'Data Uploaded by Category',
            'id': 'brick_types'
        },
        {
            'name': 'Data Sorted by Dimensionality',
            'id': 'brick_dim_types'
        },
        {
            'name': 'Data Sorted by Dimension Type',
            'id': 'brick_data_var_types'
        },
        {
            'name': 'Data Sorted by Process used to Generate Data',
            'id': 'process_types'
        },
        {
            'name': 'Data Uploaded by Lab & Person',
            'id': 'process_persons'
        },
        {
            'name': 'Data Uploaded by Campaign',
            'id': 'process_campaigns'
        }
    ]        
    return _ok_response(reports)

@app.route("/generix/reports/<id>", methods=['GET'])
def generix_report(id):
    try:
        report = getattr(svs['reports'], id)
        df = report.to_df()
        df.columns = ['Category', 'Term ID', 'Count']
        res = df.head(n=1000).to_json(orient="table", index=False)
    except Exception as e:
        return _err_response(e)

    return  _ok_response(res)

@app.route("/generix/filters", methods=['GET'])
def generix_filters():
    reports = svs['reports']

    df_campaign = reports.process_campaigns.to_df()
    df_persons = reports.process_persons.to_df()
    res = [
        {
            'categoryName': 'ENIGMA Campaigns',
            'items': _get_category_items(df_campaign, 'campaign' )
        },
        {
            'categoryName': 'ENIGMA Personnel',
            'items': _get_category_items(df_persons, 'person')
        },
    ]
    return _ok_response(res)

def _get_category_items(process_stat_df, attr):
    res = []
    for _, row in process_stat_df.sort_values('Term Name').iterrows():
        res.append(
            {
                'name': row['Term Name'],
                'queryParam': {
                    'attribute': attr,
                    'matchType':  '=' ,
                    'keyword': row['Term Name'],
                    'scalarType': 'term'
                }
            }
        )
    return res



# Test version
@app.route('/generix/types_stat', methods=['GET','POST'])
def generix_type_stat():
    arango_service = svs['arango_service']

    # query = request.json
    # request = [
    #     {
    #         'attribute': '',
    #         'matchType' '',
    #         'keyword': '',
    #         'scalarType': ''
    #     },
    # ]
    
    # Core types
    stat_type_items = []
    type_defs = svs['indexdef'].get_type_defs(category=TYPE_CATEGORY_STATIC)
    for td in type_defs:
        if td.name == 'ENIGMA':
            continue
        stat_type_items.append(
            {
                'name': td.name,
                'count': arango_service.get_core_type_count( '%s%s' %(TYPE_CATEGORY_STATIC, td.name)),
                'queryMatch': {
                    'dataType': td.name,
                    'dataModel': td.name,
                    'params': [],
                    'category': TYPE_CATEGORY_STATIC
                }
            }            
        )
    stat_type_items.sort(key=lambda x: x['name'])        

    # Dynamic types
    dyn_type_items = []
    rows = arango_service.get_brick_type_counts([],[])
    for row in rows:
        dyn_type_items.append(
            {
                'name': row['b_type'],
                'count': row['b_count'],
                'queryMatch': {
                    'dataType': row['b_type'],
                    'dataModel': 'Brick',
                    'params': [],
                    'category': TYPE_CATEGORY_DYNAMIC
                }
            }            
        )    

    # bp = dp._get_type_provider('Brick')
    # for dt_name in bp.type_names():

    #     dyn_type_items.append(
    #         {
    #             'name': dt_name,
    #             'count': random.randint(0,1000),
    #             'queryMatch': {
    #                 'dataType': dt_name,
    #                 'dataModel': 'Brick',
    #                 'params': [],
    #                 'category': TYPE_CATEGORY_DYNAMIC
    #             }
    #         }            
    #     )


    dyn_type_items.sort(key=lambda x: x['name'])        


    res = {
        'core_types' : {
            'items': stat_type_items
        },
        'dynamic_types': {
            'items': dyn_type_items
        }
    }

    return  _ok_response(res)


@app.route('/generix/dn_process_docs/<obj_id>', methods=['GET'])
def generix_dn_process_docs(obj_id):
    arango_service = svs['arango_service']
    indexdef = svs['indexdef']

    obj_type = ''
    try:
        obj_type = to_object_type(obj_id)
    except:
        return _err_response('Wrong object ID format')

    itdef = indexdef.get_type_def(obj_type)
    rows = arango_service.get_dn_process_docs(itdef, obj_id)
    process_docs = _to_process_docs(rows)

    return  _ok_response(process_docs)

@app.route('/generix/up_process_docs/<obj_id>', methods=['GET'])
def generix_up_process_docs(obj_id):
    arango_service = svs['arango_service']
    indexdef = svs['indexdef']

    obj_type = ''
    try:
        obj_type = to_object_type(obj_id)
    except:
        return _err_response('Wrong object ID format')

    itdef = indexdef.get_type_def(obj_type)
    rows = arango_service.get_up_process_docs(itdef, obj_id)
    process_docs = _to_process_docs(rows)

    return _ok_response(process_docs)


def _to_process_docs(rows):
    indexdef = svs['indexdef']
    process_docs = []
    for row in rows:
        process = row['process']

        # build docs
        docs = []
        for doc in row['docs']:
            obj_type = to_object_type(doc['_key'])
            itdef = indexdef.get_type_def(obj_type)
            docs.append({
                'id': doc['_key'],
                'type': obj_type,
                'category': itdef.category,
                'description': '' 
            })

        process_docs.append({
            'process': {
                'id':process['id'], 
                'process': process['process_term_name'], 
                'person': process['person_term_name'], 
                'campaign': process['campaign_term_name'], 
                'date_start' : process['date_start'], 
                'date_end': process['date_end']
            },
            'docs' : docs
        })
    return process_docs


@app.route('/generix/core_type_metadata/<obj_id>', methods=['GET'])
def generix_core_type_metadata(obj_id):
    obj_type = ''
    try:
        obj_type = to_object_type(obj_id)
        doc = dp.core_types[obj_type].find_one({'id':obj_id})
        res = []
        for prop in doc.properties:
            if prop.startswith('_'): continue
            res.append(
                {
                    'property': prop,
                    'value': doc[prop]
                }
            )
        return  _ok_response({ "items": res, "type": obj_type  })
       
    except:
        return _err_response('Wrong object ID format')

    
@app.route('/generix/generate_brick_template', methods=['POST'])
def generate_brick_template():
    try:
        data_id = uuid.uuid4().hex

        brick = json.loads(request.form['brick'])

        # Save birck data structure
        uds_file_name = os.path.join(TMP_DIR, _UPLOAD_DATA_STRUCTURE_PREFIX + data_id )
        with open(uds_file_name, 'w') as f:
            json.dump(brick_ds, f, sort_keys=True, indent=4)

        utp_file_name = os.path.join(TMP_DIR,_UPLOAD_TEMPLAT_PREFIX + data_id)

        dim_count = len(brick['dimensions'])
        data_var_count = len(brick['dataValues'])

        if dim_count == 1:
            template.generate_brick_1dm_template(brick, utp_file_name)
        elif dim_count == 2:
            if data_var_count == 1:
                template.generate_brick_2d_template(brick, utp_file_name)

        return send_file(utp_file_name, 
            as_attachment=True,
            attachment_filename='data_template.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    except Exception as e:
        return _err_response(r)

def _ok_response(res):
    return  json.dumps( {
            'results': res, 
            'status': 'OK', 
            'error': ''
        })

def _err_response(e):
    return  json.dumps( {
            'results': '', 
            'status': 'ERR', 
            'error': str(e)
        })

if __name__ == "__main__":
    port = cns['_WEB_SERVICE']['port']
    if cns['_WEB_SERVICE']['https']:
        app.run(host='0.0.0.0', port=port, 
            ssl_context = (cns['_WEB_SERVICE']['cert_pem'], cns['_WEB_SERVICE']['key_pem']) )
    else:
        app.run(host='0.0.0.0', port=port)



