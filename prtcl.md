# Prtcl spec

## General

Prtcl runs on udp. Each prtcl message has 6 bytes. 2 bytes are delimiting command bytes which ensure that the udp packet is not completely broken.
The remaining 4 bytes are command specific payload.
The actual game server runs on port 1337, the nameserver runs on port 1338.

## Commands

| sender      | port | cmd             | cmd byte | payload                                                                 | payload bytes example | broadcast |
|-------------|------|-----------------|----------|-------------------------------------------------------------------------|-----------------------|-----------|
| controller  | 1337 | keep alive      | 0x10     | buttons state (byte 0)                                                  | 0x23 0xXX 0xXX 0xXX   | -         |
| controller  | 1337 | buttons changed | 0x11     | new buttons state (byte 0) + button change mask (byte 1)                | 0x23 0x42 0xXX 0xXX   | -         |
| game server | 1337 | set led 0       | 0x20     | r (byte 0) + g (byte 1) + b (byte 2) + brightness (byte 3, 5 bits, lsb) | 0xFF 0xFF 0xFF 0x1F   | -         |
| game server | 1337 | set led 1       | 0x21     | r (byte 0) + g (byte 1) + b (byte 2) + brightness (byte 3, 5 bits, lsb) | 0xFF 0x00 0x00 0x1F   | -         |
| game server | 1337 | propagate host  | 0x30     | server identification color, bytes as in set led                        | -                     | *         |
| controller | 1337 | ask host        | 0x31     | not used                                                                | -                     | *         |
| controller | 1338 | set name        | 0x40     | not used                                                                | -                     | *         |

## Game server and name server

The game server and the name server communicate over a tcp connection on port 1338. The prtcl goes as follows:

1. The game server connects to the name server
2. It sends the ip address it wants to have resolved as a null terminated string
3. If a name has been set, the name server now sends this name as a null terminated string
4. Everytime the name changes, the name server sends the new name over the established tcp connection
