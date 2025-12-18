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

Verification
------------

After installation, verify everything works:

.. code-block:: bash

   ./scripts/check-environment.sh
   ./scripts/smoke-test.sh

