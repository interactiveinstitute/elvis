import datetime
import random
import tornado

import energy_watch

class EnergyWatch(energy_watch.EnergyWatch):
  def __init__(self, config, callback):
    self.callback = callback

    self.values = [1000 for color in config.COLORS]

    self.trigger()

  def trigger(self):
    index = random.randrange(len(self.values))
    self.values[index] = max(0, self.values[index] + random.uniform(-100, 100))
    self.callback(self.values)

    dt = datetime.timedelta(seconds=random.uniform(0.05, 1))
    loop = tornado.ioloop.IOLoop.instance()
    loop.add_timeout(dt, self.trigger)
