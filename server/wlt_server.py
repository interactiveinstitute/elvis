#!/usr/bin/env python

import json
import random
import time
import tornado.ioloop
import tornado.web

import energy_watch
import util

class DataHandler(tornado.web.RequestHandler):
  def initialize(self, app):
    self.app = app
    self.app.subscribe(TwistApp.Topic.TotalEnergy, self.on_total_energy_update)
    
    if self.app.config.DRY_RUN: self.closed = False
  
  @tornado.web.asynchronous
  def get(self):
    self.set_header('Content-Type', 'text/event-stream')
    self.set_header('Cache-Control', 'no-cache')
    
    if self.app.cached_energy:
      self.send_energy_data(self.app.cached_energy)
    else:
      self.write('event: init\ndata:\n\n')
      self.flush()
      
    if self.app.config.DRY_RUN:
      self.start_time = tornado.ioloop.IOLoop.instance().time()
      self.n_sent = 0
      self.random_data = [0 for circle in self.app.config.CIRCLES.keys()]

      self.send_random_data()
    
  def on_connection_close(self):
    self.app.unsubscribe(TwistApp.Topic.TotalEnergy, self.on_total_energy_update)
    if self.app.config.DRY_RUN: self.closed = True
  
  def on_total_energy_update(self, source, topic, data):
    self.send_energy_data(data)
    
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
  def initialize(self, json):
    self.json = json
    
  def get(self):
    self.set_header('Content-Type', 'application/json')
    self.set_header('Cache-Control', 'no-cache')
    self.write(json.dumps(self.json))

class TwistApp(tornado.web.Application, util.Publisher):
  class Topic:
    TotalEnergy = 1
    
  subscriptions = {}
  cached_energy = None
  
  def __init__(self, config):
    self.config = config
    
    tornado.web.Application.__init__(self, [
      (r'/app/(.*)', tornado.web.StaticFileHandler, { 'path': '../static' }),
      (r'/data', DataHandler, { 'app': self }),
      (r'/config', JsonHandler, { 'json': config.CLIENT_CONFIG }),
    ])

    if not config.DRY_RUN:
      self.watch = None
      
      loop = tornado.ioloop.IOLoop.instance()
      tornado.ioloop.PeriodicCallback(self.measure_and_publish, config.MEASURE_INTERVAL, loop).start()
    
    self.listen(config.HTTP_PORT, '0.0.0.0')
    
  def measure_and_publish(self):
    if not self.watch:
      self.watch = energy_watch.EnergyWatch(config)
    self.cached_energy = ['%.10f' % val for val in self.watch.measure()]
    self.publish(TwistApp.Topic.TotalEnergy, self.cached_energy)
    
  def run(self):
    try: tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt: print
    
if __name__ == '__main__':
  import config
  
  TwistApp(config).run()
