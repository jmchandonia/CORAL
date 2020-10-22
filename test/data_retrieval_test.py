import unittest
import os
import json
import warnings
import requests
import urllib3
import jwt
import datetime
import time
import base64
import pprint
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP

from generix.dataprovider import DataProvider

class dataRetrievalTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # filter out resource warnings and "unclosed connection" warning
        warnings.simplefilter("ignore", ResourceWarning)
        warnings.simplefilter("ignore", DeprecationWarning)
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        # get constants defined in var/config.json
        cls.dp = DataProvider()
        cls.cns = cls.dp._get_constants()
    
        # default url for web services
        host = "localhost"
        port = cls.cns['_WEB_SERVICE']['port']
        https = cls.cns['_WEB_SERVICE']['https']
        if https:
            cls.url = "https://"+host+':'+str(port)+'/generix/'
        else:
            cls.url = "http://"+host+':'+str(port)+'/generix/'

    def get_key_data_public(self):
        return self.cns['_AUTH_PUBLIC']

    def get_key_public(self):
        data = self.get_key_data_public()
        public_key = RSA.importKey(data)
        return public_key

    def get_authorized_headers(self):
        now = datetime.datetime.now(tz=datetime.timezone.utc)
        payload = {
	    'exp': now + datetime.timedelta(days=0, seconds=0, microseconds=0, milliseconds=0, minutes=120),
	    'iat': now
	}
        
        public_key = self.get_key_public()
        encryptor = PKCS1_OAEP.new(public_key)
        secret = encryptor.encrypt(str(int(now.timestamp())).encode('utf-8'))
        b64 = base64.b64encode(secret)

        new_jwt = jwt.encode(payload, 'data clearinghouse', headers={'secret':b64.decode('utf-8')}, algorithm='HS256')

        headers = {'Authorization': 'JwToken' + ' ' + new_jwt.decode(), 'content-type': 'application/json'}
        return headers
    
        
    # get TSV list of all strains
    def test_get_strains_TSV(self):
        headers = self.get_authorized_headers()
        
        # this method is @auth_ro_required, so should work
        query = {'format': 'TSV',
                 'queryMatch': {'category': 'SDT_',
                                'dataModel': 'Strain',
                                'dataType': 'Strain',
                                'params': []}}
        r = requests.post(self.url+'search', headers=headers, json=query, verify=False)
        # print (r.text)
        self.assertEqual(r.status_code,200)

    # get JSON list of all strains
    def test_get_strains_JSON(self):
        headers = self.get_authorized_headers()
        
        # this method is @auth_ro_required, so should work
        query = {'format': 'JSON',
                 'queryMatch': {'category': 'SDT_',
                                'dataModel': 'Strain',
                                'dataType': 'Strain',
                                'params': []}}
        r = requests.post(self.url+'search', headers=headers, json=query, verify=False)
        self.assertEqual(r.status_code,200)


    # get a brick as JSON
    def test_get_brick_JSON(self):
        headers = self.get_authorized_headers()
        
        # this method is @auth_ro_required, so should work
        query = {}
        r = requests.post(self.url+'brick/Brick0000001', headers=headers, json=query, verify=False)
        # print (r.text)
        self.assertEqual(r.status_code,200)
