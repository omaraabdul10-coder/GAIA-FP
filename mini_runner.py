"""Minimal test runner (no pytest): python tools/mini_runner.py tests/test_x.py ...  Runs every top-level test_* function."""
import importlib.util, os, sys, time, traceback
root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'); sys.path[:0] = [os.path.join(root, 'src'), os.path.join(root, 'tests')]
import types, inspect, tempfile, pathlib
try: import pytest  # noqa
except ImportError:
    import _minipytest; sys.modules['pytest'] = _minipytest   # raises-only shim
ok = bad = 0
for f in sys.argv[1:]:
    spec = importlib.util.spec_from_file_location(os.path.basename(f)[:-3], f); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    for n in sorted(k for k in dir(m) if k.startswith('test_') and callable(getattr(m, k))):
        t0 = time.time()
        try:
            fn = getattr(m, n); kw = {'tmp_path': pathlib.Path(tempfile.mkdtemp())} if 'tmp_path' in inspect.signature(fn).parameters else {}
            fn(**kw); ok += 1; print(f'PASS {os.path.basename(f)}::{n} ({time.time()-t0:.1f}s)')
        except Exception: bad += 1; print(f'FAIL {os.path.basename(f)}::{n}'); traceback.print_exc()
print(f'{ok} passed, {bad} failed'); sys.exit(1 if bad else 0)
