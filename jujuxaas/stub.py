#!/usr/bin/env python
# vim: syntax=python

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
  def _client(self):
    self._cache_config = None
    # TODO: Make this configurable!!
    xaas = jujuxaas.client.Client(url='http://10.0.3.1:8080/xaas', username='', password='')
    return xaas

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
    
    properties = relation.get_properties()
    
    logger.info("Got relation properties %s", properties)
    
    xaas = self._client()
    
    config = Juju.config()
    charm_id = self.config['charm']
    service_id = Juju.service_name()
    env_uuid = Juju.env_uuid()
    unit_id = Juju.unit_name()
    remote_name = os.environ["JUJU_REMOTE_UNIT"]
    relation_id = relation.relation_id
    
    # Swap the variables; we store it on the server
    # TODO: This is a little hacky
    service_id = remote_name
    tokens = service_id.split("/")
    if len(tokens) == 2:
      service_id = tokens[0]
    unit_id, remote_name = remote_name, unit_id

    xaas.update_relation_properties(env_uuid=env_uuid,
                                    service_id=service_id,
                                    charm_id=charm_id,
                                    relation=relation_name,
                                    relation_id=relation_id,
                                    unit_id=unit_id,
                                    remote_name=remote_name,
                                    action=action,
                                    properties=properties)
