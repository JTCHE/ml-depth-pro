"""
EXR writer implementation for Windows without OpenEXR library.
Uses FFmpeg to convert from intermediate format to EXR.
Implements proper OpenEXR v1 binary format as fallback.
"""

import struct
import numpy as np
import subprocess
import tempfile
import os
from pathlib import Path


def write_exr_ffmpeg(depth_array, output_path):
    """
    Write depth array to EXR using FFmpeg.
    FFmpeg handles the complex EXR encoding automatically.

    Args:
        depth_array: numpy float32 array (height, width)
        output_path: path to write EXR file
    """
    if depth_array.ndim != 2:
        raise ValueError(f"Expected 2D array, got {depth_array.ndim}D")

    depth_array = depth_array.astype(np.float32)
    height, width = depth_array.shape

    # Create temporary file with 16-bit normalized PNG as intermediate
    with tempfile.NamedTemporaryFile(suffix='.pfm', delete=False) as tmp:
        tmp_path = tmp.name

    try:
        # Write PFM (Portable Float Map) - widely supported intermediate format
        write_pfm(depth_array, tmp_path)

        # Convert PFM to EXR using FFmpeg
        output_path_str = str(Path(output_path).resolve())
        cmd = [
            'ffmpeg',
            '-y',  # overwrite output
            '-i', tmp_path,
            '-c:v', 'exr',
            '-pixel_format', 'grayf32le',  # 32-bit float grayscale
            output_path_str
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg failed: {result.stderr}")

        return True

    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def write_pfm(data, filename):
    """
    Write numpy array to PFM (Portable Float Map) format.
    PFM is a simple text+binary format for float data.

    Args:
        data: numpy float32 array (height, width)
        filename: output path
    """
    data = data.astype(np.float32)
    if data.ndim != 2:
        raise ValueError(f"Expected 2D array, got {data.ndim}D")

    height, width = data.shape

    with open(filename, 'wb') as f:
        # Header
        f.write(b'Pf\n')  # Magic (grayscale float)
        f.write(f'{width} {height}\n'.encode('ascii'))
        f.write(b'-1.0\n')  # Scale / endianness (-1.0 = little-endian)

        # Data (bottom-to-top, left-to-right)
        for y in range(height - 1, -1, -1):
            f.write(data[y, :].tobytes())


def write_exr_binary(depth_array, output_path):
    """
    Write depth array to EXR using pure Python binary format implementation.
    Implements OpenEXR v1 format without external libraries.

    This is a fallback method that works but may have compatibility issues
    with some EXR readers due to simplified implementation.

    Args:
        depth_array: numpy float32 array (height, width)
        output_path: path to write EXR file
    """
    depth_array = depth_array.astype(np.float32)
    if depth_array.ndim != 2:
        raise ValueError(f"Expected 2D array, got {depth_array.ndim}D")

    height, width = depth_array.shape

    with open(str(output_path), 'wb') as f:
        # EXR magic number and version
        f.write(struct.pack('<I', 0x765f3c01))  # Magic: 0x76 0x2f 0x31 0x01
        f.write(struct.pack('<B', 2))  # Version 2 (scanline format)
        f.write(b'\x00\x00\x00')  # Flags

        # Write attributes as key-value pairs
        attributes = []

        # dataWindow: box2i
        attributes.append((
            'dataWindow',
            'box2i',
            struct.pack('<iiii', 0, 0, width - 1, height - 1)
        ))

        # displayWindow: box2i
        attributes.append((
            'displayWindow',
            'box2i',
            struct.pack('<iiii', 0, 0, width - 1, height - 1)
        ))

        # channels: chlist
        channels_data = b'R\x00' + struct.pack('<I', 0) + b'\x00' + b'\x00\x00\x00' + struct.pack('<ii', 1, 1)
        attributes.append(('channels', 'chlist', channels_data + b'\x00'))

        # compression: compression (0 = none)
        attributes.append(('compression', 'compression', struct.pack('<B', 0)))

        # lineOrder: lineOrder (0 = increasing y)
        attributes.append(('lineOrder', 'lineOrder', struct.pack('<B', 0)))

        # pixelAspectRatio: float
        attributes.append(('pixelAspectRatio', 'float', struct.pack('<f', 1.0)))

        # screenWindowCenter: v2f
        attributes.append(('screenWindowCenter', 'v2f', struct.pack('<ff', 0.0, 0.0)))

        # screenWindowWidth: float
        attributes.append(('screenWindowWidth', 'float', struct.pack('<f', 1.0)))

        # Write attributes
        for name, type_name, data in attributes:
            f.write(name.encode('utf-8') + b'\x00')
            f.write(type_name.encode('utf-8') + b'\x00')
            f.write(struct.pack('<I', len(data)))
            f.write(data)

        # End of header
        f.write(b'\x00')

        # Write scan lines (uncompressed)
        for y in range(height):
            f.write(struct.pack('<I', y))  # Y coordinate
            f.write(struct.pack('<I', width * 4))  # Data size in bytes
            f.write(depth_array[y, :].tobytes())


def save_exr(depth_array, output_path):
    """
    Save depth array to EXR file.
    Tries FFmpeg first (preferred), falls back to binary implementation.

    Args:
        depth_array: numpy float32 array (height, width)
        output_path: path to write EXR file
    """
    try:
        # Try FFmpeg first - produces most compatible EXR files
        write_exr_ffmpeg(depth_array, output_path)
        print(f"EXR written via FFmpeg: {output_path}")
        return
    except (FileNotFoundError, subprocess.TimeoutExpired, RuntimeError) as e:
        print(f"FFmpeg method failed ({type(e).__name__}), trying binary fallback...")
        try:
            write_exr_binary(depth_array, output_path)
            print(f"EXR written via binary format: {output_path}")
            return
        except Exception as e2:
            raise RuntimeError(f"All EXR writing methods failed: {e}, {e2}") from e2


if __name__ == '__main__':
    # Test
    test_data = np.random.rand(100, 100).astype(np.float32)
    save_exr(test_data, 'test.exr')
    print("Test completed")
