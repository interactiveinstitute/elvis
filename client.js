var Canvas = require('canvas/canvas');
var EventSource = require('eventsource');
var request = require('request');

request('http://localhost:8000/config', function(error, response, body) {
  var width = 1920;
  var height = 1080;
  var config = JSON.parse(body);
  var source = new EventSource('http://localhost:8000/data');
  var canvas = new Canvas(width, height);
  var app = new App(config, canvas, source);
});

/*
var request = new XMLHttpRequest();
request.open('GET', '/config');
request.onload = function() {
  var config = JSON.parse(this.responseText);
  var source = new EventSource('/data');
  var app = new App(config, canvas, source);
  
  addEventListener('keydown', function(event) {
    switch (event.keyCode) {
      case App.KEY.DOWN:
        app.twist(App.DIRECTION.DECREASE);
        break;
      case App.KEY.UP:
        app.twist(App.DIRECTION.INCREASE);
        break;
      case App.KEY.SPACE:
        app.toggleDetails(true);
        break;
    }
  });
  addEventListener('keyup', function(event) {
    switch (event.keyCode) {
      case App.KEY.SPACE:
        app.toggleDetails(false);
        break;
    }
  });
};
request.send();
*/