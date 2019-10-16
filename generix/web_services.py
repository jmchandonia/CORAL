from flask import Flask, request, json
from flask import Response
from flask import request
from flask_cors import CORS
import pandas as pd
import re
import random 
from simplepam import authenticate
import jwt
import datetime

# from . import services
# from .brick import Brick

from .dataprovider import DataProvider
from .typedef import TYPE_CATEGORY_STATIC, TYPE_CATEGORY_DYNAMIC
from .utils import to_object_type

app = Flask(__name__)
CORS(app)
dp = DataProvider()
svs = dp._get_services()
cns = dp._get_constants()

@app.route("/")
def hello():
    return "Welcome!"

@app.route("/search_ont_dtypes/<value>", methods=['GET'])
def search_ont_dtypes(value):
    # value = request.args.get('term')
    return _search_oterms(svs['ontology'].data_types, value)

@app.route("/search_ont_all/<value>", methods=['GET'])
def search_ont_all(value):
    # value = request.args.get('term')
    return _search_oterms(svs['ontology'].all, value)

@app.route("/search_ont_units/<value>", methods=['GET'])
def search_ont_units(value):
    # value = request.args.get('term')
    return _search_oterms(svs['ontology'].units, value)

@app.route("/brick_type_templates", methods=['GET'])
def brick_type_templates():
    file_contxt = open(cns['_BRICK_TYPE_TEMPLATES_FILE']).read()
    res = json.loads( file_contxt )
    return  json.dumps( {
        'results': res['types']
    }  )

@app.route("/core_types", methods=['GET'])
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


@app.route('/map_dim_variable', methods=['GET', 'POST'])
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


@app.route('/do_search', methods=['GET', 'POST'])
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

@app.route("/brick/<brick_id>", methods=['GET'])
def get_brick(brick_id):
    bp = dp._get_type_provider('Brick')
    br = bp.load(brick_id)
    
    return json.dumps( {
            'status': 'success',
            'res': br.to_dict()
    } )




@app.route("/do_report/<value>", methods=['GET'])
def do_report(value):
    report = getattr(svs['reports'], value)
    # res = df.head(n=100).to_json(orient="table", index=False)
    res = report.to_df().head(n=100).to_json(orient="table", index=False)
    # res = df._repr_html_()

    return  json.dumps( {
            'status': 'success',
            'res': res
    } )


@app.route('/create_brick', methods=['GET', 'POST'])
def create_brick():
    if request.method == 'POST':
        brick_data = json.loads(request.form['brick'])
        br = _create_brick(brick_data)

        print('Brick created')
        print(br.data_vars[0].values)
        print(br._repr_html_())

        process_term = _get_term({'id':'PROCESS:0000031'})
        person_term = _get_term({'id':'ENIGMA:0000090'})
        campaign_term = _get_term({'id':'ENIGMA:0000021'})
        input_obj_ids = 'Well:Well0000000'


        br.save(process_term=process_term, 
            person_term=person_term, 
            campaign_term=campaign_term,
            input_obj_ids=input_obj_ids)


    return  json.dumps( {
            'status': 'success',
            'brick_id': br.id
    } )




@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    print("From uploader", request.method)
    if request.method == 'POST':
        brick = json.loads(request.form['brick'])

        print( json.dumps(brick, sort_keys=True, 
        indent=4, separators=(',', ': ') ) )
        
        # Save file
        f = request.files['files']
        file_name = './data/' + f.filename
        f.save(file_name)

        # Read df
        df = pd.read_csv(file_name, sep='\t') 

        # Build vairable values for each dims
        dims = []

        # First dim
        brick_dims = brick['dimensions'] 
        if len(brick_dims) > 0:
            dim = {
                'dim_index': 0,
                'vars': []
            }
            dims.append(dim)
            for i,v in enumerate(brick_dims[0]['variables']):
                vals = list(df[df.columns[i]].values)
                dim['vars'].append(vals)

        # Second dim
        if len(brick_dims) > 1:
            dim = {
                'dim_index': 1,
                'vars': []
            }
            dims.append(dim)
            offset = len(brick_dims[0]['variables'])
            dim['vars'].append( list(df.columns[offset:].values) )

        with open(file_name, 'r') as f:
            file_data = ' '.join( f.readlines() )

    return  json.dumps( {
            'status': 'success',
            'data': {
                'dims': dims,
                'file_name': file_name,
                'file_data': file_data
            }
    } )

def _create_brick(brick_data):
    dims_data = brick_data['dimensions']

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


def _search_oterms(ontology, value):
    if value is None:
        value = '*'
    res = []
    term_collection = ontology.find_name_pattern(value)
    for term in term_collection.terms:
        res.append({
            'id' : term.term_id,
            'text': term.term_name
        })
    return  json.dumps({
        'results': res
    })

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
        return {
            'results': '', 
            'status': 'ERR', 
            'error': 'Can not load brick: %s' % brick_id}

    # support mean
    if 'constraints' in query:
        for dimIndex, cst in query['constraints'].items():
            dimIndex = int(dimIndex)
            if cst == 'mean':
                br = br.mean(br.dims[dimIndex])

    if br.dim_count > 2:
        return {
            'results': '', 
            'status': 'ERR', 
            'error': 'The current version can support only 1D and 2D objects'}

    # Get all axes
    axes = list(query['data'].keys())
    if len(axes) != br.dim_count + 1:
        return {
            'results': '', 
            'status': 'ERR', 
            'error': '#axes should equal to #dimensions -1'}

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

    return  {
                'results': res,     
                'status': 'OK', 
                'error': ''
            }

@app.route('/generix/plotly_data', methods=['POST'])
def generix_plotly_data():
    query = request.json
    d = _get_plot_data(query)
    if d['status'] != 'OK':
        return json.dumps(d)

    rs = d['results']

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
        if 'z' in d['results']:
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

    return json.dumps({
        'results': {
            'layout': layout,
            'data': data
        },     
        'status': 'OK', 
        'error': ''
    })



@app.route('/generix/plot_data', methods=['POST'])
def generix_plot_data():
    d = _get_plot_data(request.json)
    return json.dumps(d)

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
        return json.dumps({
            'results': '', 
            'status': 'ERR', 
            'error': str(e)})
        
    return json.dumps({
        'results': plot_types, 
        'status': 'OK', 
        'error': ''})

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
    return json.dumps({
        'results': reports, 
        'status': 'OK', 
        'error': ''})

@app.route("/generix/reports/<id>", methods=['GET'])
def generix_report(id):
    try:
        report = getattr(svs['reports'], id)
        df = report.to_df()
        df.columns = ['Category', 'Term ID', 'Count']
        res = df.head(n=1000).to_json(orient="table", index=False)
    except Exception as e:
        return json.dumps({
            'results': '', 
            'status': 'ERR', 
            'error': str(e)})

    return  json.dumps( {
        'results': res, 
        'status': 'OK', 
        'error': ''
    } )

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
    return  json.dumps( {
        'results': res, 
        'status': 'OK', 
        'error': ''
    } )    

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
@app.route('/generix/types_stat', methods=['POST'])
def generix_type_stat():
    query = request.json
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
                'count': random.randint(0,1000),
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
    bp = dp._get_type_provider('Brick')
    for dt_name in bp.type_names():

        dyn_type_items.append(
            {
                'name': dt_name,
                'count': random.randint(0,1000),
                'queryMatch': {
                    'dataType': dt_name,
                    'dataModel': 'Brick',
                    'params': [],
                    'category': TYPE_CATEGORY_DYNAMIC
                }
            }            
        )      
    dyn_type_items.sort(key=lambda x: x['name'])        


    res = {
        'core_types' : {
            'items': stat_type_items
        },
        'dynamic_types': {
            'items': dyn_type_items
        }
    }

    return  json.dumps( {
        'results': res, 
        'status': 'OK', 
        'error': ''
    } )  


@app.route('/generix/dn_process_docs/<obj_id>', methods=['GET'])
def generix_dn_process_docs(obj_id):
    arango_service = svs['arango_service']
    indexdef = svs['indexdef']

    obj_type = ''
    try:
        obj_type = to_object_type(obj_id)
    except:
        return  json.dumps( {
            'results': '', 
            'status': 'ERR', 
            'error': 'Wrong object ID format'
        })

    itdef = indexdef.get_type_def(obj_type)
    rows = arango_service.get_dn_process_docs(itdef, obj_id)
    process_docs = _to_process_docs(rows)

    return  json.dumps( {
            'results': process_docs, 
            'status': 'OK', 
            'error': ''
        })   


@app.route('/generix/up_process_docs/<obj_id>', methods=['GET'])
def generix_up_process_docs(obj_id):
    arango_service = svs['arango_service']
    indexdef = svs['indexdef']

    obj_type = ''
    try:
        obj_type = to_object_type(obj_id)
    except:
        return  json.dumps( {
            'results': '', 
            'status': 'ERR', 
            'error': 'Wrong object ID format'
        })

    itdef = indexdef.get_type_def(obj_type)
    rows = arango_service.get_up_process_docs(itdef, obj_id)
    process_docs = _to_process_docs(rows)


    return  json.dumps( {
            'results': process_docs, 
            'status': 'OK', 
            'error': ''
        })   


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
        return  json.dumps( {
            'results': { "items": res, "type": obj_type  }, 
            'status': 'OK', 
            'error': ''
        })          
    except:
        return  json.dumps( {
            'results': '', 
            'status': 'ERR', 
            'error': 'Wrong object ID format'
        })

    



if __name__ == "__main__":
    port = cns['_WEB_SERVICE']['port']
    if cns['_WEB_SERVICE']['https']:
        app.run(host='0.0.0.0', port=port, 
            ssl_context = (cns['_WEB_SERVICE']['cert_pem'], cns['_WEB_SERVICE']['key_pem']) )
    else:
        app.run(host='0.0.0.0', port=port)

