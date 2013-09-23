import json
import time
import tornado
import tornado.httpclient

import energy_watch

class Plug(object):
  def __init__(self, id):
    self.id = id
    self.W = 0
    self.W_updateTime = 0
    self.kWh = 0
    self.kWh_updateTime = 0
    self.color = '#ffffff'

  def get_kWh(self):
    return self.kWh # TODO extrapolate using self.W and the updateTimes

  def __str__(self):
    return 'Plug %s (%s), P = %.2f W, E = %.2f kWh' % \
      (self.id, self.color, self.W, self.kWh)

class EnergyWatch(energy_watch.EnergyWatch):
  plugs = []

  def __init__(self, config):
    self.config = config

    self.server = self.config.ZWAVE_SERVER
    self.last_timestamp = int(time.time()) - 60 * 60
    # TODO find a usable value here
    #0 #int(time.time()) #1379269331

  def _do_http_get(self, path):
    response = None
    http_client = tornado.httpclient.HTTPClient()
    try:
      response = http_client.fetch('http://%s%s' % (self.server, path)).body
    except tornado.httpclient.HTTPError as e:
      print 'Error:', e
    http_client.close()
    return response

  def _get_data(self, since=0):
    response = self._do_http_get('/ZwaveAPI/Data/%i' % (since))
    return response

  def _get_or_create_plug(self, id):
    results = [plug for plug in self.plugs if plug.id == id]
    if len(results) == 1:
      return results[0]
    else:
      plug = Plug(id)
      plug.color = self.config.COLORS[len(self.plugs)]
      # TODO set plug LED color
      self.plugs.append(plug)
      return plug

  def _get_updates(self):
    data = self._get_data(self.last_timestamp)
    self.data = json.loads(data)
    self.last_timestamp = int(self.data["updateTime"])
    for name, value in self.data.iteritems():
      key = name.split('.')
      if key[0] == 'devices' and len(key) > 1 and key[2] == 'instances':
        id = key[1]
        instance = key[3]
        command = key[5]
        plug = self._get_or_create_plug(id)
        print plug
        if command == '49': # power
          plug.W = float(value['val']['value'])
          plug.W_updatetime = int(value['updateTime'])
        elif command == '50': # energy
          plug.kWh = float(value['val']['value'])
          plug.kWh_updatetime = int(value['updateTime'])

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
