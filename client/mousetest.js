var Canvas = require('openvg-canvas');
var Mouse = require('./mouse');

var mouse = new Mouse;

mouse.on('scroll', function(direction) {
  console.log('scroll', direction);
});
mouse.on('press', function() {
  console.log('press');
});

var i = 0;
var draw = function() {
  console.log(i++);
  requestAnimationFrame(draw);
};

requestAnimationFrame(draw);
