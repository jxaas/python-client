import json
import requests
import urlparse

import logging
logger = logging.getLogger(__name__)

class PrivateClient(object):
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
    url = self._build_url([ 'rpc', 'update_relation_properties' ])

    # Cast everything to a string
    xaas_properties = {}
    for k, v in properties.iteritems():
      xaas_properties[k] = str(v)

    payload = {}
    payload['Tenant'] = tenant
    payload['ServiceType'] = service_type

    payload['ServiceId'] = service_id
    payload['Relation'] = relation
    payload['RelationId'] = relation_id
    payload['UnitId'] = unit_id
    payload['RemoteName'] = remote_name
    payload['Action'] = action
    payload['Properties'] = xaas_properties

    headers = {}
    headers['Content-Type'] = 'application/json'

    data = json.dumps(payload)
    logging.info("Making XaaS request: POST %s with %s", url, data)

    response = requests.post(url, data=data, headers=headers)
    if response.status_code != 200:
      raise Exception("Unexpected error from XaaS API, code: %s" % response.status_code)
    logging.info("Response: %s", response.headers)
    return response.json()

