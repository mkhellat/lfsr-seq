Visualization API
==================

The visualization module provides functions for creating interactive and
publication-quality visualizations of LFSR analysis results.

.. automodule:: lfsr.visualization
   :members:
   :undoc-members:
   :show-inheritance:

Base Classes
------------

VisualizationConfig
~~~~~~~~~~~~~~~~~~~

.. autoclass:: lfsr.visualization.base.VisualizationConfig
   :members:
   :no-index:

Configuration for visualizations.

BaseVisualization
~~~~~~~~~~~~~~~~~

.. autoclass:: lfsr.visualization.base.BaseVisualization
   :members:
   :no-index:

Base class for visualizations.

Period Graphs
-------------

.. autofunction:: lfsr.visualization.period_graphs.plot_period_distribution
   :no-index:

Plot period distribution histogram.

.. autofunction:: lfsr.visualization.period_graphs.plot_period_vs_state
   :no-index:

Plot period vs initial state scatter plot.

State Diagrams
--------------

.. autofunction:: lfsr.visualization.state_diagrams.generate_state_transition_diagram
   :no-index:

Generate state transition diagram.

.. autofunction:: lfsr.visualization.state_diagrams.export_to_graphviz
   :no-index:

Export state transition diagram to Graphviz DOT format.

Statistical Plots
-----------------

.. autofunction:: lfsr.visualization.statistical_plots.plot_period_statistics
   :no-index:

Plot period statistics (histogram, box plot, etc.).

.. autofunction:: lfsr.visualization.statistical_plots.plot_sequence_analysis
   :no-index:

Plot sequence analysis (autocorrelation, frequency, etc.).

3D State Space
--------------

.. autofunction:: lfsr.visualization.state_space_3d.plot_3d_state_space
   :no-index:

Plot 3D state space visualization.

.. autofunction:: lfsr.visualization.state_space_3d.plot_state_space_projection
   :no-index:

Plot 2D projection of 3D state space.

Attack Visualization
--------------------

.. autofunction:: lfsr.visualization.attack_visualization.visualize_correlation_attack
   :no-index:

Visualize correlation attack results.

.. autofunction:: lfsr.visualization.attack_visualization.visualize_attack_comparison
   :no-index:

Visualize comparison of multiple attacks.
