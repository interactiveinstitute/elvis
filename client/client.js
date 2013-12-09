var App = require('../static/app');
var Canvas = require('openvg-canvas');
var EventSource = require('eventsource');
var request = require('request');

var init = function() {
  request({
    url: 'http://localhost:8000/config',
    timeout: 1000
  }, function(error, response, body) {
    if (error) {
      console.log('Could not contact the Python server. Trying again in 1s...');
      setTimeout(init, 1000);
    } else {
      var config = JSON.parse(body);
      var source = new EventSource('http://localhost:8000/data');
      var canvas = new Canvas;
      var app = new App(config, canvas, source);
    }
  });
};

init();
