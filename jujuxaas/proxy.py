import os
import time
import yaml

from jujucharmtoolkit.juju import Juju, Relation
import jujuxaas.client

import logging
logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.DEBUG)

def run_relation_hook():
    relation_name = os.environ["JUJU_RELATION"]
    juju_action = Juju.action()
    proxy = Proxy()
    return proxy.run_relation_hook(relation_name, juju_action)

def on_start():
    proxy = Proxy()
    return proxy.on_start()

def on_stop():
    proxy = Proxy()
    return proxy.on_stop()

def on_config_changed():
    proxy = Proxy()
    return proxy.on_config_changed()

class Proxy(object):
  def __init__(self):
    self._cache_config = None

  def _client(self):
    config = Juju.config()
    url = config.get('jxaas-url', '')
    if not url:
      raise Exception("jxaas-url is required")
    tenant = config.get('jxaas-tenant', '')
    if not tenant:
      raise Exception("jxaas-tenant is required")
    username = config.get('jxaas-user', '')
    secret = config.get('jxaas-secret', '')

    xaas = jujuxaas.client.Client(url=url, tenant=tenant, username=username, password=secret)
    return xaas

  @property
  def config(self):
    if not self._cache_config:
      config_path = os.path.join(os.environ.get("CHARM_DIR", ""), "proxy.yaml")
      with open(config_path) as f:
        self._cache_config = yaml.load(f)
    return self._cache_config

  def on_start(self):
    # We just defer to on_config_changed - everything should be idempotent
    return self.on_config_changed()

  def on_config_changed(self):
    xaas = self._client()

    config = Juju.config()
    bundle_type = self.config['charm']
    instance_id = Juju.service_name()

    logger.info("Ensuring that service is configured: %s %s", bundle_type, instance_id)
    service = xaas.ensure_instance(bundle_type=bundle_type, instance_id=instance_id, config=config)

    # TODO: Timeout & throw error after a while
    while service.get('Status') != 'started':
      logger.info("Waiting for service to reach active state.  Current state %s", service.get('State'))
      time.sleep(5)
      service = xaas.get_instance_state(bundle_type=bundle_type, instance_id=instance_id)

    return service

  def on_stop(self):
    # TODO: Stop service?
    xaas = self._client()
    # service = xaas.ensure_instance(charm=self.charm, instance_id=instance_id, env_uuid=env_uuid)

  def run_relation_hook(self, relation_name, action):
    logger.info("Running relation hook %s %s", relation_name, action)

    # TODO: Only on certain actions?
    if action == 'broken':
        return

    xaas = self._client()

    bundle_type = self.config['charm']
    instance_id = Juju.service_name()
    # config = Juju.config()
    # unit_id = Juju.unit_name()
    # remote_name = os.environ["JUJU_REMOTE_UNIT"]
    # relation_id = relation.relation_id

    logger.info("Fetching service properties")
    response = xaas.get_relation_properties(bundle_type=bundle_type,
                                                       instance_id=instance_id,
                                                       relation=relation_name)

    relation_properties = response.get('Properties', {})

    relation = Relation.default()

    logger.info("Setting relation properties to: %s", relation_properties)
    relation.set_properties(relation_properties)

