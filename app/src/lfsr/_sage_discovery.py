#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SageMath interpreter discovery.

SageMath is not available on PyPI and cannot be pip-installed into a
virtual environment. Depending on how it was installed, its modules may
live in the current interpreter's site-packages already (e.g. a venv
created with --system-site-packages against a system Python that also
hosts SageMath), or in a completely separate interpreter/prefix that
only the `sage` command on PATH knows how to locate (common with
Debian/Ubuntu, Homebrew, and conda installs).

This module has no SageMath imports of its own, so it is always safely
importable -- including when SageMath is not installed at all -- and
provides a single, reusable way to make `import sage` work regardless
of which of the above situations applies.
"""

import os
import subprocess
import sys

_discovery_attempted = False
_discovery_succeeded = False


def ensure_sage_importable(timeout: float = 5.0) -> bool:
    """Make ``import sage`` succeed in the current process if at all possible.

    Tries, in order:
    1. A direct ``import sage`` (works if SageMath's modules are already
       on ``sys.path`` -- e.g. system-site-packages venvs, or running
       under ``sage -python`` directly).
    2. Shelling out to the ``sage`` command (if present on PATH) to ask
       its own interpreter for its ``sys.path``, then inserting any new,
       existing directories from that list into this process's
       ``sys.path``. This works regardless of whether SageMath's Python
       is the system Python, a bundled interpreter, or a conda
       environment, since it never assumes anything about where
       SageMath's Python lives -- it only asks the `sage` command
       itself.

    Idempotent and cheap to call repeatedly: the outcome of the first
    call is cached and returned on subsequent calls without repeating
    the subprocess call.

    Returns:
        True if ``import sage`` can be expected to succeed after this
        call, False if SageMath could not be located at all.
    """
    global _discovery_attempted, _discovery_succeeded

    if _discovery_attempted:
        return _discovery_succeeded
    _discovery_attempted = True

    try:
        import sage  # noqa: F401

        _discovery_succeeded = True
        return True
    except ImportError:
        pass

    try:
        result = subprocess.run(
            ["sage", "-c", "import sys; print('\\n'.join(sys.path))"],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
        return False

    if result.returncode != 0:
        return False

    for path in result.stdout.strip().split("\n"):
        if path and path not in sys.path and os.path.isdir(path):
            sys.path.insert(0, path)

    try:
        import sage  # noqa: F401

        _discovery_succeeded = True
        return True
    except ImportError:
        return False
