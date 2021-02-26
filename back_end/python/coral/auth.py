from flask import url_for, current_app, redirect, request
# from rauth import OAuth2Service
from requests_oauthlib import OAuth2Session
from .dataprovider import DataProvider
import requests

import json, urllib

dp = DataProvider()
cns = dp._get_constants()

class OAuthSignin(object):
    providers = None

    def __init__(self, provider_name): # TODO: make generic for different OAuth services
        self.provider_name = provider_name
        with open(cns['_GOOGLE_OAUTH2_CREDENTIALS']) as f:
            credentials = json.load(f)

        print('CREDENTIALS>>>>>>>>>>>>>>>L>', credentials)

        self.client_id = credentials['web']['client_id']
        self.client_secret = credentials['web']['client_secret']
        self.providers = None

    def authorize(self):
        pass

    def callback(self):
        pass

    def get_callback_url(self):
        return url_for('oauth_callback', provider=self.provider_name, _external=True)

    @classmethod
    def get_provider(self, provider_name='google'):
        if self.providers is None or self.providers == {}:
            self.providers={}
            for provider_class in self.__subclasses__():
                provider = provider_class()
                self.providers[provider.provider_name] = provider
        return self.providers[provider_name]


class GoogleSignIn(OAuthSignin):

    openid_url = 'https://accounts.google.com/.well-known/openid-configuration'
    provider_name = 'google'

    def __init__(self):
        super(GoogleSignIn, self).__init__('google')
        self.openid_config = json.load(urllib.request.urlopen(self.openid_url))
        self.session = OAuth2Session(
            client_id=self.client_id,
            redirect_uri=self.get_callback_url(),
            scope=['email']
        )

    def authorize(self, auth_code):
        # print('REDIRECT URL', self.get_callback_url())
        auth_url, _ = self.session.authorization_url(
            self.openid_config["authorization_endpoint"]
        )
        # print('AUTH URL >>>', auth_url)
        # print('CODE', request.args['code'], request)
        print('AUTH_CODE', auth_code)

        # self.session.fetch_token(
        #     token_url=self.openid_config['token_endpoint'],
        #     code=auth_code,
        #     client_secret=self.client_secret
        # )

        # print('session received')

        # user = self.session.get(self.openid_config['userinfo_endpoint']).json()
        # print ('USER >>>>>', user['name'], user['email'])
        # return user['name'], user['email']
        return redirect(auth_url)
        # return self.callback()
        # x = requests.post(auth_url, {}, headers={'Accept' : 'application/json'})
        # print('XXXXXX', x)
        # print('CONTENT', x.content)

    def callback(self):
        if "code" not in request.args:
            print("CODE NOT IN REQUEST.ARGS")
            return None, None

        self.session.fetch_token(
            token_url=self.openid_config['token_endpoint'],
            code=request.args['code'],
            client_secret=self.client_secret
        )

        user = self.session.get(self.openid_config['userinfo_endpoint']).json()
        return user['name'], user['email']