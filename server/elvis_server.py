#!/usr/bin/env python
#
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

import functools
import json
import random
import struct
import time
import threading
import tornado.ioloop
import tornado.web

import util

class DataHandler(tornado.web.RequestHandler):
  'Sets up an EventSource stream to the client, emitting an energydata event with the measurement list on each update. If there are no measurements yet when the stream is set up, an init event is emitted.'

  def initialize(self, app):
    self.app = app
    self.app.subscribe(TwistApp.Topic.PowerValues, self.on_power_update)
    self.app.subscribe(TwistApp.Topic.UserInput, self.on_user_input)
    
    if self.app.config.SOURCE == 'fake': self.closed = False
  
  @tornado.web.asynchronous
  def get(self):
    self.set_header('Content-Type', 'text/event-stream')
    self.set_header('Cache-Control', 'no-cache')

    self.write('event: init\ndata:\n\n')
    self.flush()
    
    if self.app.cached_power:
      self.send_power_data(self.app.cached_power)
    
  def on_connection_close(self):
    self.app.unsubscribe(TwistApp.Topic.PowerValues, self.on_power_update)
    if self.app.config.SOURCE == 'fake': self.closed = True
  
  def on_power_update(self, source, topic, data):
    self.send_power_data(data)

  def on_user_input(self, source, topic, event):
    self.write('event: %s\ndata: 0\n\n' % event)
    self.flush()
    
  def send_power_data(self, data):
    self.write('event: powerdata\ndata: %s\n\n' % json.dumps(data))
    self.flush()
    
class JsonHandler(tornado.web.RequestHandler):
  'Sends a static JSON string to clients. Used for the configuration object.'

  def initialize(self, json):
    self.json = json
    
  def get(self):
    self.set_header('Content-Type', 'application/json')
    self.set_header('Cache-Control', 'no-cache')
    self.write(json.dumps(self.json))

class TwistApp(tornado.web.Application, util.Publisher):
  'TwistApp sets up an HTTP server that serves energy measurement data.'

  # Topics that TwistApp may publish about. Currently only contais TotalEnergy, which is used by DataHandler instances to receive updates.
  class Topic:
    TotalEnergy = 1
    UserInput = 2
    PowerValues = 3

  def __init__(self, config):
    self.input_device = None
    self.config = config
    self.cached_energy = None
    self.cached_power = None
    
    tornado.web.Application.__init__(self, [
      (r'/app/(.*)', tornado.web.StaticFileHandler, { 'path': '../static' }),
      (r'/data', DataHandler, { 'app': self }),
      (r'/config', JsonHandler, { 'json': config.CLIENT_CONFIG }),
    ])

    loop = tornado.ioloop.IOLoop.instance()
    self.setup_input()
    if self.input_device:
      self.input_thread = threading.Thread(target=self.read_input, args=(self.on_input,))
      self.input_thread.daemon = True
      self.input_thread.start()
    else:
      print 'no input device'

    if self.config.SOURCE == 'zway':
      from energy_watch_zwave import EnergyWatch
    elif self.config.SOURCE == 'fake':
      from energy_watch_fake import EnergyWatch
    self.watch = EnergyWatch(config, self.on_update)

    self.listen(config.HTTP_PORT, '0.0.0.0')

  def on_update(self, data):
    self.cached_power = data
    self.publish(TwistApp.Topic.PowerValues, data)

  def setup_input(self):
    try:
      import pyudev

      context = pyudev.Context()

      self.input_device = None
      self.is_powermate = False
      for device in context.list_devices(subsystem='input'):
        is_powermate = device.get('ID_MODEL') == 'Griffin_PowerMate'
        if ('event' in str(device.get('DEVNAME')) and device.get('ID_INPUT') == '1' and device.get('ID_INPUT_MOUSE') == '1') or \
            (is_powermate and device.get('DEVNAME') and device.get('ID_INPUT') == '1'):
          self.input_device = device
          self.is_powermate = is_powermate
    except ImportError:
      print 'no pyudev found, ignoring mice and powermates'

  def read_input(self, callback):
    # Event handling code from http://stackoverflow.com/questions/5060710
    
    
    #Add some priority to this
    import os
    os.nice(10)

    # long int, long int, unsigned short, unsigned short, unsigned int
    FORMAT = 'llHHl'
    EVENT_SIZE = struct.calcsize(FORMAT)

    in_file = open(self.input_device.get('DEVNAME'), "rb")

    event = in_file.read(EVENT_SIZE)

    while event:
      (tv_sec, tv_usec, type, code, value) = struct.unpack(FORMAT, event)

      if type == 2 and ((code == 8 and not self.is_powermate) or (code == 7 and self.is_powermate)):
        if value == 1:
          tornado.ioloop.IOLoop.instance().add_callback(functools.partial(callback, 'increase'))
        else:
          tornado.ioloop.IOLoop.instance().add_callback(functools.partial(callback, 'decrease'))
      elif type == 1:
        if value == 1:
          tornado.ioloop.IOLoop.instance().add_callback(functools.partial(callback, 'press'))
        else:
          tornado.ioloop.IOLoop.instance().add_callback(functools.partial(callback, 'release'))

      event = in_file.read(EVENT_SIZE)

    in_file.close()

  def on_input(self, event):
    self.publish(TwistApp.Topic.UserInput, event)

  def run(self):
    try: tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt: print
    
if __name__ == '__main__':
  import config
  
  TwistApp(config).run()
