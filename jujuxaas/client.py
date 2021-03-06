import json
import requests
import urlparse

import logging
logger = logging.getLogger(__name__)

class Client(object):
  def __init__(self, auth):
    self.auth = auth

  def _build_url(self, components):
    base_url = self.auth.get_base_url()
    if not base_url.endswith("/"):
      base_url = base_url + "/"
    relative_url = '/'.join(components)
    url = urlparse.urljoin(base_url, relative_url)
    return url

  def _build_service_url(self, bundle_type, extra_components):
    components = [ 'services' ]
    if bundle_type:
      components.append(bundle_type)
    components = components + extra_components
    return self._build_url(components)

  def _build_request(self, method, url, data=None, headers={}, timeout=None):
    request = {}
    request['method'] = method
    request['url'] = url
    request['headers'] = headers
    if data:
      request['data'] = data
    if timeout:
      request['timeout'] = timeout
    
    request = self.auth.decorate_request(request)

    logging.debug("Making XaaS request: %s %s", request['method'], request['url'])
    return request

  def _execute_request(self, request):
    return requests.request(**request)
    
  def _simple_get(self, bundle_type, path):
    url = self._build_service_url(bundle_type, path)

    request = self._build_request('GET', url)
    response = self._execute_request(request)
    if response.status_code != 200:
      raise Exception("Unexpected error from XaaS API, code: %s" % response.status_code)
    return response.json()

  def _simple_delete(self, bundle_type, path):
    url = self._build_service_url(bundle_type, path)

    request = self._build_request('DELETE', url)
    response = self._execute_request(request)
    if response.status_code != 202:
      raise Exception("Unexpected error from XaaS API, code: %s" % response.status_code)

  def _simple_put(self, bundle_type, path, payload):
    url = self._build_service_url(bundle_type, path)

    headers = {}
    headers['Content-Type'] = 'application/json'
    data = json.dumps(payload)

    request = self._build_request('PUT', url, data=data, headers=headers, timeout=60)
    response = self._execute_request(request)
    if response.status_code != 200:
      raise Exception("Unexpected error from XaaS API, code: %s" % response.status_code)
    return response.json()

  def ensure_instance(self, bundle_type, instance_id, options=None, units=None):
    payload = {}

    # Cast everything to a string
    if not options is None:
      xaas_options = {}
      for k, v in options.iteritems():
        xaas_options[k] = str(v)
      payload['Options'] = xaas_options

    if not units is None:
      payload['NumberUnits'] = units

    return self._simple_put(bundle_type, [instance_id], payload)

  def destroy_instance(self, bundle_type, instance_id):
    return self._simple_delete(bundle_type, [instance_id])

  def repair_instance(self, bundle_type, instance_id):
    payload = {}
    return self._simple_put(bundle_type, [instance_id, 'health'], payload)

  def list_bundle_types(self):
    return self._simple_get(None, [])

  def list_instances(self, bundle_type):
    return self._simple_get(bundle_type, [])

  def get_instance_state(self, bundle_type, instance_id):
    return self._simple_get(bundle_type, [instance_id])

  def get_relation_properties(self, bundle_type, instance_id, relation):
    return self._simple_get(bundle_type, [instance_id, 'relations', relation])

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
