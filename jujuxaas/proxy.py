import os
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
  def _client(self):
    self._cache_config = None
    # TODO: Make this configurable!!
    xaas = jujuxaas.client.Client(url='http://10.0.3.1:8080/xaas', username='', password='')
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
    charm_id = self.config['charm']
    service_id = Juju.service_name()
    tenant = Juju.env_uuid()

    logger.info("Ensuring that service is configured: %s %s %s", tenant, charm_id, service_id)
    service = xaas.ensure_service(tenant=tenant, service_type=charm_id, service_id=service_id, config=config)

    return service

  def on_stop(self):
    # TODO: Stop service?
    xaas = self._client()
    # service = xaas.ensure_service(charm=self.charm, service_id=service_id, env_uuid=env_uuid)

  def run_relation_hook(self, relation_name, action):
    logger.info("Running relation hook %s %s", relation_name, action)

    # TODO: Only on certain actions?
    if action == 'broken':
        return

    xaas = self._client()

    tenant = Juju.env_uuid()
    service_type = self.config['charm']
    service_id = Juju.service_name()
    #config = Juju.config()
    #unit_id = Juju.unit_name()
    #remote_name = os.environ["JUJU_REMOTE_UNIT"]
    #relation_id = relation.relation_id

    logger.info("Fetching service properties")
    relation_properties = xaas.get_relation_properties(tenant=tenant,
                                                       service_type=service_type,
                                                       service_id=service_id,
                                                       relation=relation)

    relation = Relation.default()

    logger.info("Setting relation properties to: %s", relation_properties)
    relation.set_properties(relation_properties.get('Properties', {}))

