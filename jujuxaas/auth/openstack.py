import json
import requests
import urlparse

try:
  #from keystoneclient.v2_0 import client as v2client
  from keystoneclient import client as client
  keystoneclient_available=True
except ImportError:
  keystoneclient_available=False

import logging
logger = logging.getLogger(__name__)

class AuthOpenstack(object):
  @staticmethod
  def available():
    return keystoneclient_available

  def __init__(self, url, username, password, tenant=None):
    self.auth_url = url
    self.tenant = tenant
    self.username = username
    self.password = password
    self.clients = {}

  def _get_client(self, project):
    keystone = self.clients.get(project)
    if keystone is None:
      keystone = client.Client(auth_url=self.auth_url,
                               username=self.username,
                               password=self.password,
                               project_name=project)
      self.clients[project] = keystone
      keystone.authenticate()
    return keystone

  def _get_auth_token(self):
    client = self._get_client(self.tenant)
    return client.auth_token

  def decorate_request(self, request):
    logger.debug("Using OpenStack authentication as user: %s", self.username)

    #request['auth'] = requests.auth.HTTPBasicAuth(self.username, self.password)
    request['headers']['X-Auth-Token'] = self._get_auth_token()
    return request

  def get_base_url(self):
    keystone = self._get_client(self.get_tenant())

    service_catalog = keystone.service_catalog
    url = service_catalog.url_for(service_type='jxaas')
    if url is None:
      logger.debug("Service catalog: %s", service_catalog)
      raise Exception("Cannot find jxaas endpoint in Keystone")
    return url

  def get_tenant_id(self):
    client = self._get_client(self.tenant)
    return client.tenant_id

  def get_tenant(self):
    return self.tenant
#     if self.tenant:
#       return self.tenant
# 
#     client = self._get_client(None)
#     print client
#     for s in client.services.list():
#       print s
#       
#     return self.tenant
