import os
import json

from pyArango.connection import Connection
from .ontology import OntologyService, CashedTermProvider
from .validator import TermValueValidationService
from .workspace import Workspace
from .typedef import TypeDefService
from .indexdef import IndexTypeDefService
from .arango_service import ArangoService


IN_ONTOLOGY_LOAD_MODE = False

__PACKAGE_DIR = os.path.dirname(os.path.dirname(__file__))
__TYPEDEF_FILE = os.path.join(__PACKAGE_DIR, 'var/typedef.json')
_DATA_DIR = os.path.join(__PACKAGE_DIR, 'data')

_BRICK_TYPE_TEMPLATES_FILE = os.path.join(__PACKAGE_DIR, 'var/brick_type_templates.json')

__CONFIG_FILE = os.path.join(__PACKAGE_DIR, 'var/config.json')
__CONFIG = json.loads(open(__CONFIG_FILE).read())

__arango_config = __CONFIG['ArangoDB']
print('__arango_config', __arango_config)
__arango_conn = Connection(arangoURL=__arango_config['url'],username=__arango_config['user'], password=__arango_config['password'])
arango_service = ArangoService(__arango_conn, __arango_config['db'])

ontology = OntologyService(arango_service)
typedef = TypeDefService(__TYPEDEF_FILE)
indexdef = IndexTypeDefService()

term_value_validator = TermValueValidationService()
term_provider = CashedTermProvider()

workspace = Workspace(arango_service)
