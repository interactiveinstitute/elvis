var App = require('../static/app');
var Canvas = require('openvg-canvas');
var EventSource = require('eventsource');
var Mouse = require('./mouse');
var request = require('request');

var mouse = new Mouse;

request('http://localhost:8000/config', function(error, response, body) {
  var config = JSON.parse(body);
  var source = new EventSource('http://localhost:8000/data');
  var canvas = new Canvas;
  var app = new App(config, canvas, source);

setTimeout(function() {
  app.twist(App.DIRECTION.INCREASE);
  app.twist(App.DIRECTION.INCREASE);
  app.twist(App.DIRECTION.INCREASE);
}, 3000);

  mouse.on('scroll', function(direction) {
    if (direction == 1)
      app.twist(App.DIRECTION.INCREASE);
    else
      app.twist(App.DIRECTION.DECREASE);
  });
  mouse.on('press', function() {
    app.toggleDetails(true);
  });
  mouse.on('release', function() {
    app.toggleDetails(false);
  });
});
