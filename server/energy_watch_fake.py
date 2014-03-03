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
import random
import tornado

import energy_watch

class EnergyWatch(energy_watch.EnergyWatch):
  def __init__(self, config, callback):
    self.callback = callback

    #self.values = [1000 for color in config.COLORS][:config.N_PLUGS]
    self.values = [1000, 0, 0, 0, 0]
    #self.values[random.randint(0, config.N_PLUGS - 1)] = -1

    #self.trigger()
    self.callback(self.values)

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

    loop = tornado.ioloop.IOLoop.instance()
    loop.add_callback(functools.partial(self.callback, self.values))

    dt = datetime.timedelta(seconds=random.uniform(0.05, 1))
    loop = tornado.ioloop.IOLoop.instance()
    loop.add_timeout(dt, self.trigger)
