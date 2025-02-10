"""
"Quiet mode" example proxy

Allows a client to turn on "quiet mode" which hides chat messages
This client doesn't handle system messages, and assumes none of them contain chat messages
"""

from twisted.internet import reactor
from quarry.types.uuid import UUID
from quarry.net.proxy import DownstreamFactory, Bridge
import logging
import math
import struct


class QuietBridge(Bridge):

    entity_id = None
    prev_pos = None
    prev_look = None

    def packet_upstream_chat_command(self, buff):
        buff.save()
        chat_message = buff.unpack_string()
        print(f" >> {chat_message}")

        if chat_message.startswith("/port"):
            _, distance = chat_message.split(" ")
            flags = 0
            teleport = 0
            dismount = 0
            x, y, z, ground = self.prev_pos
            yaw, pitch, ground = self.prev_look
            # see net.minecraft.entity.Entity:getRotationVEctor()
            f = pitch * 0.017453292
            g = -yaw * 0.017453292
            h = math.cos(g)
            i = math.sin(g)
            j = math.cos(f)
            k = math.sin(f)
            _x = i * j
            _y = -k
            _z = h * j
            x += _x * float(distance)
            y += _y * float(distance)
            z += _z * float(distance)
            buf = struct.pack('>dddffBBB', x, y, z, yaw, pitch, flags, teleport, dismount)
            self.upstream.send_packet('pos_rot', buf)

        buff.restore()
        self.upstream.send_packet("chat_command", buff.read())

    def packet_unhandled(self, buff, direction, name):
        if direction == "downstream":
            # print(f"[*][{direction}] {name}")
            self.downstream.send_packet(name, buff.read())
        elif direction == "upstream":
            self.upstream.send_packet(name, buff.read())

    def packet_downstream_player_position(self, buff):
        buf = buff.read()

        print(f"[*] player_position: {buf.hex()}")

        self.downstream.send_packet('player_position', buf)

    def packet_downstream_pos(self, buff):
        buf = buff.read()

        print(f"[*] pos: {buf.hex()}")

        self.downstream.send_packet('pos', buf)

    def packet_downstream_pos_rot(self, buff):
        buf = buff.read()

        print(f"[*] pos: {buf.hex()}")

        self.downstream.send_packet('pos', buf)

    def packet_upstream_pos(self, buff):
        buff.save()
        buf = buff.read()
        x, y, z, ground = struct.unpack('>dddB', buf)
        # print(f"[*] player_position {x} / {y} / {z} | {ground}")
        self.prev_pos = (x, y, z, ground)
        self.upstream.send_packet('pos', buf)

    def packet_upstream_rot(self, buff):
        buff.save()
        yaw, pitch, ground = struct.unpack('>ffB', buff.read())
        # print(f"[*] player_look {yaw} / {pitch} | {ground}")
        self.prev_look = (yaw, pitch, ground)
        buf = struct.pack('>ffB', yaw, pitch, ground)
        self.upstream.send_packet('rot', buf)

    # def packet_downstream_pos_rot(self, buff):
    #     buff.save()
    #     print(buff.read())
    #     x, y, z, yaw, pitch, flags = struct.unpack('>dddffB', buff.read())
    #     print(f"[*] player_position_and_look {x} / {y} / {z} | {yaw} / {pitch} | {flags}")
    #     buf = struct.pack('>dddffB', x, y, z, yaw, pitch, flags)
    #     self.downstream.send_packet('pos_rot', buf)


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
