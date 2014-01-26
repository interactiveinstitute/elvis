(e)lVis
=======

An adaptation of Watt-Lite Twist for Energy in a Box at KomTek [1]. It allows
users to choose an amount of watt-hours, measure how that amount is being
used up by multiple devices and look how the usage is distributed between
those devices.

Created at Interactive Institute in Eskilstuna [2].

[1]: https://www.tii.se/projects/energy-in-a-box-at-komtek
[2]: https://www.tii.se/contact/eskilstuna


How it works
------------

An (e)lVis setup consists of a Python web server that streams power
measurements and a JavaScript client. The client can run either in the
web browser or in Node. 

The web app has been tested in Chrome and Firefox. On Mac, it works
better in Chrome.

The Node version runs on a Raspberry Pi.

There are three implementations: `plugwise`, `zwave` and `fake`. The
`zwave` and `fake` implementations have been tested recently.


How to set up your environment
------------------------------

On a Raspberry Pi, run `tools/install.sh` to make the Node implementation
work. Otherwise, just make sure you have `python-serial` installed.


How to test it
--------------

1. Edit `config.py` to suit your needs. You may want to edit the `SOURCE`
   variable to switch between implementations.
2. Run: `cd server && ./elvis_server.py`.
3. Either open `http://localhost:8000/app/index.html` in your web browser
   or run `client/client.js` using Node (`~/node/0/bin/node` on RPi).


How to use it
-------------

Using the web interface:

1. When the _twist to start_ message is spinning, use the ↑↓ arrow keys
   to set the amount of kWh to use.
2. Connect and use devices on multiple sensor plugs.
3. Look at the changing pie chart. Keep the space bar pressed to see
   another display mode.

At any time, the arrow keys can be used to start over with another amount
of kWh.

In the Node interface, use a mouse wheel and mouse buttons instead.


How to set up autorun
---------------------

    sudo cp ~/git/elvis/tools/elvis /etc/init.d/elvis
    sudo chmod 755 /etc/init.d/elvis
    sudo update-rc.d elvis defaults

Kill it using `sudo service wltl stop`.


Where to find things
--------------------

All Python scripts are in `server/`:

- The `energy_watch*` modules will collect and make available accumulated
  energy measured in the sensors. As long as the server runs, these values
  will increase. It is up to the client to reset set a zero value based on
  when the interaction starts.
- In `util` the `Publisher` class is defined that implements a small pubsub
  system.
- The main program is in `elvis_server.py` and sets up a Tornado web server.
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

The Node client is in `client/client.js`. It provides a UI to `static/app.js`.
Mouse events are gathered using udev in `client/mouse.js`.


How to debug
------------

Use your browser’s Developer Tools to debug the interface. If you’re
confident that the sensor measurements work already, set `SOURCE = 'fake'`
in `config.py` to speed things up.

Check the (real or fake) datastream using
`curl http://localhost:8000/data`.
