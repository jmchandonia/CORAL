import os
import json
# from elasticsearch import Elasticsearch
# from neo4j.v1 import GraphDatabase
# from pymongo import MongoClient
from pyArango.connection import Connection

from .ontology import OntologyService, CashedTermProvider
from .validator import TermValueValidationService
from .workspace import Workspace
from .typedef import TypeDefService
from .indexdef import IndexTypeDefService
# from .neo_service import Neo4JService
from .arango_service import ArangoService

from .user_profile import UserProfile
from .dataprovider import BrickProvider
from .dataprovider import Query as _Query

Query = _Query

IN_ONTOLOGY_LOAD_MODE = False

__PACKAGE_DIR = os.path.dirname(os.path.dirname(__file__))
__TYPEDEF_FILE = os.path.join(__PACKAGE_DIR, 'var/typedef.json')

_BRICK_TYPE_TEMPLATES_FILE = os.path.join(__PACKAGE_DIR, 'var/brick_type_templates.json')

__CONFIG_FILE = os.path.join(__PACKAGE_DIR, 'var/config.json')
__CONFIG = json.loads(open(__CONFIG_FILE).read())

# __es_config = __CONFIG['ElasticSearch']
# __es_client = Elasticsearch(__es_config['url'])

# temp solution
# _es_client = __es_client


# __neo4j_config = __CONFIG['Neo4j']
# __neo4j_client = GraphDatabase.driver(
#     __neo4j_config['url'],
#     auth=(__neo4j_config['user'], __neo4j_config['password']))


# __mongo_client = MongoClient(port=27017)


__arango_config = __CONFIG['ArangoDB']
print('__arango_config', __arango_config)
__arango_conn = Connection(arangoURL=__arango_config['url'],username=__arango_config['user'], password=__arango_config['password'])
arango_service = ArangoService(__arango_conn, __arango_config['db'])


ontology = OntologyService(arango_service)
typedef = TypeDefService(__TYPEDEF_FILE)
indexdef = IndexTypeDefService()
workspace = Workspace(arango_service)

# neo_service = Neo4JService(__neo4j_client)

term_value_validator = TermValueValidationService()
brick_provider = BrickProvider()

user_profile = UserProfile()
term_provider = CashedTermProvider()
