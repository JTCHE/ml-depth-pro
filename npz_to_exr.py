import argparse
import sys
from pathlib import Path
import numpy as np
import OpenEXR
import Imath
from exr_writer import save_exr as _write_exr


def load_npz(npz_path):
    """Load depth data from NPZ file."""
    data = np.load(npz_path)
    print(f"Available arrays in NPZ: {data.files}")

    # Try common depth array names
    if 'depth' in data.files:
        depth = data['depth']
    elif 'arr_0' in data.files:
        depth = data['arr_0']
    else:
        raise ValueError(f"Could not find 'depth' or 'arr_0' in NPZ file. Available: {data.files}")

    return depth.astype(np.float32)


def save_exr(depth, output_path):
    """Save depth map as EXR file."""
    height, width = depth.shape
    header = OpenEXR.Header(width, height)

    pixel_type = Imath.PixelType(Imath.PixelType.FLOAT)
    header['channels'] = {'R': Imath.Channel(pixel_type)}

    exr = OpenEXR.OutputFile(str(output_path), header)
    exr.writePixels({'R': depth.tobytes()})
    exr.close()

    print(f"EXR saved: {output_path}")


def save_normalized_exr(depth, output_path):
    d_min, d_max = depth.min(), depth.max()
    normalized = ((depth - d_min) / (d_max - d_min)).astype(np.float32)
    _write_exr(normalized, output_path)
    print(f"Normalized EXR saved: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Convert NPZ depth files to EXR format',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('-i', '--input', required=True, help='Input NPZ file path')
    parser.add_argument('-o', '--output', help='Output EXR file path or directory (default: same dir as input)')
    parser.add_argument('--no-png', action='store_true', help='Skip PNG output')

    args = parser.parse_args()

    # Validate input file
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)

    # Determine output paths
    if args.output:
        out = Path(args.output)
        exr_path = (out / input_path.stem).with_suffix('.exr') if out.is_dir() else out
    else:
        exr_path = input_path.with_suffix('.exr')

    normalized_exr_path = exr_path.with_name(exr_path.stem + '_normalized.exr')

    # Process
    try:
        depth = load_npz(input_path)
        save_exr(depth, exr_path)

        if not args.no_png:
            save_normalized_exr(depth, normalized_exr_path)

        print("Conversion completed successfully")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()