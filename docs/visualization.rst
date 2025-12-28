Visualization
=============

This section provides comprehensive documentation for visualization features,
enabling interactive and publication-quality visualizations of LFSR analysis
results.

**Key Terminology**:

- **Visualization**: A graphical representation of data or analysis results
  that helps understand patterns, relationships, and properties.

- **Interactive Plot**: A plot that allows user interaction (zooming, panning,
  tooltips) typically in HTML format.

- **Static Plot**: A non-interactive image file (PNG, SVG, PDF) suitable for
  documents and presentations.

- **Publication Quality**: Visualizations suitable for research papers with
  high resolution and proper formatting.

Introduction
------------

The visualization features provide comprehensive graphical representations
of LFSR analysis results, including:

1. **Period Distributions**: Histograms and statistical plots showing how
   periods are distributed across initial states

2. **State Transitions**: Diagrams showing how states transition and form cycles

3. **Statistical Analysis**: Publication-quality plots for sequence properties

4. **3D Visualizations**: Interactive 3D representations of state spaces

5. **Attack Visualization**: Visual representation of cryptanalytic attacks

Period Distribution Visualization
----------------------------------

**What is Period Distribution Visualization?**

Period distribution visualization shows how periods are distributed across
all possible initial states, helping understand the period structure of an LFSR.

**Key Features**:

- Histogram of period distribution
- Comparison with theoretical bounds
- Cumulative distribution plots
- Interactive exploration

**Python API Usage**:

.. code-block:: python

   from lfsr.visualization.period_graphs import plot_period_distribution
   
   period_dict = {1: 1, 3: 2, 6: 4, 12: 8}
   fig = plot_period_distribution(
       period_dict,
       theoretical_max_period=15,
       is_primitive=False,
       output_file="period_dist.png"
   )

**Command-Line Usage**:

.. code-block:: bash

   lfsr-seq coefficients.csv 2 --plot-period-distribution period_dist.png

State Transition Diagrams
-------------------------

**What is a State Transition Diagram?**

A state transition diagram is a graph showing how LFSR states transition from
one to another, with cycles highlighted.

**Key Features**:

- Graph representation of state transitions
- Cycle highlighting
- State labeling
- Export to Graphviz DOT format
- Export to image formats

**Python API Usage**:

.. code-block:: python

   from lfsr.visualization.state_diagrams import generate_state_transition_diagram
   
   sequences = {0: [[1,0,0], [0,1,0], [0,0,1], [1,0,0]]}
   periods = {0: 3}
   graph = generate_state_transition_diagram(
       sequences,
       periods,
       output_file="state_diagram.png"
   )

**Command-Line Usage**:

.. code-block:: bash

   lfsr-seq coefficients.csv 2 --plot-state-transitions state_diagram.png

Statistical Distribution Plots
------------------------------

**What are Statistical Distribution Plots?**

Statistical plots provide publication-quality visualizations of period
distributions and sequence properties.

**Key Features**:

- Histograms, box plots, violin plots
- Cumulative distributions
- Statistical summaries
- Sequence analysis plots (autocorrelation, frequency, runs)

**Python API Usage**:

.. code-block:: python

   from lfsr.visualization.statistical_plots import plot_period_statistics
   
   period_dict = {1: 1, 3: 2, 6: 4, 12: 8}
   fig = plot_period_statistics(
       period_dict,
       theoretical_max_period=15,
       output_file="statistics.png"
   )

3D State Space Visualization
-----------------------------

**What is 3D State Space Visualization?**

3D visualization shows states in three-dimensional space, allowing exploration
of state space structure from different angles.

**Key Features**:

- Interactive 3D plots
- State coloring by period
- Rotation and zooming
- 2D projections using PCA or t-SNE

**Python API Usage**:

.. code-block:: python

   from lfsr.visualization.state_space_3d import plot_3d_state_space
   
   sequences = {0: [[1,0,0,1], [0,1,0,0], [0,0,1,0]]}
   periods = {0: 3}
   fig = plot_3d_state_space(
       sequences,
       periods,
       output_file="state_space_3d.html"  # Interactive HTML
   )

**Command-Line Usage**:

.. code-block:: bash

   lfsr-seq coefficients.csv 2 --plot-3d-state-space state_space_3d.html

Attack Visualization
--------------------

**What is Attack Visualization?**

Attack visualization shows the progress and results of cryptanalytic attacks,
including correlation attacks and attack comparisons.

**Key Features**:

- Correlation coefficient plots
- Attack progress visualization
- Success probability curves
- Side-by-side attack comparisons

**Python API Usage**:

.. code-block:: python

   from lfsr.visualization.attack_visualization import visualize_correlation_attack
   
   results = {
       'correlations': [0.45, 0.52, 0.38],
       'success_probability': 0.75,
       'attack_successful': True
   }
   fig = visualize_correlation_attack(
       results,
       output_file="attack_analysis.png"
   )

**Command-Line Usage**:

.. code-block:: bash

   lfsr-seq coefficients.csv 2 --visualize-attack attack_analysis.png

Output Formats
---------------

Visualizations can be exported in multiple formats:

- **PNG**: Raster image format (good for documents)
- **SVG**: Vector format (scalable, good for web)
- **PDF**: Vector format (good for publications)
- **HTML**: Interactive format (for web browsers)

**Format Selection**:

.. code-block:: python

   from lfsr.visualization.base import VisualizationConfig, OutputFormat
   
   config = VisualizationConfig(
       output_format=OutputFormat.SVG,
       interactive=False,
       width=12.0,
       height=8.0
   )

API Reference
-------------

See :doc:`api/visualization` for complete API documentation.

Glossary
--------

**3D Visualization**
   A three-dimensional graphical representation allowing viewing from
   different angles.

**Box Plot**
   A standardized way of displaying data distribution based on
   five-number summary.

**Histogram**
   A graphical representation of data distribution using bars.

**Interactive Plot**
   A plot that allows user interaction (zooming, panning, tooltips).

**Publication Quality**
   Visualizations suitable for research papers with high resolution.

**State Transition Diagram**
   A graph showing how LFSR states transition and form cycles.

**Violin Plot**
   A combination of box plot and kernel density plot.

Further Reading
---------------

- Matplotlib Documentation: https://matplotlib.org/
- Plotly Documentation: https://plotly.com/python/
- NetworkX Documentation: https://networkx.org/
