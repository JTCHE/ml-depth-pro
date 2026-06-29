# Windows Setup Notes

## Environment
- Python 3.14 at `C:\Users\john\AppData\Local\Programs\Python\Python314\`
- `depth-pro-run` installed in Python 3.14 Scripts
- FFmpeg at `C:\Program Files\ffmpeg\bin\ffmpeg.exe`

## OpenEXR Workaround
The official OpenEXR Python bindings fail to install on Windows 11 (DLL load error). Two shim files in this repo replace them transparently:

- **`OpenEXR.py`** — drop-in module that mimics the `OpenEXR` + `Imath` interfaces
- **`exr_writer.py`** — actual writer: tries FFmpeg (PFM → EXR via deflate), falls back to pure-Python binary EXR

`npz_to_exr.py` imports `OpenEXR` as normal and is completely unmodified; Python loads `OpenEXR.py` from the same directory instead of the missing library.

### FFmpeg path (preferred)
Converts float32 numpy array → PFM tempfile → `ffmpeg -vf` → EXR (scanline, deflate, float32).

### Pure Python fallback
Writes OpenEXR v1 binary directly from numpy if FFmpeg is missing. Valid but uncompressed.

## Pipeline

```
image.jpg
  └─► depth-pro-run -i image.jpg -o depth/ --skip-display
        └─► depth/image.npz  +  depth/image.npz.jpg (turbo colormap preview)
              └─► python npz_to_exr.py -i depth/image.npz --no-png
                    └─► depth/image.exr  (float32, single channel R, metric depth in metres)
```

Use `run_depth_to_exr.bat` to automate this — just drag one or more images onto it.
