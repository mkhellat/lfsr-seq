Machine Learning Integration
============================

This section provides comprehensive documentation for machine learning
integration features, including period prediction, pattern detection,
anomaly detection, and model training.

**Key Terminology**:

- **Machine Learning (ML)**: A method of data analysis that automates
  analytical model building, enabling systems to learn from data
  and make predictions or decisions.

- **Supervised Learning**: ML where models learn from labeled examples
  (input-output pairs) to make predictions on new data.

- **Feature Extraction**: Converting raw data into numerical features
  that ML models can use for learning and prediction.

Introduction
------------

The machine learning integration provides ML-based analysis capabilities
for LFSR sequences, enabling:

1. **Period Prediction**: Predict LFSR periods from polynomial structure
   without full enumeration

2. **Pattern Detection**: Automatically detect patterns in sequences
   and state transitions

3. **Anomaly Detection**: Identify anomalies in sequences and distributions

4. **Model Training**: Train custom ML models for specific analysis tasks

Period Prediction
-----------------

**What is Period Prediction?**

Period prediction uses machine learning to predict the period of an LFSR
from features extracted from its characteristic polynomial, without
computing the period directly through enumeration.

**Key Features**:

- **Feature-Based Prediction**: Extract features from polynomial structure
- **Multiple Model Types**: Random Forest and Gradient Boosting support
- **Model Training**: Train custom models on your data
- **Fast Prediction**: Predict periods without full enumeration

**Mathematical Foundation**:

The model learns a function f that maps polynomial features to periods:

.. math::

   \\text{period} = f(\\text{features}(P(t)))

where features include degree, field order, coefficient patterns, etc.

**Python API Usage**:

.. code-block:: python

   from lfsr.ml.period_prediction import PeriodPredictionModel
   from lfsr.ml.base import extract_polynomial_features
   
   # Create and train model
   model = PeriodPredictionModel(model_type="random_forest")
   X, y = generate_training_data(100)  # Generate training data
   model.train(X, y)
   
   # Predict period
   coefficients = [1, 0, 0, 1]
   predicted_period = model.predict_period(coefficients, field_order=2)
   print(f"Predicted period: {predicted_period}")

Pattern Detection
-----------------

**What is Pattern Detection?**

Pattern detection automatically identifies patterns in LFSR sequences,
including repeating subsequences, statistical anomalies, and periodicity
indicators.

**Key Features**:

- **Repeating Subsequences**: Detect subsequences that appear multiple times
- **Statistical Anomalies**: Identify windows with unusual statistics
- **Periodicity Indicators**: Detect periodic structure using autocorrelation

**Python API Usage**:

.. code-block:: python

   from lfsr.ml.pattern_detection import detect_all_patterns
   
   sequence = [1, 0, 1, 0, 1, 0, 1, 1, 0, 1]
   patterns = detect_all_patterns(sequence)
   
   for pattern_type, pattern_list in patterns.items():
       print(f"{pattern_type}: {len(pattern_list)} patterns found")

Anomaly Detection
-----------------

**What is Anomaly Detection?**

Anomaly detection identifies unusual patterns, outliers, and deviations
from expected behavior in sequences and period distributions.

**Key Features**:

- **Sequence Anomalies**: Detect outliers in sequences
- **Distribution Anomalies**: Identify anomalies in period distributions
- **Bound Violations**: Detect periods exceeding theoretical bounds
- **Multiple Methods**: Statistical and ML-based detection

**Python API Usage**:

.. code-block:: python

   from lfsr.ml.anomaly_detection import detect_all_anomalies
   
   anomalies = detect_all_anomalies(
       sequence=sequence,
       period_dict=period_dict,
       theoretical_max_period=15,
       is_primitive=False
   )
   
   for anomaly_type, anomaly_list in anomalies.items():
       print(f"{anomaly_type}: {len(anomaly_list)} anomalies")

Model Training
--------------

**What is Model Training?**

Model training generates training data and trains ML models for LFSR
analysis tasks, enabling custom models tailored to specific needs.

**Key Features**:

- **Training Data Generation**: Generate synthetic training data
- **Model Training**: Train period prediction models
- **Model Evaluation**: Evaluate model performance
- **Model Persistence**: Save and load trained models

**Python API Usage**:

.. code-block:: python

   from lfsr.ml.training import train_period_prediction_model
   
   model = train_period_prediction_model(
       model_type="random_forest",
       num_samples=100,
       max_degree=10,
       field_order=2,
       save_path="model.pkl"
   )

API Reference
-------------

See :doc:`api/ml` for complete API documentation.

Glossary
--------

**Anomaly Detection**
   The process of identifying data points or patterns that deviate
   significantly from expected behavior.

**Feature Extraction**
   Converting raw data into numerical features that ML models can use.

**Machine Learning Model**
   A mathematical model that learns patterns from data to make predictions.

**Pattern Detection**
   Automatically identifying patterns in sequences and state transitions.

**Period Prediction**
   Using ML to predict LFSR periods from polynomial structure.

**Supervised Learning**
   ML where models learn from labeled examples (input-output pairs).

**Training Data**
   A collection of input-output pairs used to train ML models.

Further Reading
---------------

- Scikit-learn Documentation: https://scikit-learn.org/
- Hastie, T., et al. (2009). "The Elements of Statistical Learning"
- Bishop, C. M. (2006). "Pattern Recognition and Machine Learning"
