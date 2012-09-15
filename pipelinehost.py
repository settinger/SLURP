#!/usr/bin/env python
"""
Hosts requests sent to the NLPipeline over sockets.

"""

# Copyright (C) 2012 Constantine Lignos
#
# This file is a part of SLURP.
#
# SLURP is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# SLURP is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SLURP.  If not, see <http://www.gnu.org/licenses/>.

import json
from commproxy import CallbackSocket, _parse_msg
from pennpipeline import parse_text, init_pipes, close_pipes

MSG_SEP = "\n"
DEFAULT_PORT = 9001


def socket_parse(**kwargs):
    """Send a remote parsing request and get a response."""
    # Get the socket out of kwargs and send over the rest
    sock = kwargs.pop('asocket')
    msg = json.dumps(kwargs) + MSG_SEP
    print "Sending:", repr(msg)
    sock.sendall(msg)
    print "Waiting for response..."
    buff = sock.recv(4096)
    msg, buff = _parse_msg(buff, MSG_SEP)
    return msg


class PipelineHost(CallbackSocket):
    """Provides a connection to pipeline over a listening socket."""
    name = "pipelinehost"
    
    def __init__(self, port, local=False):
        # Set up callback        
        CallbackSocket.__init__(self, port, MSG_SEP, local)
        self.register_callback(self.parse_text)
        # Start up the pipeline
        init_pipes()

    def __del__(self):
        # We put this check as it may already be undefined during interpreter shutdown.
        # There's no guarantee this will succeed during shutdown anyway.
        if close_pipes:
            close_pipes()

    def parse_text(self, message):
        """Send a parse request to the pipline."""
        data = json.loads(message)
        print "Message:", repr(data)
        print "Parsing..."
        response = parse_text(**data)
        print "Sending:", repr(response)
        self.send(response)


def main():
    """Start the parsing server and leave it up until KeyboardInterrupt."""
    host = PipelineHost(DEFAULT_PORT, True)
    try:
        while True:
            raw_input()
    except KeyboardInterrupt:
        pass
    except:
        raise
    finally:
        del host

    
if __name__ == "__main__":
    main()