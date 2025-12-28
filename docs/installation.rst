Installation
============

Prerequisites
-------------

- **Python 3.8 or higher**
- **SageMath 9.7 or higher** - See `SageMath Installation <https://www.sagemath.org/>`_

Installing SageMath
-------------------

SageMath must be installed separately as it's not available via PyPI:

**Debian/Ubuntu:**

.. code-block:: bash

   sudo apt-get update
   sudo apt-get install sagemath

**Fedora/RHEL:**

.. code-block:: bash

   sudo dnf install sagemath

**Arch Linux:**

.. code-block:: bash

   sudo pacman -S sagemath

**macOS (Homebrew):**

.. code-block:: bash

   brew install sagemath

**Conda:**

.. code-block:: bash

   conda install -c conda-forge sage

Installation Methods
--------------------

Quick Install (Recommended)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use the automated bootstrap script:

.. code-block:: bash

   ./bootstrap

Or with development dependencies:

.. code-block:: bash

   ./bootstrap --dev

Bootstrap script options:

.. code-block:: bash

   ./bootstrap                    # Basic installation
   ./bootstrap --dev              # With development dependencies
   ./bootstrap --no-venv          # Skip virtual environment (system-wide)
   ./bootstrap --clean            # Clean build artifacts and caches
   ./bootstrap --uninstall        # Uninstall the package

Manual Installation
~~~~~~~~~~~~~~~~~~~

1. Check your environment:

   .. code-block:: bash

      ./scripts/check-environment.sh

2. Create a virtual environment (recommended):

   .. code-block:: bash

      python3 -m venv .venv
      source .venv/bin/activate

3. Install the package:

   .. code-block:: bash

      pip install -e .

   Or with development dependencies:

   .. code-block:: bash

      pip install -e ".[dev]"

Using Make
~~~~~~~~~~

.. code-block:: bash

   make dev-setup
   source .venv/bin/activate

Available Make targets:

- ``make venv`` - Create virtual environment
- ``make install`` - Install package in development mode
- ``make install-dev`` - Install with development dependencies
- ``make test`` - Run tests
- ``make test-cov`` - Run tests with coverage report
- ``make lint`` - Run linting checks
- ``make format`` - Format code
- ``make format-check`` - Check code formatting
- ``make type-check`` - Run type checking
- ``make check-env`` - Check environment setup
- ``make smoke-test`` - Run smoke tests
- ``make build`` - Build distribution packages
- ``make clean`` - Remove build artifacts
- ``make clean-venv`` - Remove virtual environment
- ``make distclean`` - Remove all generated files (including venv)
- ``make uninstall`` - Uninstall the package
- ``make docs`` - Build Sphinx documentation (HTML)
- ``make docs-clean`` - Clean documentation build artifacts
- ``make docs-pdf`` - Build Sphinx documentation (PDF)
- ``make docs-clean-pdf`` - Clean PDF documentation build artifacts
- ``make docs-live`` - Start live documentation server (auto-reload)

Verification
------------

After installation, verify everything works:

.. code-block:: bash

   ./scripts/check-environment.sh
   ./scripts/smoke-test.sh

Cleaning and Uninstallation
----------------------------

To clean build artifacts:

.. code-block:: bash

   make clean              # Remove build artifacts
   make clean-venv         # Remove virtual environment
   make distclean          # Remove all generated files (including venv)
   ./bootstrap --clean     # Clean using bootstrap script

To uninstall the package:

.. code-block:: bash

   make uninstall          # Uninstall using Make
   ./bootstrap --uninstall # Uninstall using bootstrap script

**Note:** The ``--clean`` and ``--uninstall`` options in bootstrap do not remove the virtual environment. To remove it, use ``make clean-venv`` or ``rm -rf .venv``.

