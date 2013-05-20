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