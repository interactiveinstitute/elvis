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
