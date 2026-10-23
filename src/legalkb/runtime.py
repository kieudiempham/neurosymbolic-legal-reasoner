"""Locate SWI-Prolog without changing the shared compiler module."""
import os
import shutil
from pathlib import Path


def swipl() -> Path:
    from .compile import SWIPL
    choices = [os.environ.get('LEGALKB_SWIPL'), shutil.which('swipl'),
               '/opt/homebrew/bin/swipl', str(SWIPL)]
    for candidate in choices:
        if candidate and Path(candidate).is_file():
            return Path(candidate)
    raise RuntimeError('SWI-Prolog is required; install it or set LEGALKB_SWIPL')


def compile_sample(con, path):
    """Compile then validate with the local runtime, including on macOS/Linux."""
    import subprocess
    from .compile import write_and_check
    report = write_and_check(con, path)
    result = subprocess.run([str(swipl()), '-q', '-g',
                             f"consult('{Path(path).as_posix()}'),halt", '-t', 'halt(1)'],
                            capture_output=True, text=True, timeout=30)
    report['prolog_load_ok'] = result.returncode == 0 and 'ERROR' not in result.stderr
    if not report['prolog_load_ok']:
        raise RuntimeError(result.stderr)
    return report
