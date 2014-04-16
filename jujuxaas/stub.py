import os
import yaml

from jujucharmtoolkit.juju import Juju, Relation
import jujuxaas.client
import jujuxaas.privateclient

import logging
logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.DEBUG)

def run_relation_hook():
    relation_name = os.environ["JUJU_RELATION"]
    juju_action = Juju.action()
    stub = Stub()
    return stub.run_relation_hook(relation_name, juju_action)

def on_start():
    stub = Stub()
    return stub.on_start()

def on_stop():
    stub = Stub()
    return stub.on_stop()

def on_config_changed():
    stub = Stub()
    return stub.on_config_changed()

class Stub(object):
  def __init__(self):
    self._cache_config = None

  def _client(self):
    # TODO: Make this configurable!!
    xaas = jujuxaas.client.Client(url='http://10.0.3.1:8080/xaas', username='', password='')
    return xaas

  def _privateclient(self):
    # TODO: Make this configurable!!
    client = jujuxaas.privateclient.PrivateClient(url='http://10.0.3.1:8080/xaasprivate', username='', password='')
    return client

  @property
  def config(self):
    if not self._cache_config:
      config_path = os.path.join(os.environ.get("CHARM_DIR", ""), "stub.yaml")
      with open(config_path) as f:
        self._cache_config = yaml.load(f)
    return self._cache_config

  def on_start(self):
    # We just defer to on_config_changed - everything should be idempotent
    return self.on_config_changed()

  def on_config_changed(self):
    return None

  def on_stop(self):
    return None

  def run_relation_hook(self, relation_name, action):
    # TODO: Only on certain actions?
    logger.info("Running relation hook %s %s", relation_name, action)

    relation = Relation.default()

    properties = {}
    if not action == "broken":
        properties = relation.get_properties()

    logger.info("Got relation properties %s", properties)

    xaas = self._privateclient()

    config = Juju.config()
    bundle_type = self.config['charm']
    service_name = Juju.service_name()
    tenant = Juju.env_uuid()
    unit_id = Juju.unit_name()
    remote_name = os.environ["JUJU_REMOTE_UNIT"]
    relation_id = relation.relation_id

    new_properties = xaas.update_relation_properties(tenant=tenant,
                                                     bundle_type=bundle_type,
                                                     service_name=service_name,
                                                     relation=relation_name,
                                                     relation_id=relation_id,
                                                     unit_id=unit_id,
                                                     remote_name=remote_name,
                                                     action=action,
                                                     properties=properties)

    if new_properties:
        logger.info("Setting relation properties to: %s", new_properties)
        relation.set_properties(new_properties)
