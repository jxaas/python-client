import copy
import select
import socket
import ssl
import sys
import threading

import logging
logger = logging.getLogger(__name__)

class TlsProxyConnection(object):
  def __init__(self, server, inbound_socket, inbound_address, outbound_address):
    self.server = server
    self.inbound_socket = inbound_socket
    self.inbound_address = inbound_address
    self.outbound_socket = None
    self.outbound_address = outbound_address
    self.thread = None

  def start(self):
    self.thread = threading.Thread(target=self._proxy)
    self.thread.daemon = True
    self.thread.start()

  def _proxy(self):
    try:
      self.outbound_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      self.outbound_socket = self.server._wrap_ssl(self.outbound_socket)
      self.outbound_socket.connect(self.outbound_address)
      logger.debug("Proxy for %s: connected to remote", self.inbound_address)
      
      pairs = {}
      pairs[self.inbound_socket] = self.outbound_socket
      pairs[self.outbound_socket] = self.inbound_socket
      
      selectors = [self.inbound_socket, self.outbound_socket]
      while True:
        ready, _, _ = select.select(selectors, [], [])
        for s in ready:
          data = s.recv(8192)
          if len(data) == 0:
            # Close
            break
          else:
            other = pairs[s]
            other.send(data)
    except:
      logger.warn("Proxy for %s: error: %s", self.inbound_address, sys.exc_info())
    finally:
      logger.debug("Proxy for %s: closing", self.inbound_address)
      self.inbound_socket.close()
      if self.outbound_socket:
        self.outbound_socket.close()  

class TlsProxy(object):
  def __init__(self, ssl_context, listen_address, forward_address):
    self.listen_address = listen_address
    self.forward_address = forward_address
    self.ssl_context = ssl_context
    self._ready = threading.Event()
  
  def _serve(self):
    server = None
    try:
      server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
      server.bind(self.listen_address)
      server.listen(50)
  
      self._ready.set()
      
      while True:
        client, client_address = server.accept()
        proxy = TlsProxyConnection(self, client, client_address, self.forward_address)
        proxy.start()
    finally:
      if server:
        server.close()
        
  def start(self):
    self.thread = threading.Thread(target=self._serve)
    self.thread.daemon = True
    self.thread.start()
    self._ready.wait()
    
  def _wrap_ssl(self, socket):
    options = copy.copy(self.ssl_context)
    options['sock'] = socket
    return ssl.wrap_socket(**options)
