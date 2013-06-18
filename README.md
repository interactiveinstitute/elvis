Watt-Lite Twist Lite
====================

An adaptation of Watt-Lite Twist for Energy in a Box på KomTek. It allows
users to choose an amount of watt-hours, measure how that amount is being
used up by multiple devices and look how the usage is distributed between
those devices.


How it works
------------

A WLTL setup consists of a Python web server that streams power
measurements and a JavaScript client. The client can run either in the
web browser or in Node. 

The web app has been tested in Chrome and Firefox. On Mac, it works
better in Chrome.

The Node version requires the `node-openvg-canvas` package and is meant
to run on a Raspberry Pi.


How to set it up
----------------

1. Edit `config.py` to suit your needs.
2. Run: `cd server && ./wlt_server.py`.
3. Either open `http://localhost:8000/app/index.html` in your web browser
   or run `client.js` using Node.


How to use it
-------------

1. When the _twist to start_ message is spinning, use the ↑↓ arrow keys
   to set the amount of kWh to use.
2. Connect and use devices on multiple sensor plugs.
3. Look at the changing pie chart. Keep the space bar pressed to see
   another display mode.

At any time, the arrow keys can be used to start over with another amount
of kWh.


Where to find things
--------------------

All Python scripts are in `server/`:

- The `energy_watch*` modules will collect and make available accumulated
  energy measured in the sensors. As long as the server runs, these values
  will increase. It is up to the client to reset set a zero value based on
  when the interaction starts.
- In `util` the `Publisher` class is defined that implements a small pubsub
  system.
- The main program is in `wlt_server.py` and sets up a Tornado web server.
  This server serves three types of data:
  1. The app in the `static/` directory.
  2. The `CLIENT_CONFIG` config variable.
  3. An EventSource stream with an array of energy values.

The most interesting JavaScript happens in `static/`:

- The `App` class in `app.js` defines all drawing logic.
- In `index.html` and `main.js` an HTML DOM environment is set up to work
  with `App`.
- The alternative, static setup in `index_demo.html` can be used for showing
  a static demo, e.g. to take a picture.

The Node client is in `client.js`. It provides a UI to `static/app.js`.


How to debug
------------

Use your browser’s Developer Tools to debug the interface. If you’re
confident that the sensor measurements work already, set `DRY_RUN = True`
in `config.py` to speed things up.

Check the (real or fake) datastream using
`curl http://localhost:8000/data`.
