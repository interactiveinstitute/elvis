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
