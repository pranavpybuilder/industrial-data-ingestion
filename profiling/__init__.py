# profiling/__init__.py

"""
Profiling Module - Analyzes and scores data quality.

Key Exports:
  • ColumnClassifier: Detects column types
  • DataProfiler: Computes statistics
  • compute_data_health: Overall health scoring
"""

from profiling.column_classifier import ColumnClassifier, get_classifier
from profiling.data_profiler import DataProfiler, get_profiler, ColumnProfile
from profiling.data_health import HealthReport, compute_data_health

__all__ = [
    'ColumnClassifier',
    'get_classifier',
    'DataProfiler',
    'get_profiler',
    'ColumnProfile',
    'HealthReport',
    'compute_data_health',
]
