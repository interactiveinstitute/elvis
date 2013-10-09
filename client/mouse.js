var EventEmitter = require('events').EventEmitter;
var fs = require('fs');
var udev = require('udev');

var Mouse = function() {
  // Uses patterns from https://gist.github.com/cheery/4319107
  var me = this;
  udev.list().forEach(function(device) {
    /*if (device.syspath.match(/event[0-9]+$/) &&
        device.SUBSYSTEM == 'input' &&
        device.ID_INPUT == '1' &&
        device.ID_INPUT_MOUSE == '1') {*/
      if (device.ID_MODEL == 'Griffin_PowerMate' && device.ID_PATH) {
        
      var buffer = new Buffer(16);
      var view = new DataView(buffer);
      var fd;
      var read = function(callback) {
        fs.read(fd, buffer, 0, 16, null, function(error, bytesRead) {
          if (error && error.code == 'ENODEV') {
            fd.close();
            fd = null;
            return;
          }
          if (error) return callback(error, null);
          if (bytesRead != 16) return callback('not enough bytes read', null);
          callback(null, {
            sec: view.getInt32(0, true),
            usec: view.getInt32(4, true),
            type: view.getUint16(8, true),
            code: view.getUint16(10, true),
            value: view.getInt32(12, true)
          });
          read(callback);
        });
      };
      fs.open(device.DEVNAME, 'r+', function(error, _fd) {
        fd = _fd;
        if (error)
          console.log('ERROR', error);
        read(function(error, event) {
          console.log(event)
          if (error) throw error;
          if (event.type == 2 && event.code == 8) {
            me.emit('scroll', event.value);
          } else if (event.type == 1 /* && event.code == 274*/) {
            if (event.value == 1)
              me.emit('press');
            else
              me.emit('release');
          }
        });
      });
      console.log('connected:', device.ID_SERIAL, device.ID_PATH);
    }
  });
};

Mouse.prototype.__proto__ = EventEmitter.prototype;

module.exports = Mouse;
