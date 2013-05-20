# Copyright (C) 2011 Sven Petai <hadara@bsd.ee> 
# Use of this source code is governed by the MIT license found in the LICENSE file.


class PlugwiseException(Exception):
    pass

class ProtocolError(PlugwiseException):
    pass

class TimeoutException(PlugwiseException):
    pass
