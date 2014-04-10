#!/usr/bin/env python
# vim: syntax=python

import json
import requests
import urlparse

import logging
logger = logging.getLogger(__name__)

class Client(object):
  def __init__(self, url, username, password):
    if not url.endswith("/"):
      url = url + "/"
    self.base_url = url
    self.username = username
    self.password = password

  def _build_url(self, components):
    relative_url = '/'.join(components)
    url = urlparse.urljoin(self.base_url, relative_url)
    return url

  def _build_service_url(self, tenant, service_type, extra_components):
    components = [ tenant, 'services', service_type ]
    components = components + extra_components
    return self._build_url(components)

  def ensure_service(self, tenant, service_type, service_id, config):
    url = self._build_service_url(tenant, service_type, [service_id])

    # Cast everything to a string
    xaas_config = {}
    for k, v in config.iteritems():
      xaas_config[k] = str(v)

    payload = {'Config': xaas_config}
    headers = {}
    headers['Content-Type'] = 'application/json'
    
    data = json.dumps(payload)
    logging.info("Making XaaS request: PUT %s with %s", url, data)
    
    response = requests.put(url, data=data, headers=headers)
    if response.status_code != 200:
      raise Exception("Unexpected error from XaaS API, code: %s" % response.status_code)
    return response.json()

  def get_relation_properties(self, env_uuid, service_type, service_id):
    url = self._build_service_url(tenant, service_type, [service_id, 'properties'])
    
    headers = {}
    logging.info("Making XaaS request: GET %s", url)

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
      raise Exception("Unexpected error from XaaS API, code: %s" % response.status_code)
    return response.json()
  
  def update_relation_properties(self,
                                 tenant,
                                 service_type,
                                 service_id,
                                 relation,
                                 relation_id,
                                 unit_id,
                                 remote_name,
                                 action,
                                 properties):
    url = self._build_service_url(tenant, service_type, [service_id, 'relation', relation])
    
    # Cast everything to a string
    xaas_properties = {}
    for k, v in properties.iteritems():
      xaas_properties[k] = str(v)

    payload = {}
    payload['Properties'] = xaas_properties
    payload['Action'] = action
    payload['RelationId'] = relation_id
    payload['UnitId'] = unit_id
    payload['RemoteName'] = remote_name

    headers = {}
    headers['Content-Type'] = 'application/json'
    
    data = json.dumps(payload)
    logging.info("Making XaaS request: POST %s with %s", url, data)
    
    response = requests.post(url, data=data, headers=headers)
    if response.status_code != 200:
      raise Exception("Unexpected error from XaaS API, code: %s" % response.status_code)
    logging.info("Response: %s", response.headers)
    return response.json()

