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

#   def _client(self):
#     url = config.get('jxaas-url', '')
#     if not url:
#       raise Exception("jxaas-url is required")
#     tenant = config.get('jxaas-tenant', '')
#     if not tenant:
#       raise Exception("jxaas-tenant is required")
#     username = config.get('jxaas-user', '')
#     secret = config.get('jxaas-secret', '')
#     xaas = jujuxaas.client.Client(url=url, tenant=tenant, username=username, password=secret)
#     return xaas

  def _privateclient(self):
    config = Juju.config()
    url = config.get('jxaas-privateurl', '')
    if not url:
      raise Exception("jxaas-privateurl is required")
    tenant = config.get('jxaas-tenant', '')
    if not tenant:
      raise Exception("jxaas-tenant is required")
    username = config.get('jxaas-user', '')
    secret = config.get('jxaas-secret', '')

    client = jujuxaas.privateclient.PrivateClient(url=url, tenant=tenant, username=username, password=secret)
    return client

  def on_start(self):
    # We just defer to on_config_changed - everything should be idempotent
    return self.on_config_changed()

  def on_config_changed(self):
    return None

  def on_stop(self):
    return None

  def _run_loadbalancer_hook(self, action):
    logger.info("Running load-balancer hook %s", action)

    host = Juju.private_address()
    private_port = self.config['private-port']
    public_port = self.config['public-port']

    if private_port == 0:
      logger.info("Private port is 0; won't configure load balancer")

    if public_port == 0:
      logger.info("Public port is 0; won't configure load balancer")

    unit_id = Juju.unit_name()

    relation = Relation.default()
    relation_id = relation.relation_id

    servers = []
    servers.append(['s_1', host, private_port])

    settings = {}
    settings['service_name'] = unit_id + '_' + relation_id
    settings['service_options'] = [ 'mode http', 'balance lastconn' ]
    settings['servers'] = servers

    new_properties = {}
    new_properties['services'] = yaml.dump(settings)

    logger.info("Setting relation properties to: %s", new_properties)
    relation.set_properties(relation_properties.get('Properties', {}))

#     relation-set "services=
#     - { service_name: my_web_app,
#         service_options: [mode http, balance leastconn],
#         servers: [[my_web_app_1, $host, $port, option httpchk GET / HTTP/1.0],
#                   [... optionally more servers here ...]]}
#     - { ... optionally more services here ... }
#     "

    if new_properties:
        logger.info("Setting relation properties to: %s", new_properties)
        relation.set_properties(new_properties)

  def run_relation_hook(self, relation_name, action):
    if relation_name == 'website':
      return self._run_website_hook(action)

    # TODO: Only on certain actions?
    logger.info("Running relation hook %s %s", relation_name, action)

    relation = Relation.default()

    properties = {}
    if not action == "broken":
        properties = relation.get_properties()

    logger.info("Got relation properties %s", properties)

    xaas = self._privateclient()

    config = Juju.config()
    service_name = Juju.service_name()
    unit_id = Juju.unit_name()
    remote_name = os.environ["JUJU_REMOTE_UNIT"]
    relation_id = relation.relation_id

    new_properties = xaas.update_relation_properties(service_name=service_name,
                                                     relation=relation_name,
                                                     relation_id=relation_id,
                                                     unit_id=unit_id,
                                                     remote_name=remote_name,
                                                     action=action,
                                                     properties=properties)

    if new_properties:
        logger.info("Setting relation properties to: %s", new_properties)
        relation.set_properties(new_properties)
