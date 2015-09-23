# Prtcl spec

## General

Each prtcl message has 5 bytes. 2 bytes are delimiting command bytes which ensure that the udp packet is not completely broken.
The remaining 3 bytes are command specific payload.

## Commands

| sender     | cmd             | cmd byte | payload                                                  | payload bytes example |
|------------|-----------------|----------|----------------------------------------------------------|-----------------------|
| controller | buttons changed | 0x10     | new buttons state (byte 0) + button change mask (byte 1) | 0x11 0x10 0xXX        |
| server     | set led 0       | 0x20     | r (byte 0) + g (byte 1) + b (byte 2)                     | 0xFF 0xFF 0xFF        |
| server     | set led 1       | 0x21     | r (byte 0) + g (byte 1) + b (byte 2)                     | 0xFF 0x00 0x00        |
| server     | set led 2       | 0x22     | r (byte 0) + g (byte 1) + b (byte 2)                     | 0x00 0xFF 0x00        |
| server     | set led 3       | 0x23     | r (byte 0) + g (byte 1) + b (byte 2)                     | 0x00 0x00 0xFF        |
