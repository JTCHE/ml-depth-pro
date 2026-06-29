"""
depth_to_normals.py
Convert a folder of grayscale depth maps to RGB-encoded normal maps.
Usage: python depth_to_normals.py <input_dir> <output_dir> [--blur <sigma>]
"""
import argparse, os, glob
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter

def depth_to_normal(depth_f32, blur_sigma=2.0):
    """depth_f32: H x W float, any range. Returns H x W x 3 uint8 normal map."""
    if blur_sigma > 0:
        depth_f32 = gaussian_filter(depth_f32, sigma=blur_sigma)

    # Finite differences
    dz_dx = np.gradient(depth_f32, axis=1)
    dz_dy = np.gradient(depth_f32, axis=0)

    # Surface tangents -> normal = (-dz/dx, -dz/dy, 1), then normalize
    nx = -dz_dx
    ny = -dz_dy
    nz = np.ones_like(nx)
    length = np.sqrt(nx**2 + ny**2 + nz**2) + 1e-8
    nx /= length; ny /= length; nz /= length

    # Remap [-1,1] -> [0,255]
    rgb = np.stack([
        (nx * 0.5 + 0.5) * 255,
        (ny * 0.5 + 0.5) * 255,
        (nz * 0.5 + 0.5) * 255,
    ], axis=-1).clip(0, 255).astype(np.uint8)
    return rgb

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_dir")
    parser.add_argument("output_dir")
    parser.add_argument("--blur", type=float, default=2.0,
                        help="Gaussian blur sigma before gradient (reduces noise, default 2.0)")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    files = sorted(glob.glob(os.path.join(args.input_dir, "*.png")) +
                   glob.glob(os.path.join(args.input_dir, "*.exr")) +
                   glob.glob(os.path.join(args.input_dir, "*.tif")))

    if not files:
        print("No images found."); return

    print(f"Processing {len(files)} frames...")
    for i, fpath in enumerate(files):
        img = Image.open(fpath).convert("L")
        depth = np.array(img, dtype=np.float32) / 255.0
        normal_rgb = depth_to_normal(depth, blur_sigma=args.blur)
        out_name = os.path.splitext(os.path.basename(fpath))[0] + "_normal.png"
        Image.fromarray(normal_rgb).save(os.path.join(args.output_dir, out_name))
        if (i + 1) % 10 == 0 or i == len(files) - 1:
            print(f"  {i+1}/{len(files)}")

    print(f"Done. Normals saved to: {args.output_dir}")

if __name__ == "__main__":
    main()
