var App = require('../static/app');
var Canvas = require('openvg-canvas');
var EventSource = require('eventsource');
var request = require('request');

request('http://localhost:8000/config', function(error, response, body) {
  var config = JSON.parse(body);
  var source = new EventSource('http://localhost:8000/data');
  var canvas = new Canvas;
  var app = new App(config, canvas, source);
});
