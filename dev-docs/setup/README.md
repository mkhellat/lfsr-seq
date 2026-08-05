# Setup & Installation Documentation

This directory contains documentation about building and installing the project.

## Documents

### [BUILDING.md](./BUILDING.md)
**Building the Sphinx Documentation**

Complete guide for building Sphinx documentation, including:
- Quick start with Make
- Manual build instructions
- HTML, PDF, and other output formats
- Live documentation server
- Troubleshooting

### [INSTALLATION_LOCATION.md](./INSTALLATION_LOCATION.md)
**Installation Location Details**

Information about where the package is installed:
- Virtual environment structure
- Editable install details
- Command installation status
- Production install information

### [legacy-lfsr-seq-wrapper](./legacy-lfsr-seq-wrapper)
**Archived, non-functional pre-packaging entry point**

The original root-level `lfsr-seq` script, kept here only as historical
reference. It predates the `src/` and `app/` layout migrations and its
import no longer resolves. Use the installed console-script (`lfsr-seq`,
available on PATH once `app/.venv` is activated and the package is
installed) instead.

## Quick Links

- [Main Documentation Index](../README.md)
- [Parallel Processing Docs](../parallel/README.md)
- [Implementation Plans](../plans/README.md)
