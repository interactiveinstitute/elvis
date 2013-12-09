import json
import time
import tornado
import tornado.httpclient

import config
from pubsub import PubSub

class ZWay(PubSub):
  """Interface to the ZWay API. Publishes updates from
  /ZwaveAPI/Data as a PubSub instance and keeps track of
  info about connected devices."""

  def __init__(self, server):
    super(ZWay, self).__init__()

    self.server = server
    self.last_timestamp = 0
    self.devices = {}

  def start(self):
    self.get_updates()

    loop = tornado.ioloop.IOLoop.instance()
    tornado.ioloop.PeriodicCallback(self.get_updates, config.MEASURE_INTERVAL, loop).start()

  def run(self, command):
    return self._do_http_request('/ZwaveAPI/Run/' + command, 'POST')

  def get_data(self, since=0):
    return self._do_http_request('/ZwaveAPI/Data/%d' % (since))

  def get_updates(self):
    try:
      data = json.loads(self.get_data(self.last_timestamp))
    except TypeError:
      print 'Could not parse updates'
      return

    self.last_timestamp = int(data['updateTime'])
    self.last_own_timestamp = time.time()

    for key, data in data.iteritems():
      if key == 'devices':
        self.devices = data
      self.publish(data, key)

  def _do_http_request(self, path, method='GET'):
    response = None
    http_client = tornado.httpclient.HTTPClient()
    try:
      url = 'http://%s%s' % (self.server, path)
      if method == 'POST':
        body = ''
      else:
        body = None
      result = http_client.fetch(url, method=method, body=body)
      response = result.body
    except tornado.httpclient.HTTPError as e:
      print 'Error:', e
    except AssertionError as e:
      print 'Assertion error:', e
    http_client.close()
    return response
