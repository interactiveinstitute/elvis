import json
import time
import tornado
import tornado.httpclient

import energy_watch

class PubSub(object):
  def __init__(self):
    self._subscriptions = {}

  def publish(self, data=None, key=None):
    heard = []
    if key in self._subscriptions.keys():
      for listener in self._subscriptions[key]:
        listener(data, key)
        heard.append(listener)
    if None in self._subscriptions.keys():
      for listener in self._subscriptions[None]:
        if not listener in heard:
          listener(data, key)

  def subscribe(self, listener, key=None):
    if key in self._subscriptions.keys():
      subscriptions = self._subscriptions[key]
    else:
      subscriptions = []
      self._subscriptions[key] = subscriptions
    subscriptions.append(listener)

class ZWay(PubSub):
  def __init__(self, server):
    super(ZWay, self).__init__()

    self.server = server
    self.last_timestamp = 0
    self.devices = {}

  def start(self):
    self.get_updates()

  def run(self, command):
    return self._do_http_request('/ZwaveAPI/Run/' + command, 'POST')

  def get_data(self, since=0):
    return self._do_http_request('/ZwaveAPI/Data/%d' % (since))

  def get_updates(self):
    data = json.loads(self.get_data(self.last_timestamp))
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

class Plug(object):
  def __init__(self, id, zway):
    self.id = id
    self.W = 0
    self.W_updateTime = 0
    self.kWh = 0
    self.kWh_updateTime = 0
    self.color = 9
    self.zway = zway
    self.connected = None
    self.set_connected(not self.zway.devices[str(id)]['data']['isFailed']['value'])

    self.zway.subscribe(self.on_fail_update, 'devices.%d.data.isFailed' % id)
    self.zway.subscribe(self.on_power_update, 'devices.%d.instances.0.commandClasses.49.data.4' % id)
    self.zway.subscribe(self.on_power_update, 'devices.%d.instances.0.commandClasses.50.data.2' % id)
    self.zway.subscribe(self.on_energy_update, 'devices.%d.instances.0.commandClasses.50.data.0' % id)
    self.zway.subscribe(self.on_connection_update, 'devices.%d.instances.0.commandClasses.37.data.level' % id)

  def on_power_update(self, data, key):
    self.W = float(data['val']['value'])
    self.W_updateTime = int(data['updateTime'])

  def on_energy_update(self, data, key):
    self.kWh = float(data['val']['value'])
    self.kWh_updateTime = int(data['updateTime'])

  def on_fail_update(self, data, key):
    self.set_connected(not data['value'])

  def on_connection_update(self, data, key):
    self.set_connected(data['value'] > 0)

  def set_connected(self, connected):
    if connected != self.connected:
      self.connected = connected
      print self.id, 'connected?', self.connected

  def get_kWh(self):
    now = time.time()

    seconds_since_kWh_update = self.zway.last_timestamp - self.kWh_updateTime
    # Note: a second or less may have went by since self.watch.last_timestamp.

    kWh = (self.kWh + \
           ((float(seconds_since_kWh_update) / 3600.0) * \
            (float(self.W) / 1000.0)))
    # Note: this may be inaccurate if the power value changed during the last
    # seconds_since_kWh_update. It would be more accurate to store intermediate
    # interpolations on each W update, but for now we just assume that kWh gets
    # updated often enough to correct the value.

    return kWh

  def _set_option(self, register, value):
    command = 'devices[%d].instances[0].commandClasses[112].Set(%d,%d,1)' % \
        (self.id, register, value)
    print 'run:', command
    self.zway.run(command)

  def update_often(self):
    return
    self._set_option(42, 5) # update for every 5 % change in W
    self._set_option(45, 1) # update for every 0.01 kWh

  def _refresh(self, command_class):
    self.zway.run('devices[%d].instances[0].commandClasses[%d].Get()' % (self.id, command_class))
  def refresh_power(self): self._refresh(49) 
  def refresh_energy(self): self._refresh(50)

  def set_color(self, color):
    self.color = color
    self._set_option(61, color)

  def __str__(self):
    return 'plug %s (%s), P = %.2f W, E = %.2f kWh' % \
      (self.id, self.color, self.W, self.kWh)

class EnergyWatch(energy_watch.EnergyWatch):
  plugs = []

  def __init__(self, config):
    self.config = config

    self.zway = ZWay(config.ZWAVE_SERVER)
    self.zway.subscribe(self.update_devices, 'devices')
    self.zway.start()

    loop = tornado.ioloop.IOLoop.instance()
    tornado.ioloop.PeriodicCallback(self.refresh_all_plugs, config.ZWAVE_REFRESH_INTERVAL, loop).start()

  def update_devices(self, devices, key):
    def is_plug(info):
      return info['data']['manufacturerId']['value'] == 271 and info['data']['manufacturerProductType']['value'] == 1536
    for id, info in devices.iteritems():
      if is_plug(info):
        self._get_or_create_plug(int(id))
    self.refresh_all_plugs()

  def refresh_all_plugs(self):
    for plug in self.plugs:
      plug.refresh_energy()

  def _get_or_create_plug(self, id):
    results = [plug for plug in self.plugs if plug.id == id]
    if len(results) == 1:
      return results[0]
    else:
      plug = Plug(id, self.zway)
      plug.set_color(self.config.COLORS[len(self.plugs)][2])
      plug.update_often()
      self.plugs.append(plug)
      return plug

  def measure(self):
    self.zway.get_updates()
    return [plug.get_kWh() for plug in self.plugs]

if __name__ == '__main__':
  import tornado.ioloop

  import config

  watch = EnergyWatch(config)

  def debug():
    print ['%.10f' % val for val in watch.measure()]

  loop = tornado.ioloop.IOLoop.instance()
  tornado.ioloop.PeriodicCallback(debug, config.MEASURE_INTERVAL, loop).start()

  try: loop.start()
  except KeyboardInterrupt: print
