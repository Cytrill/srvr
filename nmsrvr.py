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

class N4meserver(object):
    HOST = "0.0.0.0"

    NAME_EXT = ".nm"

    MSG_SIZE = 6

    CMD_SET_NAME = 0x40

    def __init__(self, port, config=None):
        self.port = port
        self.names = {}
        self.req_clients = {}

        no_config_present = False

        if config:
            try:
                with open(config) as config_file:
                    config_data = json.load(config_file)

                    l.info("Loaded config file {0}...".format(config))

                    self.names_dir = config_data["names_dir"]
                    self.editor = None
                    self.timeout = config_data["timeout"]

                    if "editor" in config_data:
                        self.editor = config_data["editor"]
            except:
                no_config_present = True
                l.error("Error loading config file {0}...".format(config))
        else:
            no_config_present = True

        if no_config_present:
            self.names_dir = "names"
            self.editor = None
            self.timeout = 10

    def handle_requester(self, client):
        l.debug("New subscriber connected.")

        # wait for a string
        ip = str(client.recv(16), "utf-8")

        if not ip in self.req_clients:
            self.req_clients[ip] = [ client ]
        else:
            self.req_clients[ip].append(client)

        l.debug("The new subscriber subscribed for the ip: {0}".format(ip))

        if ip in self.names:
            client.send(bytes(self.names[ip], "utf-8"))

    def listen_for_requesters(self):
        l.info("Listening for name resolvement subscribers")

        self.req_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.req_sock.bind((self.HOST, self.port))
        self.req_sock.listen(5)

        while True:
            client, _ = self.req_sock.accept()

            self.reload_names()

            client_thread = threading.Thread(target=self.handle_requester, args=[ client ])
            client_thread.start()

    def reload_names(self):
        if not os.path.exists(self.names_dir):
            os.makedirs(self.names_dir)

        name_files = [ f for f in os.listdir(self.names_dir) if os.path.isfile(os.path.join(self.names_dir, f)) ]

        for name_file in name_files:
            base, ext = os.path.splitext(name_file)
            ip = os.path.basename(base)

            if ext == self.NAME_EXT:
                with open(os.path.join(self.names_dir, name_file), "r") as f:
                    old_name = self.names[ip] if ip in self.names else None
                    self.names[ip] = f.read().strip()

                    if old_name != self.names[ip] and ip in self.req_clients:
                        for client in self.req_clients[ip]:
                            try:
                                client.send(bytes(self.names[ip], "utf-8"))
                            except:
                                l.debug("Lost connection for client {0}, kicking it".format(client))
                                self.req_clients[ip].remove(client)

    def listen_for_name_changes(self):
        while True:
            self.reload_names()
            time.sleep(3)

    def serve(self):
        l.info("Starting nameserver on port {0}...".format(self.port))

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, True)
        self.sock.settimeout(self.timeout)

        self.server_addr = (self.HOST, self.port)
        self.sock.bind(self.server_addr)

        self.req_thread = threading.Thread(target=self.listen_for_requesters, args=())
        self.req_thread.start()

        self.change_thread = threading.Thread(target=self.listen_for_name_changes, args=())
        self.change_thread.start()

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

                if data[0] == self.CMD_SET_NAME and self.editor != None:
                    l.info("New client {0} wants to get a name!".format(client_addr[0]))

                    ip = client_addr[0]
                    name_file = os.path.join(self.names_dir, ip + self.NAME_EXT)

                    if not os.path.exists(name_file):
                        with open(name_file, "w") as f:
                            f.write(ip)

                    os.system("{0} {1}".format(self.editor, name_file))
            except socket.timeout:
                pass

def start_nmsrvr(verbose=False, port=1338, config="nmsrvr.cnfg"):
    global l

    formatter = logging.Formatter("%(asctime)s # %(levelname)-8s %(message)s")

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    l = logging.getLogger()
    l.addHandler(handler)

    if verbose:
        l.setLevel(logging.DEBUG)
    else:
        l.setLevel(logging.INFO)

    server = N4meserver(port, config)
    thread = threading.Thread(target=server.serve, args=())
    thread.daemon = True
    thread.start()

def main():
    p = argparse.ArgumentParser()
    p.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")
    p.add_argument("-p", "--port", type=int, default=1338, help="use another port")
    p.add_argument("-c", "--config", type=str, default="nmsrvr.cnfg", help="use another config file")

    args = p.parse_args()

    start_nmsrvr(args.verbose, args.port, args.config)

    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()
