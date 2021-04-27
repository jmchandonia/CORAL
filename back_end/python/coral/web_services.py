from flask import Flask, request, json, jsonify, send_file
from flask import Response
from flask import request
from flask_cors import CORS, cross_origin
from functools import wraps
from diskcache import Cache
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
import pandas as pd
import numpy as np
import traceback as tb
import networkx as nx
import re
import random 
from simplepam import authenticate
import jwt
import datetime
import uuid 
import os
import html
import sys
import pprint
import math
import base64
from contextlib import redirect_stdout
import subprocess
from pyArango.theExceptions import AQLQueryError
import requests
import smtplib, ssl

from .dataprovider import DataProvider
from .brick import Brick
from .typedef import TYPE_CATEGORY_STATIC, TYPE_CATEGORY_DYNAMIC, TYPE_NAME_PROCESS
from .utils import to_object_type
from .descriptor import IndexDocument
from .workspace import ItemAlreadyExistsException, EntityDataHolder, ProcessDataHolder, DataHolder
from . import template 

app = Flask(__name__)
app.config['CORS_HEADERS'] = 'Content-Type'
CORS(app)

DEBUG_MODE = False
dp = DataProvider()
svs = dp._get_services()
cns = dp._get_constants()

CACHE_DIR =  cns['_CACHE_DIR']
cache = Cache(CACHE_DIR)

TMP_DIR =  os.path.join(cns['_DATA_DIR'], 'tmp')  
IMAGE_DIR =  os.path.join(cns['_DATA_DIR'], 'images')
THUMBS_DIR =  os.path.join(IMAGE_DIR, 'thumbs')

_PERSONNEL_PARENT_TERM_ID = 'ENIGMA:0000029'
_CAMPAIGN_PARENT_TERM_ID = 'ENIGMA:0000002'
_PROCESS_PARENT_TERM_ID = 'PROCESS:0000001'

_UPLOAD_TEMPLATE_PREFIX = 'utp_'
_UPLOAD_DATA_STRUCTURE_PREFIX = 'uds_'
_UPLOAD_DATA_FILE_PREFIX = 'udf_'
_UPLOAD_PROCESSED_DATA_PREFIX = 'udp_'
_UPLOAD_VALIDATED_DATA_PREFIX = 'uvd_'
_UPLOAD_VALIDATED_DATA_2_PREFIX = 'uvd2_'
_UPLOAD_VALIDATION_REPORT_PREFIX = 'uvr_'
_UPLOAD_CORE_DATA_PREFIX = 'ucd_'

# for methods that only a logged in user can use
def auth_required(func):
    """
    View decorator - require valid JWT
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if valid_jwt(get_jwt()):
            return func(*args, **kwargs)
        else:
            return jsonify({"message": "UNAUTHORIZED USER"}), 401
    return wrapper

# for methods that either a logged in user, or a read only app, can use
def auth_ro_required(func):
    """
    View decorator - require valid JWT or the right public key
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        token = get_jwt()
        
        if valid_jwt(token) or valid_jwt_key(token):
            return func(*args, **kwargs)
        else:
            return jsonify({"message": "UNAUTHORIZED USER"}), 401
    return wrapper

def get_jwt():
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return False
    auth_token = auth_header.split(' ')[1] # remove bearer from the front
    return auth_token

def decrypt_token(auth_token, secret):
    # if token decoding failed then we know we didnt have a token that was encrypted with the same key
    # we can also check for valid user information or anything else we add to the token here
    payload = jwt.decode(auth_token, secret, algorithms=['HS256'])
    # s = pprint.pformat(payload)
    # sys.stderr.write(s+'\n')  

    # check time is actually good, within 5 minutes
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    exp = datetime.datetime.fromtimestamp(payload['exp'], tz=datetime.timezone.utc)
    iat = datetime.datetime.fromtimestamp(payload['iat'], tz=datetime.timezone.utc)
    leeway = datetime.timedelta(days=0, seconds=0, microseconds=0, milliseconds=0, minutes=5)
    
    if (now < iat-leeway) or (now > exp+leeway):
        raise ValueError('token not good at this time')
        
    return payload

def valid_jwt(auth_token):
    try:
        payload = decrypt_token(auth_token, cns['_AUTH_SECRET'])
        
        return True
    except Exception as e:
        sys.stderr.write('valid_jwt exception: '+str(e)+'\n') 
        return False

def valid_jwt_key(auth_token):
    try:
        # path to check public key
        headers = jwt.get_unverified_header(auth_token)
        if 'secret' not in headers:
            return False

        # decrypt with common jwt secret
        payload = decrypt_token(auth_token, 'data clearinghouse')

        # check that the decrypted secret header matches the iat time
        private_key = RSA.importKey(cns['_AUTH_SECRET'])
        decryptor = PKCS1_OAEP.new(private_key)
        secret = base64.b64decode(headers['secret'])
        decrypted_message = decryptor.decrypt(secret)

        if str(payload['iat']) == decrypted_message.decode('utf-8'):
            return True
        
    except Exception as e:
        sys.stderr.write('valid_jwt_key exception: '+str(e)+'\n') 
        return False

@app.route("/coral/", methods=['GET','POST'])
def hello():
    return ('Welcome!')
    
@app.route("/coral/test_brick_upload")
def test_brick_upload():
    data_id = 'c74928ccf2e14c87a51a03e7d879eaf5'
    uds_file_name = os.path.join(TMP_DIR, _UPLOAD_DATA_STRUCTURE_PREFIX + data_id )
    uvd_file_name = os.path.join(TMP_DIR, _UPLOAD_VALIDATED_DATA_2_PREFIX + data_id )
    brick_ds = json.loads(open(uds_file_name).read())
    brick_ds['name'] = 'test4'
    brick_data = json.loads(open(uvd_file_name).read())

    br = _create_brick(brick_ds, brick_data)        

    process_term = _get_term(brick_ds['process'])
    person_term = _get_term(brick_ds['personnel'])
    campaign_term = _get_term(brick_ds['campaign'])
    input_obj_ids = br.get_fk_refs(process_ufk=True)

    # s = br.to_json()
    # s = pprint.pformat(json.loads(s))
    s = pprint.pformat(input_obj_ids)
    return s
    
    br.save(process_term=process_term,
            person_term=person_term,
            campaign_term=campaign_term,
            input_obj_ids=input_obj_ids)

    return s
    # return br.id
    
@app.route("/coral/refs_to_core_objects", methods=['POST'])
def coral_refs_to_core_objects():
    try:
        brick_ds = json.loads(request.form['brick'])       
        data_id = brick_ds['data_id']

        # s = pprint.pformat(brick_ds)
        # sys.stderr.write(s+'\n')

        uvd_file_name = os.path.join(TMP_DIR, _UPLOAD_VALIDATED_DATA_PREFIX + data_id )
        validated_data = json.loads(open(uvd_file_name).read())

        # we need to validate / generate refs to core objects
        # from properties, because those were not previously mapped
        for prop in brick_ds['properties']:
            if prop['require_mapping']:
                vtype_term_id = prop['type']['id']
                values = np.array([prop['value']['text']], dtype='object')
                errors = svs['value_validator'].cast_var_values(values, vtype_term_id, validated_data['obj_refs'])

        # s = pprint.pformat(validated_data)
        # sys.stderr.write(s+'\n')

        # save to include the newly validated data
        uvd_file_name = os.path.join(TMP_DIR, _UPLOAD_VALIDATED_DATA_2_PREFIX + data_id )
        with open(uvd_file_name, 'w') as f:
            json.dump(validated_data, f, sort_keys=True, indent=4)
        
        res = validated_data['obj_refs']

        # res = [{
        #     'var_name': 'qqq',
        #     'count': 5
        # },{
        #     'var_name': 'aaa',
        #     'count': 4
        # }]
        return _ok_response(res)
    except Exception as e:
        return _err_response(e, traceback=True)

@app.route("/coral/search_dimension_microtypes/<value>", methods=['GET'])
def search_dimension_microtypes(value):
    if value is None:
        value = '*'
    return _search_microtypes(svs['ontology'].dimension_microtypes, value)

@app.route("/coral/search_dimension_variable_microtypes/<value>", methods=['GET'])
def search_dimension_variable_microtypes(value):
    if value is None:
        value = '*'
    return _search_microtypes(svs['ontology'].dimension_variable_microtypes, value)

@app.route("/coral/search_data_variable_microtypes/<value>", methods=['GET'])
def search_data_variable_microtypes(value):
    # TODO: do we need a special OTerm property to select data variable - specific terms
    if value is None:
        value = '*'
    return _search_microtypes(svs['ontology'].dimension_variable_microtypes, value)

@app.route("/coral/search_property_microtypes/<value>", methods=['GET'])
def search_property_microtypes(value):
    return _search_microtypes(svs['ontology'].property_microtypes, value)

def rreplace(s, old, new, occurrence):
    li = s.rsplit(old, occurrence)
    return new.join(li)

def _search_microtypes(ontology, value):
    try:
        res = []
        if value is None:
            return _ok_response(res)

        # look for exact matches first
        exact_val_pattern = '+'+value.replace(' ',',+')
        # sys.stderr.write('pattern1 '+exact_val_pattern+'\n')
        term_collection = ontology.find_name_pattern(exact_val_pattern)
        for term in term_collection.terms:
            if not term.is_hidden:
                td = term.to_descriptor()
                # sys.stderr.write('exact '+str(td)+'\n')
                res.append(td)

        # if too many exact matches, don't look for prefix matches
        if (len(res) > 50):
            # sys.stderr.write('returning '+str(res)+'\n')
            return _ok_response(res)
        
        # look for prefix matches next, only if value has enough characters
        if (len(value) > 2):
            last_prefix_pattern = rreplace(' '+value,' ',',prefix:',1).replace(' ',',+')
            if last_prefix_pattern.startswith(','):
                last_prefix_pattern = last_prefix_pattern[1:]
                # sys.stderr.write('pattern2 '+last_prefix_pattern+'\n')
                term_collection = ontology.find_name_pattern(last_prefix_pattern)
                for term in term_collection.terms:
                    if not term.is_hidden:
                        td = term.to_descriptor()
                        # sys.stderr.write('prefix '+str(td)+'\n')
                        if (td not in res):
                            res.append(td)

        return _ok_response(res)
    except Exception as e:
        return _err_response(e)

@app.route("/coral/search_property_value_oterms", methods=['POST'])
def search_property_value_oterms():
    query = request.json
    value = query['value']
    parent_term_id = query['microtype']['valid_values_parent']
    return _search_oterms(svs['ontology'].all, value, parent_term_id=parent_term_id)

@app.route("/coral/search_property_value_objrefs", methods=['POST'])
def search_property_value_objrefs():
    try:
        query = request.json
        term = _get_term({ 'id':query['term_id']})
        value = query['value']
        res = []
        fk = term.microtype_fk
        if (fk is None):
            return _err_response('no fk found for '+str(term))
            
        # sys.stderr.write('searching for '+str(fk)+'\n')

        obj_search = re.search('.*\.(.+)\.', fk)
        if obj_search is None:
            return _err_response('bad fk pattern '+fk)
        obj_type = obj_search.group(1)
        # sys.stderr.write('obj is '+obj_type+'\n')

        upk = svs['typedef'].get_type_def(obj_type).upk_property_def.name
        itdef = svs['indexdef'].get_type_def(obj_type)

        # sys.stderr.write('collection is '+itdef.collection_name+'\n')
        # sys.stderr.write('upk is '+upk+'\n')
        # sys.stderr.write('value is '+value+'\n')

        aql = """
           FOR x in @@collection
               FILTER lower(x.@upk) like concat(lower(@value),"%")
               RETURN {id: x._key, text: x.@upk}
        """
        aql_bind = {
            '@collection' : itdef.collection_name,
            'upk': upk,
            'value': value
        }

        rows = svs['arango_service'].find(aql,aql_bind)
        for row in rows:
            res.append(row)

        return _ok_response(res)
    except Exception as e:
        return _err_response(e)


def _search_oterms(ontology, value, parent_term_id=None):
    if value is None:
        value = '*'
    res = []

    if parent_term_id == '':
        parent_term_id = None
    term_collection = ontology.find_name_prefix(value, parent_term_id=parent_term_id)

    for term in term_collection.terms:
        # sys.stderr.write('id '+term.term_id+' text '+term.term_name+'\n')
        if not term.is_hidden:
            res.append({
                'id' : term.term_id,
                'text': term.term_name
            })
    return  json.dumps({
        'results': res
    })

@app.route("/coral/get_property_units_oterms", methods=['POST'])
def get_property_units_oterms():
    query = request.json
    parent_term_ids = query['microtype']['valid_units_parents']
    term_ids = query['microtype']['valid_units'] 
    return _get_oterms(svs['ontology'].all, term_ids=term_ids,  parent_term_ids=parent_term_ids)

@app.route("/coral/get_personnel_oterms", methods=['GET'])
def get_personnel_oterms():
    return _get_oterms(svs['ontology'].all,parent_term_ids=[_PERSONNEL_PARENT_TERM_ID])

@app.route("/coral/get_campaign_oterms", methods=['GET'])
def get_campaign_oterms():
    return _get_oterms(svs['ontology'].all,parent_term_ids=[_CAMPAIGN_PARENT_TERM_ID])

@app.route("/coral/get_process_oterms", methods=['GET'])
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
                if not term.is_hidden:
                    res[term.term_id] = {
                        'id' : term.term_id,
                        'text': term.term_name
                    }
    res = list(res.values())
    res.sort(key=lambda x: x['text'])
    return  json.dumps({
        'results': res
    })    


# @app.route("/coral/search_ont_dtypes/<value>", methods=['GET'])
# def search_ont_dtypes(value):
#     # value = request.args.get('term')
#     return _search_oterms(svs['ontology'].data_types, value)

# @app.route("/coral/search_ont_all/<value>", methods=['GET'])
# def search_ont_all(value):
#     # value = request.args.get('term')
#     return _search_oterms(svs['ontology'].all, value)

# @app.route("/coral/search_ont_units/<value>", methods=['GET'])
# def search_ont_units(value):
#     # value = request.args.get('term')
#     return _search_oterms(svs['ontology'].units, value)

@app.route("/coral/brick_type_templates", methods=['GET'])
def brick_type_templates():
    try:
        templates = svs['brick_template_provider'].templates
        return _ok_response(templates['types'])
    except Exception as e:
        return _err_response(e, traceback=True)

@app.route("/coral/core_types", methods=['GET'])
def core_types():
    try:
        res = []
        
        type_defs = svs['indexdef'].get_type_defs(category=TYPE_CATEGORY_DYNAMIC)
        for td in type_defs:
            res.append({'type': td.name, 'props': td.property_names})

        type_defs = svs['indexdef'].get_type_defs(category=TYPE_CATEGORY_STATIC)
        # res = [ {'type': td.name, 'props': td.property_names} for td in type_defs]
        for td in type_defs:
            res.append({'type': td.name, 'props': td.property_names})

        return _ok_response(res)
    except Exception as e:
        return _err_response(e)

# this API seems unused - see /search instead!
@app.route('/coral/do_search', methods=['GET', 'POST'])
def do_search():
    try:
        if request.method == 'POST':
            search_data = json.loads(request.form['searchBuilder'])

            s = pprint.pformat(search_data)
            sys.stderr.write('do_search search_data = '+s+'\n')
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
        return  json.dumps( {
                'status': 'success',
                'res': res
        } )

    except Exception as e:
        return _err_response(e)        

@app.route("/coral/brick/<brick_id>", methods=['GET','POST'])
@auth_ro_required
def get_brick(brick_id):
    try:
        (JSON, CSV) = range(2)
        return_format = JSON
        if request.method == 'POST':
            query = request.json
            if query is not None and 'format' in query and query['format'] == 'CSV':
                return_format = CSV

        if return_format == JSON:
            bp = dp._get_type_provider('Brick')
            br = bp.load(brick_id)
            res = br.to_dict()
        else:
            res = _brick_to_csv(brick_id)
        
        return json.dumps( {
            'status': 'success',
            'res': res
        } )
    
    except Exception as e:
        return _err_response(e)        

@app.route("/coral/filter_brick/<brick_id>", methods=['POST'])
@auth_ro_required
def filter_brick(brick_id):
    try:
        query = request.json
        res = _filter_brick(brick_id, query)
        
        return json.dumps( {
            'status': 'success',
            'res': res
        } )
    
    except Exception as e:
        return _err_response(e)        
    
@app.route("/coral/do_report/<value>", methods=['GET'])
def do_report(value):
    report = getattr(svs['reports'], value)
    # res = df.head(n=100).to_json(orient="table", index=False)
    res = report.to_df().head(n=100).to_json(orient="table", index=False)
    # res = df._repr_html_()

    return  json.dumps( {
            'status': 'success',
            'res': res
    } )


@app.route('/coral/dim_var_validation_errors/<data_id>/<dim_index>/<dim_var_index>', methods=['GET'])
def dim_var_validation_errors(data_id, dim_index, dim_var_index):
    try:
        dim_index = int(dim_index)
        dim_var_index = int(dim_var_index)

        uvd_file_name = os.path.join(TMP_DIR, _UPLOAD_VALIDATED_DATA_PREFIX + data_id )
        validated_data = json.loads(open(uvd_file_name).read())

        res = validated_data['dims'][dim_index]['dim_vars'][dim_var_index]['errors']
        return _ok_response(res) 

    except Exception as e:
        return _err_response(e)


@app.route('/coral/data_var_validation_errors/<data_id>/<data_var_index>', methods=['GET'])
def data_var_validation_errors(data_id, data_var_index):
    try:
        data_var_index = int(data_var_index)

        uvd_file_name = os.path.join(TMP_DIR, _UPLOAD_VALIDATED_DATA_PREFIX + data_id )
        validated_data = json.loads(open(uvd_file_name).read())

        res = validated_data['data_vars'][data_var_index]['errors']
        return _ok_response(res) 

    except Exception as e:
        return _err_response(e)


@app.route('/coral/create_brick', methods=['POST'])
def create_brick():
    try:
        brick_ds = json.loads(request.form['brick'])       
        data_id = brick_ds['data_id']

        # Save brick data structure (update)
        uds_file_name = os.path.join(TMP_DIR, _UPLOAD_DATA_STRUCTURE_PREFIX + data_id )
        with open(uds_file_name, 'w') as f:
            json.dump(brick_ds, f, sort_keys=True, indent=4)

        uvd_file_name = os.path.join(TMP_DIR, _UPLOAD_VALIDATED_DATA_2_PREFIX + data_id )
        brick_data = json.loads(open(uvd_file_name).read())

        br = _create_brick(brick_ds, brick_data)

        process_term = _get_term(brick_ds['process'])
        person_term = _get_term(brick_ds['personnel'])
        campaign_term = _get_term(brick_ds['campaign'])
        input_obj_ids = br.get_fk_refs(process_ufk=True)

        br.save(process_term=process_term, 
            person_term=person_term, 
            campaign_term=campaign_term,
            input_obj_ids=input_obj_ids)

        cache.clear()

        return _ok_response(br.id)

    except AQLQueryError as e:
        print(tb.print_exc())
        brick_ds = json.loads(request.form['brick'])
        brick_name = brick_ds['name']
        return _err_response(
            'Brick with name "%s" already exists in system: please use another brick name' % brick_name
        )

    except Exception as e:
        print(tb.print_exc())
        return _err_response(e, traceback=True)


    
@app.route('/coral/validate_upload', methods=['POST'])
def validate_upload():
    try:
        query = request.json
        data_id = query['data_id']
        file_name = os.path.join(TMP_DIR,_UPLOAD_PROCESSED_DATA_PREFIX 
            + data_id)            
        data = json.loads(open(file_name).read())

        file_name = os.path.join(TMP_DIR, _UPLOAD_DATA_STRUCTURE_PREFIX + data_id )
        brick_ds = json.loads(open(file_name).read())

        validated_data = {
            'dims':[],
            'data_vars': [],
            'obj_refs': []
        } 

        res = {
            'dims':[],
            'data_vars': []
        }

        # dataValues: scalarType: "text": "float"
        # dimensions: variables: scalarType: "text": "string"
        for dim_index, dim in enumerate(data['dims']):
            dim_ds = brick_ds['dimensions'][dim_index]
            res_dim_vars = []
            res['dims'].append({
                'dim_vars': res_dim_vars
            })
            validated_dim_vars = []
            validated_data['dims'].append({
                'dim_vars': validated_dim_vars
            })
            for dim_var_index, dim_var in enumerate(dim['dim_vars']):
                dim_var_ds = dim_ds['variables'][dim_var_index]
                vtype_term_id = dim_var_ds['type']['id']
                values = np.array(dim_var['values'], dtype='object')
                
                errors = svs['value_validator'].cast_var_values(values, vtype_term_id, validated_data['obj_refs'])

                total_count = values.size
                invalid_count = len(errors) 
                res_dim_vars.append({
                    'total_count': total_count,
                    'valid_count': total_count - invalid_count,
                    'invalid_count': invalid_count
                })

                validated_dim_vars.append({
                    'values': values.tolist(),
                    'errors': errors
                })

        for data_var_index, data_var in enumerate(data['data_vars']):
            data_var_ds = brick_ds['dataValues'][data_var_index]
            vtype_term_id = data_var_ds['type']['id']
            values = np.array(data_var['values'], dtype='object')
            
            errors = svs['value_validator'].cast_var_values(values, vtype_term_id)

            total_count = values.size
            invalid_count = len(errors) 
            res['data_vars'].append({
                'total_count': total_count,
                'valid_count': total_count - invalid_count,
                'invalid_count': invalid_count
            })

            validated_data['data_vars'].append({
                'values': values.tolist(),
                'errors': errors
            })

        # Save validated data
        uvd_file_name = os.path.join(TMP_DIR, _UPLOAD_VALIDATED_DATA_PREFIX + data_id )
        with open(uvd_file_name, 'w') as f:
            json.dump(validated_data, f, sort_keys=True, indent=4)

        # Save validated report
        uvr_file_name = os.path.join(TMP_DIR, _UPLOAD_VALIDATION_REPORT_PREFIX + data_id )
        with open(uvr_file_name, 'w') as f:
            json.dump(res, f, sort_keys=True, indent=4)

        return _ok_response(res) 

    except Exception as e:
        return _err_response(e)

@app.route('/coral/validate_upload_csv/<data_id>', methods=['GET'])
def validate_upload_csv(data_id):
    uds_file_name = os.path.join(TMP_DIR, _UPLOAD_DATA_STRUCTURE_PREFIX + data_id)

    with open(uds_file_name, 'r') as f:
        brick_ds = json.loads(f.read())

    try:
        validated_data = {
            'dims':[],
            'data_vars': [],
            'obj_refs': []
        } 

        res = {
            'dims':[],
            'data_vars': []
        }

        for dim in brick_ds['dim_context']:
            res_dim_vars = []
            res['dims'].append({
                'dim_vars': res_dim_vars
            })
            validated_dim_vars = []
            validated_data['dims'].append({
                'dim_vars': validated_dim_vars
            })
            for dim_var in dim['typed_values']:
                vtype_term_id = dim_var['value_type']['oterm_ref']

                if dim_var['values']['scalar_type'] in ['object_ref', 'oterm_ref']:
                    if dim_var['values']['scalar_type'] == 'object_ref':
                        dim_var_values = dim_var['values']['object_refs']
                    else:
                        dim_var_values = dim_var['values']['oterm_refs']
                else:
                    scalar_type = dim_var['values']['scalar_type']
                    dim_var_values = dim_var['values'][scalar_type + '_values']

                values = np.array(dim_var_values, dtype='object')

                errors = svs['value_validator'].cast_var_values(values, vtype_term_id, validated_data['obj_refs'])

                total_count = values.size
                invalid_count = len(errors)
                res_dim_vars.append({
                    'total_count': total_count,
                    'valid_count': total_count - invalid_count,
                    'invalid_count': invalid_count
                })

                validated_dim_vars.append({
                    'values': values.tolist(),
                    'errors': errors
                })

        for data_var in brick_ds['typed_values']:
            vtype_term_id = data_var['value_type']['oterm_ref']
            scalar_type = data_var['values']['scalar_type']
            values = np.array(data_var['values'][scalar_type + '_values'], dtype='object')

            errors = svs['value_validator'].cast_var_values(values, vtype_term_id)

            total_count = values.size
            invalid_count = len(errors)
            res['data_vars'].append({
                'total_count': total_count,
                'valid_count': total_count - invalid_count,
                'invalid_count': invalid_count
            })

            validated_data['data_vars'].append({
                'values': values.tolist(),
                'errors': errors
            })

        # Save validated data 
        uvd_file_name = os.path.join(TMP_DIR, _UPLOAD_VALIDATED_DATA_PREFIX + data_id )
        with open(uvd_file_name, 'w') as f:
            json.dump(validated_data, f, sort_keys=True, indent=4)

        # Save validated report
        uvr_file_name = os.path.join(TMP_DIR, _UPLOAD_VALIDATION_REPORT_PREFIX + data_id )
        with open(uvr_file_name, 'w') as f:
            json.dump(res, f, sort_keys=True, indent=4)

        return _ok_response(res) 

    except Exception as e:
        return _err_response(e, traceback=True)

@app.route('/coral/upload', methods=['POST'])
def upload_file():
    try:
        data_id = uuid.uuid4().hex

        brick_ds = json.loads(request.form['brick'])

        # Save brick data structure
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
        brick_data = template.parse_brick_data(brick_ds, udf_file_name)

        # Format booleans in brick data
        brick_data = _format_booleans(brick_data, brick_ds)

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
                    'size' : dim_data['size'],
                    'value_example': _dim_var_example(dim_var_data['values'])
                })

        # Calculate the expected data_var_size
        data_var_size = 1
        for dim in dims:
            data_var_size *= dim['size']

        for data_var_data in brick_data['data_vars']:
            data_vars.append({
                'size' : data_var_size,
                'value_example': _data_var_example(data_var_data['values'])
            })

        return  _ok_response({
                    'dims': dims,
                    'data_vars': data_vars,
                    'data_id': data_id
                })

    except Exception as e:
        return _err_response(e, traceback=True)

def _format_booleans(brick_data, brick_ds):
    '''
    method for converting conventional boolean formats (yes/no, true/false, etc.)
    into format recognized by the system. Turns booleans in dim vars and data vars into ints.
    '''

    def _format_data_var_bools(data_vars):
        for di, data_var in enumerate(data_vars):
            if type(data_var) is list:
                data_var = _format_data_var_bools(data_var)
            else:
                if data_var in true_values:
                    data_vars[di] = 1
                elif data_var in false_values:
                    data_vars[di] = 0
                else:
                    raise ValueError(
                        'Invalid boolean option "%s" - Please use "true/false", "yes/no", or 0/1' % data_var
                )
        return data_vars


    true_values = {'yes', 'Yes', 'y', 'Y', 'true', 'True', 'TRUE', True, 1}
    false_values = {'no', 'No', 'n', 'N', 'false', 'False', 'FALSE', False, 0}

    # convert dimension variables
    for di, dim in enumerate(brick_data['dims']):
        for dvi, dim_var in enumerate(dim['dim_vars']):
            if 'text' in brick_ds['dimensions'][di]['variables'][dvi]['scalarType']:
                scalar_type = brick_ds['dimensions'][di]['variables'][dvi]['scalarType']['text']
            else:
                scalar_type = brick_ds['dimensions'][di]['variables'][dvi]['scalarType']
            if scalar_type == 'boolean':
            # if brick_ds['dimensions'][di]['variables'][dvi]['scalarType'] == 'boolean':
                replaced_values = []
                for val in dim_var['values']:
                    if val in true_values:
                        replaced_values.append(1)
                    elif val in false_values:
                        replaced_values.append(0)
                    else:
                        raise ValueError(
                            'Invalid boolean options "%s" - Please use "true/false", "yes/no" or 0/1' % val
                    )
                dim_var['values'] = replaced_values

        # brick_data['data_vars']['values'] = _format_data_var_bools(brick_data['data_vars']['values'])
    for dvi, data_vars in enumerate(brick_data['data_vars']):
        if 'text' in brick_ds['dataValues'][dvi]['scalarType']:
            scalar_type = brick_ds['dataValues'][dvi]['scalarType']['text']
        else:
            scalar_type = brick_ds['dataValues'][dvi]['scalarType']
        if scalar_type == 'boolean':
            brick_data['data_vars'][dvi]['values'] = _format_data_var_bools(data_vars['values'])

    return brick_data






@app.route('/coral/upload_csv', methods=["POST"])
def upload_csv():
    f = request.files['files']
    data_id = uuid.uuid4().hex

    try:
        udf_file_name = os.path.join(TMP_DIR, _UPLOAD_DATA_FILE_PREFIX + data_id + '_' + f.filename)
        f.save( udf_file_name )

        uds_file_name = os.path.join(TMP_DIR, _UPLOAD_DATA_STRUCTURE_PREFIX + data_id )
        brick_ds = json.loads(_csv_to_brick(udf_file_name, uds_file_name))


        with open(uds_file_name, 'w') as f:
            f.write(Brick.read_dict(data_id, brick_ds).to_json())
            f.close()

        brick_response = {
            'type': {
                'id': brick_ds['data_type']['oterm_ref'],
                'text': brick_ds['data_type']['oterm_name']
            },
            'name': brick_ds['name'],
            'description': brick_ds['description'],
            'data_id': data_id,
            'dataValues': [],
            'dimensions': [],
            'properties': []
        }

        data_var_count = 1

        # map dimensions to front end brick format
        for di, dim_ds in enumerate(brick_ds['dim_context']):
            response_dim = {
                'index': di,
                'required': False,
                'size': dim_ds['size'],
                'type': {
                    'id': dim_ds['data_type']['oterm_ref'],
                    'text': dim_ds['data_type']['oterm_name']
                }
            }

            data_var_count *= dim_ds['size']
            variables = []
            for dvi, dim_var_ds in enumerate(dim_ds['typed_values']):
                response_dim_var = {
                    'type': {
                        'id': dim_var_ds['value_type']['oterm_ref'],
                        'text': dim_var_ds['value_type']['oterm_name']
                    },
                    'index': dvi,
                    'totalCount': dim_ds['size'],
                    'require_mapping': dim_var_ds['values']['scalar_type'] in ['object_ref', 'oterm_ref'],
                    'scalarType': dim_var_ds['values']['scalar_type'],
                }
                if 'value_units' in dim_var_ds:
                    response_dim_var['units'] = {
                        'id': dim_var_ds['value_units']['oterm_ref'],
                        'text': dim_var_ds['value_units']['oterm_name']
                    }
                else:
                    response_dim_var['units'] = None
                variables.append(response_dim_var)
            response_dim['variables'] = variables
            brick_response['dimensions'].append(response_dim)

        for dti, data_var_ds in enumerate(brick_ds['typed_values']):
            # print('data var ds')
            # print(json.dumps(data_var_ds, indent=2))
            response_dv = {
                'index': dti,
                'required': False,
                'totalCount': data_var_count,
                'scalarType': data_var_ds['values']['scalar_type'],
                'type': {
                    'id': data_var_ds['value_type']['oterm_ref'],
                    'text': data_var_ds['value_type']['oterm_name']
                }
            }
            if 'value_units' in response_dv:
                response_dv['units'] = {
                    'id': response_dv['value_units']['oterm_ref'],
                    'text': response_dv['value_units']['oterm_name']
                }
            else:
                response_dv['units'] = None
            brick_response['dataValues'].append(response_dv)

        # add properties
        for pi, property_ds in enumerate(brick_ds['array_context']):
            print('property_ds')
            print(json.dumps(property_ds, indent=2))

            microtypes = svs['ontology'].property_microtypes
            prop_microtype = microtypes.find_id(property_ds['value_type']['oterm_ref'])

            scalar_type = property_ds['value']['scalar_type']

            require_mapping = property_ds['value']['scalar_type'] in ['object_ref', 'oterm_ref']

            if require_mapping:
                if property_ds['value']['scalar_type'] == 'object_ref':
                    value = {
                        'id': property_ds['value']['object_ref'],
                        'text': property_ds['value']['string_value']
                    }
                else:
                    value = {
                        'id': property_ds['value']['oterm_ref'],
                        'text': property_ds['value']['string_value']
                    }
            else:
                value = property_ds['value'][str(scalar_type) + '_value']

            props_response = {
                'scalarType': property_ds['value']['scalar_type'],
                'type': {
                    'id': property_ds['value_type']['oterm_ref'],
                    'text': property_ds['value_type']['oterm_name']
                },
                'value': value,
                'microType': {
                    'valid_units': prop_microtype.microtype_valid_units,
                    'valid_units_parents': prop_microtype.microtype_valid_units_parents,
                    'fk': prop_microtype.microtype_fk,
                    'valid_values_parent': prop_microtype.microtype_valid_values_parent
                },
                'require_mapping': require_mapping,
            }

            if 'value_units' in property_ds:
                props_response['units'] = {
                    'id': property_ds['value_units']['oterm_ref'],
                    'text': property_ds['value_units']['oterm_name']
                }
            else:
                props_response['units'] = None
            
            brick_response['properties'].append(props_response)

        return _ok_response(brick_response)

    except Exception as e:
        return _err_response(e, traceback=True)


@app.route('/coral/core_type_names', methods=["GET"])
@auth_required
def get_core_type_names():
    type_def_names = svs['typedef'].get_type_names()
    return _ok_response([name for name in type_def_names if name != 'ENIGMA'])

@app.route('/coral/get_provenance/<type_name>')
@auth_required
def get_provenance(type_name):
    type_def = svs['typedef'].get_type_def(type_name)

    requires_processes = False
    # check if entity is "top-level" and requires no input processes
    # TODO: remove specific checks for 'ENIGMA' and create is_root property
    for process_list in type_def.process_input_type_defs:
        if requires_processes:
            break
        for process in process_list:
            if process != 'ENIGMA':
                requires_processes = True
                break
    return _ok_response({'requires_processes': requires_processes})

@app.route('/coral/validate_core_tsv_headers', methods=["POST"])
@auth_required
def validate_core_tsv_headers():
    # Validate headers of TSV before uploading each item individually
    try:
        # Check for headers against core typedef
        type_name = request.form['type']
        _validate_headers(request.files['file'], type_name)

        # Check process headers against process, if processes are required
        if 'process_file' in request.files:
            _validate_headers(request.files['process_file'], 'Process')

        return _ok_response({'message': 'Validated successfully'})
    
    except Exception as e:
        return str(e), 400


def _validate_headers(upload_file, type_name) -> None:
    df = pd.read_csv(upload_file, sep='\t')

    typedef = svs['typedef'].get_type_def(type_name)

    # Check that there are no missing required fields
    for pname in typedef.property_names:
        prop_def = typedef.property_def(pname)
        if prop_def.required and pname not in df.columns.values and not prop_def.is_pk:
            raise ValueError('Error: required property field "%s" is missing from %s TSV headers' % (pname, type_name))

    # Make sure there are no keys not defined in typedef
    for value in df.columns.values:
        if value not in typedef.property_names:
            raise ValueError('Error: Unrecognized property "%s" for type %s' % (value, type_name))

@app.route('/coral/upload_core_type_tsv', methods=["POST"])
@auth_required
def upload_core_type_tsv():

    def upload_progress(df, process_df, batch_id, type_name):
        n_rows = df.shape[0]
        result_data = {
            'type_name': type_name,
            'success': [],
            'errors': [],
            'warnings': [],
            'process_errors': [],
            'process_warnings': []
        }

        type_def_service = svs['typedef']
        type_def = type_def_service.get_type_def(type_name)

        if process_df is not None:
            process_typedef = svs['typedef'].get_type_def(TYPE_NAME_PROCESS)

        for ri, row in df.iterrows():
            try:
                data = row.to_dict()
                data_holder = EntityDataHolder(type_name, data)
                if process_df is not None:
                    # Ensure that there exactly 1 reference to core type in process TSV
                    upk_id = data[type_def.upk_property_def.name]
                    core_process_rows = process_df.loc[process_df['output_objects'].str.contains(upk_id)]

                    if len(core_process_rows.index) != 1:
                        if len(core_process_rows.index) == 0:
                            result_data['process_errors'].append({
                                'data': process_dataholder.data,
                                'message': 'Link to %s with id "%s" not found in process file' % (type_name, upk_id)
                            })
                        else:
                            result_data['process_errors'].append({
                                'data': process_dataholder.data,
                                'message': 'Conflicting input objects found in process file for %s with id "%s"' % (type_name, upk_id)
                            })
                        yield "data: error--\n\n"
                        continue

                    process_data = core_process_rows.iloc[0].to_dict()

                    process_dataholder = ProcessDataHolder(process_data)

                    # Validate if input objects exist and are correct
                    # TODO: Check how to validate inputs based on typedef.json schema
                    for input_object in process_dataholder.data['input_objects'].split(','):
                        input_type_name, input_upk_id = process_dataholder.get_process_id(input_object)
                        try:
                            pk_id = ws._get_pk_id(input_type_name, input_upk_id)
                        except ValueError as e:
                            result_data['process_errors'].append({
                                'data': process_dataholder.data,
                                'message': 'Input object %s does not exist for process connecting to %s' % (input_upk_id, upk_id)
                            })

                    for output_object in process_dataholder.data['output_objects'].split(','):
                        # try to find existing process from output ids
                        output_type_name, output_upk_id = process_dataholder.get_process_id(output_object)

                        pk_id = ws._get_pk_id_or_none(output_type_name, output_upk_id)

                        if pk_id is not None:
                            # find out if process exists and throw a warning if fields are different
                            output_index_def = indexdef.get_type_def(output_type_name)
                            saved_processes = svs['arango_service'].get_up_processes(output_index_def, pk_id)
                            process_doc = IndexDocument.build_index_doc(process_dataholder)

                            if len(saved_processes) == 0:
                                continue

                            # TODO: figure out if it needs to validate for multiple up processes
                            saved_process = saved_processes[0]

                            matches_saved_process = True

                            for k, v in process_doc.items():
                                if k.startswith('_') or k == 'input_objects' or k == 'output_objects':
                                    continue

                                if saved_process[k] != v:
                                    matches_saved_process = False
                                    break

                            if not matches_saved_process:
                                result_data['process_warnings'].append({
                                    'message': 'Process id %s already exists with values differing from incoming upload' % saved_process['id'],
                                    'old_data': saved_process,
                                    'new_data': process_doc,
                                    'data_holder': process_dataholder.data
                                })
                                yield "data: warning--\n\n"
                                continue

                    try:
                        process_typedef.validate_data(process_dataholder.data, ignore_pk=True)
                        # ws.validate_process_exists(process_dataholder)
                    # except ItemAlreadyExistsException as ie:
                    #     if ie.changed_data:
                    #         result_data['process_warning'].append({
                    #             'message': ie.message,
                    #             'old_data': ie.old_data,
                    #             'new_data': ie.new_data,
                    #             'data_holder': ie.data_holder
                    #         })
                    #         yield "data: warning--{}\n\n".format(ie.message)
                    #         continue

                    except Exception as e:
                        tb.print_exc()
                        print ('bad process validation', str(e))
                        result_data['process_errors'].append({
                            'data': process_dataholder.data,
                            'message': str(e)
                        })
                        yield "data: error--\n\n"
                        continue

                    ws.save_data_if_not_exists(data_holder, preserve_logs=True)
                    ws.save_process(process_dataholder, update_object_ids=True)
                else:
                    ws.save_data_if_not_exists(data_holder, preserve_logs=True)

                result_data['success'].append(data_holder.data)
                yield "data: success--\n\n"

            except ItemAlreadyExistsException as ie:
                if ie.changed_data:
                    result_data['warnings'].append({
                        'message': ie.message,
                        'old_data': ie.old_data,
                        'new_data': ie.new_data,
                        'data_holder': ie.data_holder
                    })
                    yield "data: warning--{}\n\n".format(ie.message)
                else:
                    result_data['success'].append(data_holder.data)
                    yield "data: success--\n\n"

            except ValueError as e:
                tb.print_exc()
                result_data['errors'].append({
                    'data': data_holder.data,
                    'message': str(e)
                })
                yield "data: error--{}\n\n".format(e)

            except Exception as e:
                print('something went wrong', tb.print_exc())

            yield "data: progress--{}\n\n".format((ri + 1) / n_rows)

        # Add units to display in result table UI, if applicable
        ontology = svs['ontology']
        prop_units = {}
        # type_def_service = svs['typedef']
        # type_def = type_def_service.get_type_def(type_name)

        for prop_name in type_def.property_names:
            prop_def = type_def.property_def(prop_name)
            if prop_def.has_units_term_id():
                term = ontology._get_term(prop_def.units_term_id)
                prop_units[prop_name] = term.term_name

        result_data['property_units'] = prop_units

        with open(os.path.join(TMP_DIR, _UPLOAD_CORE_DATA_PREFIX + batch_id), 'w') as f:
            json.dump(result_data, f, indent=4, sort_keys=False)
        yield "data: complete--{}\n\n".format(batch_id)

    batch_id = uuid.uuid4().hex
    tmp_batch_file = os.path.join(TMP_DIR, _UPLOAD_CORE_DATA_PREFIX + batch_id)

    type_name = request.form['type']
    upload_file = request.files['file']

    indexdef = svs['indexdef']
    ws = svs['workspace']

    index_type_def = indexdef.get_type_def(type_name)
    index_type_def._ensure_init_index()

    df = pd.read_csv(upload_file, sep='\t')
    df = df.replace({np.nan: None})

    # get process upload file if it exists
    process_df = None
    if 'process_file' in request.files:
        process_file = request.files['process_file']
        process_df = pd.read_csv(process_file, sep='\t')
        process_df = process_df.replace({np.nan: None})

    return Response(upload_progress(df, process_df, batch_id, type_name), mimetype='text/event-stream')

@app.route('/coral/get_core_type_results/<batch_id>', methods=["GET"])
@auth_required
def get_core_type_results(batch_id):
    upload_result_path = os.path.join(TMP_DIR, _UPLOAD_CORE_DATA_PREFIX + batch_id) 
    with open(upload_result_path) as f:
        upload_result = json.loads(f.read())

    # strip NaN values from JSON
    for error in upload_result['errors']:
        error['data'] = {k: None if v != v else v for k, v in error['data'].items()}

    return _ok_response(upload_result, sort_keys=False)

@app.route('/coral/update_core_duplicates', methods=["POST"])
@auth_required
def update_core_duplicates():
    # Overwrite existing uploads after prompting warning window to user
    batch_id = request.json['batch_id']
    upload_result_path = os.path.join(TMP_DIR, _UPLOAD_CORE_DATA_PREFIX + batch_id)

    with open(upload_result_path) as f:
        upload_result = json.loads(f.read())
        core_duplicates = upload_result['warnings']
        type_name = upload_result['type_name']

    ws = svs['workspace']
    indexdef = svs['indexdef']
    index_type_def = indexdef.get_type_def(type_name)
    index_type_def._ensure_init_index()

    update_results = []
    for duplicate in core_duplicates:
        try:
            data_holder = EntityDataHolder(type_name, duplicate['data_holder'])
            ws.update_data(data_holder)
            update_results.append({'error': False, 'data': duplicate['new_data'], 'message': ''})
        except Exception as e:
            print(e)
            tb.format_exc()
            # add validation exception to response
            update_results.append({'error': True, 'data': duplicate['new_data'], 'message': str(e)})
    
    return _ok_response(update_results)


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

def _brick_to_csv(brick_id):
    file_name_json = os.path.join(cns['_DATA_DIR'],brick_id)
    file_name_csv = os.path.join(TMP_DIR,brick_id+'.csv')
    cmd = os.path.join(cns['_PROJECT_ROOT'], 'bin', 'ConvertGeneric.sh') + ' ' + file_name_json + ' ' + file_name_csv
    sys.stderr.write('running '+cmd+'\n')
    output = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=None, shell=True, cwd=os.path.join(cns['_PROJECT_ROOT'],'bin'))
    with open(file_name_csv, 'r') as file:
        data = file.read()
    return data

def _csv_to_brick(file_name_csv, file_name_json):
    # for uploading CSVs as bricks, stored in /tmp directory

    cmd = os.path.join(cns['_PROJECT_ROOT'], 'bin', 'ConvertGeneric.sh') + ' ' + file_name_csv + ' ' + file_name_json
    sys.stderr.write('running '+cmd+'\n')
    output = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=None, shell=True, cwd=os.path.join(cns['_PROJECT_ROOT'],'bin'))
    with open(file_name_json, 'r') as file:
        data = file.read()
    return data

def _filter_brick(brick_id, query):
    file_name_json = os.path.join(cns['_DATA_DIR'],brick_id)
    file_name_out = os.path.join(TMP_DIR,brick_id+'_filtered.json')
    # cmd = '/home/coral/prod/bin/FilterGeneric.sh '+file_name_json+' \''+json.dumps(query)+'\''
    cmd = os.path.join(cns['_PROJECT_ROOT'], 'bin', 'FilterGeneric.sh') + ' ' + file_name_json + ' \'' + json.dumps(query) + '\'' 
    sys.stderr.write('running '+cmd+'\n')
    output = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=None, shell=True, cwd=os.path.join(cns['_PROJECT_ROOT'],'bin'))
    try:
        data = json.loads(output.stdout)
        return data
    except Exception as e:
        raise Exception('FAILED brick filter: '+str(output.stdout))

def _create_brick(brick_ds, brick_data):
    # TODO: check "brick type" and "brick name"
    brick_dims = brick_ds['dimensions']
    brick_data_vars = brick_ds['dataValues']
    brick_properties = brick_ds['properties']

    dim_type_terms = []
    dim_sizes = []

    for dim_index, dim in enumerate(brick_dims):
        dim_type_term = _get_term(dim['type'])
        dim_type_terms.append( dim_type_term )

        for dim_var in brick_data['dims'][dim_index]['dim_vars']:
            dim_size = len(dim_var['values']) 
        dim_sizes.append( dim_size )
        
    brick_type_term = _get_term(brick_ds['type'])
    brick_name = brick_ds['name'] 
    brick_description = brick_ds['description'] 

    bp = dp._get_type_provider('Brick')
    br = bp.create_brick(type_term = brick_type_term, 
                         dim_terms = dim_type_terms, 
                         shape = dim_sizes,
                         name = brick_name,
                         description = brick_description
    )

    # add dim variables
    for dim_index, dim in enumerate(brick_dims):
        for dim_var_index, dim_var in enumerate(dim['variables']):
            var_type_term = _get_term(dim_var['type'])
            var_units_term = _get_term(dim_var['units'])

            values = brick_data['dims'][dim_index]['dim_vars'][dim_var_index]['values']
            if var_type_term.microtype_value_scalar_type == 'oterm_ref':
                for i, val in enumerate(values):
                    values[i] = _get_term(val)

            v = br.dims[dim_index].add_var(var_type_term, var_units_term, values, 
                scalar_type=var_type_term.microtype_value_scalar_type)
            if 'context' in dim_var: 
                _add_var_context(v, dim_var['context'])

    # add data
    for data_var_index, data_var in enumerate(brick_data_vars):
        data_type_term = _get_term(data_var['type'])
        data_units_term = _get_term(data_var['units'])
        v = br.add_data_var(data_type_term, data_units_term, 
            brick_data['data_vars'][data_var_index]['values'],
            scalar_type=data_type_term.microtype_value_scalar_type)
        if 'context' in data_var: 
            _add_var_context(v, data_var['context'])


    # add brick properties
    for prop in brick_properties:
        var_type_term = _get_term(prop['type'])
        var_units_term = _get_term(prop['units'])
        scalar_type = var_type_term.microtype_value_scalar_type
        value = prop['value']
        if (scalar_type == 'oterm_ref'):
            value = value['id']
        if (scalar_type == 'object_ref'):
            value = value['text']
        br.add_attr(var_type_term, var_units_term, scalar_type, value)

    return br


def _add_var_context(brick_var, context_elems):
    for ce in context_elems:
        type_term = _get_term(ce.get('type'))
        units_term = _get_term(ce.get('units'))
        scalar_type = type_term.microtype_value_scalar_type        
        value = _get_term(ce.get('value')) if  scalar_type == 'oterm_ref' else ce.get('value')['text']
        brick_var.add_attr(type_term=type_term, units_term=units_term, 
            scalar_type=scalar_type, value=value)

def _get_term(term_data):
    return svs['term_provider'].get_term( term_data['id'] ) if term_data and term_data['id'] != '' else None


########################################################################################
## NEW VERSION
##########################################################################################

@app.route("/coral/google_auth_code_store", methods=["POST"])
def handle_auth_code():

    with open(cns['_GOOGLE_OAUTH2_CREDENTIALS']) as f:
        client_credentials =  json.load(f)

    result = requests.post('https://www.googleapis.com/oauth2/v4/token', {
        'client_id': client_credentials['web']['client_id'],
        'client_secret': client_credentials['web']['client_secret'],
        'redirect_uri': 'postmessage',
        'grant_type': 'authorization_code',
        'code': request.json['authCode']
    })

    tokens = json.loads(result.content.decode('utf-8'))
    access_token = tokens['access_token']
    # refresh_token = tokens['refresh_token']
    # TODO: store access_token and refresh_token ?

    user = requests.get('https://www.googleapis.com/oauth2/v1/userinfo?access_token=' + access_token)

    user_email = json.loads(user.content.decode('utf-8'))['email']

    with open(cns['_USERS']) as user_file:
        registered_users = json.load(user_file)

    match_user = None
    for registered_user in registered_users:
        if registered_user['email'] == user_email:
            match_user = registered_user

    if match_user == None:
        return _ok_response({
            'success': False,
            'message': 'User not registered in system'
        })

    try:
        payload = {
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=0, seconds=0, milliseconds=0, microseconds=0, minutes=120),
            'iat': datetime.datetime.utcnow(),
            'sub': match_user['username']
        }

        new_jwt = jwt.encode(payload, cns['_AUTH_SECRET'], algorithm='HS256')
        return _ok_response({'success': True, 'token': new_jwt, 'user': match_user})
    except Exception as e:
        return json.dumps({'success': False, 'message': 'Something went wrong.'})


@app.route("/coral/request_registration", methods=['POST'])
def process_registration_request():
    recaptcha_token = request.json['token']
    recaptcha_request = requests.post('https://www.google.com/recaptcha/api/siteverify', {
        'secret': cns['_GOOGLE_RECAPTCHA_SECRET'],
        'response': recaptcha_token
    })

    recaptcha_result = json.loads(recaptcha_request.content.decode('utf-8'))
    print(recaptcha_result)

    if 'success' in recaptcha_result:
        first_name = request.json['firstName']
        last_name = request.json['lastName']
        email = request.json['email']

        port = 465
        pw = cns['_WEB_SERVICE']['project_email_password']
        sender_email = cns['_WEB_SERVICE']['project_email']
        receiver_email = cns['_WEB_SERVICE']['admin_email']
        context = ssl.create_default_context()

        with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
            server.login(sender_email, pw)

            message = """\
                Subject: New User Registration

                %s %s has requested access to your CORAL application, using the email address %s. To approve this user, add their information to the users.json file in your config.
            """ % (first_name, last_name, email)

            server.sendmail(sender_email, receiver_email, message)

        return _ok_response({'success': True})
            
    
    else:
        return _err_response({'message': 'invalid captcha', 'success': False})

@cross_origin
@app.route("/coral/user_login", methods=['GET', 'POST'])
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
		        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=0, seconds=0, microseconds=0, milliseconds=0, minutes=120),
		        'iat': datetime.datetime.utcnow(),
		        'sub': login['username']
	        }

            new_jwt = jwt.encode(payload, cns['_AUTH_SECRET'], algorithm='HS256')
            return json.dumps({'success': True, 'token': new_jwt})
        
        except Exception as e:
            return json.dumps({'success': False,
                               'message': 'Something went wrong.'
                               # 'message': 'Something went wrong: '+str(e)
            })  


@app.route("/coral/data_types", methods=['GET'])
@auth_required
def coral_data_types():
    res = []
    
    # Core types
    type_defs = svs['indexdef'].get_type_defs(category=TYPE_CATEGORY_STATIC)
    for td in type_defs:
        if td.name == 'ENIGMA': continue
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

@app.route("/coral/data_models", methods=['GET'])
@auth_required
def coral_data_models():
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

@app.route('/coral/brick_dimension/<brick_id>/<dim_index>', methods=['GET'])
@auth_required
def coral_brick_dimension(brick_id, dim_index):
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
            var_data = {
                'type':{
                    'id': dim_var.type_term.term_id,
                    'text': dim_var.type_term.term_name
                },
                'units':{
                    'id': dim_var.units_term.term_id if dim_var.units_term else '',
                    'text': dim_var.units_term.term_name if dim_var.units_term else ''
                },
                'values': list([ str(val) for val in dim_var.values][:MAX_ROW_COUNT]),
                'context': []
            }
            var_data['type_with_units'] = dim_var.type_term.term_name
            for attr in dim_var.attrs:
                var_data['context'].append({
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
                var_data['type_with_units'] += ', '+attr.type_term.term_name+'='+str(attr.value)
                if attr.units_term:
                    var_data['type_with_units'] += ', '+attr.units_term.term_name
            if dim_var.units_term:
                var_data['type_with_units'] += ' ('+dim_var.units_term.term_name+')'

            res['dim_vars'].append(var_data)
            
    except Exception as e:
        return _err_response(e)

    return _ok_response(res)

@app.route('/coral/brick_map/<brick_id>', methods=['POST'])
@auth_required
def coral_brick_map_data(brick_id):
    bp = dp._get_type_provider('Brick')
    br = bp.load(brick_id)
    body = request.json
    dim_constraints = []
    if body['constrainingRequired']:
        for constraint in body['constraints']:
            if constraint['dim_idx'] == 0: # or constraint['disabled']:
                continue
            for dv in constraint['variables']:
                # TODO: this method only works for non combinatorial brick dimensions
                if dv['type'] == 'flatten':
                    dim_constraints.append(dv['selected_value'])
                    break
    if 'data_variable' in body['colorField']:
        color_values = []
        cfi = body['colorField']['data_variable']
        for i in range(br.dims[0].size):
            data_vars = br.data_vars[cfi].values[i]
            for j in dim_constraints:
                data_vars = data_vars[j]
            color_values.append(data_vars)

    if 'data_variable' in body['labelField']:
        label_values = []
        lfi = body['labelField']['data_variable']
        for i in range(br.dims[0].size):
            data_vars = br.data_vars[lfi].values[i]
            for j in dim_constraints:
                data_vars = data_vars[j]
            label_values.append(data_vars)
        
    # assume for now Lat and Long vars reside in first dimension
    for idx, dv in enumerate(br.dims[0].vars):
        if dv.name == 'Latitude':
            lat_idx = idx
        if dv.name == 'Longitude':
            long_idx = idx

    if 'dimension_variable' in body['colorField']:
        dv_cf = body['colorField']['dimension_variable']
    if 'dimension_variable' in body['labelField']:
        dv_lf = body['labelField']['dimension_variable']

    res = []
    for i in range(br.dims[0].size):
        item = dict(
            latitude=br.dims[0].vars[lat_idx].values[i],
            longitude=br.dims[0].vars[long_idx].values[i]
        )
        if 'dimension_variable' in body['colorField']:
            # item[body['colorField']['name']] = br.dims[0].vars[dv_cf].values[i]
            item['color'] = br.dims[0].vars[dv_cf].values[i]
        elif color_values:
            # item[body['colorField']['name']] = color_values[i]
            item['color'] = color_values[i]
        if 'dimension_variable' in body['labelField']:
            # item[body['labelField']['name']] = br.dims[0].vars[dv_lf].values[i]
            item['label_text'] = str(br.dims[0].vars[dv_lf].values[i])
        elif label_values:
            # item[body['labelField']['name']] = label_values[i]
            item['label_text'] = str(label_values[i])
        res.append(item)
    return _ok_response(res)


@app.route('/coral/brick_plot_metadata/<brick_id>/<limit>', methods=['GET'])
@auth_required
def coral_brick_plot_metadata(brick_id, limit):
    bp = dp._get_type_provider('Brick')
    br = bp.load(brick_id)

    return br.to_json(exclude_data_values=True, typed_values_property_name=False, truncate_variable_length=int(limit), show_unique_indices=True)

@app.route('/coral/brick_dim_var_values/<brick_id>/<dim_idx>/<dv_idx>/<keyword>', methods=['GET'])
@auth_required
def get_brick_dim_var_values(brick_id, dim_idx, dv_idx, keyword):
    # used for populating plot constraints for dimensions with more than the specified amount of variables
    bp = dp._get_type_provider('Brick')
    br = bp.load(brick_id)
    dim_var = br.dims[int(dim_idx)].vars[int(dv_idx)]
    dv_results = [{'display': v, 'index': i} for i, v in enumerate(dim_var.values) if v.find(keyword) > 0]
    return _ok_response(dv_results)

@app.route('/coral/brick_metadata/<brick_id>', methods=['GET'])
@auth_required
def coral_brick_metadata(brick_id):
    bp = dp._get_type_provider('Brick')
    br = bp.load(brick_id)
    
    return br.to_json(exclude_data_values=False, typed_values_property_name=False)

def _get_plot_data(query):
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

@app.route('/coral/plotly_core_data', methods=["POST"])
def coral_plotly_core_data():
    body = request.json
    try:
        rs = _get_core_plot_data(body['query'])
        layout = {
            'x': 800,
            'y': 600,
            'title': body['title'],
            **body['plot_type']['plotly_layout']
        }
        if 'x' in body['axes']:
            if body['axes']['x']['show_title']:
                layout['xaxis'] = {
                    'title': body['axes']['x']['title']
                }
        if 'y' in body['axes']:
            if body['axes']['y']['show_title']:
                layout['yaxis'] = {
                    'title': body['axes']['y']['title']
                }

        x_field = body['axes']['x']['data']['name']
        y_field = body['axes']['y']['data']['name']
        data = [{
            'x': [i for i in rs[x_field]],
            'y': [i for i in rs[y_field]],
            **body['plot_type']['plotly_trace']
        }]

        return _ok_response({
            'layout': layout,
            'data': data
        })
    except Exception as e:
        return _err_response(e)

    return json.dumps({'test': 'testing core type plot'}), 200

def _get_core_plot_data(search_data):
    query_match = search_data['queryMatch'] # change field name here
    provider = dp._get_type_provider(query_match['dataModel'])
    q = provider.query()

    for criterion in query_match['params']:
        (prop_name, prop_value, operation) = _extract_criterion_props(criterion)
        q.has({prop_name: {operation: prop_value}})

    if 'processesUp' in search_data:
        for criterion in search_data['processesUp']:
            (prop_name, prop_value, operation) = _extract_criterion_props(criterion)
            q.is_output_of_process({prop_name: {operation: prop_value}})
            # hack to search all people in labs
            if operation == '=' and prop_name == 'person' and 'term' in criterion:
                children = svs['ontology'].enigma.find_id(criterion['term']).children
                for x in children:
                    q.is_output_of_process({prop_name: {operation: x.term_name}})
                    
        if 'searchAllProcessesUp' in search_data:
            if search_data['searchAllProcessesUp'] == True:
                q.search_all_up(True)
        if 'searchAllProcessesDown' in search_data:
            if search_data['searchAllProcessesDown'] == True:
                q.search_all_down(True)

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
            params[prop_name] = {operation: prop_value}

        q.linked_up_to(connects_up_to['dataModel'],  params )

    # Do connectsDownTo
    if 'connectsDownTo' in search_data:
        connects_down_to = search_data['connectsDownTo']
        params = {}
        for criterion in connects_down_to['params']:
            (prop_name, prop_value, operation) = _extract_criterion_props(criterion)
            params[prop_name] = {operation: prop_value}

        q.linked_down_to(connects_down_to['dataModel'],  params )

    # do immediate parent
    if 'parentProcesses' in search_data:
        q.immediate_parent(search_data['parentProcesses'])

    # do the search
    res_df = q.find().to_df()
    return res_df

@app.route('/coral/plotly_data', methods=['POST'])
@auth_required
def coral_plotly_data():
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

@app.route('/coral/plot_data', methods=['POST'])
@auth_required
def coral_plot_data():
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


@app.route('/coral/plot_data_test', methods=['POST'])
@auth_required
def coral_plot_data_test():
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


@app.route('/coral/search', methods=['POST'])
@auth_ro_required
def coral_search():
    try:
        search_data = request.json
        # Do queryMatch
        query_match = search_data['queryMatch']
        provider = dp._get_type_provider(query_match['dataModel'])
        q = provider.query()

        s = pprint.pformat(search_data)
        sys.stderr.write('search_data = '+s+'\n')

        (JSON, CSV) = range(2)
        return_format = JSON
        if 'format' in search_data and search_data['format'] == 'CSV':
            return_format = CSV

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
                # hack to search all people in labs
                if operation == '=' and prop_name == 'person' and 'term' in criterion:
                    children = svs['ontology'].enigma.find_id(criterion['term']).children
                    for x in children:
                        q.is_output_of_process({prop_name: {operation: x.term_name}})
                    
            if 'searchAllProcessesUp' in search_data:
                if search_data['searchAllProcessesUp'] == True:
                    q.search_all_up(True)
            if 'searchAllProcessesDown' in search_data:
                if search_data['searchAllProcessesDown'] == True:
                    q.search_all_down(True)

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
                params[prop_name] = {operation: prop_value}

            q.linked_up_to(connects_up_to['dataModel'],  params )

        # Do connectsDownTo
        if 'connectsDownTo' in search_data:
            connects_down_to = search_data['connectsDownTo']
            params = {}
            for criterion in connects_down_to['params']:
                (prop_name, prop_value, operation) = _extract_criterion_props(criterion)
                params[prop_name] = {operation: prop_value}

            q.linked_down_to(connects_down_to['dataModel'],  params )

        # do immediate parent
        if 'parentProcesses' in search_data:
            q.immediate_parent(search_data['parentProcesses'])

        # do the search
        res_df = q.find().to_df()
        if return_format==JSON:
            # remove term ids from result
            term_cols = []
            for column in res_df.columns:
                if column.endswith('_term_id'):
                    col = column[:-8]
                    if (col+'_term_name') in res_df.columns:
                        term_cols.append(column)
            if len(term_cols) > 0:
                res_df.drop(columns=term_cols, inplace=True)
                col_map = {}
                for column in term_cols:
                    col = column[:-8]
                    col_map[col+'_term_name'] = col
                res_df.rename(columns=col_map, inplace=True)
            # remove empty columns from search results
            empty_cols = []
            #for column in res_df.columns:
                #if len(res_df[column].value_counts())==0:
                #empty_cols.append(column)
            if len(empty_cols) > 0:
                res_df.drop(columns=empty_cols, inplace=True)
            # return result as json table
            res = res_df.to_json(orient="table", index=False)
        else: # TSV
            res = res_df.to_csv(sep='\t')
        # return  json.dumps( {'res': res} )
        return res
    except Exception as e:
        return _err_response(e,traceback=True)

@app.route("/coral/search_operations", methods=['GET'])
@auth_required
def coral_search_operations():
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

@app.route("/coral/plot_types", methods=['GET'])
@auth_required
def coral_plot_types():
    fname = cns['_PLOT_TYPES_FILE']
    try:
        plot_types = json.loads(open(fname).read())['plot_types']
    except Exception as e:
        return _err_response(e)
        
    return _ok_response(plot_types)

@app.route("/coral/report_plot_data/<report_id>", methods=['GET'])
@auth_required
def coral_report_plot_data(report_id):
    reports_map = {
        'report1': 'brick_types',
        'report2': 'process_campaigns'
    }

    try:
        report = getattr(svs['reports'], reports_map[report_id])
        title = report.name
        x = report.values(0)
        y = report.counts

        # Build layout
        layout = {
            # 'width': 800,
            # 'height': 600,
            'title': title
        }
        data = [{
            'x': x,
            'y': y,
            'type': 'bar'
        }]

        return _ok_response({
                'layout': layout,
                'data': data
            })

    except Exception as e:
        return _err_response(e)


@app.route("/coral/reports", methods=['GET'])
@auth_required
def coral_reports():

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

@app.route("/coral/reports/<id>", methods=['GET'])
@auth_required
def coral_report(id):
    try:
        report = getattr(svs['reports'], id)
        df = report.to_df()
        df.columns = ['Category', 'Term ID', 'Count']
        res = df.head(n=1000).to_json(orient="table", index=False)
    except Exception as e:
        return _err_response(e)

    return  _ok_response(res)

@app.route("/coral/filters", methods=['GET'])
@auth_required
def coral_filters():
    reports = svs['reports']

    df_campaign = reports.process_campaigns.to_df()
    df_persons = reports.process_persons.to_df()
    res = [
        {
            'categoryName': 'ENIGMA Campaigns',
            'items': _get_category_items(df_campaign, 'campaign' )
        },
        {
            'categoryName': 'ENIGMA Labs/People',
            'items': _get_category_items(df_persons, 'person')
        },
    ]
    # s = pprint.pformat(res)
    # return s
    return _ok_response(res)

def _get_category_items(process_stat_df, attr):
    term_ids = []
    for _, row in process_stat_df.sort_values('Term Name').iterrows():
        term_ids.append(row['Term ID'])
    term_ids_hash = svs['ontology'].enigma.find_ids_hash(term_ids)
    res = []
    # hack to sort labs before people:
    for term_id in sorted(term_ids,
                          key=lambda x:'000'+term_ids_hash[x].term_name if term_ids_hash[x].term_name.endswith(' Lab') else term_ids_hash[x].term_name):
        res.append(
            {
                'name': term_ids_hash[term_id].term_name,
                'queryParam': {
                    'attribute': attr,
                    'matchType':  '=' ,
                    'keyword': term_ids_hash[term_id].term_name,
                    'term': term_ids_hash[term_id].term_id,
                    'scalarType': 'term'
                }
            }
        )
    return res

# Test version
@app.route('/coral/types_stat', methods=['GET','POST'])
@auth_required
def coral_type_stat():
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
        # sys.stderr.write('name '+td.name+'\n')
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
    # sys.stderr.write('rows: '+str(rows)+'\n')
    # sys.stderr.write('len: '+str(len(rows))+'\n')
    # sys.stderr.write('type: '+str(type(rows))+'\n')
    # Note: awkward code below works around https://github.com/ArangoDB-Community/pyArango/issues/160
    # can't do 'for row in rows:' because query returns infinite empty lists
    for i in range(len(rows)):
        row = rows[i]
        # sys.stderr.write('row: '+str(row)+'\n')
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

# for (relative) line thickness in graphs
def line_thickness(n):
    return int(round(math.log10(n)))+1

# assign x, y to all static and intermediate nodes.
# just assign y to dynamic nodes, and don't process any of their children
def assign_xy_static(nodes, usedPos, i, x, y):
    sys.stderr.write('axys '+str(i)+' '+str(x)+' '+str(y)+' '+str(nodes[i]['name'])+' '+str(nodes[i]['category'])+'\n')
    # skip if already done
    if 'y' in nodes[i]:
        # sys.stderr.write('already assigned y to '+str(nodes[i]['name'])+'\n')
        return
    # assign positions
    nodes[i]['y'] = y
    if nodes[i]['category'] == TYPE_CATEGORY_DYNAMIC and 'isParent' not in nodes[i]:
        return
    elif 'isParent' not in nodes[i]:
        nodes[i]['x'] = x
    if not 'children' in nodes[i]:
        # sys.stderr.write('no children for node '+str(nodes[i]['name'])+'\n')
        return
    # do children of static/intermediate nodes
    for c in nodes[i]['children']:
        if 'y' in nodes[c]:
            continue
        dX = 100
        dY = 100
        if 'dynamic' in nodes[c]:
            assign_xy_static(nodes, usedPos, c, x, y)
            continue
        else:
            # sys.stderr.write('new static '+str(nodes[c]['name'])+'\n')
            proposedY = y+dY
            proposedX = x
            pos = str(int(proposedX))+','+str(int(proposedY))
            # sys.stderr.write('pos '+pos+'\n')
            direction = 1
            while (pos in usedPos):
                proposedX += direction * dX
                pos = str(int(proposedX))+','+str(int(proposedY))
                # sys.stderr.write('pos '+pos+'\n')
                direction = (abs(direction)+1) * int(np.sign(direction)) * -1
            usedPos[pos] = True
            assign_xy_static(nodes, usedPos, c, proposedX, proposedY)

# fix cases where A->B->C and A->C, where all have the same x
# ignore x requirement for now, bc children tend to be approximately vertical
def reposition_static(nodes, edges, usedPos):
    for a in nodes:
        if 'unused' in a or 'children' not in a or 'x' not in a or 'dynamic' in a:
            continue
        for i in a['children']:
            b = nodes[i]
            if 'x' not in b or 'y' not in b or 'dynamic' in b or b['index'] == a['index']:
                continue
            for j in b['children']:
                c = nodes[j]
                if 'x' not in c or b['index'] == c['index']:
                    continue
                sys.stderr.write('checking '+str(a['name'])+' '+str(b['name'])+' '+str(c['name'])+'\n')
                for e in edges:
                    # look for A->C edge
                    if e['source']==a['index'] and e['target']==c['index']:
                        sys.stderr.write('abc '+str(a['name'])+' '+str(b['name'])+' '+str(c['name'])+'\n')
                        # move B
                        dX = 100
                        x = b['x'] + dX
                        y = b['y']
                        pos = str(int(x))+','+str(int(y))
                        while pos in usedPos:
                            x += dX
                            pos = str(int(x))+','+str(int(y))
                        usedPos[pos] = True
                        b['x'] = x
                        break

def reposition_intermediate_nodes(nodes):
    for n in nodes:
        if n['category'] is False and 'unused' not in n and 'parents' in n and 'children' in n:
            minX = False
            minY = False
            maxX = False
            maxY = False
            nX = 0
            nY = 0
            totalX = 0
            totalY = 0
            for i in n['parents']:
                if 'x' in nodes[i]:
                    totalX += nodes[i]['x']
                    nX += 1
                    if minX is False or nodes[i]['x'] < minX:
                        minX = nodes[i]['x']
                    if minX is False or nodes[i]['x'] > maxX:
                        maxX = nodes[i]['x']
                if 'y' in nodes[i]:                    
                    totalY += nodes[i]['y']
                    nY += 1
                    if minY is False or nodes[i]['y'] > maxY:
                        maxY = nodes[i]['y']
                    if minY is False or nodes[i]['y'] < minY:
                        minY = nodes[i]['y']

            # average position of parents
            if minX is not False:
                n['x'] = totalX / nX
            if minY is not False:
                n['y'] = totalY / nY

            minX = False
            minY = False
            maxX = False
            maxY = False
            nX = 0
            nY = 0
            totalX = 0
            totalY = 0
            for i in n['children']:
                if 'x' in nodes[i]:
                    totalX += nodes[i]['x']
                    nX += 1
                    if minX is False or nodes[i]['x'] < minX:
                        minX = nodes[i]['x']
                    if minX is False or nodes[i]['x'] > maxX:
                        maxX = nodes[i]['x']
                if 'y' in nodes[i]:                    
                    totalY += nodes[i]['y']
                    nY += 1
                    if minY is False or nodes[i]['y'] > maxY:
                        maxY = nodes[i]['y']
                    if minY is False or nodes[i]['y'] < minY:
                        minY = nodes[i]['y']
                        
            # average with average position of children
            if minX is not False:
                # n['x'] = (minX + maxX) / 2
                n['x'] = int((totalX / nX + n['x'])/2.0)
            if minY is not False:
                # n['y'] = (minY + maxY) / 2
                n['y'] = int((totalY / nY + n['y'])/2.0)

def assign_xy_dynamic(nodes, usedPos):
    # put dynamic nodes on left or right side, depending on where their
    # parents are relative to the average at that Y level
    dX = 100
    for repeat in range(2): # do it twice to catch intermediate nodes
        for n in nodes:
            # sys.stderr.write('axyd '+str(n['index'])+' '+str(n['name'])+' '+str(n['category'])+'\n')
            if 'dynamic' in n and 'y' in n and 'x' not in n:
                y = n['y']

                # calculate average static x near this y
                avgX = 0
                nX = 0
                for n2 in nodes:
                    if n2['category'] == TYPE_CATEGORY_STATIC and 'unused' not in n2 and 'y' in n2 and 'x' in n2:
                        if n2['y'] >= y-150 and n2['y'] <= y+150:
                            avgX += n2['x']
                            nX += 1
                
                            if nX > 0:
                                avgX /= nX

                # arrange x based on which side of x is average
                direction = 0
                for i in n['parents']:
                    if 'x' in nodes[i]:
                        parentX = nodes[i]['x']
                        if parentX > avgX:
                            direction = 1
                        else:
                            direction = -1
                if direction != 0:
                    x = parentX + direction * dX
                    pos = str(int(x))+','+str(int(y))
                    # sys.stderr.write('pos '+pos+'\n')
                    while pos in usedPos:
                        x += direction * dX
                        pos = str(int(x))+','+str(int(y))
                        # sys.stderr.write('pos '+pos+'\n')
                    usedPos[pos] = True
                    n['x'] = x
            elif 'dynamic' in n and 'y' not in n:
                sys.stderr.write('error - dynamic but no y\n')
                sys.stderr.write('parents are '+', '.join(str(x) for x in n['parents'])+'\n')

# use NetworkX to lay out nodes, spring layout
def reposition_spring(nodes, edges, k):
    G = nx.Graph()
    G_fixed = []
    G_pos = {}
    for n in nodes:
        if not 'unused' in n:
            G.add_node(n['index'])
            if 'x' in n and 'y' in n:
                G_pos[n['index']] = (n['x'], n['y'])
                if n['category'] == TYPE_CATEGORY_STATIC:
                    G_fixed.append(n['index'])
    for e in edges:
        G.add_edge(e['source'], e['target'], weight=e['thickness'])
    # sys.stderr.write('graph '+str(nx.node_link_data(G))+'\n')
    nx.nx_agraph.write_dot(G, "/tmp/graph0.dot")
    pos = nx.spring_layout(G, pos=G_pos, fixed=G_fixed, k=k, seed=1)
    for index, xy in pos.items():
        # sys.stderr.write('nx '+str(index)+' '+str(nodes[index]['name'])+' '+str(nodes[index]['category'])+'\n')
        if 'x' not in nodes[index]:
            nodes[index]['x'] = -1
        if 'y' not in nodes[index]:
            nodes[index]['y'] = -1
        pos = str(nodes[index]['x'])+','+str(nodes[index]['y'])+' -> '+str(int(xy[0]))+','+str(int(xy[1]))
        # sys.stderr.write('pos '+pos+'\n')
        nodes[index]['x'] = int(xy[0])
        nodes[index]['y'] = int(xy[1])

# use NetworkX to lay out nodes, using graphviz neato
def reposition_graphviz(nodes, edges, args):
    G = nx.Graph()
    for n in nodes:
        if not 'unused' in n:
            label = str(n['name'])
            if '<br>' in label:
                label = label[0:label.index('<br>')]
            if 'x' in n and 'y' in n:
                if n['category'] == TYPE_CATEGORY_STATIC:
                    static = '!'
                else:
                    static = ''
                G.add_node(n['index'], label=label, pos=str(n['x'])+','+str(n['y'])+static)
            else:
                G.add_node(n['index'], label=label)
    for e in edges:
        G.add_edge(e['source'], e['target'])
    # sys.stderr.write('graph '+str(nx.node_link_data(G))+'\n')
    # nx.nx_agraph.write_dot(G, "/tmp/graph3.dot")
    pos = nx.nx_agraph.graphviz_layout(G, prog='neato', args=args)
    # re-scale static nodes back to where they started out
    minX = False
    minY = False
    dX = False
    dY = False
    scaleX = False
    scaleY = False
    for index, xy in pos.items():
        if nodes[index]['category'] == TYPE_CATEGORY_STATIC and 'x' in nodes[index] and 'y' in nodes[index]:
            if dX is False:
                dX = nodes[index]['x'] - xy[0]
                x1 = nodes[index]['x']
            elif (abs(nodes[index]['x'] - x1) > 10) and scaleX is False:
                x2 = nodes[index]['x']
                scaleX = (xy[0] - x1 + dX) / (x2 - x1)
                # sys.stderr.write('x1 '+str(x1)+' x2 '+str(x2)+' dx '+str(dX)+' '+str(xy[0])+'\n')
            if minX is False or nodes[index]['x'] < minX:
                minX = nodes[index]['x']
                dX = nodes[index]['x'] - xy[0]
            if dY is False:
                dY = nodes[index]['y'] - xy[1]
                y1 = nodes[index]['y']
            elif (abs(nodes[index]['y'] - y1) > 10) and scaleY is False:
                y2 = nodes[index]['y']
                scaleY = (xy[1] - y1 + dY) / (y2 - y1)
            if minY is False or nodes[index]['y'] < minY:
                minY = nodes[index]['y']
                dY = nodes[index]['y'] - xy[1]
    if scaleY is False:
        scaleY = 1
    if scaleX is False:
        scaleX = scaleY
    if dX is False:
        dX = 0
        minX = 0
    if dY is False:
        dY = 0
        minY = 0
    # sys.stderr.write('minX '+str(minX)+' scaleX '+str(scaleX)+' dx '+str(dX)+'\n')
    # rescale all nodes as the static nodes were scaled
    for index, xy in pos.items():
        if nodes[index]['category'] != TYPE_CATEGORY_STATIC:
            # sys.stderr.write('gv '+str(index)+' '+str(nodes[index]['name'])+' '+str(nodes[index]['category'])+'\n')
            if 'x' not in nodes[index]:
                nodes[index]['x'] = -1
            if 'y' not in nodes[index]:
                nodes[index]['y'] = -1
            # pos = str(nodes[index]['x'])+','+str(nodes[index]['y'])+' -> '+str(int((xy[0] + dX - minX) / scaleX + minX + 0.5))+','+str(int((xy[1] + dY - minY) / scaleY + minY))
            # sys.stderr.write('pos '+pos+'\n')
            nodes[index]['x'] = int((xy[0] + dX - minX) / scaleX + minX)
            nodes[index]['y'] = int((xy[1] + dY - minY) / scaleY + minY)

# rescale both axes so left/top position is 0
# considered changing longest/shortest edge
def rescale_xy(nodes, edges):
    minX = False
    minY = False
    # maxDX = False
    # maxDY = False
    # minDX = False
    # minDY = False
    for n in nodes:
        if 'x' in n and 'y' in n and not 'unused' in n:
            if minX is False or n['x'] < minX:
                minX = n['x']
            if minY is False or n['y'] < minY:
                minY = n['y']
    # for e in edges:
    # dX = abs(nodes[e['source']]['x'] - nodes[e['target']]['x'])
    # dY = abs(nodes[e['source']]['y'] - nodes[e['target']]['y'])
    # if maxDX is False or dX > maxDX:
    # maxDX = dX
    # if maxDY is False or dY > maxDY:
    # maxDY = dY
    # if minDX is False or dX < minDX:
    # minDX = dX
    # if minDY is False or dY < minDY:
    # minDY = dY
    for n in nodes:
        if 'x' in n and 'y' in n and not 'unused' in n:
            n['x'] = int(n['x'] - minX)
            n['y'] = int(n['y'] - minY)

# if nodes are too close, stretch edges to avoid collisions
def stretch_avoid_collisions(nodes, edges):
    # how much overlap is needed to move?
    olapX = 90
    olapY = 40
    for repeat in range(3): # multiple cycles to avoid secondary effects
        for n1 in nodes:
            if 'unused' in n1 or not 'x' in n1 or not 'y' in n1 or n1['category'] != TYPE_CATEGORY_DYNAMIC:
                continue
            # figure out closest intersection with other nodes
            hasOverlap = True
            while (hasOverlap):
                hasOverlap = False
                for n2 in nodes:
                    if 'unused' in n2 or not 'x' in n2 or not 'y' in n2 or n1['index']==n2['index']:
                        continue
                    dX = abs(n1['x']-n2['x'])
                    dY = abs(n1['y']-n2['y'])
                    # dist = math.sqrt(dX**2 + dY**2)
                    # sys.stderr.write('dist '+str(n1['name'])+' '+str(n2['name'])+' '+str(dist)+' '+str(dX)+' '+str(dY)+'\n')
                    if (dY < olapY) and (dX < olapX):
                        hasOverlap = True
                        break
                if hasOverlap:
                    # push n1 further out along edge from parent
                    # sys.stderr.write('OVERLAP '+str(n1['name'])+' '+str(n2['name'])+' '+str(dX)+' '+str(dY)+'\n')
                    for e in edges:
                        if e['target'] != n1['index'] or e['source'] == n1['index']:
                            continue
                        n3 = nodes[e['source']]
                        # calculate distance from source
                        dX2 = n1['x']-n3['x']
                        dY2 = n1['y']-n3['y']
                        # sys.stderr.write('SOURCE '+str(n3['name'])+' '+str(dX2)+' '+str(dY2)+'\n')
                        # move further along that direction, at least 10 units
                        moves = 10
                        dX3 = moves * (dX2 / (abs(dX2) + abs(dY2)))
                        dY3 = moves * (dY2 / (abs(dX2) + abs(dY2)))
                        n1['x'] += dX3
                        n1['y'] += dY3
                        # if cluster node, move kids as well
                        if 'isParent' in n1:
                            for i in n1['children']:
                                n4 = nodes[i]
                                if 'x' in n4 and 'y' in n4:
                                    n4['x'] += dX3
                                    n4['y'] += dY3
                        break
            # make positions integers again
            n1['x'] = int(n1['x'])
            n1['y'] = int(n1['y'])
            if 'isParent' in n1:
                for i in n1['children']:
                    n4 = nodes[i]
                    if 'x' in n4 and 'y' in n4:
                        n4['x'] = int(n4['x'])
                        n4['y'] = int(n4['y'])
            
# for types graph on front page
@app.route('/coral/types_graph', methods=['GET','POST'])
@auth_ro_required
def coral_type_graph():
    arango_service = svs['arango_service']

    # load filters
    query = request.json
    s = pprint.pformat(query)
    sys.stderr.write('query = '+s+'\n')
    filterCampaigns = set()
    filterPersonnel = set()
    filtering = False
    if query is not None:
        for q in query:
            if q['attribute'] == 'campaign':
                filterCampaigns.add(q['term'])
                filtering = True
            elif q['attribute'] == 'person':
                filterPersonnel.add(q['term'])                
                filtering = True
                # expand labs to all people in the lab
                children = svs['ontology'].enigma.find_id(q['term']).children
                for x in children:
                    filterPersonnel.add(x.term_id)
            else:
                return _err_response('unparseable query '+s)

    cacheKey = "types_graph_"+str(filterCampaigns)+str(filterPersonnel)
    # if cacheKey in cache:
    #    sys.stderr.write('cache hit '+cacheKey+'\n')
    #    return  _ok_response(cache[cacheKey])
    #else:
    #    sys.stderr.write('cache miss '+cacheKey+'\n')

    # s = pprint.pformat(filterCampaigns)
    # sys.stderr.write('campaigns = '+s+'\n')
    # s = pprint.pformat(filterPersonnel)
    # sys.stderr.write('personnel = '+s+'\n')
    # sys.stderr.write('filtering = '+str(filtering)+'\n')

    # map names and indices back to nodes
    nodeMap = {}

    # Core types
    nodes = []
    index=0
    if not filtering:
        type_defs = svs['indexdef'].get_type_defs(category=TYPE_CATEGORY_STATIC)
        for td in type_defs:
            if not td.for_provenance:
                continue
            count = arango_service.get_core_type_count( '%s%s' %(TYPE_CATEGORY_STATIC, td.name))
            if count==0:
                continue
            nodes.append(
                {
                    'index': index,
                    'category': TYPE_CATEGORY_STATIC,
                    'name': td.name,
                    'dataModel': td.name,
                    'dataType': td.name,
                    'count': count
                }
            )
            # sys.stderr.write('added static node '+td.name+'\n')
            nodeMap[td.name] = nodes[index]
            nodeMap[index] = nodes[index]
            index+=1

    # Dynamic types and processes
    rows = arango_service.get_process_type_count(filterCampaigns=filterCampaigns, filterPersonnel=filterPersonnel)
    edgeTuples = dict()
    # Note: awkward code below works around https://github.com/ArangoDB-Community/pyArango/issues/160
    # can't do 'for row in rows:' because query returns infinite empty lists
    for i in range(len(rows)):
        row = rows[i]
        # sys.stderr.write('row: '+str(row)+'\n')
        key = ''
        newFromTypes = set()
        newFromIds = set()
        froms = row['from'].split(',')
        for fr in froms:
            elements = fr.split('/')
            newFromIds.add(fr)
            if elements[0] not in newFromTypes:
                newFromTypes.add(elements[0])
                key += elements[0]+'+'
        key = key[:-1]+ '>' # strip trailing +
        newToTypes = set()
        newToIds = set()
        tos = row['to'].split(',')
        for to in tos:
            elements = to.split('/')
            if (elements[0].startswith("DDT_")):
                newKey = "DDT_"+elements[2]
            else:
                newKey = elements[0]
            newToIds.add(newKey+"/"+elements[1])
            if newKey not in newToTypes:
                newToTypes.add(newKey)
                key += newKey+"+"
        key = key[:-1] # strip trailing +
        if key in edgeTuples:
            edgeTuples[key]['num'] += 1
            fromIds = edgeTuples[key]['from']
            toIds = edgeTuples[key]['to']
            procs = edgeTuples[key]['proc']
            fromIds.update(newFromIds)
            toIds.update(newToIds)
            procs.add(row['pname'])
        else:
            edgeTuples[key] = dict()
            edgeTuples[key]['num'] = 1
            edgeTuples[key]['from'] = newFromIds
            edgeTuples[key]['to'] = newToIds
            edgeTuples[key]['proc'] = set()
            edgeTuples[key]['proc'].add(row['pname'])
            edgeTuples[key]['in_filter'] = False
        if filtering:
            if row['in_filter']:
                edgeTuples[key]['in_filter'] = True

    # combine similar elements:
    # must have one process, input, and output in common
    keys = list(edgeTuples.keys())
    for key1 in keys:
        (fromAll1, toAll1) = key1.split('>')
        # if all TOs are DDT_, not eligible for merging
        if not "SDT_" in toAll1:
            continue;
        froms1 = set(fromAll1.split('+'))
        tos1 = set(toAll1.split('+'))
        for key2 in keys:
            if key1 == key2:
                continue
            # check that we didn't already merge them:
            if not key1 in edgeTuples:
                continue
            if not key2 in edgeTuples:
                continue

            # common process?
            if edgeTuples[key1]['proc'].isdisjoint(edgeTuples[key2]['proc']):
                continue

            # parse froms, tos
            (fromAll2, toAll2) = key2.split('>')
            # if all TOs are DDT_, not eligible for merging
            if not "SDT_" in toAll2:
                continue;
            froms2 = set(fromAll2.split('+'))
            if froms2.isdisjoint(froms1):
                continue
            tos2 = set(toAll2.split('+'))
            if tos2.isdisjoint(tos1):
                continue
            
            # all match; merge them
            # sys.stderr.write('merging key: '+key1+' into '+key2+'\n')
            num = edgeTuples[key1]['num'] + edgeTuples[key2]['num']
            froms = edgeTuples[key1]['from']
            froms.update(edgeTuples[key2]['from'])
            tos = edgeTuples[key1]['to']
            tos.update(edgeTuples[key2]['to'])
            procs = edgeTuples[key1]['proc']
            procs.update(edgeTuples[key2]['proc'])
            inFilter = edgeTuples[key1]['in_filter'] | edgeTuples[key2]['in_filter']
            del edgeTuples[key1]
            del edgeTuples[key2]
            # add new key
            froms1.update(froms2)
            tos1.update(tos2)
            key = '+'.join(froms1)+'>'+'+'.join(tos1)
            edgeTuples[key] = dict()
            edgeTuples[key]['num'] = num
            edgeTuples[key]['from'] = froms
            edgeTuples[key]['to'] = tos
            edgeTuples[key]['proc'] = procs
            edgeTuples[key]['in_filter'] = inFilter

    # process edges from keys, adding new DDT_ nodes, and SDT_ nodes if filtering
    edges = []
    staticEdges = []
    for key in edgeTuples.keys():
        newEdges = []
        # sys.stderr.write('key: '+key+'\n')
        (fromAll, toAll) = key.split('>')
        if filtering:
            # add SDT nodes if not present
            nn = fromAll.split('+') + toAll.split('+')
            for n in nn:
                if n.startswith('SDT_'):
                    n = n[4:]
                    if n not in nodeMap:
                        sys.stderr.write('adding static node '+n+'\n')
                        nodes.append(
                            {
                                'index': index,
                                'category': TYPE_CATEGORY_STATIC,
                                'name': n,
                                'dataModel': n,
                                'dataType': n,
                                'count': 0,
                                'ids': set()
                            }
                        )
                        nodeMap[n] = nodes[index]
                        nodeMap[index] = nodes[index]
                        index+=1

        # don't show ddt outbound (e.g., computational results) in graph
        if "DDT_" in fromAll:
            continue
        froms = fromAll.split('+')
        tos = toAll.split('+')
        intermed = 0
        if len(froms)>1 or len(tos)>1:
            # make intermediate node
            intermed = index
            sys.stderr.write('adding intermediate node\n')
            nodes.append(
                {
                    'index': intermed,
                    'category': False,
                    'name': False,
                    'count': 0
                })
            index += 1
        linkText = str(edgeTuples[key]['num'])+' '+', '.join(edgeTuples[key]['proc'])
        totalThickness = line_thickness(edgeTuples[key]['num'])
        for i in range(len(froms)):
            fr = froms[i]
            num = len(edgeTuples[key]['from'])
            totalNum = num
            if (len(froms)>1):
                searchKey = fr+'/'
                num = 0
                for k in edgeTuples[key]['from']:
                    if k.startswith(searchKey):
                        num+=1
                        if filtering:
                            nodes[nodeMap[fr[4:]]['index']]['ids'].add(k)
                thickness = int(round(num/totalNum*totalThickness))
                if (thickness==totalThickness):
                    thickness = totalThickness-1
                if (thickness==0):
                    thickness = 1
            else:
                thickness = totalThickness
                if filtering:
                    nodes[nodeMap[fr[4:]]['index']]['ids'].update(edgeTuples[key]['from'])
                        
            fr = fr[4:]
            if (i==0):
                linkText += '<br>'
            else:
                linkText += ', '
            linkText += str(num)+' '+fr
            
            if (intermed > 0):
                newEdges.append(
                    {
                        'source': nodeMap[fr]['index'],
                        'target': intermed,
                        'thickness': thickness,
                        'in_filter': edgeTuples[key]['in_filter']
                    }
                )

        for i in range(len(tos)):
            to = tos[i]
            num = len(edgeTuples[key]['to'])
            totalNum = num
            if (len(tos)>1):
                searchKey = to+'/'
                num = 0
                for k in edgeTuples[key]['to']:
                    if k.startswith(searchKey):
                        num+=1
                        if filtering and to.startswith('SDT_'):
                            nodes[nodeMap[to[4:]]['index']]['ids'].add(k)
                thickness = int(round(num/totalNum*totalThickness))
                if (thickness==totalThickness):
                    thickness = totalThickness-1
                if (thickness==0):
                    thickness = 1
            else:
                thickness = totalThickness
                if filtering and to.startswith('SDT_'):
                    nodes[nodeMap[to[4:]]['index']]['ids'].update(edgeTuples[key]['to'])

            # if to is DDT, need to add new node for it
            if 'DDT_' in to:
                to = to[4:]
                node_to = index
                sys.stderr.write('adding dynamic node '+to+'\n')
                nodes.append(
                    {
                        'index': node_to,
                        'category': TYPE_CATEGORY_DYNAMIC,
                        'name': to+'<br>Dataset'+('','s')[num>1],
                        'dataModel': 'Brick',
                        'dataType': to,
                        'count': num
                    }
                )
                index += 1
            else:
                to = to[4:]
                node_to = nodeMap[to]['index']
                        
            if (i==0):
                linkText += ' &rarr; '
            else:
                linkText += ', '
            linkText += str(num)+' '+to

            if (intermed == 0 and fr in nodeMap):
                intermed = nodeMap[fr]['index']

            e = {
                    'source': intermed,
                    'target': node_to,
                    'thickness': thickness,
                    'in_filter': edgeTuples[key]['in_filter']
                }

            newEdges.append(e)
            if TYPE_CATEGORY_STATIC in to:
                staticEdges.append(e)
            
        # make all new edges have same linkText
        for e in newEdges:
            e['text'] = linkText
            edges.append(e)

    # count objects in static nodes, if filtering
    if filtering:
        for n in nodes:
            if 'ids' in n:
                n['count'] = len(n['ids'])
                del n['ids']

    # if not filtering, find static categories not actually used in provenance
    else:
        unused = set(range(index))
        for e in edges:
            if e['source'] in unused:
                unused.remove(e['source'])
            if e['target'] in unused:
                unused.remove(e['target'])
        for i in unused:
            if not 'isParent' in nodes[i]:
                nodes[i]['unused'] = True
                # sys.stderr.write('unused node '+nodes[i]['name']+'\n')

    # cluster ddt nodes from same sdt
    clusterNodes = []
    clusterEdges = []
    for n in nodes:
        if n['category'] != TYPE_CATEGORY_STATIC:
            continue
        linkedDDTNodes = []
        inFilter = False
        linkedEdges = []
        for e in edges:
            if e['source'] != n['index']:
                continue
            if nodes[e['target']]['category'] != TYPE_CATEGORY_DYNAMIC:
                continue
            linkedDDTNodes.append(e['target'])
            inFilter |= e['in_filter']
            linkedEdges.append(e)
            
        # cluster nodes if there are more than MAX_DYNAMIC_NODES
        MAX_DYNAMIC_NODES = 2
        if len(linkedDDTNodes) > MAX_DYNAMIC_NODES:
            num = 0
            sys.stderr.write('adding cluster node\n')
            newDDTNodes = []
            for i in linkedDDTNodes:
                num += nodes[i]['count']
                nodes[i]['parent'] = index
                newDDTNodes.append(nodes[i])
            # add 'clustered' node
            clusterNodes.append(
                {
                    'index': index,
                    'category': TYPE_CATEGORY_DYNAMIC,
                    'name': 'Datasets',
                    'dataModel': 'Brick',
                    'dataType': 'Dataset',
		    'count': num,
                    'isParent': True
                }
            )
            # move other edges, and collect processes
            procs = []
            for e in linkedEdges:
                e['source'] = index
                pos = e['text'].index('<br>')
                # sys.stderr.write('match: '+e['text'][0:pos]+'\n')
                procs.append(e['text'][0:pos])
                
            # add edge to cluster node
            clusterEdges.append(
                {
                    'source': n['index'],
                    'target': index,
                    'thickness': line_thickness(num),
                    'inFilter': inFilter,
                    'text': ',<br>'.join(procs)
                }
            )

            index += 1

    # add new cluster nodes and edges
    nodes.extend(clusterNodes)
    edges.extend(clusterEdges)

    # provide approximate locations.
    # first, find roots, and reversible direct edges
    roots = set(range(index))
    directEdges = {}
    for e in edges:
         if e['target'] in roots:
             roots.remove(e['target'])
         # check for reversible direct edges
         if e['source'] != e['target']:
             directEdges[str(e['source'])+'-'+str(e['target'])] = e
             if str(e['target'])+'-'+str(e['source']) in directEdges:
                 e['reversible'] = True
                 directEdges[str(e['target'])+'-'+str(e['source'])]['reversible'] = True
    for i in roots:
        nodes[i]['root'] = True
        # sys.stderr.write('root node '+nodes[i]['name']+'\n')

    # make sets of parents/children for all nodes
    for n in nodes:
        if 'unused' not in n:
            n['children'] = set()
            n['parents'] = set()
            # track intermediate nodes that only
            # lead to dynamic nodes
            if n['category'] != TYPE_CATEGORY_STATIC:
                n['dynamic'] = True 
    for e in edges:
        nodes[e['source']]['children'].add(e['target'])
        nodes[e['target']]['parents'].add(e['source'])
        if nodes[e['target']]['category'] == TYPE_CATEGORY_STATIC:
            if 'dynamic' in nodes[e['source']]:
                del nodes[e['source']]['dynamic']

    # do DFS of each root, assigning x and y to static, just y to dynamic:
    usedPos = {}
    x = 0
    for i in roots:
        assign_xy_static(nodes, usedPos, i, x, 0)
        x += 100

    reposition_static(nodes, edges, usedPos)
    reposition_intermediate_nodes(nodes)
    assign_xy_dynamic(nodes, usedPos)
    reposition_intermediate_nodes(nodes)
    for repeat in range(1): # multiple cycles to smooth things out
        reposition_spring(nodes, edges, 100)
        reposition_intermediate_nodes(nodes)
        reposition_graphviz(nodes, edges, '-Ginputscale=120 -Goverlap=false')
        reposition_intermediate_nodes(nodes)
        reposition_graphviz(nodes, edges, '-Gmode=KK -Ginputscale=100 -Goverlap=false')
        reposition_intermediate_nodes(nodes)
        stretch_avoid_collisions(nodes, edges)
    rescale_xy(nodes, edges)
    
    # remove unused properties
    for n in nodes:
        if 'children' in n:
            del n['children']
        if 'parents' in n:
            del n['parents']
        if 'dynamic' in n:
            del n['dynamic']
    
    # remove unused nodes
    if not filtering:
        for n in nodes:
            if 'unused' in n:
                nodes.remove(n)

    # combine everything and return graph
    res = {
        'nodes' : nodes,
        'links' : edges
    }

    # s = pprint.pformat(res,width=999)
    # return s
    cache[cacheKey] = res
    return  _ok_response(res)


@app.route('/coral/dn_process_docs/<obj_id>', methods=['GET'])
@auth_required
def coral_dn_process_docs(obj_id):
    try:
        arango_service = svs['arango_service']
        indexdef = svs['indexdef']

        obj_type = ''
        try:
            obj_type = to_object_type(obj_id)
        except:
            raise ValueError('Wrong object ID format: %s' % obj_id)

        itdef = indexdef.get_type_def(obj_type)
        rows = arango_service.get_dn_process_docs(itdef, obj_id)
        process_docs = _to_process_docs(rows)

        return  _ok_response(process_docs)
    except Exception as e:
        return _err_response(e)


@app.route('/coral/up_process_docs/<obj_id>', methods=['GET'])
@auth_required
def coral_up_process_docs(obj_id):
    try:
        arango_service = svs['arango_service']
        indexdef = svs['indexdef']

        obj_type = ''
        try:
            obj_type = to_object_type(obj_id)
        except:
            raise ValueError('Wrong object ID format: %s' % obj_id)

        itdef = indexdef.get_type_def(obj_type)
        rows = arango_service.get_up_process_docs(itdef, obj_id)
        process_docs = _to_process_docs(rows)

        return _ok_response(process_docs)
    except Exception as e:
        return _err_response(e)


def _to_process_docs(rows):
    typedef = svs['typedef']
    indexdef = svs['indexdef']
    process_docs = []
    # Note: awkward code below works around https://github.com/ArangoDB-Community/pyArango/issues/160
    # can't do 'for row in rows:' because query returns infinite empty lists
    for i in range(len(rows)):
        row = rows[i]
        process = row['process']

        # build docs
        docs = []
        for doc in row['docs']:
            obj_type = to_object_type(doc['_key'])
            itdef = indexdef.get_type_def(obj_type)

            upk = typedef.get_type_def(obj_type).upk_property_def if obj_type != 'Brick' else None
            description = doc[upk.name] if upk else ''

            docs.append({
                'id': doc['_key'],
                'type': obj_type,
                'category': itdef.category,
                'description': description
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


@app.route('/coral/microtypes', methods=['GET'])
@auth_required
def coral_microtypes():
    try:
        res = []
        term_collection = svs['ontology'].all.find_microtypes()

        # we want these sorted into tree
        term_dict = dict()
        for term in term_collection:
            # sys.stderr.write(term.term_id+"\n")
            term_dict[term.term_id] = term
        
        # store children for each term in a dict
        children = dict()
        for term in term_collection:
            children[term.term_id] = []

        # populate children elements
        for term in term_collection:
            for parent in term.parent_ids:
                try:
                    children[parent].append(term.term_id)
                except KeyError: # requrired because some parents don't exist
                    pass

        # next, print any "root" terms:
        for term in term_collection:
            if (len(term.parent_ids)==0):
                append_with_children(res,children,term_dict,term.term_id)
                
        return _ok_response(res)       
    except Exception as e:
        return _err_response(e)

def append_with_children(res,children,term_dict,term_id):
    try:
        term = term_dict.pop(term_id)
    except KeyError:
        sys.stderr.write("already printed: "+term_id+"\n")
        return
    if term.is_hidden:
        sys.stderr.write("hidden term: "+term.term_id+"\n")
    # don't print hidden and root terms:
    if ((not term.is_hidden) and (len(term.parent_ids)>0)):
        sys.stderr.write("printing term: "+term.term_id+"\n")
        term_desc = term.term_def;
        if (len(term.synonyms) > 0):
            term_desc += ' ['+', '.join(term.synonyms)+']'
        scalar_type = term.microtype_value_scalar_type
        if (term.microtype_value_scalar_type == 'object_ref'):
            scalar_type = 'link to static object'
        elif (term.microtype_value_scalar_type == 'oterm_ref'):
            scalar_type = 'list of choices'
        res.append({
            'term_id': term.term_id,
            'term_name': term.term_name,
            'term_def': term.term_def,
            'term_desc': term_desc,
            'mt_microtype': term.is_microtype,
            'mt_dimension': term.is_dimension,
            'mt_dim_var': term.is_dimension_variable,
            'mt_data_var': term.is_dimension_variable,
            'mt_property': term.is_property,
            'mt_value_scalar_type': scalar_type,
            'mt_parent_term_ids': term.parent_ids
        })
    for child in children[term_id]:
        sys.stderr.write("process child: "+child+"\n")
        append_with_children(res,children,term_dict,child)
    return

@app.route('/coral/core_type_props/<obj_name>', methods=['GET'])
@auth_ro_required
def coral_core_type_props(obj_name):
    """ Gets list of property names as axis options for plotting """
    core_type = svs['typedef'].get_type_def(obj_name)
    response = []
    for field in core_type.property_names:
        property = core_type.property_def(field)
        if (property.units_term_id is not None):
            units_term = svs['ontology'].units.find_id(property.units_term_id)
            response.append(dict(name=property.name,
                                 scalar_type=property.type,
                                 term_id=property.term_id,
                                 units=units_term.term_name,
                                 display_name='%s (%s)' % (property.name, units_term.term_name)
                                ))
        else:
            response.append(dict(name=property.name, display_name=property.name, scalar_type=property.type, term_id=property.term_id))
    return json.dumps({"results": response})
               
@app.route('/coral/core_type_metadata/<obj_id>', methods=['GET','POST'])
@auth_ro_required
def coral_core_type_metadata(obj_id):
    obj_type = ''
    try:
        (JSON, CSV) = range(2)
        return_format = JSON
        if request.method == 'POST':
            query = request.json
            if query is not None and 'format' in query and query['format'] == 'CSV':
                return_format = CSV
        
        sys.stderr.write('obj_id = '+str(obj_id)+'\n')
        obj_type = to_object_type(obj_id)
        doc = dp.core_types[obj_type].find_one({'id':obj_id})
        if return_format == JSON:
            res = []
            for prop in doc.properties:
                if prop.startswith('_'): continue
                res.append(
                    {
                        'property': prop,
                        'value': doc[prop]
                    }
                )
        else: # TSV
            props = []
            values = []
            for prop in doc.properties:
                if prop.startswith('_'): continue
                props.append(str(prop))
                values.append(str(doc[prop]))
            res = '\t'.join(props)+'\n'+'\t'.join(values)
        return  _ok_response({ "items": res, "type": obj_type  })
       
    except Exception as e:
        return _err_response(e)

@app.route('/coral/image', methods=['POST'])
@auth_required
def get_image():
    try:
        url = request.json['url']
        if 'thumb' in request.json:
            wantThumb = True;
        else:
            wantThumb = False;

        if not url.startswith('images/') and not url.startswith('/images/'):
            return _err_response('not a local image: '+str(url))

        if url.startswith('images/'):
            fileName = url[7:]
        else:
            fileName = url[8:]

        width = False
        height = False
        imagePath = False
        
        if wantThumb:
            files = os.listdir(THUMBS_DIR)
            thumbPattern = '(\d+)x(\d+)-(.*)'
            for f in files:
                if not f.endswith(fileName):
                    continue
       	        match = re.search(thumbPattern, f)
                if match:
                    width = int(match.group(1))
                    height = int(match.group(2))
                    f2 = match.group(3)
                    if f2 != fileName:
                        continue
                    imagePath = os.path.join(THUMBS_DIR, f)
                    break
        else:
            imagePath = os.path.join(IMAGE_DIR, fileName)
            if not os.path.isfile(imagePath):
                imagePath = False

        if imagePath is False:
            return _err_response('image not found:'+str(url))

        with open(imagePath, "rb") as imageFile:
            imageData = base64.b64encode(imageFile.read()).decode('utf-8')

        if width is False or height is False:
            return  _ok_response({'image':imageData})
        else:
            return  _ok_response({'image':imageData,
                                  'width':width,
                                  'height':height })
    except Exception as e:
        return _err_response(e)

    
@app.route('/coral/generate_brick_template', methods=['POST'])
@auth_required
def generate_brick_template():
    try:
        data_id = uuid.uuid4().hex

        brick_ds = json.loads(request.form['brick'])

        # Save brick data structure
        uds_file_name = os.path.join(TMP_DIR, _UPLOAD_DATA_STRUCTURE_PREFIX + data_id )
        with open(uds_file_name, 'w') as f:
            json.dump(brick_ds, f, sort_keys=True, indent=4)

        utp_file_name = os.path.join(TMP_DIR,_UPLOAD_TEMPLATE_PREFIX + data_id)

        if brick_ds['sheet_template_type'] == 'tab_data':
            template.generate_brick_template(brick_ds, utp_file_name, tab_data=True)
        elif brick_ds['sheet_template_type'] == 'tab_dims':
            template.generate_brick_template(brick_ds, utp_file_name)
        elif brick_ds['sheet_template_type'] == 'interlace':
            template.generate_brick_interlace_template(brick_ds, utp_file_name)

        return send_file(utp_file_name, 
            as_attachment=True,
            attachment_filename='data_template.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    except Exception as e:
        return _err_response(e, traceback=True)

def _ok_response(res, sort_keys=True):
    return  json.dumps( {
            'results': res, 
            'status': 'OK', 
            'error': ''
        }, sort_keys=sort_keys)

def _err_response(e, traceback=False):
    err = str(e)
    if traceback or DEBUG_MODE:
        body = tb.format_exc()
        err = '<PRE>' +  html.escape(body) + '</PRE>' 

    return  json.dumps( {
            'results': '', 
            'status': 'ERR', 
            'error': err
        })

if __name__ == "__main__":
    port = cns['_WEB_SERVICE']['port']
    if cns['_WEB_SERVICE']['https']:
        app.run(host='0.0.0.0', port=port, 
            ssl_context = (cns['_WEB_SERVICE']['cert_pem'], cns['_WEB_SERVICE']['key_pem']) )
    else:
        app.run(host='0.0.0.0', port=port)



