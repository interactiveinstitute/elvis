class EnergyWatch(object):
  'Return the accumulated energy in the configured plugs on .measure()'

  def __init__(self, config):
    'Configure the sensor'
    raise NotImplementedError

  def measure(self):
    'Return a list of the accumulated amount of kWh of each configured plug'
    raise NotImplementedError
