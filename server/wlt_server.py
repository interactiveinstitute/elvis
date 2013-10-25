#!/usr/bin/env python

import functools
import json
import pyudev
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
    self.app.subscribe(TwistApp.Topic.TotalEnergy, self.on_total_energy_update)
    self.app.subscribe(TwistApp.Topic.UserInput, self.on_user_input)
    
    if self.app.config.SOURCE == 'fake': self.closed = False
  
  @tornado.web.asynchronous
  def get(self):
    self.set_header('Content-Type', 'text/event-stream')
    self.set_header('Cache-Control', 'no-cache')
    
    if self.app.cached_energy:
      self.send_energy_data(self.app.cached_energy)
    else:
      self.write('event: init\ndata:\n\n')
      self.flush()
      
    if self.app.config.SOURCE == 'fake':
      self.start_time = tornado.ioloop.IOLoop.instance().time()
      self.n_sent = 0
      self.random_data = [0 for circle in self.app.config.CIRCLES.keys()]

      self.send_random_data()
    
  def on_connection_close(self):
    self.app.unsubscribe(TwistApp.Topic.TotalEnergy, self.on_total_energy_update)
    if self.app.config.SOURCE == 'fake': self.closed = True
  
  def on_total_energy_update(self, source, topic, data):
    self.send_energy_data(data)

  def on_user_input(self, source, topic, event):
    self.write('event: %s\ndata: 0\n\n' % event)
    self.flush()
    
  def send_energy_data(self, data):
    self.write('event: energydata\ndata: %s\n\n' % json.dumps(data))
    self.flush()
    
  def send_random_data(self):
    if self.closed: return
    
    self.write('event: energydata\ndata: %s\n\n' % json.dumps(self.random_data))
    self.flush()
    
    for i in range(len(self.random_data)):
      self.random_data[i] += random.random() / 100
    
    self.n_sent += 1
    deadline = self.start_time + self.n_sent * self.app.config.MEASURE_INTERVAL / 1000
    tornado.ioloop.IOLoop.instance().add_timeout(deadline, self.send_random_data)

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

  def __init__(self, config):
    self.config = config
    self.cached_energy = None
    
    tornado.web.Application.__init__(self, [
      (r'/app/(.*)', tornado.web.StaticFileHandler, { 'path': '../static' }),
      (r'/data', DataHandler, { 'app': self }),
      (r'/config', JsonHandler, { 'json': config.CLIENT_CONFIG }),
    ])

    loop = tornado.ioloop.IOLoop.instance()
    self.setup_input()
    if self.input_device:
      self.thread = threading.Thread(target=self.read_input, args=(self.on_input,))
      self.thread.daemon = True
      self.thread.start()
    else:
      print 'no input device'

    # Call .measure_and_publish periodically if sensor data is used.
    if config.SOURCE != 'fake':
      self.watch = None

      tornado.ioloop.PeriodicCallback(self.measure_and_publish, config.MEASURE_INTERVAL, loop).start()

    self.listen(config.HTTP_PORT, '0.0.0.0')

  def setup_input(self):
    context = pyudev.Context()

    self.input_device = None
    self.is_powermate = False
    for device in context.list_devices(subsystem='input'):
      is_powermate = device.get('ID_MODEL') == 'Griffin_PowerMate'
      if ('event' in str(device.get('DEVNAME')) and device.get('ID_INPUT') == '1' and device.get('ID_INPUT_MOUSE') == '1') or \
          (is_powermate and device.get('DEVNAME') and device.get('ID_INPUT') == '1'):
        self.input_device = device
        self.is_powermate = is_powermate

  def read_input(self, callback):
    # Event handling code from http://stackoverflow.com/questions/5060710

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

  def measure_and_publish(self):
    if not self.watch:
      if self.config.SOURCE == 'plugwise':
        from energy_watch_plugwise import EnergyWatch
      elif self.config.SOURCE == 'zway':
        from energy_watch_zwave import EnergyWatch
      self.watch = EnergyWatch(config)
    self.cached_energy = ['%.10f' % val for val in self.watch.measure()]
    self.publish(TwistApp.Topic.TotalEnergy, self.cached_energy)

  def run(self):
    try: tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt: print
    
if __name__ == '__main__':
  import config
  
  TwistApp(config).run()
