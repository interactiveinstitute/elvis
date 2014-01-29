/*
 * This file is part of (e)lVis.
 * Copyright 2013-2014 Interactive Institute Swedish ICT AB.
 *
 * (e)lVis is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * (e)lVis is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with (e)lVis.  If not, see <http://www.gnu.org/licenses/>.
 */

'use strict';

window.requestAnimationFrame = window.requestAnimationFrame || window.webkitRequestAnimationFrame || window.mozRequestAnimationFrame || function(callback) {
  window.setTimeout(callback, 1000 / 60);
};

var init = function(canvas) {
  var app = new App(canvas);

  var connect = function() {
    var request = new XMLHttpRequest();
    request.open('GET', '/config');
    request.onload = function() {
      var config = JSON.parse(this.responseText);
      var source = new EventSource('/data');
      app.setServer(config, source);
      
      addEventListener('keydown', function(event) {
        switch (event.keyCode) {
          case App.KEY.DOWN:
            app.twist(App.DIRECTION.DECREASE);
            break;
          case App.KEY.UP:
            app.twist(App.DIRECTION.INCREASE);
            break;
          case App.KEY.SPACE:
            app.onButtonDown();
            break;
        }
      });
      addEventListener('keyup', function(event) {
        switch (event.keyCode) {
          case App.KEY.SPACE:
            app.onButtonUp();
            break;
        }
      });
    };
    request.send();
  };

  connect();
};
