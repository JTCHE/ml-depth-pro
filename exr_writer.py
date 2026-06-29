import struct
import numpy as np
from pathlib import Path


def save_exr(depth_array, output_path):
    """Write float32 depth array to a single-channel (R) uncompressed EXR file."""
    depth_array = depth_array.astype(np.float32)
    if depth_array.ndim != 2:
        raise ValueError(f"Expected 2D array, got {depth_array.ndim}D")

    height, width = depth_array.shape
    buf = bytearray()

    def w_attr(name, type_name, data):
        buf.extend(name.encode('ascii') + b'\x00')
        buf.extend(type_name.encode('ascii') + b'\x00')
        buf.extend(struct.pack('<I', len(data)))
        buf.extend(data)

    # Magic + version (2 = scanline, no flags)
    buf.extend(b'\x76\x2f\x31\x01')
    buf.extend(struct.pack('<I', 2))

    # channels: R, FLOAT(2), pLinear=0, xSampling=1, ySampling=1, list terminator
    chan = b'R\x00' + struct.pack('<i', 2) + b'\x00\x00\x00\x00' + struct.pack('<ii', 1, 1) + b'\x00'
    w_attr('channels',            'chlist',      chan)
    w_attr('compression',         'compression', b'\x00')  # NO_COMPRESSION
    w_attr('dataWindow',          'box2i',       struct.pack('<iiii', 0, 0, width - 1, height - 1))
    w_attr('displayWindow',       'box2i',       struct.pack('<iiii', 0, 0, width - 1, height - 1))
    w_attr('lineOrder',           'lineOrder',   b'\x00')  # INCREASING_Y
    w_attr('pixelAspectRatio',    'float',       struct.pack('<f', 1.0))
    w_attr('screenWindowCenter',  'v2f',         struct.pack('<ff', 0.0, 0.0))
    w_attr('screenWindowWidth',   'float',       struct.pack('<f', 1.0))
    buf.extend(b'\x00')  # end of header

    # Scanline offset table — one uint64 per scanline, filled in below
    offset_table_pos = len(buf)
    buf.extend(b'\x00' * (height * 8))

    # Pixel data
    for y in range(height):
        struct.pack_into('<Q', buf, offset_table_pos + y * 8, len(buf))
        buf.extend(struct.pack('<i', y))
        buf.extend(struct.pack('<I', width * 4))
        buf.extend(depth_array[y].tobytes())

    with open(str(output_path), 'wb') as f:
        f.write(buf)
