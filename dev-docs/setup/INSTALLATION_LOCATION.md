# Installation Location

## Current State

After running `make install` or `make install-dev`, the package is installed in **editable mode** (development mode) in the virtual environment.

### Package Installation Location

- **Virtual Environment**: `.venv/` (created automatically)
- **Package Location**: `.venv/lib/python3.X/site-packages/lfsr-seq.egg-link`
  - Points to the project root directory (editable install)
- **Package Metadata**: `.venv/lib/python3.X/site-packages/lfsr-seq.egg-info/`

### Command Installation

**Currently**: `lfsr-seq` is **NOT** installed as a command because entry points are not yet configured.

- The script `lfsr-seq` in the project root must be run directly: `./lfsr-seq`
- No command is created in `.venv/bin/lfsr-seq`

**After Refactoring** (when entry points are enabled):

- **Command Location**: `.venv/bin/lfsr-seq`
- **Access**: Available as `lfsr-seq` command when venv is activated
- **Installation**: Created automatically by pip when installing the package

### Verification

To check where the package is installed:

```bash
# Activate venv
source .venv/bin/activate

# Check package location
python -c "import lfsr; print(lfsr.__file__)"  # After refactoring

# Check if command exists (after entry points are enabled)
which lfsr-seq  # Should show: /path/to/project/.venv/bin/lfsr-seq

# List installed packages
pip list | grep lfsr-seq
```

### Editable Install Details

With `pip install -e .` (editable mode):
- Changes to source code are immediately available
- No need to reinstall after code changes
- Package points to project root directory
- Perfect for development

### Production Install

When building a wheel and installing from it:
- Package would be installed in `.venv/lib/python3.X/site-packages/lfsr_seq/`
- Command would be at `.venv/bin/lfsr-seq` (after entry points enabled)
- Changes require rebuilding and reinstalling

