"""
Drop-in replacement module for OpenEXR library.
Allows existing npz_to_exr.py to work without installing OpenEXR.
Uses the exr_writer module for actual EXR writing.
"""

import sys
from pathlib import Path
import struct
import numpy as np

# Import our custom writer
from exr_writer import save_exr as _save_exr_impl


class PixelType:
    """Mimics Imath.PixelType"""
    FLOAT = 0
    HALF = 1
    UINT = 2

    def __init__(self, type_val):
        self.value = type_val


class Channel:
    """Mimics Imath.Channel"""
    def __init__(self, pixel_type):
        self.pixel_type = pixel_type


class Header:
    """Mimics OpenEXR.Header"""
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.channels = {}
        self._attributes = {
            'dataWindow': (0, 0, width - 1, height - 1),
            'displayWindow': (0, 0, width - 1, height - 1),
        }

    def __setitem__(self, key, value):
        if key == 'channels':
            self.channels = value
        else:
            self._attributes[key] = value

    def __getitem__(self, key):
        if key == 'channels':
            return self.channels
        return self._attributes.get(key)


class OutputFile:
    """Mimics OpenEXR.OutputFile"""
    def __init__(self, filename, header):
        self.filename = str(filename)
        self.header = header
        self.pixels = {}

    def writePixels(self, pixels_dict):
        """
        Write pixels to file.
        pixels_dict should be {'R': byte_data, ...}
        """
        self.pixels = pixels_dict

    def close(self):
        """
        Close and write the file.
        Converts the stored pixel data back to array and writes EXR.
        """
        if not self.pixels or 'R' not in self.pixels:
            raise ValueError("No pixel data written")

        # Reconstruct float32 array from bytes
        pixel_bytes = self.pixels['R']
        height, width = self.header.height, self.header.width

        # Convert bytes back to float32 array
        data = np.frombuffer(pixel_bytes, dtype=np.float32).reshape((height, width))

        # Write using our implementation
        _save_exr_impl(data, self.filename)


# Expose as module
sys.modules['OpenEXR'] = sys.modules[__name__]
sys.modules['Imath'] = sys.modules[__name__]
