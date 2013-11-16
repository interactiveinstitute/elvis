'use strict';

var sum = function(a, b) { return a + b; };

var map = function(fn, t, imin, ival, omin, omax) {
  return omin + (omax - omin) * fn((t - imin) / (ival - (imin % ival)) % 1);
};

var easeInOutCubic = function(t) {
  // Based on https://gist.github.com/gre/1650294
  return t < .5 ? 4*t*t*t*t : (t-1)*(2*t-2)*(2*t-2)+1;
};

var easeInOutCirc = function(t) {
  // Based on http://www.gizma.com/easing/
  return t < .5 ? -.5 * (Math.sqrt(1 - 4 * t*t) - 1) : .5 * (Math.sqrt(1 - (t*2-2)*(t*2-2)) + 1);
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
  PROGRESS_DETAILS: 5,
  FINISHED: 6,
  FINISHED_DETAILS: 7
};

App.DIRECTION = {
  INCREASE: 0,
  DECREASE: 1
};

App.prototype.construct = function(config, canvas, source) {
  this.config = config;
  this.canvas = canvas;
  
  this.drawUtil = {
    width: this.canvas.width,
    height: this.canvas.height,
    cx: this.canvas.width / 2,
    cy: this.canvas.height / 2,
    colors: []
  };
  this.config.colors.forEach(function(values, i) {
    this.drawUtil.colors[i] = values[1];
  }, this);
  
  this.measure = this.config.watthour.start;

  this.watts = [];
  this.used = [];
  this.lastUsedUpdate = 0;
  
  source.addEventListener('init', function(event) {
    this.setState(App.STATE.INTRO);
  }.bind(this));
  source.addEventListener('powerdata', function(event) {
    var data = JSON.parse(event.data).map(parseFloat);
    this.watts = data;

    if (this.state == App.STATE.INITIALIZING) this.setState(App.STATE.INTRO);
    
    if (this.state == App.STATE.PROGRESS || this.state == App.STATE.PROGRESS_DETAILS) {
      this.updateUsed();

      var total = this.used.reduce(sum);
      if (total > this.measure) {
        var factor = this.measure / total;
        this.used = this.used.map(function(Wh) { return Wh * factor; });
        this.end = +new Date;
        this.setState(App.STATE.FINISHED);
      }
    }
  }.bind(this));
  source.addEventListener('increase', function(event) {
    this.twist(App.DIRECTION.INCREASE);
  }.bind(this));
  source.addEventListener('decrease', function(event) {
    this.twist(App.DIRECTION.DECREASE);
  }.bind(this));
  source.addEventListener('press', function(event) {
    this.toggleDetails(true);
  }.bind(this));
  source.addEventListener('release', function(event) {
    this.toggleDetails(false);
  }.bind(this));

  this.setState(App.STATE.INITIALIZING);
    
  this.draw();
};

App.prototype.round = function(Wh) {
  var rounded = Math.round(Wh * 10) / 10;
  return Math.floor(rounded) + '.' + (rounded % 1 * 10);
};

App.prototype.updateUsed = function() {
  if (this.lastUsedUpdate == 0) {
    this.lastUsedUpdate = +new Date;
  } else {
    var now = +new Date;
    var millis = now - this.lastUsedUpdate;
    var watts = this.watts;
    for (var i = 0; i < this.watts.length; i++) {
      var add = watts[i] / 1000.0 / 3600.0;
      this.used[i] = (this.used[i] || 0) + add;
    }
    this.lastUsedUpdate = now;
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
  if (direction == App.DIRECTION.DECREASE) var factor = -1;
  else if (direction == App.DIRECTION.INCREASE) var factor = 1;
  
  if (this.countdown) clearTimeout(this.countdown);
  
  this.measure += factor * this.config.watthour.step;
  if (this.measure < this.config.watthour.min) this.measure = this.config.watthour.min;
  if (this.measure > this.config.watthour.max) this.measure = this.config.watthour.max;
  
  if (this.state != App.STATE.WINDING) this.setState(App.STATE.WINDING);
  
  this.countdown = setTimeout(function() {
    delete this.firstData;
    this.used = this.config.colors.map(function() { return 0; });
    this.start = +new Date;
    this.setState(App.STATE.PROGRESS);
  }.bind(this), this.config.countdown);
};

App.prototype.toggleDetails = function(show) {
  switch (this.state) {
    case App.STATE.PROGRESS:
      if (show) this.setState(App.STATE.PROGRESS_DETAILS); break;
    case App.STATE.PROGRESS_DETAILS:
      if (!show) this.setState(App.STATE.PROGRESS); break;
    case App.STATE.FINISHED:
      if (show) this.setState(App.STATE.FINISHED_DETAILS); break;
    case App.STATE.FINISHED_DETAILS:
      if (!show) this.setState(App.STATE.FINISHED); break;
  }
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
  ctx.rect(0, 0, this.canvas.width, this.canvas.height);
  ctx.fillStyle = 'black';
  ctx.fill();

  this.draw[this.state].bind(this)(ctx, t, this.drawUtil);
};

App.prototype.draw[App.STATE.INITIALIZING] = function(ctx) {
  ctx.font = this.getFont(18);
  ctx.fillStyle = '#fff';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText('initializing…', this.canvas.width / 2, this.canvas.height / 2);
};

App.prototype.draw[App.STATE.INTRO] = function(ctx, t, u) {
  var size = this.canvas.height / 2 - this.config.display.padding - this.config.display.lineWidth;
  
  ctx.beginPath();
  ctx.fillStyle = '#000';
  ctx.strokeStyle = '#fff';
  ctx.lineWidth = this.config.display.lineWidth;
  ctx.arc(u.cx, u.cy, size, 0, 2 * Math.PI, false);
  ctx.fill();
  ctx.stroke();

  ctx.save();
  ctx.translate(u.cx, u.cy);
  var angle = map(linear, t, u.t0, u.t0 + 7000, -Math.PI / 4, 7/4 * Math.PI);
  ctx.rotate(angle);
  ctx.font = this.getFont(18);
  ctx.fillStyle = '#fff';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText('twist to start', 0, u.height / 2 - 3 * 18);
  ctx.restore();
};

App.prototype.draw[App.STATE.WINDING] = function(ctx, t, u) {
  var size = this.getSizeForEnergy(this.measure);
  
  ctx.beginPath();
  ctx.fillStyle = '#fff';
  ctx.arc(u.cx, u.cy, size, 0, 2 * Math.PI, false);
  ctx.fill();
  
  ctx.save();
  ctx.translate(u.cx, u.cy);
  ctx.rotate(Math.PI / 4)
  ctx.fillStyle = '#fff';
  ctx.font = this.getFont(18);
  ctx.textAlign = 'center';
  ctx.textBaseline = 'bottom';
  ctx.fillText(this.round(this.measure), 0, -(size));
  ctx.restore();
};

App.prototype.draw[App.STATE.PROGRESS] = function(ctx, t, u) {
  this.updateUsed();

  var size = this.getSizeForEnergy(this.measure);

  var left = (this.measure - this.used.reduce(sum)) / this.measure;
  
  ctx.beginPath();
  ctx.fillStyle = '#fff';
  ctx.moveTo(u.cx, u.cy);
  if (left == 1)
    ctx.arc(u.cx, u.cy, size, 0, 2 * Math.PI, false);
  else
    ctx.arc(u.cx, u.cy, size, -.5 * Math.PI, (-.5 + left * 2) * Math.PI, false);
  ctx.closePath();
  ctx.fill();
  
  ctx.save();
  ctx.translate(u.cx, u.cy);
  ctx.rotate(Math.PI / 4)
  ctx.fillStyle = '#fff';
  ctx.font = this.getFont(18);
  ctx.textAlign = 'center';
  ctx.textBaseline = 'bottom';
  ctx.fillText(this.round(this.measure - this.used.reduce(sum)), 0, -(size));
  ctx.restore();
};

App.prototype.draw[App.STATE.PROGRESS_DETAILS] = function(ctx, t, u) {
  this.updateUsed();

  var size = this.getSizeForEnergy(this.measure);

  this.drawSlices(ctx, t, u, size);
  
  ctx.save();
  ctx.translate(u.cx, u.cy);
  ctx.rotate(Math.PI / 4)
  ctx.fillStyle = '#fff';
  ctx.font = this.getFont(18);
  ctx.textAlign = 'center';
  ctx.textBaseline = 'bottom';
  ctx.fillText(this.round(this.used.reduce(sum)), 0, -(size));
  ctx.restore();
};

App.prototype.draw[App.STATE.FINISHED] = function(ctx, t, u) {
  var size = this.getSizeForEnergy(this.measure);
  
  ctx.beginPath();
  ctx.fillStyle = '#000';
  ctx.strokeStyle = '#fff';
  ctx.lineWidth = this.config.display.lineWidth;
  ctx.arc(u.cx, u.cy, size, 0, 2 * Math.PI, false);
  ctx.fill();
  ctx.stroke();
  
  ctx.save();
  ctx.translate(u.cx, u.cy);
  ctx.rotate(Math.PI / 4)
  ctx.fillStyle = '#fff';
  ctx.font = this.getFont(18);
  ctx.textAlign = 'center';
  ctx.textBaseline = 'bottom';
  ctx.fillText(this.round(this.measure), 0, -(size));
  ctx.restore();
  
  ctx.save();
  ctx.translate(u.cx, u.cy);
  ctx.rotate(Math.PI / 4)
  ctx.fillStyle = '#fff';
  ctx.font = this.getFont(10);
  ctx.textAlign = 'center';
  ctx.textBaseline = 'bottom';
  ctx.fillText('Wh', 0, -(size) + 20);
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
  ctx.fillText(time, 0, -(size));
  ctx.restore();
  
  ctx.save();
  ctx.translate(u.cx, u.cy);
  ctx.rotate(5 * Math.PI / 4)
  ctx.fillStyle = '#fff';
  ctx.font = this.getFont(10);
  ctx.textAlign = 'center';
  ctx.textBaseline = 'bottom';
  ctx.fillText('hours', 0, -(size) + 20);
  ctx.restore();
  
  ctx.save();
  ctx.translate(u.cx, u.cy);
  ctx.rotate(7 * Math.PI / 4)
  ctx.fillStyle = '#fff';
  ctx.font = this.getFont(10);
  ctx.textAlign = 'center';
  ctx.textBaseline = 'bottom';
  ctx.fillText('twist', 0, -(size) + 20);
  ctx.restore();
};

App.prototype.draw[App.STATE.FINISHED_DETAILS] = function(ctx, t, u) {
  var size = this.getSizeForEnergy(this.measure);
  
  this.drawSlices(ctx, t, u, size);
  
  ctx.save();
  ctx.translate(u.cx, u.cy);
  ctx.rotate(Math.PI / 4)
  ctx.fillStyle = '#fff';
  ctx.font = this.getFont(18);
  ctx.textAlign = 'center';
  ctx.textBaseline = 'bottom';
  ctx.fillText(this.round(this.measure), 0, -(size));
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
  ctx.fillText(time, 0, -(size));
  ctx.restore();
};

App.prototype.drawSlices = function(ctx, t, u, size) {
  var angle = -Math.PI / 2;
  this.used.forEach(function(Wh, i) {
    var add = Wh / this.measure * 2 * Math.PI;
    ctx.beginPath();
    ctx.fillStyle = u.colors[i];
    ctx.moveTo(u.cx, u.cy);
    ctx.arc(u.cx, u.cy, size, angle, angle -= add, true);
    ctx.closePath();
    ctx.fill();
  }.bind(this));
};

App.prototype.getSizeForEnergy = function(energy) {
  var maxSize = this.canvas.height / 2 - this.config.display.padding - this.config.display.lineWidth;
  var minSize = this.config.display.minSize * maxSize;
  var maxEnergy = this.config.watthour.max;
  
  return minSize + (energy / maxEnergy) * (maxSize - minSize);
};

App.prototype.getFont = function(size) {
  //return size + 'pt HelveticaNeue-Bold';
  return 'bold ' + size + 'pt sans-serif';
};

if (typeof module !== 'undefined' && module.exports) {
  module.exports = App;
}
