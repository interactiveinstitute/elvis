var Canvas = require('./node-openvg-canvas/lib/canvas');

var width = 1920;
var height = 1080;
var padding = 20;
var lineWidth = 4;

var canvas = new Canvas(width, height);
var ctx = canvas.getContext('2d');

var start = +new Date;

function map(fn, t, imin, ival, omin, omax) {
  return omin + (omax - omin) * fn((t - imin) / (ival - (imin % ival)) % 1);
};

function easeInOutCubic(t) {
  // https://gist.github.com/gre/1650294
  return t < .5 ? 4*t*t*t*t : (t-1)*(2*t-2)*(2*t-2)+1;
};

function easeInOutCirc(t) {
  // http://www.gizma.com/easing/
  //t *= 2;
  //return t < .5 ? -1/2 * (Math.sqrt(1 - 4 * t*t) - 1) : 1/2 * (Math.sqrt(1 - (t-1)*(t-1)) + 1);
  return t < .5 ? -.5 * (Math.sqrt(1 - 4 * t*t) - 1) : .5 * (Math.sqrt(1 - (t*2-2)*(t*2-2)) + 1);
};

function draw(t) {
  ctx.clearRect(0, 0, width, height);
  
  var size = height / 2 - padding - lineWidth;
  
  ctx.beginPath();
  ctx.strokeStyle = '#ffffff';
  ctx.lineWidth = lineWidth;
  ctx.arc(width / 2, height / 2, size, 0, 2 * Math.PI, false);
  ctx.stroke();
  
  ctx.font = '18pt DejaVu Sans';
  ctx.fillStyle = '#ffffff';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  
  ctx.save();
  ctx.translate(width / 2, height / 2);
  var angle = map(easeInOutCirc, t, start, 5000, -Math.PI / 4, 7/4 * Math.PI);
  //console.log(angle);
  ctx.rotate(angle);
  ctx.fillText('twist to start', 0, height / 2 - 100);
  ctx.restore();
  
  requestAnimationFrame(draw);
};

requestAnimationFrame(draw);