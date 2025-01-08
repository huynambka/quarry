"""
"Quiet mode" example proxy

Allows a client to turn on "quiet mode" which hides chat messages
This client doesn't handle system messages, and assumes none of them contain chat messages
"""

from twisted.internet import reactor
from quarry.types.uuid import UUID
from quarry.net.proxy import DownstreamFactory, Bridge
import logging


class QuietBridge(Bridge):
    
    def packet_unhandled(self, buff, direction, name):
        if direction == "downstream":
            self.downstream.send_packet(name, buff.read())
        elif direction == "upstream":
            print(f"[*][{direction}] {name}")
            self.upstream.send_packet(name, buff.read())



class QuietDownstreamFactory(DownstreamFactory):
    bridge_class = QuietBridge
    motd = "Proxy Server"
    log_level = logging.DEBUG


def main(argv):
    # Parse options
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--listen-host", default="", help="address to listen on")
    parser.add_argument("-p", "--listen-port", default=25565, type=int, help="port to listen on")
    parser.add_argument("-b", "--connect-host", default="127.0.0.1", help="address to connect to")
    parser.add_argument("-q", "--connect-port", default=25565, type=int, help="port to connect to")
    args = parser.parse_args(argv)

    # Create factory
    factory = QuietDownstreamFactory()
    factory.connect_host = args.connect_host
    factory.connect_port = args.connect_port

    # Listen
    factory.listen(args.listen_host, args.listen_port)
    reactor.run()


if __name__ == "__main__":
    import sys
    main(sys.argv[1:])