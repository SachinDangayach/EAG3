#!/usr/bin/env python3
"""Generate solid-color PNG icons for the Pomodoro Timer extension."""
import struct
import zlib
import os


def png_chunk(chunk_type, data):
    body = chunk_type + data
    crc = zlib.crc32(body) & 0xFFFFFFFF
    return struct.pack('>I', len(data)) + body + struct.pack('>I', crc)


def create_png(size, r, g, b):
    ihdr = png_chunk(b'IHDR', struct.pack('>IIBBBBB', size, size, 8, 2, 0, 0, 0))
    row = b'\x00' + bytes([r, g, b] * size)
    raw = row * size
    idat = png_chunk(b'IDAT', zlib.compress(raw, 9))
    iend = png_chunk(b'IEND', b'')
    return b'\x89PNG\r\n\x1a\n' + ihdr + idat + iend


os.makedirs('icons', exist_ok=True)

# Tomato red: #E74C3C
for size in [16, 32, 48, 128]:
    path = f'icons/icon{size}.png'
    with open(path, 'wb') as f:
        f.write(create_png(size, 231, 76, 60))
    print(f'Created {path}')

print('Done!')
