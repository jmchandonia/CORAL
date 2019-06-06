from flask import Flask, request, json
from flask import Response
from flask import request
from flask_cors import CORS
import pandas as pd
from . import services
from .brick import Brick
from .dataprovider import DataProvider
from .typedef import TYPE_CATEGORY_STATIC

app = Flask(__name__)
CORS(app)


@app.route("/")
def hello():
    return "Welcome!"

@app.route("/search_ont_dtypes/<value>", methods=['GET'])
def search_ont_dtypes(value):
    # value = request.args.get('term')
    return _search_oterms(services.ontology.data_types, value)

@app.route("/search_ont_all/<value>", methods=['GET'])
def search_ont_all(value):
    # value = request.args.get('term')
    return _search_oterms(services.ontology.all, value)

@app.route("/search_ont_units/<value>", methods=['GET'])
def search_ont_units(value):
    # value = request.args.get('term')
    return _search_oterms(services.ontology.units, value)

@app.route("/brick_type_templates", methods=['GET'])
def brick_type_templates():
    file_contxt = open(services._BRICK_TYPE_TEMPLATES_FILE).read()
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

    type_defs = services.indexdef.get_type_defs(category=TYPE_CATEGORY_STATIC)
    res = [ {'type': td.name, 'props': td.property_names} for td in type_defs]

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

        dp = DataProvider()
        provider = dp._get_type_provider(search_data['dataType'])
        q = provider.query()
        for criterion in search_data['criteriaHas']:
            # print('criterion = ', criterion)
            if 'property' not in criterion:
                continue
            q.has({criterion['property']: criterion['value']})
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

@app.route("/do_report/<value>", methods=['GET'])
def do_report(value):
    dp = DataProvider()
    df = getattr(dp.reports, value)
    res = df.head(n=100).to_json(orient="table", index=False)

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
    brick_type_term = services.ontology.data_types.find_id('DA:0000028')
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
    return services.ontology.all.find_id( term_data['id'] ) if term_data['id'] != '' else None


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



if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8081)
