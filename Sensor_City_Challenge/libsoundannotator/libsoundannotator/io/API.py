 # -*- coding: utf-8 -*-
__author__ = "Arryon Tijsma"
__copyright__ = "Copyright 2015, SoundAppraisal B.V."

import requests, json, time, sys, datetime, oauthlib.oauth1, urllib

#Custom exceptions

class AuthException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class OAuthCredentialsException(AuthException):
    def __init__(self, *args, **kwargs):
        super(OAuthCredentialsException, self).__init__(*args, **kwargs)

class BadRequestException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class BadFormatException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class APIRequest(object):
    API = 'http://localhost:1337'
    credentials = {}
    auth = True

    def __init__(self, *args, **kwargs):
        if 'logger' in kwargs:
            self.logger = kwargs.get('logger')
        self.API = kwargs.get('API', self.API)
        self.credentials = {
            "key": kwargs.get('key', None),
            "secret": kwargs.get('secret', None),
            "uid": kwargs.get('uid', None)
        }
        # if more than one value is None, but not all, that's not good
        nones = self.credentials.values().count(None)
        if 0 < nones < len(self.credentials.values()):
            raise OAuthCredentialsException("Some of 'key', 'secret', 'uid' are not given: {0}".format(self.credentials))

        # whether we use OAuth or not
        if nones == len(self.credentials.values()):
            self.auth = False
            self._logInfo("Not using Auth because credentials are not given")
        else:
            self.client = oauthlib.oauth1.Client(self.credentials["key"], client_secret=self.credentials["secret"])
            self._logDebug("Client constructed")

    def get(self, url, params=None):
        url = "{0}{1}".format(self.API, url)
        if params is not None:
            paramstr = urllib.encode(params)
            url = "{0}?{1}".format(url, paramstr)

        if self.auth:
            uri, headers, body = self.client.sign(url, "GET")
            headers['uid'] = self.credentials["uid"]
        else:
            headers = {}

        return requests.get(url, headers=headers)

    def post(self, url, body):
        url = "{0}{1}".format(self.API, url)
        headers = {
            "Content-Type":"application/x-www-form-urlencoded"
        }
        body["uid"] = self.credentials["uid"]
        if body is None:
            raise BadRequestException("Should call APIRequest.post using body, currently 'None' given")
        if self.auth:
            uri, headers, body = self.client.sign(url, "POST", self._body_to_unicode(body), headers=headers)
            headers['uid'] = self.credentials["uid"]
        return requests.post(url, data=body, headers=headers)

    """
    Convert all python dictionary values to unicode strings. Needed to sign a POST request
    """
    def _body_to_unicode(self, body):
        if body == None:
            return body
        uni = {}
        for key in body:
            uni[key] = unicode(str(body[key]))
        return uni

    def _logError(self, msg):
        if hasattr(self, 'logger'):
            self.logger.error(msg)
        else:
            print "[ERROR]: {0}".format(msg)

    def _logInfo(self, msg):
        if hasattr(self, 'logger'):
            self.logger.info(msg)
        else:
            print "[INFO]: {0}".format(msg)

    def _logDebug(self, msg):
        if hasattr(self, 'logger'):
            self.logger.debug(msg)
        else:
            print "[DEBUG]: {0}".format(msg)
