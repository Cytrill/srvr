import uinput
import time
import socketserver
import select
import threading
import socket
import time

class C0ntroller(uinput.Device):
    BTN_0_MASK = 0x10
    BTN_1_MASK = 0x20
    BTN_22MASK = 0x40
    BTN_3_MASK = 0x80
    JOY_UP_MASK = 0x01
    JOY_RIGHT_MASK = 0x02
    JOY_DOWN_MASK = 0x04
    JOY_LEFT_MASK = 0x08

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

            if event_diff & self.BTN_0_MASK != 0:
                if event & self.BTN_0_MASK != 0:
                    self.emit(uinput.BTN_0, 1)
                else:
                    self.emit(uinput.BTN_0, 0)

            if event_diff & self.BTN_1_MASK != 0:
                if event & self.BTN_1_MASK != 0:
                    self.emit(uinput.BTN_1, 1)
                else:
                    self.emit(uinput.BTN_1, 0)

            if event_diff & self.BTN_2_MASK != 0:
                if event & self.BTN_2_MASK != 0:
                    self.emit(uinput.BTN_2, 1)
                else:
                    self.emit(uinput.BTN_2, 0)

            if event_diff & self.BTN_3_MASK != 0:
                if event & self.BTN_3_MASK != 0:
                    self.emit(uinput.BTN_3, 1)
                else:
                    self.emit(uinput.BTN_3, 0)

        self.prev_event = event

class S3rver(object):
    HOST = "0.0.0.0"
    PORT = 1337

    CMD_KEEP_ALIVE = 0x7F
    CMD_FIRE = 0xFF

    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.server_addr = (self.HOST, self.PORT)
        self.sock.bind(self.server_addr)

        self.controllers = {}

    def serve(self):
        while True:
            data, client_addr = self.sock.recvfrom(2)

            if client_addr in self.controllers:
                if data[0] == self.CMD_KEEP_ALIVE:
                    self.controllers[client_addr].refresh()
                    print("keep alive")
                elif data[0] == self.CMD_FIRE:
                    self.controllers[client_addr].fire(data[1])
                    self.controllers[client_addr].refresh()
            else:
                self.controllers[client_addr] = C0ntroller(str(client_addr))

def main():
    server = S3rver()
    server.serve()

if __name__ == "__main__":
    main()
