import os
import json
from elasticsearch import Elasticsearch
from neo4j.v1 import GraphDatabase
from pymongo import MongoClient

from .ontology import OntologyService, CashedTermProvider
from .validator import TermValueValidationService
from .indexer import SearchIndexerService
from .search import SearchService
from .workspace import Workspace
from .typedef import TypeDefService
from .es_service import ElasticSearchService
from .neo_service import Neo4JService
from .dataprovider import Query, BrickProvider
from .user_profile import UserProfile

QQuery = Query


IN_ONTOLOGY_LOAD_MODE = False

__PACKAGE_DIR = os.path.dirname(os.path.dirname(__file__))
__TYPEDEF_FILE = os.path.join(__PACKAGE_DIR, 'var/typedef.json')

__CONFIG_FILE = os.path.join(__PACKAGE_DIR, 'var/config.json')
__CONFIG = json.loads(open(__CONFIG_FILE).read())

__es_config = __CONFIG['ElasticSearch']
__es_client = Elasticsearch(__es_config['url'])

# temp solution
_es_client = __es_client


__neo4j_config = __CONFIG['Neo4j']
__neo4j_client = GraphDatabase.driver(
    __neo4j_config['url'],
    auth=(__neo4j_config['user'], __neo4j_config['password']))


__mongo_client = MongoClient(port=27017)

ontology = OntologyService(__es_client)
typedef = TypeDefService(__TYPEDEF_FILE)
workspace = Workspace(__mongo_client)

es_indexer = SearchIndexerService(__es_client)
es_search = SearchService(__es_client)
es_service = ElasticSearchService(__es_client)

neo_service = Neo4JService(__neo4j_client)

term_value_validator = TermValueValidationService()
brick_provider = BrickProvider()

user_profile = UserProfile()
term_provider = CashedTermProvider()
