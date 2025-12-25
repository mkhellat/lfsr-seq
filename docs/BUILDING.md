# Building the Sphinx Documentation

This guide explains how to build and use the Sphinx documentation for lfsr-seq.

## Prerequisites

Before building the documentation, ensure you have:

1. **Python 3.8+** installed
2. **SageMath** installed (for running examples)
3. **Virtual environment** set up (recommended)

## Quick Start

### Using Make (Recommended)

The easiest way to build the documentation is using the Makefile:

```bash
# Build HTML documentation
make docs

# Clean documentation build artifacts
make docs-clean

# Start live documentation server (auto-reload on changes)
make docs-live
```

The built documentation will be in `docs/_build/html/`. Open `docs/_build/html/index.html` in your browser.

### Manual Build

If you prefer to build manually:

1. **Install Sphinx and theme**:
   ```bash
   # In your virtual environment
   pip install sphinx sphinx-rtd-theme
   
   # Or system-wide
   python3 -m pip install sphinx sphinx-rtd-theme
   ```

2. **Build HTML documentation**:
   ```bash
   cd docs
   sphinx-build -b html . _build/html
   ```

3. **View the documentation**:
   ```bash
   # Open in browser
   # Linux:
   xdg-open _build/html/index.html
   
   # macOS:
   open _build/html/index.html
   
   # Windows:
   start _build/html/index.html
   ```

## Build Options

### HTML Output (Default)

Builds HTML documentation with the Read the Docs theme:

```bash
make docs
# or
cd docs && sphinx-build -b html . _build/html
```

### PDF Output

Build PDF documentation (requires LaTeX):

```bash
cd docs
sphinx-build -b latex . _build/latex
cd _build/latex
make pdf
```

### Other Formats

Sphinx supports many output formats:

```bash
cd docs

# EPUB (e-book format)
sphinx-build -b epub . _build/epub

# Single HTML page
sphinx-build -b singlehtml . _build/singlehtml

# Man pages
sphinx-build -b man . _build/man

# Texinfo
sphinx-build -b texinfo . _build/texinfo
```

## Live Documentation Server

For development, you can use a live server that automatically rebuilds when files change:

```bash
# Install sphinx-autobuild
pip install sphinx-autobuild

# Start server
make docs-live
# or
cd docs && sphinx-autobuild . _build/html --host 0.0.0.0 --port 8000
```

The documentation will be available at `http://localhost:8000` and will automatically reload when you make changes.

## Documentation Structure

The documentation is organized as follows:

```
docs/
├── conf.py              # Sphinx configuration
├── index.rst            # Main documentation index
├── installation.rst     # Installation guide
├── user_guide.rst      # User guide
├── mathematical_background.rst  # Mathematical theory
├── examples.rst         # Usage examples
├── api/                 # API reference
│   ├── index.rst       # API index
│   ├── core.rst        # Core module
│   ├── analysis.rst    # Analysis module
│   ├── polynomial.rst  # Polynomial module
│   ├── field.rst       # Field module
│   ├── synthesis.rst  # Synthesis module
│   ├── statistics.rst # Statistics module
│   ├── export.rst     # Export module
│   ├── io.rst         # I/O module
│   ├── formatter.rst  # Formatter module
│   └── cli.rst        # CLI module
└── _build/             # Build output (generated)
```

## Configuration

The Sphinx configuration is in `docs/conf.py`. Key settings:

- **Project name**: `lfsr-seq`
- **Theme**: Read the Docs (`sphinx_rtd_theme`)
- **Extensions**: autodoc, viewcode, napoleon, mathjax, intersphinx
- **Math support**: MathJax for LaTeX equations

## Troubleshooting

### Import Errors

If you get import errors when building:

1. **Ensure the package is installed**:
   ```bash
   pip install -e .
   ```

2. **Check Python path**: The `conf.py` adds the project root to `sys.path`, but ensure you're in the right directory.

### Missing Dependencies

If Sphinx extensions fail:

```bash
pip install sphinx sphinx-rtd-theme sphinx-autobuild
```

### SageMath Import Issues

If SageMath imports fail during documentation build:

- The documentation will still build, but examples requiring SageMath won't run
- This is expected if SageMath isn't available
- The API documentation will still be generated correctly

### Clean Build

If you encounter issues, try a clean build:

```bash
make docs-clean
make docs
```

## Continuous Integration

The documentation can be built in CI/CD pipelines:

```yaml
# Example GitHub Actions step
- name: Build documentation
  run: |
    pip install sphinx sphinx-rtd-theme
    cd docs
    sphinx-build -b html . _build/html
```

## Publishing Documentation

### Read the Docs

To publish on Read the Docs:

1. Connect your GitHub repository to Read the Docs
2. Read the Docs will automatically build from the `docs/` directory
3. Ensure `requirements.txt` or `pyproject.toml` includes Sphinx dependencies

### GitHub Pages

To publish on GitHub Pages:

1. Build the documentation:
   ```bash
   make docs
   ```

2. Copy to `gh-pages` branch:
   ```bash
   git checkout --orphan gh-pages
   git rm -rf .
   cp -r docs/_build/html/* .
   git add .
   git commit -m "Add documentation"
   git push origin gh-pages
   ```

3. Enable GitHub Pages in repository settings

### Local Web Server

For local viewing:

```bash
cd docs/_build/html
python3 -m http.server 8000
# Open http://localhost:8000 in browser
```

## Updating Documentation

When adding new modules or functions:

1. **Add API documentation**: Create or update files in `docs/api/`
2. **Update index**: Add new sections to `docs/index.rst` if needed
3. **Rebuild**: Run `make docs` to see changes
4. **Test**: Verify all links work and examples run correctly

## Best Practices

1. **Keep documentation up to date**: Update docs when code changes
2. **Use examples**: Include code examples for all major functions
3. **Cross-reference**: Use `:ref:` and `:mod:` for linking between sections
4. **Math notation**: Use proper LaTeX for mathematical expressions
5. **Version control**: Commit documentation changes with code changes

## Additional Resources

- [Sphinx Documentation](https://www.sphinx-doc.org/)
- [Read the Docs Theme](https://sphinx-rtd-theme.readthedocs.io/)
- [reStructuredText Primer](https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html)
