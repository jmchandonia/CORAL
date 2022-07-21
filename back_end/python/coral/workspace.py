import numpy as np
import json
import dumper
import sys
from . import services
from .typedef import TYPE_NAME_PROCESS, TYPE_NAME_BRICK, TYPE_CATEGORY_SYSTEM, TYPE_CATEGORY_STATIC
from .descriptor import IndexDocument
import pandas as pd
import traceback as tb
import os
import csv

_COLLECTION_ID = 'ID'
_COLLECTION_OBJECT_TYPE_ID = 'ObjectTypeID'

class ItemAlreadyExistsException(ValueError):
    def __init__(self, *args, **kwargs):
        if args:
            self.message = args[0]
        else:
            self.message = None

        if kwargs['old_data'] is not None:
            self.old_data = kwargs['old_data']
        if kwargs['new_data'] is not None:
            self.new_data = kwargs['new_data']
        if kwargs['data_holder'] is not None:
            self.data_holder = kwargs['data_holder']

        # Compare old item with new item to see if any values are different
        self.changed_data = False
        for key, val in self.old_data.items():
            if self.new_data[key] != val:
                self.changed_data = True

class DataHolder:
    def __init__(self, type_name, data):
        self.__type_name = type_name
        self.__type_def = None 
        if self.__type_name not in [TYPE_NAME_BRICK]:
            try:
                self.__type_def = services.typedef.get_type_def(self.__type_name)
            except:
                print ('No typedef for %s' % type_name)
        self.__data = data
        self.__id = None

    @property
    def type_name(self):
        return self.__type_name

    @property
    def type_def(self):
        return self.__type_def

    @property
    def data(self):
        return self.__data

    @property
    def id(self):
        return self.__id

    def set_id(self, val):
        self.__id = val
        self._set_data_id(val)

    def _set_data_id(self, val):
        self.__data['id'] = val


class EntityDataHolder(DataHolder):
    def __init__(self, type_name, data, file_name=None):
        super().__init__(type_name, data)
        self.__file_name = file_name

    @property
    def file_name(self):
        return self.__file_name

    def update_fk_ids(self):
        pass


class ProcessDataHolder(DataHolder):
    def __init__(self, data):
        super().__init__(TYPE_NAME_PROCESS, data)

    def __update_object_ids(self, ids_prop_name):
        obj_ids = []

        for _, input_object in enumerate(list(csv.reader([self.data[ids_prop_name]], delimiter=',', quotechar='"',skipinitialspace=True))[0]):
            # was: self.data[ids_prop_name].split(',')):
            type_name, upk_id = input_object.split(':',1)
            type_name = type_name.strip()
            upk_id = upk_id.strip()

            # hack for imported files
            if type_name == 'Generic':
                type_name = 'Brick'

            # skip types not used for provenance
            if not type_name.startswith('Brick'):
                typedef = services.typedef.get_type_def(type_name)
                if not typedef.for_provenance:
                    continue

            # get pk
            pk_id = services.workspace._get_pk_id(type_name, upk_id)

            # add data model term id to bricks
            full_type_name = type_name
            if type_name == 'Brick':
                br = services.workspace.get_brick_data(pk_id)
                full_type_name += '-'+str(br['data_type']['oterm_ref'])[3:]
                # sys.stderr.write('full_type_name for '+str(pk_id)+' = '+str(full_type_name)+'\n')

            obj_ids.append('%s:%s' % (full_type_name, pk_id))

        self.data[ids_prop_name] = obj_ids

    def update_object_ids(self):
        self.__update_object_ids('input_objects')
        self.__update_object_ids('output_objects')

    def validate_output_objects(self):
        for output_object in list(csv.reader([self.data['output_objects']], delimiter=',', quotechar='"',skipinitialspace=True))[0]:
            # was: self.data['output_objects'].split(','):
            type_name, upk_id = output_object.split(':',1)
            type_name = type_name.strip()
            upk_id = upk_id.strip()

            typedef = services.typedef.get_type_def(type_name)
            typedef.validate_data(dh.data)

    def get_process_id(self, obj):
        type_name, upk_id = obj.split(':')
        type_name = type_name.strip()
        upk_id = upk_id.strip()

        return type_name, upk_id




class BrickDataHolder(DataHolder):
    def __init__(self, brick):
        super().__init__(TYPE_NAME_BRICK, brick)

    @property
    def brick(self):
        return self.data

    def _set_data_id(self, val):
        self.brick._set_id(val)


class Workspace:
    __ID_PATTERN = '%s%07d'

    def __init__(self, arango_service):
        self.__arango_service = arango_service
        self.__dtype_2_id_offset = {}
        self.__init_id_offsets()
        # print('Workspace initialized!')


        # self.__dtype_2_id_offset = {}
        # self.__id_2_file_name = {}
        # self.__id_2_text_id = {}
        # self.__file_name_2_id = {}
        # self.__text_id_2_id = {}

    def __init_id_offsets(self):
        registered_type_names = set()

        rows = self.__arango_service.find_all(_COLLECTION_ID, TYPE_CATEGORY_SYSTEM)

        for row in rows:
            type_name = row['dtype']
            registered_type_names.add(type_name)
            self.__dtype_2_id_offset[type_name] = row['id_offset']

        for type_name in services.indexdef.get_type_names():
            if type_name not in registered_type_names:
                self.__arango_service.index_doc(
                    {'dtype': type_name, 'id_offset': 0},
                    _COLLECTION_ID, 
                    TYPE_CATEGORY_SYSTEM)
                self.__dtype_2_id_offset[type_name] = 0

    def next_id(self, type_name):
        id_offset = self.__dtype_2_id_offset[type_name]
        id_offset += 1

        aql = """
            FOR x IN @@collection
            FILTER x.dtype == @dtype
            UPDATE x WITH @doc IN @@collection
        """
        aql_bind = {
            '@collection': TYPE_CATEGORY_SYSTEM + _COLLECTION_ID,
            'doc': {'id_offset':id_offset},
            'dtype':  type_name}
        self.__arango_service.db.AQLQuery(aql, bindVars=aql_bind)
        self.__dtype_2_id_offset[type_name] = id_offset
        return Workspace.__ID_PATTERN % (type_name, id_offset)


    def get_brick_data(self, brick_id):
        file_name = services._DATA_DIR + brick_id
        with open(file_name, 'r') as f:
            doc = json.loads(f.read())
        return doc

    def save_process(self, data_holder, update_object_ids=False):
        self._generate_id(data_holder)
        self._validate_process(data_holder)
        self._store_process(data_holder)
        self._index_process(data_holder, update_object_ids=update_object_ids)

    def save_data_if_not_exists(self, data_holder, preserve_logs=False):
        upk_prop_name = data_holder.type_def.upk_property_def.name
        upk_id = data_holder.data[upk_prop_name]
        try:
            current_pk_id = self._get_pk_id(data_holder.type_name, upk_id)
        except:
            current_pk_id = None
        if current_pk_id is None:
            self.save_data(data_holder)
        else:
            print('skipping %s due to older object' % upk_id)
            if preserve_logs:
                # validate new data with old id before raising ItemAlreadyExistsError
                data_holder_2 = EntityDataHolder(data_holder.type_name, data_holder.data)
                data_holder_2.set_id(current_pk_id)
                self._validate_object(data_holder_2)

                # if validation passes, get original data for comparison
                aql = 'FOR x IN @@collection FILTER x.id == @pk_id RETURN x'
                aql_bind = {
                    '@collection': TYPE_CATEGORY_STATIC + data_holder.type_name,
                    'pk_id': current_pk_id
                }

                new_data = IndexDocument.build_index_doc(data_holder)

                result = self.__arango_service.find(aql, aql_bind)
                raise ItemAlreadyExistsException(
                    'object %s already exists in system' % upk_id,
                    new_data=new_data,
                    old_data={k: v for (k, v) in result[0].items() if not k.startswith('_')},
                    data_holder={k: v for (k, v) in data_holder.data.items() if not k.startswith('_')}
                )
            # check for consistency
            # for now throw an error, although we may want to upsert instead
            # data_holder_2 = EntityDataHolder(data_holder.type_name,
            # data_holder.data)
            # data_holder_2.set_id(current_pk_id)
            # self._load_object(data_holder_2)
            # print("new data")
            # dumper.dump(data_holder)
            # print("old data")
            # dumper.dump(data_holder_2)

    def save_data(self, data_holder):
        self._generate_id(data_holder)
        self._validate_object(data_holder)
        self._store_object(data_holder)
        self._index_object(data_holder)

    def update_data(self, data_holder):
        self._validate_object(data_holder)
        self._update_object(data_holder)

    def _generate_id(self, data_holder):
        id = self.next_id(data_holder.type_name)
        data_holder.set_id(id)

    def _validate_object(self, data_holder, ignore_pk=False):
        if type(data_holder) is EntityDataHolder:
            data_holder.type_def.validate_data(data_holder.data, ignore_pk=ignore_pk)
        elif type(data_holder) is BrickDataHolder:
            pass

    def _validate_process(self, data_holder):
        # data_holder.type_def.validate_data(data_holder.data)

        # Check for NaN
        for key, value in data_holder.data.items():
            if value != value:
                data_holder.data[key] = None

    def _update_object(self, data_holder):
        # Currently used in UI when users confirm they want to overwrite existing data
        # TODO: Figure out solution for upserting rather than erasing old data
        doc = IndexDocument.build_index_doc(data_holder)
        if type(data_holder) is EntityDataHolder:
            aql = """
                FOR x IN @@collection
                FILTER x.id == @pk_id
                UPDATE x WITH @doc IN @@collection
            """

            aql_bind = {
                '@collection': TYPE_CATEGORY_STATIC + data_holder.type_name,
                'pk_id': data_holder.data['id'],
                'doc': doc
            }
            self.__arango_service.db.AQLQuery(aql, bindVars=aql_bind)
        else:
            # TODO: determine if we need to create an update method for non-core types
            pass

    def _store_object(self, data_holder):
        type_name = data_holder.type_name
        pk_id = data_holder.id
        upk_id = None

        if type(data_holder) is EntityDataHolder:
            upk_prop_name = data_holder.type_def.upk_property_def.name
            upk_id = data_holder.data[upk_prop_name]

            # self.__enigma_db.get_collection(
            #     data_holder.type_name).insert_one(data_holder.data)
        elif type(data_holder) is BrickDataHolder:
            upk_id = data_holder.brick.name
            brick_id = data_holder.brick.id
            data_json = data_holder.brick.to_json()
            data = json.loads(data_json)

            file_name = services._DATA_DIR + brick_id
            with open(file_name, 'w') as outfile:  
                json.dump(data, outfile)

        self._store_object_type_ids(type_name, pk_id, upk_id)

    def _load_object(self, data_holder):
        pk_id = data_holder.id
        aql = 'RETURN DOCUMENT(@@collection/@pk_id)'
        aql_bind = {
            '@collection': TYPE_CATEGORY_SYSTEM + _COLLECTION_OBJECT_TYPE_ID,
            'pk_id': pk_id
        }
        res = self.__arango_service.find(aql,aql_bind)
        type2objects = {}
        for row in res:
            _id = row['_id']
            type_name = _id.split('/')[0][4:]
        
            objs = type2objects.get(type_name)
            if objs is None:
                objs = []
                type2objects[type_name] = objs
            objs.append(row)
        # dumper.dump(type2objects)

    def _get_pk_id(self, type_name, upk_id):

        aql = 'FOR x IN @@collection FILTER x.type_name == @type_name and x.upk_id == @upk_id return x'
        aql_bind = {
            '@collection': TYPE_CATEGORY_SYSTEM + _COLLECTION_OBJECT_TYPE_ID,
            'type_name': type_name,
            'upk_id': upk_id
        }

        res = self.__arango_service.find(aql,aql_bind)
        if len(res) == 0:
            raise ValueError('Can not find pk_id for %s: %s' %
                             (type_name, upk_id))
        if len(res) > 1:
            raise ValueError('There is more than one pk_id for %s: %s' %
                             (type_name, upk_id))

        res = res[0]
        return res['pk_id']

    def _get_pk_id_or_none(self, type_name, upk_id):
        aql = 'FOR x IN @@collection FILTER x.type_name == @type_name and x.upk_id == @upk_id return x'
        aql_bind = {
            '@collection': TYPE_CATEGORY_SYSTEM + _COLLECTION_OBJECT_TYPE_ID,
            'type_name': type_name,
            'upk_id': upk_id
        }

        res = self.__arango_service.find(aql, aql_bind)
        if len(res) > 1:
            raise ValueError('There is more than one pk_id for %s: %s' % (type_name, upk_id))

        return res[0]['pk_id'] if len(res) else None

    def _store_object_type_ids(self, type_name, pk_id, upk_id):
        self.__arango_service.index_doc(
            {
            'type_name': type_name,
            'pk_id': pk_id,
            'upk_id': upk_id
            },
            _COLLECTION_OBJECT_TYPE_ID,
            TYPE_CATEGORY_SYSTEM
        )

    def _store_process(self, data_holder):
        pass
        # TODO
        # self.__enigma_db.get_collection(
        #     data_holder.type_name).insert_one(data_holder.data)

    def _index_object(self, data_holder):
        if type(data_holder) is EntityDataHolder:
            services.arango_service.index_data(data_holder)
        elif type(data_holder) is BrickDataHolder:
            services.arango_service.index_brick(data_holder)

    def _index_process(self, data_holder, update_object_ids=False):

        # Update object ids to DB ids (for processes being uploaded through GUI)
        if update_object_ids:
            data_holder.update_object_ids()
        
        # create a record in the SYS_Process table
        self.__arango_service.index_data(data_holder)

        process = data_holder.data
        process_db_id = '%s/%s' % (data_holder.type_def.collection_name, data_holder.id) 
        # sys.stderr.write('process_dbid = '+str(process_db_id)+'\n')
        
        # Do input objects
        for input_object in process['input_objects']:
            type_name, obj_id = input_object.split(':',1)
            if type_name.startswith('Brick-'):
                type_name = 'Brick'
            type_def = services.indexdef.get_type_def(type_name)
            # sys.stderr.write('from = '+str(type_def.collection_name+':'+type_name+'/'+obj_id)+'\n')

            self.__arango_service.index_doc(
                {
                    '_from': '%s/%s' % (type_def.collection_name, obj_id),
                    '_to': process_db_id
                }, 'ProcessInput', TYPE_CATEGORY_SYSTEM
            )      

        # Do output objects
        for output_object in process['output_objects']:
            type_name, obj_id = output_object.split(':',1)
            if type_name.startswith('Brick-'):
                type_name = 'Brick'
            type_def = services.indexdef.get_type_def(type_name)
            # sys.stderr.write('to = '+str(type_def.collection_name+':'+type_name+'/'+obj_id)+'\n')

            self.__arango_service.index_doc(
                {
                    '_from': process_db_id,
                    '_to': '%s/%s' % (type_def.collection_name, obj_id) 
                }, 'ProcessOutput', TYPE_CATEGORY_SYSTEM
            )      

class EntityDataWebUploader:


    def __init__(self, data_id, type_name, core_tsv, process_tsv=None, warnings=None, process_warnings=None):
        # hash table for core types with errors
        self.__error_items = {}
        self.results = {
            'errors': [],
            'warnings': [],
            'process_errors': [],
            'process_warnings': [],
            # 'success': [],
            'successful_uploads': 0,
            'type_name': type_name # TODO: figure out best way to save type name when youre done
        }
        self.__type_name = type_name
        self.__type_def = services.typedef.get_type_def(self.__type_name)
        self.__upk_property_name = self.__type_def.upk_property_name
        self.__data_id = data_id
        self.__warnings = None
        self.__process_warnings = None

        if core_tsv is not None:
            self.__core_df = pd.read_csv(core_tsv, sep='\t').replace({np.nan: None})
        if process_tsv is not None:
            self.__process_df = pd.read_csv(process_tsv, sep='\t').replace({np.nan: None})
        else:
            self.__process_df = None

        # add warnings for core types that were attempted to be uploaded (for overwriting)
        if warnings is not None:
            self.__warnings = warnings

        if process_warnings is not None:
            self.__process_warnings = process_warnings


    @staticmethod
    def from_file(data_id):
        _UPLOAD_CORE_DATA_PREFIX = 'ucd_'
        _UPLOAD_CORE_FILE_PREFIX = 'ucf_'
        _UPLOAD_PROCESS_FILE_PREFIX = 'upf_'
        TMP_DIR = os.path.join(services._DATA_DIR, 'tmp')

        # get type name
        tmp_results = os.path.join(TMP_DIR, _UPLOAD_CORE_DATA_PREFIX + data_id)
        with open(tmp_results, 'r') as f:
            results = json.load(f)
            type_name = results['type_name']
            warning_results = results['warnings']
            process_warning_results = results['process_warnings']

        return EntityDataWebUploader(data_id,
                                    type_name,
                                    None,
                                    None,
                                    warnings=warning_results,
                                    process_warnings=process_warning_results)

    def upload_standalone_core_types(self):
        # upload core types that do not require connecting upstream processes
        n_rows = self.__core_df.shape[0]

        for ri, row in self.__core_df.iterrows():
            try:
                data = row.to_dict()
                dh = EntityDataHolder(self.__type_name, data)
                services.workspace.save_data_if_not_exists(dh, preserve_logs=True)
                # self.results['success'].append(dh.data)
                self.results['successful_uploads'] += 1
                yield "data: success--\n\n"

            except ItemAlreadyExistsException as ie:
                if ie.changed_data:
                    self.results['warnings'].append({
                        'message': ie.message,
                        'old_data': ie.old_data,
                        'new_data': ie.new_data,
                        'data_holder': ie.data_holder
                    })
                    yield 'data: warning--{}\n\n'.format(ie.message)
                else:
                    # self.results['success'].append(dh.data)
                    self.results['successful_uploads'] += 1
                    yield 'data: success--\n\n'

            except ValueError as e:
                self.results['errors'].append({
                    'data': dh.data,
                    'message': str(e)
                })
                yield 'data: error--{}\n\n'.format(e)

            yield 'data: progress--{}\n\n'.format((ri + 1) / n_rows)

        self._save_tmp_file()
        yield 'data: complete--{}\n\n'.format(self.__data_id)

    def upload_core_types_with_processes(self):

        self._validate_core_items()

        n_rows = self.__process_df['output_objects'].str.count(',').add(2).sum()
        completed_rows = 0

        for ri, row in self.__process_df.iterrows():
            yield "data: progress--{}\n\n".format(ri / n_rows)

            has_errors = False
            has_missing_ids = False

            process_data = row.to_dict()
            pdh = ProcessDataHolder(process_data)
            # output_objects = pdh.data['output_objects'].split(',')
            output_objects = list(csv.reader([pdh.data['output_objects']], delimiter=',', quotechar='"',skipinitialspace=True))[0]
            # input_objects = pdh.data['input_objects'].split(',')
            input_objects = list(csv.reader([pdh.data['input_objects']], delimiter=',', quotechar='"',skipinitialspace=True))[0]

            # check if there are errors from the core types connected to process
            output_errors, missing_id_errors = self._get_output_errors(pdh, output_objects)
            if len(output_errors):
                has_errors = True

            if len(missing_id_errors):
                has_errors = True
                has_missing_ids = True
            # validate process, add message about bad outputs if process is fine
            try:
                pdh.type_def.validate_data(pdh.data, ignore_pk=True)
                self._ensure_input_objects_exist(pdh, input_objects)
                if has_missing_ids:
                    self.results['process_errors'].append({
                        'data': pdh.data,
                        'message': 'Output objects in process not found in %s upload file: %s'
                            % (self.__type_name, ','.join(missing_id_errors))
                    })
                elif has_errors:
                    self.results['process_errors'].append({
                        'data': pdh.data,
                        # TODO: give real error messages
                        'message': 'At least one core type connected to this process was malformed'
                    })
            except ValueError as e:
                has_errors = True
                self.results['process_errors'].append({
                    'data': pdh.data,
                    # TODO: remove something was wrong bit
                    'message': str(e)
                })

            # add errors for core types if theyre not good
            if has_errors:
                for output_object in output_objects:
                    missing_id = False # TODO
                    yield "data: error--\n\n"
                    _, output_upk_id = pdh.get_process_id(output_object)
                    if output_upk_id in output_errors:
                        self.results['errors'].append(output_errors[output_upk_id])
                    else:
                        try:
                            output_data = self._get_data(output_upk_id)
                            self.results['errors'].append({
                                'message': 'At least one parent process or sibling item was malformed',
                                'data': output_data
                            })
                        except Exception as e:
                            # add error for each output object that has process with nonexistant output object
                            tb.print_exc()
                            if not missing_id:
                                missing_id = True
                                self.results['process_errors'].append({
                                    'message': 'process with output %s is missing from core upload file' % (output_upk_id),
                                    'data': pdh.data
                                })

                # yield one more error for process
                yield "data: error--\n\n"
                continue

            # continue with adding warnings
            has_warnings = False
            output_warnings, ok_outputs = self._get_output_warnings(pdh, output_objects)
            if len(output_warnings):
                has_warnings = True

            missing_ids, process_warning = self._get_process_warning(pdh)
            if missing_ids is not None:
                self.results['process_errors'].append({
                    'message': 'Missing the following already existing id(s) from process file: %s' % ','.join(missing_ids),
                    'data': pdh.data
                })
                for i in range(len(output_objects) + 1):
                    yield 'data: error--\n\n'
                continue

            if process_warning is not None:
                self.results['process_warnings'].append({
                    'message': 'Process id %s already exists connecting to at least 1 item being uploaded' % process_warning['old_data']['id'],
                    'old_data': process_warning['old_data'],
                    'new_data': process_warning['new_data'],
                    'dataholder': pdh.data,
                    # 'output_data_holders': [dh.data for dh in ok_outputs]
                    'output_data_holders': self._get_output_data_holders(pdh, output_objects)
                })
                has_warnings = True

            if has_warnings:
                for output_warning in output_warnings:
                    self.results['warnings'].append(output_warning)

                # TODO: figure out formatting for error result schema, It might need to be different than whats added here
                for ok_output in ok_outputs:
                    self.results['warnings'].append({
                        'message': 'At least one parent process or sibling object related to this item has a conflict in the system.',
                        'old_data': ok_output.data,
                        'new_data': ok_output.data
                    })
                    yield "data: warning--\n\n"

                if process_warning is None:
                    self.results['process_warnings'].append({
                        'message': 'At least one output object from this process has a conflict with an existing object in the system',
                        'old_data': pdh.data,
                        'new_data': pdh.data,
                        'dataholder': pdh.data,
                        'output_data_holders': self._get_output_data_holders(pdh, output_objects)
                    })
                    yield "data: warning--\n\n"
                continue

            for output in ok_outputs:
                if 'id' not in output.data:
                    services.workspace.save_data(output)
                # self.results['success'].append(output.data)
                self.results['successful_uploads'] += 1
                yield "data: success--\n\n"

            if 'id' not in pdh.data:
                services.workspace.save_process(pdh, update_object_ids=True)

            completed_rows += len(output_objects) + 1
            yield "data: progress--{}\n\n".format(completed_rows / n_rows)

        self._save_tmp_file()
        yield "data: complete--{}\n\n".format(self.__data_id)

    def _ensure_input_objects_exist(self, pdh, input_objects):
        for input_object in input_objects:
            input_type_name, input_upk_id = pdh.get_process_id(input_object)
            services.workspace._get_pk_id(input_type_name, input_upk_id)

    def _get_output_data_holders(self, pdh, output_objects):
        output_data_holders = []
        for output_object in output_objects:
            _, oid = pdh.get_process_id(output_object)
            data = self._get_data(oid)
            pk_id = services.workspace._get_pk_id_or_none(self.__type_name, oid)
            if pk_id is not None:
                data['id'] = pk_id
            output_data_holders.append(data)
        return output_data_holders

    def _get_output_errors(self, pdh, output_objects):
        output_errors = {}
        missing_id_errors = []
        for output_object in output_objects:
            _, output_upk_id = pdh.get_process_id(output_object)

            try:
                data = self._get_data(output_upk_id)
            except IndexError:
                missing_id_errors.append(output_upk_id)

            if output_upk_id in self.__error_items:
                output_errors[output_upk_id] = self.__error_items[output_upk_id]
        return output_errors, missing_id_errors

    def _get_output_warnings(self, pdh, output_objects):
        output_warnings = []
        ok_outputs = []
        for output_object in output_objects:
            _, upk_id = pdh.get_process_id(output_object)
            data = self._get_data(upk_id)
            dataholder = EntityDataHolder(self.__type_name, data)

            # check to see if upk_id already exists in system
            pk_id = services.workspace._get_pk_id_or_none(self.__type_name, upk_id)
            if pk_id is None:
                ok_outputs.append(dataholder)
                continue

            # validate new data against already saved data for discrepancies
            dataholder.set_id(pk_id)

            aql = 'FOR x IN @@collection FILTER x.id == @pk_id RETURN x'
            aql_bind = {
                '@collection': TYPE_CATEGORY_STATIC + self.__type_name,
                'pk_id': pk_id
            }

            new_data = IndexDocument.build_index_doc(dataholder)
            result = services.arango_service.find(aql, aql_bind)
            old_data = result[0]

            # check keys in old data against new data to see if theyre the same
            matches_old_data = True
            for key, val in old_data.items():
                if key.startswith('_'):
                    continue
                if new_data[key] != val:
                    output_warnings.append({
                        'message': 'object %s already exists in system' % upk_id,
                        'new_data': new_data,
                        'old_data': old_data,
                        'data_holder': dataholder.data
                    })
                    matches_old_data = False
                    break

            if matches_old_data:
                ok_outputs.append(dataholder)

        return output_warnings, ok_outputs

    def _get_process_warning(self, pdh):
        outputs = pdh.data['output_objects']
        # output_objects = [pdh.get_process_id(o) for o in outputs.split(',')]
        output_objects = [pdh.get_process_id(o) for o in list(csv.reader([outputs], delimiter=',', quotechar='"',skipinitialspace=True))[0]]
        output_ids = [oid for _, oid in output_objects]

        inputs = pdh.data['input_objects']
        # input_objects = [pdh.get_process_id(i) for i in inputs.split(',')]
        input_objects = [pdh.get_process_id(i) for i in list(csv.reader([inputs], delimiter=',', quotechar='"',skipinitialspace=True))[0]]
        input_ids = [iid for _, iid in input_objects]

        process_duplicate_error = False ###
        missing_id_references = []
        saved_process = None # TODO: handle multiple process inputs

        for type_name, upk_id in output_objects:
            pk_id = services.workspace._get_pk_id_or_none(type_name, upk_id)

            if pk_id is not None:
                # get connecting upstream process from first existing output
                index_def = services.indexdef.get_type_def(type_name)
                saved_processes = services.arango_service.get_up_processes(index_def, pk_id)

                if len(saved_processes) == 0:
                    # TODO: this should most likely be thrown as an error
                    continue

                saved_process = saved_processes[0]
                pdh.set_id(saved_process['id'])

                # get db process output upk ids
                db_upks = [self._get_upk_id(pk)[1] for pk in saved_process['output_objects']]

                for db_upk in db_upks:
                    # try to find upks missing from output objects elsewhere in process tsv
                    if db_upk not in output_ids and self._find_process_with_output(db_upk) is None:
                        missing_id_references.append(db_upk)
                break

        if len(missing_id_references):
            return missing_id_references, None

        if saved_process == None:
            return None, None

        process_doc = IndexDocument.build_index_doc(pdh)

        # check if metedata values are different
        items_match = True
        for k, v in process_doc.items():
            if k.startswith('_') or k == 'output_objects' or k == 'input_objects':
                continue
            if saved_process[k] != v:
                items_match = False

        # Format input and output objects to upk id for comparison with incoming data
        # change formats to upk id for displaying comparison results in UI
        saved_process['input_objects'] = ['%s:%s' % self._get_upk_id(i) for i in saved_process['input_objects']]
        process_doc['input_objects'] = ['%s:%s' % i for i in input_objects]

        saved_process['output_objects'] = ['%s:%s' % self._get_upk_id(o) for o in saved_process['output_objects']]
        process_doc['output_objects'] = ['%s:%s' % o for o in output_objects]

        # compare upstream objects
        if len(saved_process['input_objects']) != len(input_objects):
            items_match = false
        else:
            for ii, input_object in enumerate(saved_process['input_objects']):
                if input_object != process_doc['input_objects'][ii]:
                    items_match = False

        # compare downstream objects
        if len(saved_process['output_objects']) != len(output_objects):
            items_match = False
        else:
            for oi, output_object in enumerate(saved_process['output_objects']):
                if output_object != process_doc['output_objects'][oi]:
                    items_match = False

        if items_match:
            return None, None

        return None, {
            # TODO: same issue with pk_ids and upK_ids being both displayed in UI, make items coming back upk ids
            'message': 'Process id %s already exists with values differing from incoming upload' % saved_process['id'],
            'old_data': saved_process,
            'new_data': process_doc,
            'data_holder': pdh.data,
            'core_data_holders': []
        }

    def _get_data(self, upk_id):
        return self.__core_df[self.__core_df[self.__upk_property_name] == upk_id].to_dict('records')[0]

    def _find_process_with_output(self, upk_id):
        sub_df = self.__process_df.loc[self.__process_df['output_objects'].str.contains(upk_id)]
        return sub_df if not sub_df.empty else None


    def _get_upk_id(self, db_object):
        type_name, db_pk_id = db_object.split(':',1)
        type_def = services.typedef.get_type_def(type_name)

        type_name = type_name.strip()
        db_pk_id = db_pk_id.strip()

        # get reference to upk id for processes stored in database
        aql = "FOR x IN @@collection FILTER x.id == @id RETURN DISTINCT x"
        aql_bind = {
            '@collection': TYPE_CATEGORY_STATIC + type_name,
            'id': db_pk_id
        }
        result = services.arango_service.find(aql, aql_bind)[0]
        return type_name, result[type_def.upk_property_name]

    def _validate_core_items(self):
        # Run through core tsv to find core type errors that would effect process and sibling core types
        for ri, row in self.__core_df.iterrows():
            data = row.to_dict()
            upk_id = data[self.__type_def.upk_property_name]
            data_holder = EntityDataHolder(self.__type_name, data)

            # make sure there is exactly 1 reference to core type in process file
            upk_pattern = fr":\s*{upk_id}\s*(,|$)"
            core_process_rows = self.__process_df.loc[self.__process_df['output_objects'].str.contains(upk_pattern)]
            if len(core_process_rows.index) != 1:
                if len(core_process_rows.index) == 0:
                    self.__error_items[upk_id] = {
                        'data': data_holder.data,
                        'message': 'Link to %s with id "%s" not found in process file'
                            % (self.__type_name, upk_id)
                    }
                else:
                    self.__error_items[upk_id] = {
                        'data': data_holder.data,
                        'message': 'Conflicting input objects found in process file for %s with id "%s"' % (self.__type_name, upk_id)
                    }
            # validate core types since were looping through the tsv already
            try:
                self.__type_def.validate_data(data_holder.data, ignore_pk=True)
            except ValueError as e:
                tb.print_exc()
                self.__error_items[upk_id] = {
                    'data': data_holder.data,
                    'message': str(e)
                }

    def overwrite_existing_data(self):
        if len(self.__process_warnings) == 0:
            n_rows = len(self.__warnings)
            for i, warning in enumerate(self.__warnings):
                dataholder = EntityDataHolder(self.__type_name, warning['data_holder'])
                services.workspace.update_data(dataholder)
                yield "data: progress--{}\n\n".format((i + 1) / n_rows)
            yield "data: complete--\n\n"
            return

        n_rows = 0
        for process_warning in self.__process_warnings:
            n_rows += (1 + len(process_warning['output_data_holders']))
        completed_rows = 0
        for process_warning in self.__process_warnings:
            # overwrite outputs first
            pdh = ProcessDataHolder(process_warning['dataholder'])
            existing_processes = []
            for output in process_warning['output_data_holders']:
                output_dh = EntityDataHolder(self.__type_name, output)
                # check if ID exists
                if 'id' in output_dh.data:
                    services.workspace.update_data(output_dh)
                    # check to see if theres an upstream process already (for seeing if theres more than 1)
                    index_def = services.indexdef.get_type_def(self.__type_name)
                    saved_processes = services.arango_service.get_up_processes(index_def, output_dh.data['id'])
                    if len(saved_processes) == 0:
                        # in case processes were already deleted from a previous update
                        continue
                    saved_process = saved_processes[0]
                    process_id = saved_process['id']
                    if process_id not in existing_processes:
                        existing_processes.append(process_id)
                else:
                    services.workspace.save_data(output_dh)

            # delete existing processes and save new one
            for existing_process in existing_processes:
                self._delete_process(existing_process)

            services.workspace.save_process(pdh, update_object_ids=True)
            completed_rows += (1 + len(process_warning['output_data_holders']))
            yield 'data: progress--{}\n\n'.format(completed_rows / n_rows)

        self._update_tmp_file()
        yield 'data: complete--\n\n'

    def _delete_process(self, process_id):
        # delete system process inputs(s)
        aql_bind = {
            'id': 'SYS_Process/%s' % process_id
            }
        aql = "FOR pi IN SYS_ProcessInput FILTER pi._to == @id REMOVE pi IN SYS_ProcessInput"
        services.arango_service.db.AQLQuery(aql, bindVars=aql_bind)

        # delete input object
        aql = "FOR po in SYS_ProcessOutput FILTER po._from == @id REMOVE po IN SYS_ProcessOutput"
        services.arango_service.db.AQLQuery(aql, bindVars=aql_bind)

        # delete actual process
        aql = "FOR x in SYS_Process FILTER x._id == @id REMOVE x IN SYS_Process"
        services.arango_service.db.AQLQuery(aql, bindVars=aql_bind)

    def _update_process_output(type_name, output_id, process_id):
        aql = '''
            FOR po IN SYS_ProcessOutput
            FILTER po._to == @output
            UPDATE { _from: @process } IN SYS_ProcessOutput
        '''
        aql_bind = {
            'output': 'SDT_%s/%s' % (type_name, output_id),
            'process': 'SYS_Process/%s' % process_id
        }
        services.arango_service.AQLQuery(aql, aql_bind)

    def _update_tmp_file(self):
        # update results to move warnings to success columns after overwriting
        _UPLOAD_CORE_DATA_PREFIX = 'ucd_'
        TMP_DIR = os.path.join(services._DATA_DIR, 'tmp')

        tmp_results = os.path.join(TMP_DIR, _UPLOAD_CORE_DATA_PREFIX + self.__data_id)

        with open(tmp_results, 'r') as f:
            data = json.load(f)

        # data['success'].extend([d['new_data'] for d in data['warnings']])
        data['successful_uploads'] += len(data['warnings'])
        data['warnings'].clear()
        data['process_warnings'].clear()

        with open(tmp_results, 'w') as f:
            json.dump(data, f, indent=4, sort_keys=False)

    def _save_tmp_file(self):
        _UPLOAD_CORE_DATA_PREFIX = 'ucd_'
        _UPLOAD_CORE_FILE_PREFIX = 'ucf_'
        _UPLOAD_PROCESS_FILE_PREFIX = 'upf_'
        TMP_DIR = os.path.join(services._DATA_DIR, 'tmp')

        tmp_results = os.path.join(TMP_DIR, _UPLOAD_CORE_DATA_PREFIX + self.__data_id)
        with open(tmp_results, 'w') as f:
            json.dump(self.results, f, indent=4, sort_keys=False)
