# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
import warnings
import logging

# CRITICAL: Suppress SageMath deprecation warnings BEFORE any imports
# These warnings cause Sphinx to hang during autodoc processing
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=".*is superseded.*")
warnings.filterwarnings("ignore", message=".*Importing.*from here is deprecated.*")
warnings.filterwarnings("ignore", message=".*combinat.species.*")

# Set up logging filter EARLY to suppress duplicate warnings
# This must be done before Sphinx initializes its logging system
class DuplicateWarningFilter(logging.Filter):
    """Filter to suppress duplicate object description warnings."""
    def filter(self, record):
        try:
            msg = record.getMessage()
        except:
            try:
                if hasattr(record, 'args') and record.args:
                    msg = str(record.msg) % record.args
                else:
                    msg = str(record.msg)
            except:
                msg = str(record)
        if "duplicate object description" in msg.lower():
            return False
        return True

# Apply filter to root logger early
_dup_filter = DuplicateWarningFilter()
_root_logger = logging.getLogger()
for handler in _root_logger.handlers:
    handler.addFilter(_dup_filter)
# Also add to any future handlers
_original_addHandler = _root_logger.addHandler
def _addHandler_with_filter(handler):
    handler.addFilter(_dup_filter)
    return _original_addHandler(handler)
_root_logger.addHandler = _addHandler_with_filter

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

# Configure autodoc to not process type hints as objects
# This prevents duplicate warnings when the same type appears in multiple modules
autodoc_type_aliases = {
    'TextIO': 'typing.TextIO',
    'Optional': 'typing.Optional',
    'List': 'typing.List',
    'Dict': 'typing.Dict',
    'Tuple': 'typing.Tuple',
    'Set': 'typing.Set',
    'Any': 'typing.Any',
    'Union': 'typing.Union',
}

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Options for HTML output -------------------------------------------------

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

# -- Extension configuration -------------------------------------------------

# RST substitutions for special characters
rst_epilog = """
.. |rho| unicode:: U+03C1 .. Greek small letter rho
"""

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

# Suppress duplicate object warnings by not documenting type annotations
autodoc_typehints = "none"  # Don't document type hints to avoid duplicate warnings
autodoc_typehints_format = "short"  # Use short format if typehints are shown
autodoc_preserve_defaults = False  # Don't preserve default values to reduce complexity

# Don't create cross-references for typing types to avoid duplicate warnings
nitpicky = False  # Don't warn about missing cross-references
nitpick_ignore = [
    ("py:class", "typing.TextIO"),
    ("py:class", "typing.Any"),
    ("py:class", "typing.Optional"),
    ("py:class", "typing.List"),
    ("py:class", "typing.Dict"),
    ("py:class", "typing.Tuple"),
    ("py:class", "typing.Set"),
    ("py:class", "typing.Union"),
    ("py:class", "cysignals.signals.AlarmInterrupt"),
    ("py:class", "cysignals.signals.SignalError"),
    ("py:class", "cypari2.handle_error.PariError"),
    ("py:class", "sage.matrix.matrix_space.MatrixSpace"),
]

# Ignore certain members that come from SageMath
autodoc_mock_imports = []

# Skip certain modules during autodoc to avoid hanging
# (This lambda is replaced by the function below)

# Suppress warnings from SageMath's internal docstrings and formatting issues
# Note: Duplicate object warnings are suppressed via logging filter and ref.duplicate
suppress_warnings = [
    "autodoc.import_object",
    "ref.python",
    "autodoc",
    "ref.ref",
    "ref.doc",
    "app.add_directive",
    "misc.highlighting_failure",  # Suppress unknown lexer warnings (e.g., csv)
    "ref.duplicate",  # Suppress duplicate object description warnings (typing.*, sage.*, etc.)
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
    # Skip documenting imported types from typing, cysignals, cypari2, sage modules
    # These cause duplicate object warnings when documented across multiple modules
    # This includes type annotations that appear in docstrings
    if what in ("class", "data", "attribute", "exception"):
        if hasattr(obj, "__module__") and obj.__module__:
            module = obj.__module__
            # Skip standard library typing types (typing.TextIO, typing.Any, etc.)
            if module.startswith("typing"):
                return True
            # Skip SageMath-related types (cysignals, cypari2, sage modules)
            if any(module.startswith(prefix) for prefix in ["cysignals", "cypari2", "sage"]):
                return True
    # Skip if it's a SageMath object (check type string)
    if hasattr(obj, "__module__") and obj.__module__ and "sage" in obj.__module__:
        if name not in ["GF", "MatrixSpace", "VectorSpace", "SR"]:  # Keep essential ones
            return True
    return skip

def setup(app):
    """Setup function for Sphinx."""
    app.connect("autodoc-skip-member", autodoc_skip_member)
    
    # Suppress duplicate object warnings using Sphinx's warning system
    # The root cause: Sphinx creates object descriptions for types in docstrings
    # When the same type appears in multiple modules, it's seen as a duplicate
    import sphinx.util.logging
    import logging
    
    # Create comprehensive filter
    class DuplicateWarningFilter(logging.Filter):
        """Filter to suppress duplicate object description warnings."""
        def filter(self, record):
            try:
                msg = record.getMessage()
            except:
                try:
                    if hasattr(record, 'args') and record.args:
                        msg = str(record.msg) % record.args
                    else:
                        msg = str(record.msg)
                except:
                    msg = str(record)
            if "duplicate object description" in msg.lower():
                return False
            return True
    
    # Apply filter comprehensively to all loggers
    dup_filter = DuplicateWarningFilter()
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        handler.addFilter(dup_filter)
    
    # Also add to Sphinx-specific loggers
    for name in ['sphinx', 'sphinx.ref', 'sphinx.application', 'sphinx.environment']:
        logger = logging.getLogger(name)
        for handler in logger.handlers:
            handler.addFilter(dup_filter)
    
    # The suppress_warnings is already configured in the config above
    # No need to add it again here

# Intersphinx mapping
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "sage": ("https://doc.sagemath.org/html/en/reference/", None),
}

# LaTeX configuration for PDF output (texinfo-style)
# Define SageMath-specific LaTeX commands and Unicode symbols that appear in docstrings

# LaTeX document class and options (texinfo style)
latex_documents = [
    ('index', 'lfsr-seq.tex', 'lfsr-seq Documentation',
     'Mohammadreza Khellat', 'manual'),
]

# LaTeX settings for texinfo-style output
latex_logo = None  # No logo for cleaner texinfo style
latex_show_urls = 'footnote'  # Show URLs as footnotes (texinfo style)
latex_show_pagerefs = True  # Show page references
latex_toplevel_sectioning = 'section'  # Use sections as top-level

latex_elements = {
    # Use article class with two-column layout (texinfo style)
    'papersize': 'a4paper',
    'pointsize': '10pt',
    'preamble': r'''
% Fix for \omit errors in nested align/split/equation environments
% This is a known issue with Sphinx-generated LaTeX (nested math environments)
\makeatletter
% Comprehensive fix for align environment \omit errors
% Patch the math@cr@@@ command to handle nested structures
\let\old@math@cr@@@\math@cr@@@
\def\math@cr@@@{\old@math@cr@@@}
% Alternative: Allow display breaks to help with nested structures
\allowdisplaybreaks
\makeatother
% Define SageMath-specific LaTeX commands
% Note: amsmath is loaded by Sphinx automatically, don't reload it
\newcommand{\ZZ}{\mathbb{Z}}
\newcommand{\QQ}{\mathbb{Q}}
\newcommand{\RR}{\mathbb{R}}
\newcommand{\CC}{\mathbb{C}}
\newcommand{\FF}{\mathbb{F}}
\newcommand{\NN}{\mathbb{N}}

% Support for Unicode characters that appear in docstrings
\usepackage{textcomp}
\usepackage{amssymb}
% Use inputenc and fontenc for better Unicode support
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
% Fallback for unknown Unicode characters (texinfo style - replace with placeholder)
\DeclareUnicodeCharacter{254E}{-}  % Box-drawing character → dash
\DeclareUnicodeCharacter{2705}{[OK]}  % Checkmark emoji → [OK]
\DeclareUnicodeCharacter{274C}{[X]}  % Cross mark emoji → [X]
\DeclareUnicodeCharacter{26A0}{[!]}  % Warning sign → [!]
% General fallback: use \DeclareUnicodeCharacter for specific characters as needed
% Define Unicode symbol ≡ (U+2261) - use text mode equivalent
% The symbol appears in text, so we need a text-mode version
\DeclareUnicodeCharacter{2261}{$\equiv$}
% Define other common Unicode math symbols (use math mode for text context)
\DeclareUnicodeCharacter{2260}{$\neq$}
\DeclareUnicodeCharacter{2264}{$\leq$}
\DeclareUnicodeCharacter{2265}{$\geq$}
\DeclareUnicodeCharacter{2248}{$\approx$}  % Approximately equal (≈)
\DeclareUnicodeCharacter{2212}{-}
\DeclareUnicodeCharacter{2217}{*}
% Superscript n (ⁿ) - U+207F - use math mode
\DeclareUnicodeCharacter{207F}{\ensuremath{^n}}

% Texinfo-style formatting
% Note: geometry is already loaded by Sphinx, use \geometry{} to modify
\geometry{margin=1in}
% Note: multicol not needed when using twocolumn class option
% Minimal package loading to avoid conflicts with amsmath align environments
% Note: booktabs, titlesec, enumitem, fancyhdr, microtype removed - all cause \omit errors
% Using minimal packages to ensure align environments work correctly
% \usepackage{fancyhdr}  % Commented out - causes \omit errors
% \usepackage{microtype}  % Commented out - causes \omit errors

% Two-column layout (texinfo style)
% Note: twocolumn is set via extraclassoptions
% Set column separation for two-column layout
\setlength{\columnsep}{0.5in}
\setlength{\columnseprule}{0.4pt}

% Compact spacing (texinfo style)
\setlength{\parskip}{0.5em}
\setlength{\parindent}{0pt}
\setlength{\topskip}{1em}

% Professional typography
% Note: microtype removed to avoid \omit errors
% \microtypecontext{spacing=nonfrench}  % Commented out - microtype removed
% \DisableLigatures{encoding = *, family = *}  % Commented out - microtype removed

% Headers and footers (texinfo style)
% Note: fancyhdr removed to avoid \omit errors
% \pagestyle{fancy}  % Commented out - fancyhdr removed
% \fancyhf{}  % Commented out
% \fancyhead[LE]{\leftmark}  % Commented out
% \fancyhead[RO]{\rightmark}  % Commented out
% \fancyfoot[C]{\thepage}  % Commented out
% \renewcommand{\headrulewidth}{0.4pt}  % Commented out
% \renewcommand{\footrulewidth}{0pt}  % Commented out
% Use default page style instead

% Compact section formatting
% Note: titlesec removed to avoid \omit conflicts, using standard LaTeX spacing
% \titlespacing*{\section}{0pt}{1.5em}{0.8em}  % Commented out - titlesec removed
% \titlespacing*{\subsection}{0pt}{1.2em}{0.6em}  % Commented out
% \titlespacing*{\subsubsection}{0pt}{1em}{0.4em}  % Commented out

% Compact list spacing
% enumitem can conflict with amsmath align environments causing \omit errors
% Removed to fix LaTeX compilation issues
% \usepackage{enumitem}  % Commented out - causes \omit errors
% \setlist{nosep, leftmargin=*}  % Commented out
% \setlist[itemize]{topsep=0.2em, itemsep=0.1em}  % Commented out
% \setlist[enumerate]{topsep=0.2em, itemsep=0.1em}  % Commented out
% \setlist[description]{topsep=0.2em, itemsep=0.1em}  % Commented out
% Use standard LaTeX list spacing instead (texinfo style is still maintained)
''',
    # Use two-column layout (texinfo style)
    # Note: twocolumn can cause \omit errors in align environments
    # Temporarily disabled to test if it's the cause
    # 'extraclassoptions': 'twocolumn',  # Commented out - testing if this causes \omit
    # Compact document settings
    'sphinxsetup': 'verbatimwithframe=false, verbatimwrapslines=true, verbatimhintsturnover=false',
}

# Add project description
project_description = (
    "A comprehensive tool for analyzing Linear Feedback Shift Register sequences, "
    "computing periods, and determining characteristic polynomials over finite fields."
)

# HTML theme options (Read the Docs theme)
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

