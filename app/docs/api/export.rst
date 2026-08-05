Export Module
==============

The export module provides functions for exporting LFSR analysis results in various formats: JSON, CSV, and XML.

.. automodule:: lfsr.export
   :members:
   :undoc-members:
   :show-inheritance: False
   :imported-members: False

Functions
---------

.. autofunction:: lfsr.export.export_to_json
   :no-index:

Exports analysis results to JSON format with structured metadata and data.

.. autofunction:: lfsr.export.export_to_csv
   :no-index:

Exports analysis results to CSV format with tabular data.

.. autofunction:: lfsr.export.export_to_xml
   :no-index:

Exports analysis results to XML format with hierarchical structure.

.. autofunction:: lfsr.export.get_export_function
   :no-index:

Returns the appropriate export function for a given format name.

NIST Test Suite Export Functions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The export module also provides specialized functions for exporting NIST SP 800-22
test suite results in multiple formats.

.. autofunction:: lfsr.export.export_nist_to_json
   :no-index:

Exports NIST test suite results to JSON format with complete metadata and test results.

.. autofunction:: lfsr.export.export_nist_to_csv
   :no-index:

Exports NIST test suite results to CSV format with tabular data.

.. autofunction:: lfsr.export.export_nist_to_xml
   :no-index:

Exports NIST test suite results to XML format with hierarchical structure.

.. autofunction:: lfsr.export.export_nist_to_html
   :no-index:

Exports NIST test suite results to HTML format with professional styling.

.. autofunction:: lfsr.export.get_nist_export_function
   :no-index:

Returns the appropriate NIST export function for a given format name.

Example
~~~~~~~

.. code-block:: python

   from lfsr.export import export_to_json, export_to_csv, export_to_xml
   from lfsr.core import build_state_update_matrix
   from lfsr.analysis import lfsr_sequence_mapper
   from sage.all import *
   
   # Perform analysis
   coeffs = [1, 1, 0, 1]
   C, CS = build_state_update_matrix(coeffs, 2)
   V = VectorSpace(GF(2), 4)
   seq_dict, period_dict, max_period, periods_sum = lfsr_sequence_mapper(
       C, V, 2, output_file=None, no_progress=True
   )
   
   # Export to different formats
   export_to_json(seq_dict, period_dict, max_period, "results.json", 2, coeffs)
   export_to_csv(seq_dict, period_dict, max_period, "results.csv", 2, coeffs)
   export_to_xml(seq_dict, period_dict, max_period, "results.xml", 2, coeffs)

NIST Test Suite Export Example
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from lfsr.nist import run_nist_test_suite
   from lfsr.export import (
       export_nist_to_json,
       export_nist_to_csv,
       export_nist_to_xml,
       export_nist_to_html
   )
   
   # Run NIST test suite
   sequence = [1, 0, 1, 0] * 250  # 1000 bits
   suite_result = run_nist_test_suite(sequence)
   
   # Export to different formats
   with open('nist_results.json', 'w') as f:
       export_nist_to_json(suite_result, f)
   
   with open('nist_results.csv', 'w') as f:
       export_nist_to_csv(suite_result, f)
   
   with open('nist_results.xml', 'w') as f:
       export_nist_to_xml(suite_result, f)
   
   with open('nist_results.html', 'w') as f:
       export_nist_to_html(suite_result, f)
