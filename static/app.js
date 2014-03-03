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

var sum = function(a, b) { return a + b; };

var map = function(fn, t, imin, ival, omin, omax) {
  return omin + (omax - omin) * fn((t - imin) / (ival - (imin % ival)) % 1);
};

var easeInOutCubic = function(t) {
  // Based on https://gist.github.com/gre/1650294
  return t < .5 ? 4*t*t*t*t : (t-1)*(2*t-2)*(2*t-2)+1;
};

var easeOutQuart = function(t) {
  // Based on https://gist.github.com/gre/1650294
  return 1-(--t)*t*t*t;
};

var easeInOutCirc = function(t) {
  // Based on http://www.gizma.com/easing/
  return t < .5 ? -.5 * (Math.sqrt(1 - 4 * t*t) - 1) : .5 * (Math.sqrt(1 - (t*2-2)*(t*2-2)) + 1);
};

var easeOutElastic = function(t, b, c, d, a, p) {
  // Based on http://www.dzone.com/snippets/robert-penner-easing-equations
  b = 0; // beginning value
  c = 1; // change in value
  d = 1; // duration
  a = 1; // amplitude
  p = .3; // period
 
  if (t == 0) return b;
  if ((t /= d) == 1) return b + c;
  if (!p) p = d * .3;
  if (a < Math.abs(c)) {
    a = c;
    var s = p / 4;
  } else
    var s = p / ( 2 * Math.PI) * Math.asin(c / a);
  return a * Math.pow(2, -10 * t) * Math.sin((t * d - s) * (2 * Math.PI) / p) + c + b;
};

var linear = function(t) { return t; };

var App = function() {
  this.construct.apply(this, arguments);
};

App.KEY = {
  DOWN: 40,
  UP: 38,
  SPACE: 32
};

App.STATE = {
  IDLE: 0,
  INITIALIZING: 1,
  INTRO: 2,
  WINDING: 3,
  PROGRESS: 4,
  FINISHED: 5,
  RESETTING: 6
};

App.DIRECTION = {
  INCREASE: 0,
  DECREASE: 1
};

App.prototype.construct = function(canvas) {
  this.canvas = canvas;
  
  this.drawUtil = {
    width: this.canvas.width,
    height: this.canvas.height,
    cx: this.canvas.width / 2,
    cy: this.canvas.height / 2,
    colors: []
  };

  this.setState(App.STATE.INITIALIZING);
    
  this.draw(+new Date);
};

App.prototype.setServer = function(config, source) {
  this.config = config;
  this.config.colors.forEach(function(values, i) {
    this.drawUtil.colors[i] = values[1];
  }, this);

  this.measure = this.config.watthour.min;
  this.input = Math.sqrt(this.measure / this.config.watthour.mapping);

  this.watts = [];
  this.lastUsedUpdate = 0;
  this.used = [];
  this.wasConnected = [];
  for (var i = 0; i < config.nPlugs; i++) {
    this.watts[i] = -1;
    this.used[i] = 0;
    this.wasConnected[i] = false;
  }

  // In most cases, the maximum amount of watthours cannot be reached exactly.
  // Therefore, we assume the maximum when the value should actually be just
  // over the maximum. The previous value is then stored as beforeMaximum.
  this.beforeMaximum = -1;

  source.addEventListener('init', function(event) {
    this.setState(App.STATE.INTRO);
  }.bind(this));
  source.addEventListener('powerdata', function(event) {
    var data = JSON.parse(event.data).map(parseFloat);
    this.watts = data;

    for (var i = 0; i < this.watts.length; i++)
      if (this.watts[i] != -1) this.wasConnected[i] = true;

    if (this.state == App.STATE.INITIALIZING) this.setState(App.STATE.INTRO);
    if (this.state == App.STATE.PROGRESS ||
        (this.state == App.STATE.RESETTING &&
         this.preResetState == App.STATE.PROGRESS)) this.updateUsed();
  }.bind(this));
  source.addEventListener('increase', function(event) {
    this.twist(App.DIRECTION.INCREASE);
  }.bind(this));
  source.addEventListener('decrease', function(event) {
    this.twist(App.DIRECTION.DECREASE);
  }.bind(this));
  source.addEventListener('press', function(event) {
    this.onButtonDown();
  }.bind(this));
  source.addEventListener('release', function(event) {
    this.onButtonUp();
  }.bind(this));
};

App.prototype.round = function(Wh) {
  return Wh.toFixed(3);
};

App.prototype.updateUsed = function() {
  if (this.lastUsedUpdate == 0) {
    this.lastUsedUpdate = +new Date;
  } else {
    var now = +new Date;
    var millis = now - this.lastUsedUpdate;
    var watts = this.watts;
    for (var i = 0; i < this.watts.length; i++) {
      if (watts[i] != -1) {
        var add = watts[i] / 1000.0 / 3600.0;
        this.used[i] = (this.used[i] || 0) + add;
      }
    }
    this.lastUsedUpdate = now;

    var total = this.used.reduce(sum);
    if (total > this.measure) {
      var factor = this.measure / total;
      this.used = this.used.map(function(Wh) { return Wh * factor; });
      this.end = +new Date;
      this.setState(App.STATE.FINISHED);
    }
  }
};

App.prototype.setState = function(state) {
  var name = Object.keys(App.STATE).filter(function(key, i) { return i == state; })[0];
  console.log('state:', name);
  this.previousState = this.state || App.STATE.IDLE;
  this.drawUtil.t0 = +new Date;
  this.state = state;
};

App.prototype.twist = function(direction) {
  if (this.state == App.STATE.INTRO) {
    this.buttonPressed = 0;
    this.setState(App.STATE.WINDING);
  }
  if (this.state != App.STATE.WINDING) return;

  if (direction == App.DIRECTION.DECREASE) var factor = -1;
  else if (direction == App.DIRECTION.INCREASE) var factor = 1;
  
  if (this.countdown) clearTimeout(this.countdown);
  
  var newInput = this.input + factor;
  var newMeasure = this.config.watthour.mapping * Math.pow(newInput, 2);
  newMeasure = Math.round(newMeasure * 10) / 10;
  if (this.config.watthour.min <= newMeasure && newMeasure <= this.config.watthour.max) {
    this.input = newInput;
    this.measure = (this.beforeMaximum == -1) ? newMeasure : this.beforeMaximum;
    this.beforeMaximum = -1;
  } else if (newMeasure > this.config.watthour.max && this.beforeMaximum == -1) {
    this.input = newInput;
    this.beforeMaximum = this.measure;
    this.measure = this.config.watthour.max;
  }
};

App.prototype.onButtonDown = function() {
  switch (this.state) {
    case App.STATE.PROGRESS:
    case App.STATE.FINISHED:
      this.startResetting();
      break;
    case App.STATE.WINDING:
      if (!this.buttonPressed) this.buttonPressed = +new Date;
  }
};

App.prototype.onButtonUp = function() {
  switch (this.state) {
    case App.STATE.RESETTING:
      this.stopResetting();
      break;
    case App.STATE.WINDING:
      delete this.firstData;
      this.used = this.used.map(function() { return 0; });
      this.start = +new Date;
      this.setState(App.STATE.PROGRESS);
  }
};

App.prototype.startResetting = function() {
  this.preResetState = this.state;
  this.setState(App.STATE.RESETTING);
};

App.prototype.stopResetting = function() {
  this.setState(this.preResetState);
};

App.prototype.draw = function(t) {
  requestAnimationFrame(this.draw.bind(this));
  
  var changed = this.state != this.previousState;
  if (changed) {
    this.drawUtil.t0 = t;
    this.previousState = this.state;
  }
  
  var ctx = this.canvas.getContext('2d');

  ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
  ctx.beginPath();
  ctx.rect(0, 0, this.canvas.width, this.canvas.height);
  ctx.fillStyle = 'black';
  ctx.fill();

  this.draw[this.state].bind(this)(ctx, t, this.drawUtil);
};

App.prototype.draw[App.STATE.INITIALIZING] = function(ctx, t, u) {
  ctx.font = this.getFont(10);
  ctx.fillStyle = '#ffffff';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText('initialising...', u.cx, u.cy);
};

App.prototype.draw[App.STATE.INTRO] = function(ctx, t, u) {
  var duration = this.config.startAnimation.duration;
  if (!this.measure && t - u.t0 < duration) {
    var scale = map(easeOutElastic, t - u.t0, 0, duration, 0, 1);
  } else var scale = 1;

  var size = this.getSizeForEnergy(this.measure || this.config.watthour.min);
  
  ctx.beginPath();
  ctx.lineWidth = this.config.display.lineWidth * scale;
  ctx.fillStyle = '#000';
  ctx.strokeStyle = '#fff';
  ctx.arc(u.cx, u.cy, size * scale, 0, 2 * Math.PI, false);
  ctx.fill();
  ctx.stroke();

  ctx.save();
  ctx.translate(u.cx, u.cy);
  ctx.scale(scale, scale);

  var angle = map(linear, t, u.t0, u.t0 + 7000, -Math.PI / 4, 7/4 * Math.PI);
  ctx.rotate(angle);
  ctx.font = this.getFont(18);
  ctx.fillStyle = '#fff';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText('twist', 0, size - 2 * 18);
  ctx.font = this.getFont(10);
  ctx.fillText('to set Wh', 0, size - 1 * 18);

  ctx.restore();

  this.drawList(ctx, t, u);
};

App.prototype.draw[App.STATE.RESETTING] = function(ctx, t, u) {
  var elapsed = t - u.t0;
  var seconds = this.config.resetTiming.waitSeconds;
  var ms = seconds * 1000;

  if (elapsed >= ms) {
    this.setState(App.STATE.INTRO);
    return;
  }

  this.draw[this.preResetState].bind(this)(ctx, t, u);

  var appear = this.config.resetTiming.appearMs;
  var scale1 = (elapsed > appear) ? 1 : map(easeOutQuart, elapsed, 0, appear, 0, 1);
  var inner = 50;
  var size = this.getSizeForEnergy(this.measure || this.config.watthour.max);
  var perCircle = size / seconds;

  for (var i = 0; i < seconds; i++) {
    ctx.beginPath();
    ctx.strokeStyle = '#000';
    ctx.lineWidth = this.config.display.lineWidth * scale1;
    ctx.arc(u.cx, u.cy, i * perCircle * scale1, 0, 2 * Math.PI, false);
    ctx.stroke();
  }

  var radius = Math.max(inner, (Math.floor(elapsed / 1000) + map(/*easeOutQuart*/ easeOutElastic, elapsed, 0, 1000, 0, 1)) * perCircle);
  ctx.beginPath();
  ctx.fillStyle = '#000';
  ctx.strokeStyle = '#fff';
  ctx.lineWidth = this.config.display.lineWidth * scale1;
  ctx.arc(u.cx, u.cy, radius * scale1, 0, 2 * Math.PI, false);
  ctx.fill();
  ctx.stroke();

  ctx.save();
  ctx.translate(u.cx, u.cy);
  ctx.scale(scale1, scale1);

  if (elapsed > ms - appear) {
    var scale2 = map(/*easeOutQuart*/ easeOutElastic, elapsed - appear, 0, appear, 1, 0);
    ctx.scale(scale2, scale2);
  }
  ctx.font = this.getFont(18);
  ctx.fillStyle = '#fff';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText('reset?', 0, 0);

  ctx.restore();
};

App.prototype.draw[App.STATE.WINDING] = function(ctx, t, u) {
  var size = this.getSizeForEnergy(this.measure);
  var dt = new Date - this.buttonPressed;
  var duration = this.config.startAnimation.duration;
  var max = this.config.startAnimation.scale;
  if (0 <= dt && dt < duration) {
    var scale = map(easeOutElastic, dt, 0, duration, 1, max);
  } else if (!this.buttonPressed) {
    var scale = 1;
  } else {
    var scale = max;
  }
  var duration = 100;
  if (0 <= dt && dt < duration) {
    var label = map(easeOutQuart, dt, 0, duration, 1, 0);
  } else if (!this.buttonPressed) {
    var label = 1;
  } else {
    var label = 0;
  }

  ctx.beginPath();
  ctx.fillStyle = '#fff';
  ctx.arc(u.cx, u.cy, size * scale, 0, 2 * Math.PI, false);
  ctx.fill();

  ctx.save();
  ctx.translate(u.cx, u.cy);
  ctx.scale(scale, scale);

  ctx.save();
  ctx.scale(label, label);

  ctx.fillStyle = '#000';
  ctx.font = this.getFont(18);
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText('press', 0, 0);

  ctx.fillStyle = '#000';
  ctx.font = this.getFont(10);
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText('to start', 0, 20);

  ctx.restore();

  this.drawAmount(ctx, t, u, size, this.measure);

  ctx.restore();

  this.drawList(ctx, t, u);
};

App.prototype.draw[App.STATE.PROGRESS] = function(ctx, t, u) {
  this.updateUsed();

  var size = this.getSizeForEnergy(this.measure);
  var left = (this.measure - this.used.reduce(sum)) / this.measure;

  var duration = this.config.startAnimation.duration;
  var max = this.config.startAnimation.scale;
  var dt = new Date - this.start;
  if (0 <= dt && dt < duration)
    var scale = map(easeOutElastic, dt, 0, duration, max, 1);
  else
    var scale = 1;

  ctx.save();
  ctx.translate(u.cx, u.cy);
  ctx.scale(scale, scale);
  
  ctx.beginPath();
  ctx.fillStyle = '#fff';
  ctx.moveTo(0, 0);
  ctx.arc(0, 0, size, 0, 2 * Math.PI, false);
  ctx.closePath();
  ctx.fill();

  ctx.restore();

  this.drawSlices(ctx, t, u, size);

  ctx.save();
  ctx.translate(u.cx, u.cy);
  ctx.scale(scale, scale);
  
  this.drawAmount(ctx, t, u, size, this.measure - this.used.reduce(sum));

  ctx.restore();

  this.drawList(ctx, t, u);
};

App.prototype.draw[App.STATE.FINISHED] = function(ctx, t, u) {
  var size = this.getSizeForEnergy(this.measure);
  
  this.drawSlices(ctx, t, u, size);
  
  ctx.save();
  ctx.translate(u.cx, u.cy);
  ctx.rotate(Math.PI / 4)
  ctx.fillStyle = '#fff';
  ctx.font = this.getFont(18);
  ctx.textAlign = 'center';
  ctx.textBaseline = 'bottom';
  ctx.fillText(this.round(this.measure), 0, -size - 20);
  ctx.restore();
  
  ctx.save();
  ctx.translate(u.cx, u.cy);
  ctx.rotate(Math.PI / 4)
  ctx.fillStyle = '#fff';
  ctx.font = this.getFont(10);
  ctx.textAlign = 'center';
  ctx.textBaseline = 'bottom';
  ctx.fillText('Wh used', 0, -size - 5);
  ctx.restore();
  
  var totalMinutes = (this.end - this.start) / 1000 / 60;
  var hours = Math.floor(totalMinutes / 60);
  var minutes = Math.round(totalMinutes % 60);
  var time = + hours + ':' + ((minutes < 10) ? '0' : '') + minutes;
  
  ctx.save();
  ctx.translate(u.cx, u.cy);
  ctx.rotate(5 * Math.PI / 4)
  ctx.fillStyle = '#fff';
  ctx.font = this.getFont(18);
  ctx.textAlign = 'center';
  ctx.textBaseline = 'bottom';
  ctx.fillText(time, 0, -size - 20);
  ctx.restore();
  
  ctx.save();
  ctx.translate(u.cx, u.cy);
  ctx.rotate(5 * Math.PI / 4)
  ctx.fillStyle = '#fff';
  ctx.font = this.getFont(10);
  ctx.textAlign = 'center';
  ctx.textBaseline = 'bottom';
  ctx.fillText('hours', 0, -size - 5);
  ctx.restore();

  this.drawList(ctx, t, u);
};

App.prototype.drawSlices = function(ctx, t, u, size) {
  var angle = -Math.PI / 2;
  for (var i = this.used.length - 1; i >= 0; i--) {
    var add = this.used[i] / this.measure * 2 * Math.PI;
    ctx.beginPath();
    ctx.fillStyle = u.colors[i];
    ctx.moveTo(u.cx, u.cy);
    ctx.arc(u.cx, u.cy, size, angle, angle += add, false);
    ctx.closePath();
    ctx.fill();
  }
};

App.prototype.drawAmount = function(ctx, t, u, size, amount) {
  ctx.rotate(Math.PI / 4)
  ctx.fillStyle = '#fff';
  ctx.font = this.getFont(18);
  ctx.textAlign = 'center';
  ctx.textBaseline = 'bottom';
  ctx.fillText(this.round(amount), 0, -size - 20);

  ctx.font = this.getFont(10);
  ctx.fillStyle = '#fff';
  ctx.font = this.getFont(10);
  ctx.textAlign = 'center';
  ctx.textBaseline = 'bottom';
  ctx.fillText('Wh left', 0, -size - 5);
};

App.prototype.drawList = function(ctx, t, u) {
  if (!this.config.display.list.show) return;
  var n = this.used.length;

  var width = this.config.display.list.valueWidth + this.config.display.list.percentageWidth;
  var cl = this.config.display.list;
  this.used.forEach(function(Wh, i) {
    ctx.beginPath();
    ctx.fillStyle = u.colors[i];
    ctx.rect(u.width - cl.spacing - width, u.height - cl.size - cl.spacing - (n - i - 1) * (cl.size + 6), cl.size, cl.size);
    ctx.fill();

    ctx.font = this.getFont(10);
    ctx.fillStyle = '#999';
    ctx.textAlign = 'right';
    ctx.textBaseline = 'bottom';
    var amount = '';
    var percentage = '';
    if (this.state == App.STATE.FINISHED || (this.state == App.STATE.RESETTING && this.preResetState == App.STATE.FINISHED)) {
      if (this.wasConnected[i]) {
        amount = this.round(this.used[i]) + ' Wh';
        percentage = (this.used[i] / this.used.reduce(sum) * 100.0).toFixed(1) + ' %';
      } else {
        amount = '-.--- Wh';
        percentage = '-.- %';
      }
    } else {
      if (this.watts[i] == -1)
        amount = '-.- W';
      else
        amount = this.watts[i].toFixed(1) + ' W';
    }
    ctx.fillText(amount, u.width - cl.spacing - cl.percentageWidth, u.height - cl.spacing - (n - i - 1) * (cl.size + 6));
    if (percentage)
      ctx.fillText(percentage, u.width - cl.spacing, u.height - cl.spacing - (n - i - 1) * (cl.size + 6));
  }.bind(this));
};

App.prototype.getSizeForEnergy = function(energy) {
  var maxSize = this.canvas.height / 2 - this.config.display.padding - this.config.display.lineWidth;
  var minSize = this.config.display.minSize * maxSize;
  var maxEnergy = this.config.watthour.max;
  
  return minSize + Math.sqrt(energy / maxEnergy) * (maxSize - minSize);
};

App.prototype.getFont = function(size) {
  //return size + 'pt HelveticaNeue-Bold';
  return 'bold ' + size + 'pt sans-serif';
};

if (typeof module !== 'undefined' && module.exports) {
  module.exports = App;
}
