# Prtcl spec

## General

Each prtcl message has 6 bytes. 2 bytes are delimiting command bytes which ensure that the udp packet is not completely broken.
The remaining 4 bytes are command specific payload.

## Commands

| sender     | cmd             | cmd byte | payload                                                                 | payload bytes example | broadcast |
|------------|-----------------|----------|-------------------------------------------------------------------------|-----------------------|-----------|
| controller | keep alive      | 0x10     | buttons state (byte 0)                                                  | 0x11 0x10 0xXX 0xXX   | -         |
| controller | buttons changed | 0x11     | new buttons state (byte 0) + button change mask (byte 1)                | 0x11 0xXX 0xXX 0xXX   | -         |
| server     | set led 0       | 0x20     | r (byte 0) + g (byte 1) + b (byte 2) + brightness (byte 3, 5 bits, lsb) | 0xFF 0xFF 0xFF 0x1F   | -         |
| server     | set led 1       | 0x21     | r (byte 0) + g (byte 1) + b (byte 2) + brightness (byte 3, 5 bits, lsb) | 0xFF 0x00 0x00 0x1F   | -         |
| server     | set host        | 0x30     | not used                                                                | -                     | *         |
| controller | ask host        | 0x31     | not used                                                                | -                     | *         |
