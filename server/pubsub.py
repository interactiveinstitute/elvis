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
