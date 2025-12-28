Visualization
=============

This section provides comprehensive documentation for advanced visualization
features, enabling interactive and publication-quality visualizations of LFSR
analysis results.

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

The visualization features provide powerful tools for understanding and
presenting LFSR analysis results through graphical representations.

**Available Visualizations**:

1. **Period Graphs**: Interactive and static period distribution visualizations
2. **State Transition Diagrams**: Graph representations of state transitions
3. **Statistical Plots**: Publication-quality statistical visualizations
4. **3D State Space**: Interactive 3D visualizations of state spaces
5. **Attack Visualization**: Visualizations of attack processes and results

Period Distribution Visualization
---------------------------------

**What is Period Distribution Visualization?**

Period distribution visualization shows how periods are distributed across
all possible initial states, helping understand the period structure of an LFSR.

**Key Features**:

- Histogram of period distribution
- Comparison with theoretical bounds
- Interactive tooltips and zooming
- Export to multiple formats

**Python API Usage**:

.. code-block:: python

   from lfsr.visualization.period_graphs import plot_period_distribution
   from lfsr.visualization.base import VisualizationConfig, OutputFormat
   
   period_dict = {1: 1, 3: 2, 6: 4, 12: 8}
   
   # Static plot
   config = VisualizationConfig(interactive=False, output_format=OutputFormat.PNG)
   fig = plot_period_distribution(period_dict, theoretical_max_period=15, config=config)
   fig.savefig("period_dist.png")
   
   # Interactive plot
   config = VisualizationConfig(interactive=True, output_format=OutputFormat.HTML)
   fig = plot_period_distribution(period_dict, theoretical_max_period=15, config=config)
   fig.write_html("period_dist.html")

State Transition Diagrams
---------------------------

**What is a State Transition Diagram?**

A state transition diagram is a graph showing how LFSR states transition from
one to another, revealing the cycle structure of the state space.

**Key Features**:

- Graph representation of transitions
- Cycle highlighting
- State labeling
- Export to Graphviz DOT format
- Export to image formats

**Python API Usage**:

.. code-block:: python

   from lfsr.visualization.state_diagrams import generate_state_transition_diagram
   
   sequences = {0: [[1,0,0], [0,1,0], [0,0,1], [1,0,0]]}
   periods = {0: 3}
   
   fig = generate_state_transition_diagram(sequences, periods, max_states=50)
   fig.savefig("state_diagram.png")

Statistical Distribution Plots
-------------------------------

**What are Statistical Distribution Plots?**

Statistical plots provide publication-quality visualizations of period
distributions and sequence properties using various plot types.

**Available Plot Types**:

- **Histogram**: Frequency distribution of periods
- **Box Plot**: Summary statistics (quartiles, median, outliers)
- **Violin Plot**: Distribution shape and summary statistics
- **Autocorrelation Plot**: Sequence autocorrelation analysis
- **Frequency Distribution**: Element frequency in sequences
- **Runs Analysis**: Distribution of run lengths

**Python API Usage**:

.. code-block:: python

   from lfsr.visualization.statistical_plots import plot_period_statistics
   
   period_dict = {1: 1, 3: 2, 6: 4, 12: 8}
   
   # Histogram
   fig = plot_period_statistics(period_dict, plot_type="histogram")
   
   # Box plot
   fig = plot_period_statistics(period_dict, plot_type="box")
   
   # Violin plot
   fig = plot_period_statistics(period_dict, plot_type="violin")

3D State Space Visualization
------------------------------

**What is 3D State Space Visualization?**

3D visualization provides interactive exploration of LFSR state spaces,
allowing viewing from different angles and perspectives.

**Key Features**:

- Interactive 3D scatter plots
- State coloring by period
- Rotation and zooming
- 2D projections (PCA, simple)

**Python API Usage**:

.. code-block:: python

   from lfsr.visualization.state_space_3d import plot_3d_state_space
   
   sequences = {...}
   periods = {...}
   
   fig = plot_3d_state_space(sequences, periods, max_states=100)
   fig.write_html("state_space_3d.html")

Attack Visualization
--------------------

**What is Attack Visualization?**

Attack visualization shows the progress and results of cryptanalytic attacks,
helping understand attack effectiveness and identify vulnerabilities.

**Key Features**:

- Correlation coefficient plots
- Attack progress tracking
- Success probability curves
- Side-by-side attack comparisons

**Python API Usage**:

.. code-block:: python

   from lfsr.visualization.attack_visualization import visualize_correlation_attack
   
   results = {
       'correlations': {'LFSR1': 0.7, 'LFSR2': 0.3},
       'progress': {'iterations': [1,2,3], 'candidates_tested': [10,20,30]}
   }
   
   plots = visualize_correlation_attack(results)
   plots[0].savefig("correlation_attack.png")

Command-Line Usage
------------------

Visualizations can be generated from the command line:

**Basic Usage**:

.. code-block:: bash

   lfsr-seq coefficients.csv 2 --plot-period-distribution period_plot.png

**State Transition Diagram**:

.. code-block:: bash

   lfsr-seq coefficients.csv 2 --plot-state-transitions state_diagram.png

**3D State Space**:

.. code-block:: bash

   lfsr-seq coefficients.csv 2 --plot-3d-state-space state_space.html

**CLI Options**:
- ``--plot-period-distribution FILE``: Generate period distribution plot
- ``--plot-state-transitions FILE``: Generate state transition diagram
- ``--plot-3d-state-space FILE``: Generate 3D state space visualization
- ``--visualize-attack TYPE``: Visualize attack results
- ``--output-format FORMAT``: Specify format (png, svg, pdf, html)

API Reference
-------------

See :doc:`api/visualization` for complete API documentation.

Glossary
--------

**3D Visualization**
   A three-dimensional graphical representation allowing viewing from different angles.

**Autocorrelation**
   A measure of similarity between a sequence and a shifted version of itself.

**Box Plot**
   A standardized display of data distribution showing quartiles and outliers.

**Histogram**
   A graphical representation of data distribution using bars.

**Interactive Plot**
   A plot allowing user interaction such as zooming and panning.

**Publication Quality**
   Visualizations suitable for research papers with high resolution.

**State Transition Diagram**
   A graph showing how LFSR states transition and form cycles.

**Violin Plot**
   A combination of box plot and kernel density plot showing distribution shape.

Further Reading
---------------

- Matplotlib Documentation: https://matplotlib.org/
- Plotly Documentation: https://plotly.com/python/
- NetworkX Documentation: https://networkx.org/
