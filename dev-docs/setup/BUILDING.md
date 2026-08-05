# Building the Sphinx Documentation

This guide explains how to build and use the Sphinx documentation for lfsr-seq.

**All commands below are run from `app/`**, not the git repository root —
that's where `docs/`, the `Makefile`, and `pyproject.toml` live (see the
root `CLAUDE.md` for the full repository layout).

## Prerequisites

Before building the documentation, ensure you have:

1. **Python 3.8+** installed
2. **SageMath** installed (for running examples; the build itself succeeds
   without it, but autodoc-driven API pages for sage-dependent modules
   will be sparser — see "SageMath Import Issues" below)
3. **Virtual environment** set up (recommended)

## Quick Start

### Using Make (Recommended)

The easiest way to build the documentation is using the Makefile:

```bash
# Build HTML documentation
make docs

# Build PDF documentation (requires LaTeX)
make docs-pdf

# Clean documentation build artifacts
make docs-clean

# Clean PDF documentation build artifacts
make docs-clean-pdf

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

**Using Make (Recommended)**:
```bash
make docs-pdf
```

**Manual Build**:
```bash
cd docs
sphinx-build -b latex . _build/latex
cd _build/latex
make all-pdf
```

The PDF will be generated in `docs/_build/latex/` with a name like `lfsr-seq.pdf`.

**Note**: Building PDF requires a LaTeX distribution (e.g., TeX Live, MiKTeX). On Linux:
```bash
# Debian/Ubuntu
sudo apt-get install texlive-latex-base texlive-latex-extra texlive-fonts-recommended

# Arch Linux
sudo pacman -S texlive-core texlive-bin texlive-latexextra
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

The documentation lives in `app/docs/` and is organized as follows:

```
app/docs/
├── conf.py                          # Sphinx configuration
├── index.rst                        # Main documentation index
├── installation.rst                 # Installation guide
├── user_guide.rst                   # User guide (includes Glossary)
├── examples.rst                     # Usage examples
├── mathematical_background.rst      # Mathematical theory
├── correlation_attacks.rst          # Correlation attack framework
├── algebraic_attacks.rst            # Berlekamp-Massey / algebraic attacks
├── time_memory_tradeoff.rst         # TMTO attacks
├── stream_ciphers.rst               # Stream cipher implementations
├── advanced_lfsr_structures.rst     # NFSR/filtered/clock-controlled/multi-output
├── theoretical_analysis.rst         # Theoretical analysis features
├── ml_integration.rst               # Machine learning integration
├── parallelization.rst              # Parallel state enumeration
├── optimization_techniques.rst      # Optimization/caching techniques
├── nist_sp800_22.rst                # NIST SP 800-22 statistical test suite
├── visualization.rst                # Visualization features
├── api/                             # API reference (one file per lfsr module)
│   ├── index.rst
│   ├── core.rst
│   ├── analysis.rst
│   ├── polynomial.rst
│   ├── field.rst
│   ├── synthesis.rst
│   ├── statistics.rst
│   ├── export.rst
│   ├── io.rst
│   ├── formatter.rst
│   ├── cli.rst
│   ├── attacks.rst
│   ├── tmto.rst
│   ├── nist.rst
│   ├── optimization.rst
│   ├── ciphers.rst
│   ├── advanced.rst
│   └── visualization.rst
└── _build/                          # Build output (generated, gitignored)
```

This list reflects the current set of `.rst` files; if you add a new one,
update this tree and `app/docs/index.rst`'s toctree together so this guide
doesn't drift out of sync again.

## Configuration

The Sphinx configuration is in `app/docs/conf.py`. Key settings:

- **Project name**: `lfsr-seq`
- **Theme**: Read the Docs (`sphinx_rtd_theme`)
- **Extensions**: autodoc, viewcode, napoleon, mathjax, intersphinx, sphinx_proof (theorem/proof environments)
- **Math support**: MathJax for LaTeX equations

## Troubleshooting

### Import Errors

If you get import errors when building:

1. **Ensure the package is installed**:
 ```bash
 pip install -e .
 ```

2. **Check Python path**: `conf.py` adds `app/src` to `sys.path` (relative to `app/docs/`), so autodoc can import `lfsr` directly even without an editable install — but you still need to run the build from `app/docs/` (or via `make docs` from `app/`) for that relative path to resolve correctly.

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

**Status quo**: `.github/workflows/ci.yml` does **not** currently build the
documentation — it only runs tests, lint/format checks, and package
builds. Documentation building is a manual (`make docs`) or local step
today, not a CI gate.

If you want to add it, a step like this would work (adjust
`working-directory` to match the job's `defaults`, since the package now
lives under `app/`):

```yaml
# Example GitHub Actions step (not currently present in ci.yml)
- name: Build documentation
  working-directory: app
  run: |
    pip install sphinx sphinx-rtd-theme
    cd docs
    sphinx-build -b html . _build/html
```

## Publishing Documentation

**Status quo**: neither Read the Docs nor GitHub Pages is currently
configured for this project — there is no `.readthedocs.yaml` in the
repo and no Pages-publishing workflow in `.github/workflows/`. The
sections below are setup instructions for if/when you want to wire one
of these up, not a description of an existing pipeline.

### Read the Docs (not yet configured)

To publish on Read the Docs:

1. Connect your GitHub repository to Read the Docs
2. Add a `.readthedocs.yaml` at the git repository root pointing Read the
   Docs at `app/docs/conf.py` and telling it to install the package from
   `app/` (Read the Docs' default assumes `docs/` and `pyproject.toml`
   sit at the repo root, which is no longer true here — this needs
   explicit `sphinx.configuration`/`python.install` overrides)
3. Ensure `app/pyproject.toml`'s `dev` extra includes Sphinx dependencies

### GitHub Pages (not yet configured)

To publish on GitHub Pages:

1. Build the documentation:
   ```bash
   cd app
   make docs
   ```

2. Copy to `gh-pages` branch (paths below assume you're at the git
   repository root, not `app/`):
   ```bash
   git checkout --orphan gh-pages
   git rm -rf .
   cp -r app/docs/_build/html/* .
   git add .
   git commit -m "Add documentation"
   git push origin gh-pages
   ```

3. Enable GitHub Pages in repository settings

### Local Web Server

For local viewing:

```bash
cd app/docs/_build/html
python3 -m http.server 8000
# Open http://localhost:8000 in browser
```

## Updating Documentation

When adding new modules or functions:

1. **Add API documentation**: Create or update files in `app/docs/api/`
2. **Update index**: Add new sections to `app/docs/index.rst` if needed
3. **Rebuild**: Run `make docs` (from `app/`) to see changes
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
