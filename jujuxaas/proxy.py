import os
import time
import yaml

from jujucharmtoolkit.juju import Juju, Relation
import jujuxaas.auth.direct
import jujuxaas.auth.openstack
import jujuxaas.client
from jujuxaas import utils

import logging
logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.DEBUG)

def run_relation_hook(interface_id=None):
    relation_name = os.environ["JUJU_RELATION"]
    juju_action = Juju.action()
    proxy = Proxy()
    return proxy.run_relation_hook(relation_name, juju_action, interface_id=interface_id)

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
    authmode = config.get('jxaas-authmode', '')
    tenant = config.get('jxaas-tenant', '')
    if not tenant:
      raise Exception("jxaas-tenant is required")
    username = config.get('jxaas-user', '')
    secret = config.get('jxaas-secret', '')

    authmode = authmode.strip().lower()
    if authmode == 'openstack':
      auth = jujuxaas.auth.openstack.AuthOpenstack(url=url, tenant=tenant, username=username, password=secret)
    else:
      auth = jujuxaas.auth.direct.AuthDirect(url=url, tenant=tenant, username=username, password=secret)

    xaas = jujuxaas.client.Client(auth)
    return xaas

  @property
  def config(self):
    if not self._cache_config:
      config_path = os.path.join(os.environ.get("CHARM_DIR", ""), "proxy.yaml")
      with open(config_path) as f:
        self._cache_config = yaml.load(f)
    return self._cache_config

  def on_start(self):
    # Install the stunnel4 package
    utils.apt_get_install(['stunnel4'])

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
      logger.info("Waiting for service to reach active state.  Current state %s", service.get('Status'))
      time.sleep(5)
      service = xaas.get_instance_state(bundle_type=bundle_type, instance_id=instance_id)

    return service

  def on_stop(self):
    # TODO: Stop service?
    xaas = self._client()
    # service = xaas.ensure_instance(charm=self.charm, instance_id=instance_id, env_uuid=env_uuid)

  def run_relation_hook(self, relation_name, action, interface_id=None):
    logger.info("Running relation hook %s %s", relation_name, action)

    # TODO: Only on certain actions?
    if action == 'broken':
        return

    xaas = self._client()

    bundle_type = self.config['charm']
    instance_id = Juju.service_name()

    if interface_id is None:
      interface_id = instance_id

    logger.info("Fetching service properties for %s/%s/%s",
                bundle_type, instance_id, interface_id)
    response = xaas.get_relation_properties(bundle_type=bundle_type,
                                            instance_id=instance_id,
                                            relation=interface_id)

    relation_properties = response.get('Properties', {})

    protocol = relation_properties.get('protocol')
    if protocol == 'tls':
      relation_properties = self._ensure_tls(bundle_type, relation_properties)

    relation = Relation.default()

    logger.info("Setting relation properties to: %s", relation_properties)
    relation.set_properties(relation_properties)

  def _get_default_port(self, bundle_type):
    if bundle_type == 'mysql':
      return 3306
    if bundle_type == 'postgres':
      return 5432
    logger.warn("Unknown bundle_type in _get_default_port (%s), defaulting to 9999", bundle_type)
    return 9999

  def _ensure_tls(self, bundle_type, properties):
    # TODO: We could create some system properties here, that work everywhere
    host = properties.get('host') or properties.get('private-address')
    port = properties.get('port')

    logger.info("Properties before rewrite: %s" % properties)

    default_port = self._get_default_port(bundle_type)

    # By using the default_port again, we can make things easier for clients
    # that don't support the port
    accept = '0.0.0.0:' + str(default_port)
    connect = host + ':' + str(port)

    stunnel_config = """
client=yes

[tlswrap]
accept=%s
connect=%s
""" % (accept, connect)

    changed = False
    if utils.write_file('/etc/stunnel/tlswrap.conf', stunnel_config):
      changed = True

    if utils.update_keyvalue('/etc/default/stunnel4', { 'ENABLED': '1' }):
      changed = True

    if changed:
      utils.run_command(['/etc/init.d/stunnel4', 'start'])
      utils.run_command(['/etc/init.d/stunnel4', 'reload'])

    if 'hopst' in properties:
      properties['host'] = Juju.private_address()
    if 'private-address' in properties:
      properties['private-address'] = Juju.private_address()
    properties['port'] = str(default_port)

    logger.info("Properties after rewrite: %s" % properties)

    return properties

