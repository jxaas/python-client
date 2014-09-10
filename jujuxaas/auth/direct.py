import requests

import logging
logger = logging.getLogger(__name__)

class AuthDirect(object):
  def __init__(self, url, username, password, tenant):
    self.base_url = url
    self.tenant = tenant
    self.username = username
    self.password = password

  def decorate_request(self, request):
    request['auth'] = requests.auth.HTTPBasicAuth(self.username, self.password)
    return request

  def get_base_url(self):
    return self.base_url + '/' + self.tenant
  
  def get_tenant(self):
    return self.tenant