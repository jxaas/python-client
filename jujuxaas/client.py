import json
import requests
import urlparse

import logging
logger = logging.getLogger(__name__)

class Client(object):
  def __init__(self, url, tenant, username, password):
    if not url.endswith("/"):
      url = url + "/"
    self.base_url = url
    self.tenant = tenant
    self.username = username
    self.password = password

  def _build_url(self, components):
    relative_url = '/'.join(components)
    url = urlparse.urljoin(self.base_url, relative_url)
    return url

  def _build_service_url(self, bundle_type, extra_components):
    components = [ self.tenant, 'services' ]
    if bundle_type:
      components.append(bundle_type)
    components = components + extra_components
    return self._build_url(components)

  def _simple_get(self, bundle_type, path):
    url = self._build_service_url(bundle_type, path)

    headers = {}
    logging.debug("Making XaaS request: GET %s", url)

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
      raise Exception("Unexpected error from XaaS API, code: %s" % response.status_code)
    return response.json()

  def _simple_put(self, bundle_type, path, payload):
    url = self._build_service_url(bundle_type, path)

    headers = {}
    headers['Content-Type'] = 'application/json'

    data = json.dumps(payload)
    logging.debug("Making XaaS request: PUT %s with %s", url, data)

    response = requests.put(url, data=data, headers=headers)
    if response.status_code != 200:
      raise Exception("Unexpected error from XaaS API, code: %s" % response.status_code)
    return response.json()

  def ensure_instance(self, bundle_type, instance_id, config=None, units=None):
    payload = {}

    # Cast everything to a string
    if not config is None:
      xaas_config = {}
      for k, v in config.iteritems():
        xaas_config[k] = str(v)
      payload['Config'] = xaas_config

    if not units is None:
      payload['NumberUnits'] = units

    return self._simple_put(bundle_type, [instance_id], payload)

  def destroy_instance(self, bundle_type, instance_id):
    url = self._build_service_url(bundle_type, [instance_id])

    headers = {}

    logging.debug("Making XaaS request: DELETE %s", url)

    response = requests.delete(url, headers=headers)
    if response.status_code != 202:
      raise Exception("Unexpected error from XaaS API, code: %s" % response.status_code)

  def repair_instance(self, bundle_type, instance_id):
    url = self._build_service_url(bundle_type, [instance_id, 'health'])

    headers = {}

    payload = {}
    data = json.dumps(payload)

    logging.debug("Making XaaS request: POST %s with %s", url, data)

    response = requests.post(url, data=data, headers=headers)
    if response.status_code != 200:
      raise Exception("Unexpected error from XaaS API, code: %s" % response.status_code)

  def list_bundle_types(self):
    url = self._build_service_url(None, [])

    headers = {}
    logging.debug("Making XaaS request: GET %s", url)
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
      raise Exception("Unexpected error from XaaS API, code: %s" % response.status_code)
    return response.json()

  def list_instances(self, bundle_type):
    url = self._build_service_url(bundle_type, [])

    headers = {}
    logging.debug("Making XaaS request: GET %s", url)
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
      raise Exception("Unexpected error from XaaS API, code: %s" % response.status_code)
    return response.json()

  def get_instance_state(self, bundle_type, instance_id):
    url = self._build_service_url(bundle_type, [instance_id])

    headers = {}
    logging.debug("Making XaaS request: GET %s", url)

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
      raise Exception("Unexpected error from XaaS API, code: %s" % response.status_code)
    return response.json()

  def get_relation_properties(self, bundle_type, instance_id, relation):
    url = self._build_service_url(bundle_type, [instance_id, 'relations', relation])

    headers = {}
    logging.debug("Making XaaS request: GET %s", url)

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
      raise Exception("Unexpected error from XaaS API, code: %s" % response.status_code)
    return response.json()

  def get_log(self, bundle_type, instance_id):
    json = self._simple_get(bundle_type, [instance_id, 'log'])

    return json['Lines']

  def get_health(self, bundle_type, instance_id):
    return self._simple_get(bundle_type, [instance_id, 'health'])

  def get_metrics(self, bundle_type, instance_id):
    return self._simple_get(bundle_type, [instance_id, 'metrics'])

  def get_metric_values(self, bundle_type, instance_id, metric_key):
    return self._simple_get(bundle_type, [instance_id, 'metrics', metric_key])

  def get_scaling(self, bundle_type, instance_id):
    return self._simple_get(bundle_type, [instance_id, 'scaling'])

  def set_scaling(self, bundle_type, instance_id, policy):
    return self._simple_put(bundle_type, [instance_id, 'scaling'], policy)
