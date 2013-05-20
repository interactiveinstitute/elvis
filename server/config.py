# Which system is being used? 'rpi' for Raspberry Pi, 'mba' for MacBook Air.
SYSTEM = 'mba'
if SYSTEM == 'rpi':
  STICK_PORT = '/dev/ttyUSB0'
elif SYSTEM == 'mba':
  STICK_PORT = '/dev/tty.usbserial-A80060FG'

HTTP_PORT = 8000

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

MEASURE_INTERVAL = 1000 # ms

RECOVERY_TIME = 1000 # ms

DRY_RUN = False

CLIENT_CONFIG = {
  "circles": CIRCLES,
  "dry_run": DRY_RUN,
  "display": {
    "padding": 20,
    "lineWidth": 2,
    "minSize": .5
  },
  "watthour": {
    "min": 100,
    "max": 10000,
    "start": 0,
    "step": 100
  },
  "countdown": 100
}
