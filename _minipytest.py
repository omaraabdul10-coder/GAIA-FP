"""Fallback so the new tests also run where pytest is not installed (e.g. the offline analysis sandbox). Provides pytest.raises only."""
import contextlib
@contextlib.contextmanager
def raises(exc, match=None):
    try: yield
    except exc as e:
        if match and match not in str(e): raise AssertionError(f'{type(e).__name__} message {str(e)!r} lacks {match!r}')
        return
    raise AssertionError(f'DID NOT RAISE {exc.__name__}')
