"""Render SVGs with distro libraries in an isolated system-Python worker.

The caller may be Conda Python. Do not dlopen system graphics libraries in
that process: its already-loaded libraries and loader paths can be incompatible.
"""
import argparse
import ctypes as C
import ctypes.util
import os
from pathlib import Path
import re
import subprocess
import sys


def worker_environment():
    env = os.environ.copy()
    for key in ('LD_LIBRARY_PATH', 'LD_PRELOAD', 'LD_AUDIT', 'PYTHONHOME', 'PYTHONPATH'):
        env.pop(key, None)
    # ctypes.find_library may invoke ldconfig/compiler tools; use distro tools.
    env['PATH'] = os.defpath
    return env


def worker_command():
    for python in ('/usr/bin/python3', '/bin/python3'):
        if Path(python).is_file():
            return [python, '-I', '-S', str(Path(__file__).resolve())]
    raise RuntimeError('System Python is required for SVG rendering; install python3')


def run_worker(*args):
    result = subprocess.run(worker_command()+list(map(str,args)),
                            env=worker_environment(), capture_output=True,
                            text=True, timeout=60)
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip() or f'exit {result.returncode}'
        raise RuntimeError('Isolated SVG renderer failed: '+detail)


def check_native_renderer():
    run_worker('--check')


def render_png(source, target):
    run_worker(Path(source).resolve(), Path(target).resolve())


def load_libraries():
    names = [ctypes.util.find_library(lib) for lib in ('rsvg-2','cairo','gobject-2.0')]
    if not all(names):
        raise RuntimeError('missing librsvg/Cairo/GObject; install librsvg2-2 libcairo2')
    return [C.CDLL(name) for name in names]


def render_native(source, target, libraries):
    raw = source.read_bytes()
    size = re.search(r'width="(\d+)" height="(\d+)"',raw.decode())
    if size is None:
        raise ValueError('SVG must give integer width and height')
    w,h = map(int,size.groups())
    rsvg,cairo,go = libraries
    rsvg.rsvg_handle_new_from_data.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p]
    rsvg.rsvg_handle_new_from_data.restype=C.c_void_p
    rsvg.rsvg_handle_render_cairo.argtypes=[C.c_void_p,C.c_void_p]
    rsvg.rsvg_handle_render_cairo.restype=C.c_int
    cairo.cairo_image_surface_create.argtypes=[C.c_int,C.c_int,C.c_int]
    cairo.cairo_image_surface_create.restype=C.c_void_p
    cairo.cairo_create.argtypes=[C.c_void_p]
    cairo.cairo_create.restype=C.c_void_p
    cairo.cairo_surface_write_to_png.argtypes=[C.c_void_p,C.c_char_p]
    cairo.cairo_surface_write_to_png.restype=C.c_int
    cairo.cairo_destroy.argtypes=[C.c_void_p]
    cairo.cairo_surface_destroy.argtypes=[C.c_void_p]
    go.g_object_unref.argtypes=[C.c_void_p]
    handle = rsvg.rsvg_handle_new_from_data(raw,len(raw),None)
    if not handle:
        raise RuntimeError('librsvg could not parse SVG')
    surface = ctx = None
    try:
        surface = cairo.cairo_image_surface_create(0,w,h)
        ctx = cairo.cairo_create(surface)
        if not rsvg.rsvg_handle_render_cairo(handle,ctx):
            raise RuntimeError('librsvg could not render SVG')
        status = cairo.cairo_surface_write_to_png(surface,os.fsencode(target))
        if status:
            raise RuntimeError(f'Cairo could not write PNG (status {status})')
    finally:
        if ctx:
            cairo.cairo_destroy(ctx)
        if surface:
            cairo.cairo_surface_destroy(surface)
        go.g_object_unref(handle)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true')
    parser.add_argument('paths',nargs='*',type=Path)
    args = parser.parse_args()
    if (args.check and args.paths) or (not args.check and len(args.paths)!=2):
        parser.error('use --check or SOURCE.svg TARGET.png')
    try:
        libraries = load_libraries()
        if not args.check:
            render_native(*args.paths,libraries)
    except (OSError,RuntimeError,ValueError) as exc:
        print(str(exc),file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
