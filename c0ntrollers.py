#!/usr/bin/env python2
import uinput
import time
import select
import threading
import socket
import time
import subprocess
import os
import logging
import argparse

l = None

class C0ntroller(uinput.Device):
    JOY_UP_MASK = 0x01
    JOY_RIGHT_MASK = 0x02
    JOY_DOWN_MASK = 0x04
    JOY_LEFT_MASK = 0x08
    BTN_X_MASK = 0x10
    BTN_A_MASK = 0x20
    BTN_B_MASK = 0x40
    BTN_Y_MASK = 0x80

    KEEP_ALIVE_TIMEOUT = 10

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

    def is_alive(self):
        return time.time() - self.refresh_time < self.KEEP_ALIVE_TIMEOUT

    def fire(self, event):
        event_diff = event ^ self.prev_event

        if event_diff != 0:
            if event_diff & self.JOY_UP_MASK != 0:
                if event & self.JOY_UP_MASK != 0:
                    self.emit(uinput.ABS_Y, 255)
                else:
                    self.emit(uinput.ABS_Y, 128)
            elif event_diff & self.JOY_DOWN_MASK != 0:
                if event & self.JOY_DOWN_MASK != 0:
                    self.emit(uinput.ABS_Y, 0)
                else:
                    self.emit(uinput.ABS_Y, 128)

            if event_diff & self.JOY_LEFT_MASK != 0:
                if event & self.JOY_LEFT_MASK != 0:
                    self.emit(uinput.ABS_X, 0)
                else:
                    self.emit(uinput.ABS_X, 128)
            elif event_diff & self.JOY_RIGHT_MASK != 0:
                if event & self.JOY_RIGHT_MASK != 0:
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

    CMD_SET_LED_0 = 0x20
    CMD_SET_LED_1 = 0x21

    CMD_PROPAGATE_HOST = 0x30
    CMD_ASK_HOST = 0x31

    def __init__(self, port):
        self.port = port
        self.controllers = {}

    def propagate_host(self):
        l.debug("Propagating the new game server (me)...")
        set_host_msg = "\x30\x00\x00\xFF\x0F\x30"
        self.sock.sendto(set_host_msg, ("<broadcast>", self.port))

    def serve(self):
        l.info("Starting server on port {0}...".format(self.port))

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, True)

        self.server_addr = (self.HOST, self.port)
        self.sock.bind(self.server_addr)

        self.propagate_host()

        while True:
            data, client_addr = self.sock.recvfrom(self.MSG_SIZE)

            l.debug("Received data from {0}:".format(client_addr[0]) + str([ int(ord(c)) for c in data ]))

            if len(data) != self.MSG_SIZE:
                l.warn("{0}: Not a valid command: wrong packet length!".format(client_addr))
                continue

            if data[0] != data[self.MSG_SIZE - 1]:
                l.warn("{0}: Not a valid command: first byte and last byte mismatching!".format(client_addr))
                continue

            if ord(data[0]) == self.CMD_PROPAGATE_HOST:
                continue

            if not client_addr in self.controllers:
                self.controllers[client_addr] = C0ntroller(client_addr[0])
                l.info("New client {0} connected!".format(client_addr[0]))

            if ord(data[0]) == self.CMD_KEEP_ALIVE:
                self.controllers[client_addr].fire(ord(data[1]))
                self.controllers[client_addr].refresh()
            elif ord(data[0]) == self.CMD_BUTTONS_CHANGED:
                self.controllers[client_addr].fire(ord(data[1]))
                self.controllers[client_addr].refresh()
            elif ord(data[0]) == self.CMD_ASK_HOST:
                l.debug("Client asked for a game server.")
                self.propagate_host()

def main():
    global l

    p = argparse.ArgumentParser()
    p.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")
    p.add_argument("-p", "--port", type=int, default=1337, help="use another port")

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
    dev_null = open(os.devnull, 'w')
    result = subprocess.call([ "modprobe", "uinput"], stdout=dev_null, stderr=dev_null)
    dev_null.close()

    if result == 0:
        server = S3rver(args.port)
        server.serve()
    else:
        l.error("Could not load uinput kernel module! Am I root?")

if __name__ == "__main__":
    main()
