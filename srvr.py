#!/usr/bin/env python
import uinput
import time
import json
import threading
import socket
import time
import subprocess
import os
import logging
import argparse

l = None

def hex_to_rgb(value):
    value = value.lstrip('#')
    length = len(value)

    return tuple(int(value[i:i + length // 3], 16) for i in range(0, length, length // 3))

class C0ntroller(uinput.Device):
    JOY_UP_MASK = 0x01
    JOY_RIGHT_MASK = 0x02
    JOY_DOWN_MASK = 0x04
    JOY_LEFT_MASK = 0x08
    BTN_X_MASK = 0x10
    BTN_A_MASK = 0x20
    BTN_B_MASK = 0x40
    BTN_Y_MASK = 0x80

    EVENTS = (
        uinput.BTN_0,
        uinput.BTN_1,
        uinput.BTN_2,
        uinput.BTN_3,
        uinput.ABS_X + (0, 255, 0, 0),
        uinput.ABS_Y + (0, 255, 0, 0))

    def __init__(self, name):
        uinput.Device.__init__(self, self.EVENTS, name)

        self.name = name
        self.refresh_time = time.time()
        self.prev_event = 0x00

        # sync joystick to center
        self.emit(uinput.ABS_X, 128, syn=False)
        self.emit(uinput.ABS_Y, 128)

    def refresh(self):
        self.refresh_time = time.time()

    def dead_time(self):
        return time.time() - self.refresh_time

    def fire(self, event):
        event_diff = event ^ self.prev_event

        if event_diff != 0:
            if event_diff & (self.JOY_UP_MASK | self.JOY_DOWN_MASK) != 0:
                if event & self.JOY_UP_MASK != 0 and not event & self.JOY_DOWN_MASK != 0:
                    self.emit(uinput.ABS_Y, 0)
                elif event & self.JOY_DOWN_MASK != 0 and not event & self.JOY_UP_MASK != 0:
                    self.emit(uinput.ABS_Y, 255)
                else:
                    self.emit(uinput.ABS_Y, 128)

            if event_diff & (self.JOY_LEFT_MASK | self.JOY_RIGHT_MASK) != 0:
                if event & self.JOY_LEFT_MASK != 0 and not event & self.JOY_RIGHT_MASK != 0:
                    self.emit(uinput.ABS_X, 0)
                elif event & self.JOY_RIGHT_MASK != 0 and not event & self.JOY_LEFT_MASK != 0:
                    self.emit(uinput.ABS_X, 255)
                else:
                    self.emit(uinput.ABS_X, 128)

            if event_diff & self.BTN_X_MASK != 0:
                if event & self.BTN_X_MASK != 0:
                    self.emit(uinput.BTN_0, 1)
                else:
                    self.emit(uinput.BTN_0, 0)

            if event_diff & self.BTN_A_MASK != 0:
                if event & self.BTN_A_MASK != 0:
                    self.emit(uinput.BTN_1, 1)
                else:
                    self.emit(uinput.BTN_1, 0)

            if event_diff & self.BTN_B_MASK != 0:
                if event & self.BTN_B_MASK != 0:
                    self.emit(uinput.BTN_2, 1)
                else:
                    self.emit(uinput.BTN_2, 0)

            if event_diff & self.BTN_Y_MASK != 0:
                if event & self.BTN_Y_MASK != 0:
                    self.emit(uinput.BTN_3, 1)
                else:
                    self.emit(uinput.BTN_3, 0)

            self.syn()

        self.prev_event = event

class S3rver(object):
    HOST = "0.0.0.0"

    MSG_SIZE = 6

    CMD_KEEP_ALIVE = 0x10
    CMD_BUTTONS_CHANGED = 0x11

    CMD_SET_LED_LEFT = 0x20
    CMD_SET_LED_RIGHT = 0x21

    CMD_PROPAGATE_HOST = 0x30
    CMD_ASK_HOST = 0x31

    def __init__(self, port, config=None):
        self.port = port
        self.controllers = {}

        no_config_present = False

        if config:
            try:
                with open(config) as config_file:
                    config_data = json.load(config_file)

                    l.info("Loaded config file {0}...".format(config))

                    self.color = hex_to_rgb(config_data["color"])
                    self.timeout = config_data["timeout"]
            except:
                no_config_present = True
        else:
            no_config_present = True

        if no_config_present:
            self.color = (0xFF, 0xFF, 0xFF)
            self.timeout = 10

    def propagate_host(self):
        l.debug("Propagating the new game server (me)...")
        set_host_msg = bytes([ 0x30, self.color[0], self.color[1], self.color[2], 0xFF, 0x30 ])
        self.sock.sendto(set_host_msg, ("<broadcast>", self.port))

    def serve(self):
        l.info("Starting server on port {0}...".format(self.port))

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, True)
        self.sock.settimeout(self.timeout)

        self.server_addr = (self.HOST, self.port)
        self.sock.bind(self.server_addr)

        self.propagate_host()

        while True:
            try:
                data, client_addr = self.sock.recvfrom(self.MSG_SIZE)

                l.debug("Received data from {0}: ".format(client_addr[0]) + str(data))

                if len(data) != self.MSG_SIZE:
                    l.warn("{0}: Not a valid command: wrong packet length!".format(client_addr))
                    continue

                if data[0] != data[self.MSG_SIZE - 1]:
                    l.warn("{0}: Not a valid command: first byte and last byte mismatching!".format(client_addr))
                    continue

                if data[0] == self.CMD_PROPAGATE_HOST:
                    continue

                if data[0] in [ self.CMD_KEEP_ALIVE, self.CMD_BUTTONS_CHANGED, self.CMD_ASK_HOST ]:
                    if client_addr in self.controllers:
                        self.controllers[client_addr].refresh()
                    else:
                        l.info("New client {0} connected!".format(client_addr[0]))
                        self.controllers[client_addr] = C0ntroller(client_addr[0])

                if data[0] == self.CMD_KEEP_ALIVE:
                    self.controllers[client_addr].fire(data[1])
                elif data[0] == self.CMD_BUTTONS_CHANGED:
                    self.controllers[client_addr].fire(data[1])
                elif data[0] == self.CMD_ASK_HOST:
                    l.debug("Client asked for a game server.")
                    self.propagate_host()
            except socket.timeout:
                pass

            clients_to_kick = []

            for client_addr in self.controllers:
                if self.controllers[client_addr].dead_time() > self.timeout:
                    clients_to_kick.append(client_addr)

            for client_addr in clients_to_kick:
                l.info("Kicked client {0}! (timeout)".format(client_addr[0]))
                del self.controllers[client_addr]

def main():
    global l

    p = argparse.ArgumentParser()
    p.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")
    p.add_argument("-p", "--port", type=int, default=1337, help="use another port")
    p.add_argument("-c", "--config", type=str, default="srvr.cnfg", help="use another config file")

    args = p.parse_args()

    formatter = logging.Formatter("%(asctime)s # %(levelname)-8s %(message)s")

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    l = logging.getLogger()
    l.addHandler(handler)

    if args.verbose:
        l.setLevel(logging.DEBUG)
    else:
        l.setLevel(logging.INFO)

    l.info("Loading uinput kernel module, if it has not been loaded yet...")
    dev_null = open(os.devnull, "w")
    result = subprocess.call([ "modprobe", "uinput"], stdout=dev_null, stderr=dev_null)
    dev_null.close()

    if result == 0:
        server = S3rver(args.port, args.config)
        server.serve()
    else:
        l.error("Could not load uinput kernel module! Am I root?")

if __name__ == "__main__":
    main()
