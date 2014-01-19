import datetime
import random
import tornado

import energy_watch

class EnergyWatch(energy_watch.EnergyWatch):
  def __init__(self, config, callback):
    self.callback = callback

    self.values = [1000 for color in config.COLORS][:config.N_PLUGS]
    self.values[random.randint(0, config.N_PLUGS - 1)] = -1

    self.trigger()

  def trigger(self):
    index = random.randrange(len(self.values))
    if random.randint(0, 5) == 0:
      if self.values[index] == -1:
        self.values[index] = random.uniform(900, 1100)
      else:
        self.values[index] = -1
    elif self.values[index] != -1:
      self.values[index] = max(0, round(self.values[index] + random.uniform(-100, 100), 1))
    self.values[2] = -1
    self.callback(self.values)

    dt = datetime.timedelta(seconds=random.uniform(0.05, 1))
    loop = tornado.ioloop.IOLoop.instance()
    loop.add_timeout(dt, self.trigger)
