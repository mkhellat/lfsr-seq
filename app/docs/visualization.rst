Visualization
=============

This section provides comprehensive documentation for visualization features,
enabling interactive and publication-quality graphical representations of LFSR
analysis results.

**Key Terminology**:

- **Visualization**: A graphical representation of data or analysis results.
  Visualizations help understand patterns, relationships, and properties that
  may not be obvious from raw data.

- **Static Plot**: A non-interactive image file (PNG, SVG, PDF) that can be
  included in documents or presentations.

- **Interactive Plot**: A plot that allows user interaction (zooming, panning,
  tooltips) typically in HTML format using libraries like Plotly.

- **Publication Quality**: Visualizations suitable for inclusion in research
  papers, with high resolution, proper formatting, and clear labels.

Introduction
------------

The visualization features provide graphical representations of LFSR analysis
results, enabling:

1. **Period Analysis**: Visualize period distributions and relationships
2. **State Space Exploration**: Understand state transitions and cycles
3. **Statistical Insights**: See statistical properties graphically
4. **Attack Visualization**: Understand attack processes and results
5. **Publication Support**: Generate publication-quality figures

Period Distribution Visualization
---------------------------------

**What is Period Distribution Visualization?**

Period distribution visualization shows how periods are distributed across all
possible initial states of an LFSR, helping understand the period structure.

**Key Features**:

- **Histogram Plots**: Bar charts showing period frequency
- **Theoretical Bounds**: Overlay theoretical maximum period
- **Interactive Exploration**: Zoom, pan, and hover for details
- **Multiple Formats**: Export to PNG, SVG, PDF, HTML

**Python API Usage**:

.. code-block:: python

   from lfsr.visualization import plot_period_distribution
   from lfsr.visualization.base import VisualizationConfig, OutputFormat
   
   period_dict = {1: 1, 3: 2, 6: 4, 12: 8}
   config = VisualizationConfig(
       interactive=True,
       output_format=OutputFormat.HTML
   )
   
   fig = plot_period_distribution(
       period_dict,
       theoretical_max_period=15,
       is_primitive=False,
       config=config,
       output_file="period_dist.html"
   )

**Command-Line Usage**:

.. code-block:: bash

   lfsr-seq coefficients.csv 2 --plot-period-distribution period_dist.png

State Transition Diagrams
-------------------------

**What is a State Transition Diagram?**

A state transition diagram is a graph showing how LFSR states transition from
one to another, revealing the cycle structure of the state space.

**Key Features**:

- **Graph Representation**: Nodes (states) and edges (transitions)
- **Cycle Highlighting**: Visual identification of cycles
- **State Labeling**: Clear state representation
- **Export Formats**: PNG, SVG, PDF, Graphviz DOT

**Python API Usage**:

.. code-block:: python

   from lfsr.visualization import generate_state_transition_diagram
   
   # After analysis
   graph = generate_state_transition_diagram(
       state_sequences,
       period_dict,
       max_states=50,
       output_file="transitions.png"
   )

**Command-Line Usage**:

.. code-block:: bash

   lfsr-seq coefficients.csv 2 --plot-state-transitions transitions.png

Statistical Distribution Plots
------------------------------

**What are Statistical Distribution Plots?**

Statistical plots visualize the statistical properties of LFSR sequences,
including period distributions, sequence analysis, and comparisons.

**Key Features**:

- **Histogram Plots**: Period frequency distributions
- **Box Plots**: Statistical summaries
- **Comparison Plots**: Multiple LFSR comparisons
- **Publication Quality**: High-resolution output

**Python API Usage**:

.. code-block:: python

   from lfsr.visualization import plot_period_statistics
   
   fig = plot_period_statistics(
       period_dict,
       theoretical_max_period=15,
       is_primitive=False,
       output_file="stats.png"
   )

**Command-Line Usage**:

.. code-block:: bash

   lfsr-seq coefficients.csv 2 --plot-period-statistics stats.png

3D State Space Visualization
----------------------------

**What is 3D State Space Visualization?**

3D visualization provides an interactive three-dimensional representation of
the LFSR state space, enabling exploration of state relationships.

**Key Features**:

- **3D Scatter Plots**: States represented in 3D space
- **Cycle Visualization**: Cycles shown as paths
- **Interactive Exploration**: Rotate, zoom, pan
- **State Coloring**: Color by period or other properties

**Python API Usage**:

.. code-block:: python

   from lfsr.visualization import plot_3d_state_space
   
   fig = plot_3d_state_space(
       state_sequences,
       period_dict,
       max_states=100,
       output_file="state_space_3d.html"
   )

**Command-Line Usage**:

.. code-block:: bash

   lfsr-seq coefficients.csv 2 --plot-3d-state-space state_space.html

Attack Visualization
--------------------

**What is Attack Visualization?**

Attack visualization shows the progress and results of cryptanalytic attacks,
helping understand attack effectiveness and identify vulnerabilities.

**Key Features**:

- **Correlation Plots**: Visualize correlation coefficients
- **Success Probability Curves**: Show attack success over time
- **Attack Comparison**: Compare multiple attack methods
- **Progress Tracking**: Visualize attack progress

**Python API Usage**:

.. code-block:: python

   from lfsr.visualization import visualize_correlation_attack
   
   attack_results = {
       'correlations': [0.5, 0.3, 0.7],
       'success_probability': 0.8,
       'attack_successful': True
   }
   
   fig = visualize_correlation_attack(
       attack_results,
       output_file="attack_viz.png"
   )

**Command-Line Usage**:

.. code-block:: bash

   lfsr-seq coefficients.csv 2 --visualize-attack attack.png

Output Formats
--------------

Visualizations can be exported in multiple formats:

- **PNG**: Raster image format (good for documents)
- **SVG**: Vector format (scalable, good for web)
- **PDF**: Vector format (good for papers)
- **HTML**: Interactive format (requires plotly)

**Format Selection**:

.. code-block:: bash

   # Static PNG
   lfsr-seq coefficients.csv 2 --plot-period-distribution plot.png --viz-format png
   
   # Interactive HTML
   lfsr-seq coefficients.csv 2 --plot-period-distribution plot.html --viz-format html
   
   # Or use --viz-interactive flag
   lfsr-seq coefficients.csv 2 --plot-period-distribution plot.html --viz-interactive

API Reference
-------------

See :doc:`api/visualization` for complete API documentation.

Glossary
--------

**3D Visualization**
   A three-dimensional graphical representation of data, allowing interactive
   exploration from different angles.

**Histogram**
   A graphical representation of data distribution using bars, where each bar
   represents a range of values.

**Interactive Plot**
   A plot that allows user interaction such as zooming, panning, and viewing
   detailed information on hover.

**Publication Quality**
   Visualizations suitable for inclusion in research papers, with high
   resolution, proper formatting, and clear labels.

**State Transition Diagram**
   A graph representation showing how LFSR states transition from one to
   another, with nodes representing states and edges representing transitions.

**Static Plot**
   A non-interactive image file that can be included in documents or
   presentations.

**Visualization**
   A graphical representation of data or analysis results.

Further Reading
---------------

- Matplotlib Documentation: https://matplotlib.org/
- Plotly Documentation: https://plotly.com/python/
- NetworkX Documentation: https://networkx.org/
