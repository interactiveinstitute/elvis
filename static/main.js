'use strict';

window.requestAnimationFrame = window.requestAnimationFrame || window.webkitRequestAnimationFrame || window.mozRequestAnimationFrame || function(callback) {
  window.setTimeout(callback, 1000 / 60);
};

var init = function(canvas) {
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
          app.startResetting();
          break;
      }
    });
    addEventListener('keyup', function(event) {
      switch (event.keyCode) {
        case App.KEY.SPACE:
          app.stopResetting();
          break;
      }
    });
  };
  request.send();
};
