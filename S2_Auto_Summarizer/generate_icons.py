"""Generate teal (#4ECDC4) placeholder PNG icons for the Auto Summarizer extension."""

import os
import struct
import zlib

ICON_COLOR = (0x4E, 0xCD, 0xC4)  # #4ecdc4 — teal accent
SIZES = [16, 48, 128]


def make_png(size, r, g, b):
    def chunk(name, data):
        c = struct.pack('>I', len(data)) + name + data
        return c + struct.pack('>I', zlib.crc32(name + data) & 0xFFFFFFFF)

    ihdr = struct.pack('>IIBBBBB', size, size, 8, 2, 0, 0, 0)
    raw_rows = b''
    for _ in range(size):
        row = b'\x00' + bytes([r, g, b] * size)
        raw_rows += row
    idat = zlib.compress(raw_rows)

    return (
        b'\x89PNG\r\n\x1a\n'
        + chunk(b'IHDR', ihdr)
        + chunk(b'IDAT', idat)
        + chunk(b'IEND', b'')
    )


def main():
    icons_dir = os.path.join(os.path.dirname(__file__), 'icons')
    os.makedirs(icons_dir, exist_ok=True)
    r, g, b = ICON_COLOR
    for size in SIZES:
        path = os.path.join(icons_dir, f'icon{size}.png')
        with open(path, 'wb') as f:
            f.write(make_png(size, r, g, b))
        print(f'Created {path}')


if __name__ == '__main__':
    main()
