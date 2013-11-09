import functools
import tornado

import energy_watch
from pubsub import PubSub
from zway import ZWay

class Plug(PubSub):
  def __init__(self, id, zway):
    super(Plug, self).__init__()

    self.id = id
    self.W = 0
    self.color = 9
    self.zway = zway
    self.connected = None
    self.set_connected(not self.zway.devices[str(id)]['data']['isFailed']['value'])

    self.zway.subscribe(self.on_fail_update, 'devices.%d.data.isFailed' % id)
    self.zway.subscribe(self.on_power_update, 'devices.%d.instances.0.commandClasses.49.data.4' % id)
    self.zway.subscribe(self.on_connection_update, 'devices.%d.instances.0.commandClasses.37.data.level' % id)

  def on_power_update(self, data, key):
    self.W = float(data['val']['value'])
    self.publish()

  def on_fail_update(self, data, key):
    self.set_connected(not data['value'])

  def on_connection_update(self, data, key):
    self.set_connected(data['value'] > 0)
    self.publish()

  def set_connected(self, connected):
    if connected != self.connected:
      self.connected = connected
      print self.id, 'connected?', self.connected

  def _set_option(self, register, value):
    command = 'devices[%d].instances[0].commandClasses[112].Set(%d,%d,1)' % \
        (self.id, register, value)
    print 'run:', command
    self.zway.run(command)

  def configure(self):
    self._set_option(40, 1) # report power changes immediately starting at 1 %
    self._set_option(42, 1) # report standard power changes starting at 1 %
    self._set_option(43, 255) # send reports only when polling
    self._set_option(47, 3600) # send unrecorded power reports every hour
    self._set_option(52, 0) # don't turn on or off devices

  def _refresh(self, command_class):
    self.zway.run('devices[%d].instances[0].commandClasses[%d].Get()' % (self.id, command_class))
  def refresh_power(self): self._refresh(49) 

  def set_color(self, color):
    self.color = color
    self._set_option(61, color)
    self._set_option(62, color)
    self._set_option(63, color)

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

    self.values = []

  def trigger(self, data=None, key=None):
    old_values = self.values
    self.values = [plug.W for plug in self.plugs]
    if old_values != self.values:
      self.call_back()

  def call_back(self):
    self.callback([plug.W for plug in self.plugs])

  def update_devices(self, devices, key):
    def is_plug(info):
      return info['data']['manufacturerId']['value'] == 271 and info['data']['manufacturerProductType']['value'] == 1536
    for id, info in devices.iteritems():
      if is_plug(info):
        self._get_or_create_plug(int(id))

  def _get_or_create_plug(self, id):
    results = [plug for plug in self.plugs if plug.id == id]
    if len(results) == 1:
      return results[0]
    else:
      plug = Plug(id, self.zway)
      plug.set_color(self.config.COLORS[len(self.plugs)][2])
      plug.configure()
      plug.refresh_power()
      plug.subscribe(self.trigger)
      self.plugs.append(plug)
      return plug

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
