# This file is part of (e)lVis.
# Copyright 2013-2014 Interactive Institute Swedish ICT AB.
#
# (e)lVis is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# (e)lVis is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with (e)lVis.  If not, see <http://www.gnu.org/licenses/>.

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
    self.stalled = []

  def start(self):
    self.get_updates()

    loop = tornado.ioloop.IOLoop.instance()
    tornado.ioloop.PeriodicCallback(self.get_updates, config.MEASURE_INTERVAL, loop).start()

  def run(self, command):
    return self._do_http_request('/ZwaveAPI/Run/' + command, 'POST')

  def get_data(self, since=0):
    return self._do_http_request('/ZwaveAPI/Data/%d' % (since))
    
  def get_data_queue(self):
    return self._do_http_request('/ZWaveAPI/InspectQueue')
    
  def get_plugs_with_stalled_data(self):
    
    Stalled = []
    
    try:
      data = json.loads(self.get_data_queue())
    except TypeError:
      print 'Could not parse data queue'
      return
    
    for f in data:
      if f[1][0] > 1:
        Stalled.append(f[2])

    #self.Stalled = Stalled

    return Stalled

  def get_updates(self):
    try:
      data = json.loads(self.get_data(self.last_timestamp))
    except TypeError:
      print 'Could not parse updates'
      return

    self.last_timestamp = int(data['updateTime'])
    self.last_own_timestamp = time.time()
    
    self.stalled = self.get_plugs_with_stalled_data()

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

if __name__ == '__main__':
  # Test the ZWay implementation

  zway = ZWay(config.ZWAVE_SERVER)

  def update_devices(devices, key):
    def is_plug(info):
      return info['data']['manufacturerId']['value'] == 271 and \
        info['data']['manufacturerProductType']['value'] == 1536
    for str_id, info in devices.iteritems():
      if is_plug(info):
        id = int(str_id)

        print 'device', id

        color_id = 0 # red
        color = config.COLORS[color_id][2]
        set_option(id, 61, color) # when the devices is on
        #set_option(id, 62, 8) # when the device is off, turn light off
        set_option(id, 62, 8) # when the device is off, turn light off
        set_option(id, 63, color) # z-wave network alarm detection

  zway.subscribe(update_devices, 'devices')

  def set_option(id, register, value):
    command = 'devices[%d].instances[0].commandClasses[112].Set(%d,%d,1)' % \
        (id, register, value)
    zway.run(command)

  zway.start()
