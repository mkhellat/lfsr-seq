# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
import warnings

# CRITICAL: Suppress SageMath deprecation warnings BEFORE any imports
# These warnings cause Sphinx to hang during autodoc processing
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=".*is superseded.*")
warnings.filterwarnings("ignore", message=".*Importing.*from here is deprecated.*")
warnings.filterwarnings("ignore", message=".*combinat.species.*")

# Add the project root to the path
sys.path.insert(0, os.path.abspath(".."))

# -- Project information -----------------------------------------------------

project = "lfsr-seq"
copyright = "2023-2025, Mohammadreza Khellat"
author = "Mohammadreza Khellat"
release = "0.2.0"

# -- General configuration ----------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
    "sphinx.ext.mathjax",
    "sphinx.ext.intersphinx",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Options for HTML output -------------------------------------------------

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

# -- Extension configuration -------------------------------------------------

# Napoleon settings for Google-style docstrings
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False

# Autodoc settings
autodoc_member_order = "bysource"
autodoc_default_options = {
    "members": True,
    "undoc-members": False,  # Don't show undocumented members to reduce noise
    "show-inheritance": False,  # Disable to avoid SageMath inheritance chains
    "imported-members": False,  # Don't show imported members from SageMath
    "special-members": False,  # Don't show special members (__init__, etc.) unless documented
}

# Ignore certain members that come from SageMath
autodoc_mock_imports = []

# Skip certain modules during autodoc to avoid hanging
# (This lambda is replaced by the function below)

# Suppress warnings from SageMath's internal docstrings and formatting issues
suppress_warnings = [
    "autodoc.import_object",
    "ref.python",
    "autodoc",
    "ref.ref",
    "ref.doc",
]

# Skip members that cause issues with SageMath
def autodoc_skip_member(app, what, name, obj, skip, options):
    """Skip problematic members during autodoc."""
    # Skip private members
    if name.startswith("_"):
        return True
    # Skip SageMath functions that cause docstring errors
    if name == "lattice_polytope":
        return True
    # Skip if it's a SageMath object (check type string)
    if hasattr(obj, "__module__") and obj.__module__ and "sage" in obj.__module__:
        if name not in ["GF", "MatrixSpace", "VectorSpace", "SR"]:  # Keep essential ones
            return True
    return skip

def setup(app):
    """Setup function for Sphinx."""
    app.connect("autodoc-skip-member", autodoc_skip_member)

# Intersphinx mapping
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "sage": ("https://doc.sagemath.org/html/en/reference/", None),
}

# Add project description
project_description = (
    "A comprehensive tool for analyzing Linear Feedback Shift Register sequences, "
    "computing periods, and determining characteristic polynomials over finite fields."
)

# HTML theme options
html_theme_options = {
    "prev_next_buttons_location": "bottom",
    "style_external_links": False,
    "vcs_pageview_mode": "",
    "style_nav_header_background": "#2980B9",
    # Toc options
    "collapse_navigation": True,
    "sticky_navigation": True,
    "navigation_depth": 4,
    "includehidden": True,
    "titles_only": False,
}

# Add custom CSS
html_css_files = [
    "custom.css",
]

# Logo (if you have one)
# html_logo = "../artwork/icon.png"
# html_favicon = "../artwork/icon.png"

