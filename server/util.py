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

class Publisher(object):
  subscriptions = {}
    
  def subscribe(self, topic, handler):
    if not topic in self.subscriptions: self.subscriptions[topic] = []
    self.subscriptions[topic].append(handler)
    
  def unsubscribe(self, topic, handler):
    handlers = self.subscriptions[topic]
    for i in range(len(handlers)):
      if handlers[i] is handler:
        del handlers[i]
    
  def publish(self, topic, data):
    if topic in self.subscriptions:
      for handler in self.subscriptions[topic]:
        handler(self, topic, data)
