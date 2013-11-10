# Which system is being used? 'rpi' for Raspberry Pi, 'mba' for MacBook Air.
SYSTEM = 'mba'
if SYSTEM == 'rpi':
  STICK_PORT = '/dev/ttyUSB0'
elif SYSTEM == 'mba':
  STICK_PORT = '/dev/tty.usbserial-A80060FG'

# Port from which to serve the interface.
HTTP_PORT = 8000

# MAC addresses and colors for Plugwise Circle plugs.
CIRCLES = {
  '000D6F0000AF6437': '#ff0000', # red
  '000D6F0000D32407': '#0000ff', # blue
  '000D6F00039745FC': '#00ff00', # green
  '000D6F00039745F1': '#ffff00', # yellow
  '000D6F000397AB06': '#ff00ff', # purple
#  '000D6F00039790A4': '#ff8900', # orange doesn't work
  '000D6F00039744C0': '#ff007f', # pink
  '000D6F00039790A3': '#aaaaaa', # gray
}

# Interval at which to poll the Circles.
MEASURE_INTERVAL = 50 # ms

# The source can be 'zway', 'plugwise' or 'fake'.
SOURCE = 'zway' #'fake'

COLORS = [ # name, rgb (hex), fibaro
  ['red',    '#ff0000', 3],
  ['blue',   '#0000ff', 5],
  ['green',  '#00ff00', 4],
  ['yellow', '#ffff00', 6],
  ['purple', '#ff00ff', 8],
  ['cyan',   '#99cccc', 7],
  ['white',  '#aaaaaa', 2]
]

# A configuration JSON object sent to the client.
CLIENT_CONFIG = {
#  "circles": CIRCLES,
  "colors": COLORS,
  "dry_run": SOURCE == 'fake',
  "display": {
    "padding": 20,
    "lineWidth": 2,
    "minSize": .5
  },
  "watthour": {
    "min": 10,
    "max": 10000,
    "start": 0,
    "step": 10
  },
  "countdown": 100
}

# Zway 
ZWAVE_SERVER = 'localhost:8083'
ZWAVE_START_FROM = 60 * 60 # seconds before now to use for the first query
ZWAVE_TRY_IDS = range(2, 12) # device IDs to try contacting
ZWAVE_REFRESH_INTERVAL = 1000
ZWAVE_INTERPOLATE = False
