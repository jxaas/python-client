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
    config = Juju.config()
    open_ports = config.get('open-ports', '')
    for open_port in open_ports.split(','):
      open_port = open_port.strip()
      if open_port == "":
        continue
      Juju.open_port(open_port)

    return None

  def on_stop(self):
    return None

  def _run_loadbalancer_hook(self, action):
    logger.info("Running load-balancer hook %s", action)

    host = Juju.private_address()
    config = Juju.config()
    private_port = config['private-port']
    if private_port == 0:
      logger.info("Private port is 0; won't configure load balancer")

    public_port = config['public-port']
    if public_port == 0:
      logger.info("Public port is 0; won't configure load balancer")

    protocol = config.get('protocol', '').strip().lower()

    service_name = Juju.unit_name()
    service_name = service_name.split('/')[0]

    relation = Relation.default()
    relation_id = relation.relation_id

    servers = []
    servers.append(['s_1', host, private_port, ''])

    service_options = [ 'mode tcp', 'balance leastconn' ]
    if protocol == 'tls':
      service_options.append('ssl')
    service = {}
    service['service_name'] = service_name
    service['service_options'] = service_options
    service['servers'] = servers

    # Must set both service_host and service_port, or else haproxy ignores the other
    service['service_host'] = '0.0.0.0'
    service['service_port'] = public_port

    services = []
    services.append(service)

    new_properties = {}
    new_properties['services'] = yaml.dump(services)

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
    # TODO: It would be nice to use our own relation here, rather than reusing the 'website' relation
    if relation_name == 'website':
      return self._run_loadbalancer_hook(action)

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
