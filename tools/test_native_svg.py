"""Regression for a Conda-style Fontconfig collision with system librsvg."""
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import warnings

from native_svg import check_native_renderer, render_png, worker_command, worker_environment


class NativeSvgTests(unittest.TestCase):
    def test_renderer_environment_is_local_to_worker(self):
        with patch.dict(os.environ, {'LD_LIBRARY_PATH':'/conda/lib',
                                     'LD_PRELOAD':'/conda/lib/old.so',
                                     'PYTHONHOME':'/conda', 'PYTHONPATH':'/conda/site'}):
            env=worker_environment()
            for key in ('LD_LIBRARY_PATH','LD_PRELOAD','PYTHONHOME','PYTHONPATH'):
                self.assertNotIn(key,env)
                self.assertIn(key,os.environ)
            self.assertEqual(env['PATH'],os.defpath)

    def test_atlas_source_compiles_with_escape_warnings_as_errors(self):
        source=Path(__file__).resolve().parents[1]/'20-tide-decentralized-neural-network/explorers/hb-timed/build_atlas.py'
        with warnings.catch_warnings():
            warnings.simplefilter('error',SyntaxWarning)
            warnings.simplefilter('error',DeprecationWarning)
            compile(source.read_text(),str(source),'exec')

    def test_png_render_survives_incompatible_fontconfig_search_path(self):
        compiler=shutil.which('cc')
        if not compiler:
            self.skipTest('native collision fixture requires a C compiler')
        try:
            check_native_renderer()
        except (RuntimeError,OSError,subprocess.SubprocessError) as exc:
            self.skipTest(f'native graphics dependencies unavailable: {exc}')
        with tempfile.TemporaryDirectory(prefix='svg-fontconfig-collision-') as directory:
            root=Path(directory)
            fake=root/'libfontconfig.so.1'
            subprocess.run([compiler,'-shared','-fPIC','-Wl,-soname,libfontconfig.so.1',
                            '-x','c','-','-o',str(fake)],
                           input='int tide_incompatible_fontconfig(void) { return 0; }\n',
                           text=True,capture_output=True,check=True)
            poison=os.environ.copy()
            poison['LD_LIBRARY_PATH']=str(root)
            control=subprocess.run(worker_command()+['--check'],env=poison,
                                   text=True,capture_output=True,timeout=30)
            self.assertNotEqual(control.returncode,0,'fixture did not reproduce a library collision')
            self.assertIn('undefined symbol',control.stderr)
            source,target=root/'sample.svg',root/'sample.png'
            source.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="12" height="10">'
                              '<rect width="12" height="10" fill="blue"/></svg>')
            with patch.dict(os.environ,poison):
                render_png(source,target)
            raw=target.read_bytes()
            self.assertEqual(raw[:8],b'\x89PNG\r\n\x1a\n')
            self.assertEqual(struct.unpack('>II',raw[16:24]),(12,10))


if __name__=='__main__':
    unittest.main()
