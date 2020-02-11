import os
import json

from pyArango.connection import Connection
# from . import ontology as ontology_mudule
# from . import validator as validator_module
# from . import workspace as workspace_module
# from . import typedef as typedef_module
# from . import indexdef as indexdef_module
# from . import arango_service as arango_service_module
# from . import report as report_module


from .ontology import OntologyService, CachedTermProvider
from .validator import ValueValidationService
from .workspace import Workspace
from .typedef import TypeDefService
from .indexdef import IndexTypeDefService
from .arango_service import ArangoService
from .report import ReportBuilderService
from .brick import BrickTemplateProvider


IN_ONTOLOGY_LOAD_MODE = False

__PACKAGE_DIR = os.path.dirname(os.path.dirname(__file__))
__CONFIG_FILE = os.path.join(__PACKAGE_DIR, 'var/config.json')
__CONFIG = json.loads(open(__CONFIG_FILE).read())

_DATA_DIR = __CONFIG['Workspace']['data_dir']
_IMPORT_DIR_ONTOLOGY = __CONFIG['Import']['ontology_dir']
_IMPORT_DIR_ENTITY = __CONFIG['Import']['entity_dir']
_IMPORT_DIR_PROCESS = __CONFIG['Import']['process_dir']
_IMPORT_DIR_BRICK = __CONFIG['Import']['brick_dir']

__TYPEDEF_FILE = os.path.join(__PACKAGE_DIR, 'var/typedef.json')
_BRICK_TYPE_TEMPLATES_FILE = os.path.join(__PACKAGE_DIR, 'var/brick_type_templates.json')
_UPLOAD_CONFIG_FILE = os.path.join(__PACKAGE_DIR, 'var/upload_config.json')

_WEB_SERVICE = __CONFIG['WebService']
_PLOT_TYPES_FILE = os.path.join(__PACKAGE_DIR, 'var/' + _WEB_SERVICE['plot_types_file'])

arango_service = None

def _init_db_connection():
    __arango_config = __CONFIG['ArangoDB']
    __arango_conn = Connection(arangoURL=__arango_config['url'],username=__arango_config['user'], password=__arango_config['password'])

    global arango_service
    arango_service = ArangoService(__arango_conn, __arango_config['db'])


ontology = None
typedef = None
indexdef = None
value_validator = None
term_provider = None
workspace = None
reports = None
brick_template_provider = None

def _init_services():
    _init_db_connection()

    global ontology 
    ontology = OntologyService(arango_service)

    global typedef
    typedef = TypeDefService(__TYPEDEF_FILE)

    global indexdef
    indexdef = IndexTypeDefService()

    global value_validator
    value_validator = ValueValidationService()

    global term_provider
    term_provider = CachedTermProvider()

    global workspace
    workspace = Workspace(arango_service)

    global reports
    reports = ReportBuilderService()

    global brick_template_provider
    if not IN_ONTOLOGY_LOAD_MODE:
        brick_template_provider = BrickTemplateProvider(_BRICK_TYPE_TEMPLATES_FILE)

