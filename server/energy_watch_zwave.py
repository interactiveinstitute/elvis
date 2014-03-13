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

import datetime
import functools
import json
import tornado

import energy_watch
from pubsub import PubSub
from zway import ZWay
from time import time

class Plug(PubSub):
  def __init__(self, id, zway):
    super(Plug, self).__init__()

    self.id = id
    self.W = -1
    self.color = 9
    self.zway = zway
    self.connected = False
    self.set_connected(not self.zway.devices[str(id)]['data']['isFailed']['value'])
    self.updateTime = 0
    self.configTime = 0
    self.lastdataTime = 0
    self.lastsendTime = 0

    self.zway.subscribe(self.on_fail_update, 'devices.%d.data.isFailed' % id)
    self.zway.subscribe(self.on_update, 'updateTime')
    self.zway.subscribe(self.on_power_update, 'devices.%d.instances.0.commandClasses.49.data.4' % id)
    self.zway.subscribe(self.on_connection_update, 'devices.%d.instances.0.commandClasses.37.data.level' % id)
    self.zway.subscribe(self.on_lastdata_update, 'devices.%d.data.lastReceived' % id)
    self.zway.subscribe(self.on_lastsend_update, 'devices.%d.data.lastSend' % id)
    

  def get_power(self):
    if self.connected:
      return self.W
    else:
      return -1

  def on_power_update(self, data, key):
    old_W = self.W
    self.W = float(data['val']['value'])

    #Store time everytime we get an update.
    self.updateTime = int(data['val']['updateTime'])  

    if self.W != old_W:
      self.publish()
      
  def on_lastdata_update(self,data,key):
    self.lastdataTime = data["updateTime"]
    
    return
  
  def on_lastsend_update(self,data,key):
    self.lastsendTime = data["updateTime"]
    return
  
  
      

  def on_update(self,data,key):
    
    #Check against our last update.
    ThisTime = int(data)
    
    
    #How long ago did we hear from this plug.   
    #TimeSinceHeardOf = ThisTime - self.lastdataTime
    
    #Have we gotten a reply to the last question. 
    #HasReplied = self.lastdataTime >= self.lastsendTime
    
    #if not HasReplied and (TimeSinceHeardOf > 6) :
    TimeSincePowerUpdate = ThisTime - self.updateTime
    
    if TimeSincePowerUpdate > 6:
      changed = self.set_connected(False)
    else:
      changed = self.set_connected(True)
      
    if changed:
      self.publish()
      
    if TimeSincePowerUpdate > 4:
      self.refresh_power()
    
    return

  def on_fail_update(self, data, key):
    self.set_connected(not data['value'])
    self.publish()

  def on_connection_update(self, data, key):
    self.set_connected(data['value'] > 0)
    self.publish()

  def set_connected(self, connected):
    if connected != self.connected:
      self.connected = connected
      if not connected:
        self.W = -1
      else:
        self.configure()
      print self.id, 'connected?', self.connected
      
      return True
    else:
      return False

  def _set_option(self, register, value):
    # Not sure what this parameter does, but this reflects the web interface's behavior
    if value < 3600:
      last_param = 1
    else:
      last_param = 2

    command = 'devices[%d].instances[0].commandClasses[112].Set(%d,%d,%d)' % \
        (self.id, register, value, last_param)
    self.zway.run(command)

  def configure(self):
    
    #Configur only if not configured recently. 
    currentTime = time()
    
    try:
      if (currentTime - self.configTime) < 60:
        return
      else:
        self.configTime = currentTime
    except AttributeError:
        self.configTime = currentTime
    
    print 'configure:', self.id
    self._set_option(1, 0) # plugs always active
    self._set_option(16, 1) # Remembers state after power loss. 
    self._set_option(40, 1) # report power changes immediately starting at 1 %
    self._set_option(42, 1) # report standard power changes starting at 1 %
    self._set_option(43, 255) # send reports  1 ever sec  # only when polling
    self._set_option(47, 3600) #  send unrecorded power reports every hour
    self._set_option(52, 0) # don't turn on or off devices

    # Colors
    self._set_option(61, self.color) # when the device is on
    self._set_option(62, 8) # when the device is off, turn light off
    self._set_option(63, self.color) # z-wave network alarm detection

  def _refresh(self, command_class):
    self.zway.run('devices[%d].instances[0].commandClasses[%d].Get()' % (self.id, command_class))
  def refresh_power(self): self._refresh(49) 

  def set_color(self, color):
    self.color = color

  def __str__(self):
    return 'plug %s (%s), P = %.2f W' % (self.id, self.color, self.W)

class EnergyWatch(energy_watch.EnergyWatch):
  def __init__(self, config, callback):
    self.config = config
    self.callback = callback

    self.plugs = []

    self.zway = ZWay(config.ZWAVE_SERVER)
    self.zway.subscribe(self.update_devices, 'devices')
    self.zway.start()

    self.values = [-1] * self.config.N_PLUGS

    self._configure_all()
    self._request_from_all()

    self._inspect_queue()

  def trigger(self, data=None, key=None):
    old_values = self.values
    self.values = self.collect_values()
    if old_values != self.values:
      self.call_back()

  def call_back(self):
    self.callback(self.collect_values())

  def collect_values(self):
    return [plug.get_power() for plug in self.plugs] + [-1] * max(0, self.config.N_PLUGS - len(self.plugs))

  def update_devices(self, devices, key):
    def is_plug(info):
      return (info['data']['manufacturerId']['value'] == 271 and info['data']['manufacturerProductType']['value'] == 1536) or (info['data']['deviceTypeString']['value'] == 'Binary Power Switch')
    ids = devices.keys()
    ids.sort()
    for id in ids:
      info = devices[id]
      if is_plug(info):
        self._get_or_create_plug(int(id))

  def _get_plug(self, id):
    results = [plug for plug in self.plugs if plug.id == id]
    if len(results) == 1:
      return results[0]
    else:
      return None

  def _get_or_create_plug(self, id):
    plug = self._get_plug(id)
    if plug:
      return plug
    else:
      plug = Plug(id, self.zway)
      plug.set_color(self.config.COLORS[len(self.plugs)][2])
      plug.configure()
      plug.refresh_power()
      plug.subscribe(self.trigger)
      self.plugs.append(plug)
      return plug

  def _configure_all(self):
    print 'configuring all plugs'

    for plug in self.plugs:
      if plug.connected:
        plug.configure()

    dt = datetime.timedelta(milliseconds=self.config.ZWAVE_RECONFIGURE_INTERVAL)
    loop = tornado.ioloop.IOLoop.instance()
    loop.add_timeout(dt, self._configure_all)

  def _request_from_all(self):
    for plug in self.plugs:
      plug.refresh_power()

    dt = datetime.timedelta(milliseconds=self.config.ZWAVE_REFRESH_INTERVAL)
    loop = tornado.ioloop.IOLoop.instance()
    loop.add_timeout(dt, self._request_from_all)

  def _inspect_queue(self):
    try:
      inspection = json.loads(self.zway._do_http_request('/ZWaveAPI/InspectQueue'))

      dt = datetime.timedelta(milliseconds=self.config.ZWAVE_REFRESH_INTERVAL)
      loop = tornado.ioloop.IOLoop.instance()
      loop.add_timeout(dt, self._inspect_queue)
    except TypeError:
      dt = datetime.timedelta(milliseconds=self.config.ZWAVE_REFRESH_INTERVAL)
      loop = tornado.ioloop.IOLoop.instance()
      loop.add_timeout(dt, self._inspect_queue)
      return
    
    result = {}
    for line in inspection:
      id = line[2]
      if line[4]:
        status = line[4].splitlines()[0]
      else:
        status = None

      if status == 'Not delivered to recipient':
        result[id] = False
      elif status == 'Delivered':
        result[id] = True

    for id, status in result.items():
      plug = self._get_plug(id)
      if plug:
        if status == False:
          if plug.connected:
            print 'disconnecting due to failure', id
            plug.set_connected(False)
        else:
          if not plug.connected:
            print 'should be connected', id

if __name__ == '__main__':
  import tornado.ioloop

  import config

  def debug(power):
    print power

  watch = EnergyWatch(config, debug)

  watch.call_back()

  loop = tornado.ioloop.IOLoop.instance()

  try: loop.start()
  except KeyboardInterrupt: print
