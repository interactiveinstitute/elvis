import json
import time
import tornado
import tornado.httpclient

import energy_watch

class Plug(object):
  def __init__(self, id, watch):
    self.id = id
    self.W = 0
    self.W_updateTime = 0
    self.kWh = 0
    self.kWh_updateTime = 0
    self.color = 9
    self.watch = watch

  def get_kWh(self):
    now = time.time()

    seconds_since_kWh_update = self.watch.last_timestamp - self.kWh_updateTime
    # Note: a second or less may have went by since self.watch.last_timestamp.

    kWh = (self.kWh + \
           ((float(seconds_since_kWh_update) / 3600.0) * \
            (float(self.W) / 1000.0)))
    # Note: this may be inaccurate if the power value changed during the last
    # seconds_since_kWh_update. It would be more accurate to store intermediate
    # interpolations on each W update, but for now we just assume that kWh gets
    # updated often enough to correct the value.
    #
    # Alternatively, call
    #
    #     /ZWaveAPI/Run/devices[DEVICE_ID].instances[0].commandClasses[50].Get()
    #
    # from time to time in order to force a kWh update. We are not doing this
    # yet because it is unclear whether this will overload the network.

    return kWh

  def _set_option(self, register, value):
    command = 'devices[%d].Configuration.Set(%d,%d)' % \
        (self.id, register, value)
    print 'run:', command
    self.watch._run(command)

  def update_often(self):
    self._set_option(42, 5) # update for every 5 % change in W
    self._set_option(45, 1) # update for every 0.01 kWh

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

    self.server = self.config.ZWAVE_SERVER

    self._determine_start_timestamp()

  def _determine_start_timestamp(self):
    first = json.loads(self._get_data(0))['updateTime']
    self.last_timestamp = first - self.config.ZWAVE_START_FROM

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

  def _run(self, command):
    return self._do_http_request('/ZwaveAPI/Run/' + command, 'POST')

  def _get_data(self, since=0):
    return self._do_http_request('/ZwaveAPI/Data/%d' % (since))

  def _get_or_create_plug(self, id):
    results = [plug for plug in self.plugs if plug.id == id]
    if len(results) == 1:
      return results[0]
    else:
      plug = Plug(id, self)
      plug.set_color(self.config.COLORS[len(self.plugs)][2])
      plug.update_often()
      self.plugs.append(plug)
      return plug

  def _get_updates(self):
    data = self._get_data(self.last_timestamp)
    self.data = json.loads(data)
    self.last_timestamp = int(self.data["updateTime"])
    self.last_own_timestamp = time.time()
    for name, value in self.data.iteritems():
      key = name.split('.')
      if key[0] == 'devices' and len(key) > 1 and key[2] == 'instances':
        id = int(key[1])
        instance = int(key[3])
        command = int(key[5])
        data_id = int(key[7])
        plug = self._get_or_create_plug(id)
        utime = int(value['updateTime'])
        if command == 49 or \
            (command == 50 and value['scaleString']['value'] == 'W'): # power
          if utime > plug.W_updateTime:
            plug.W = float(value['val']['value'])
            plug.W_updateTime = utime
        elif command == 50: # energy
          if utime > plug.kWh_updateTime:
            plug.kWh = float(value['val']['value'])
            plug.kWh_updateTime = utime
        print 'updated', plug

  def measure(self):
    self._get_updates()
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
