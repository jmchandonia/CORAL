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

from coral.dataprovider import DataProvider

class dataAccessAPITest(unittest.TestCase):

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
            cls.url = "https://"+host+':'+str(port)+'/coral/'
        else:
            cls.url = "http://"+host+':'+str(port)+'/coral/'

    def get_key_data_public(self):
        return self.cns['_AUTH_PUBLIC']

    def get_key_data_secret(self):
        return self.cns['_AUTH_SECRET']    

    def get_key_public(self):
        data = self.get_key_data_public()
        public_key = RSA.importKey(data)
        return public_key

    # test that the key loads
    def test_get_key_public(self):
        key = self.get_key_public()
        self.assertTrue(key)

    # test connection to unvalidated API on server
    def test_web_services_unsecured(self):
        r = requests.post(self.url, verify=False)
        self.assertEqual(r.text,'Welcome!')
        
    # test connection to validated API, without using token
    def test_web_services_unauthorized(self):
        r = requests.post(self.url+'plot_data', verify=False)
        # should get "unauthorized"
        self.assertEqual(r.status_code,401)

    # test connection to validated API, using login-type token
    def test_web_services_authorized_login(self):
        now = datetime.datetime.now(tz=datetime.timezone.utc)
        payload = {
	    'exp': now + datetime.timedelta(days=0, seconds=0, microseconds=0, milliseconds=0, minutes=120),
	    'iat': now
	}

        # this is a real 'logged in' jwt:
        secret = self.get_key_data_secret()
        new_jwt = jwt.encode(payload, secret, algorithm='HS256')

        headers = {'Authorization': 'JwToken' + ' ' + new_jwt, 'content-type': 'application/json'}

        # this method is @auth_required
        r = requests.get(self.url+'data_types', headers=headers, verify=False)
        self.assertEqual(r.status_code,200)

    # test connection to validated API, using expired login-type token
    def test_web_services_authorized_expired(self):
        now = datetime.datetime.now(tz=datetime.timezone.utc)
        payload = {
	    'exp': now + datetime.timedelta(days=0, seconds=1, microseconds=0, milliseconds=0, minutes=0),
	    'iat': now
	}

        # this is a real 'logged in' jwt:
        secret = self.get_key_data_secret()
        new_jwt = jwt.encode(payload, secret, algorithm='HS256')

        headers = {'Authorization': 'JwToken' + ' ' + new_jwt, 'content-type': 'application/json'}

        # wait for token to expire
        time.sleep(2)

        # this method is @auth_required
        r = requests.get(self.url+'data_types', headers=headers, verify=False)
        self.assertEqual(r.status_code,401)
        
    # test connection to validated API, using public key token
    def test_web_services_unauthorized_wrong_key_type(self):
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

        headers = {'Authorization': 'JwToken' + ' ' + new_jwt, 'content-type': 'application/json'}

        # this method is @auth_required, so should fail
        r = requests.get(self.url+'data_types', headers=headers, verify=False)
        self.assertEqual(r.status_code,401)
        

    # test connection to validated API, using public key token
    def test_web_services_authorized_public_key(self):
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

        headers = {'Authorization': 'JwToken' + ' ' + new_jwt, 'content-type': 'application/json'}

        # this method is @auth_ro_required, so should work
        r = requests.post(self.url+'types_graph', headers=headers, json='', verify=False)
        self.assertEqual(r.status_code,200)

