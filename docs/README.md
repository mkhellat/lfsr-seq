# Sphinx Documentation for lfsr-seq

This directory contains the Sphinx documentation for the lfsr-seq package.

## Quick Start

### Build Documentation

```bash
# From project root
make docs
```

The built documentation will be in `docs/_build/html/`. Open `docs/_build/html/index.html` in your browser.

### Live Development Server

For development with auto-reload:

```bash
make docs-live
```

The documentation will be available at `http://localhost:8000` and will automatically reload when files change.

## Documentation Structure

```
docs/
├── conf.py                    # Sphinx configuration
├── index.rst                   # Main documentation index
├── BUILDING.md                 # Detailed build instructions
├── installation.rst           # Installation guide
├── user_guide.rst             # User guide and CLI usage
├── examples.rst                # Usage examples
├── mathematical_background.rst # Mathematical theory
├── api/                        # API reference
│   ├── index.rst              # API index
│   ├── core.rst               # Core module
│   ├── analysis.rst           # Analysis module
│   ├── polynomial.rst        # Polynomial module
│   ├── field.rst              # Field module
│   ├── synthesis.rst         # Synthesis module
│   ├── statistics.rst        # Statistics module
│   ├── export.rst            # Export module
│   ├── io.rst                 # I/O module
│   ├── formatter.rst          # Formatter module
│   └── cli.rst                # CLI module
└── _static/                    # Static files (CSS, images)
    └── custom.css             # Custom styling
```

## Available Make Targets

- `make docs` - Build HTML documentation
- `make docs-clean` - Clean documentation build artifacts
- `make docs-live` - Start live documentation server (auto-reload)

## Output Formats

The documentation can be built in multiple formats:

- **HTML** (default): `make docs` or `sphinx-build -b html . _build/html`
- **PDF**: Requires LaTeX, see `docs/BUILDING.md`
- **EPUB**: `sphinx-build -b epub . _build/epub`
- **Single HTML**: `sphinx-build -b singlehtml . _build/singlehtml`

## Requirements

- Python 3.8+
- Sphinx (`pip install sphinx sphinx-rtd-theme`)
- SageMath (for running examples, optional for building docs)

## For More Information

See `docs/BUILDING.md` for comprehensive build instructions, troubleshooting, and publishing options.
