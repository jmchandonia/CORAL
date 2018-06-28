import os
import json
from elasticsearch import Elasticsearch
from neo4j.v1 import GraphDatabase

from .ontology import OntologyService
from .validator import TermValueValidationService
from .indexer import SearchIndexerService
from .search import SearchService
from .provenance import ProvenanceIndexerService, ProvenanceSearchService
from .workspace import Workspace

__PACKAGE_DIR = os.path.dirname(os.path.dirname(__file__))
__CONFIG_FILE = os.path.join(__PACKAGE_DIR, 'var/config.json')
__CONFIG = json.loads(open(__CONFIG_FILE).read())

__es_config = __CONFIG['ElasticSearch']
__es_client = Elasticsearch(__es_config['url'])


__neo4j_config = __CONFIG['Neo4j']
__neo4j_client = GraphDatabase.driver(
    __neo4j_config['url'],
    auth=(__neo4j_config['user'], __neo4j_config['password']))


ontology = OntologyService(__es_client)
workspace = Workspace()

es_indexer = SearchIndexerService(__es_client)
es_search = SearchService(__es_client)
neo_indexer = ProvenanceIndexerService()
neo_search = ProvenanceSearchService(__neo4j_client)


term_value_validator = TermValueValidationService()
