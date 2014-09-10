import json
import requests
import urlparse
#from keystoneclient.v2_0 import client as v2client
from keystoneclient import client as client

import logging
logger = logging.getLogger(__name__)

class AuthOpenstack(object):
  def __init__(self, url, username, password, tenant=None):
    self.auth_url = url
    self.tenant = tenant
    self.username = username
    self.password = password
    self.clients = {}

  def _get_client(self, project):
    keystone = self.clients.get(project)
    if keystone is None:
      keystone = client.Client(auth_url=self.auth_url + '/v2.0',
                               username=self.username,
                               password=self.password,
                               project_name=project)
      self.clients[project] = keystone
      print "auth_ref %s"  % keystone.auth_ref
    return keystone

  def decorate_request(self, request):
    return request

  def get_base_url(self):
    client = self._get_client(self.get_tenant())

    for s in client.endpoints.list():
      print s

    return None
  
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