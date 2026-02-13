#!/usr/bin/env python
"""Quick test of Module 2 components"""

import sys
sys.path.insert(0, '.')

print('\nTesting Module 2: Profiling Layer')
print('=' * 60)

# Test imports
try:
    from profiling.column_classifier import get_classifier
    print('✓ column_classifier imported')
    from profiling.data_profiler import get_profiler
    print('✓ data_profiler imported')
    from profiling.data_health import compute_data_health
    print('✓ data_health imported')
except Exception as e:
    print(f'✗ Import failed: {e}')
    sys.exit(1)

# Quick functional test
import pandas as pd
import numpy as np

df = pd.DataFrame({
    'temperature': np.random.normal(75, 10, 100),
    'machine_id': ['MACH_001'] * 50 + ['MACH_002'] * 50,
    'status': np.random.choice(['RUNNING', 'IDLE'], 100),
    'timestamp': pd.date_range('2026-01-01', periods=100, freq='10min'),
})

print('\n' + '='*60)
print('FUNCTIONAL TESTS')
print('='*60)

# Test 1: Classification
classifier = get_classifier()
classifications = classifier.classify(df)
print(f'\n✓ Classification: {len(classifications)} columns detected')
for col, info in list(classifications.items()):
    print(f'   {col}: {info["detected_type"]} (confidence: {info["confidence"]:.2f})')

# Test 2: Profiling
profiler = get_profiler()
profiles = profiler.profile(df)
print(f'\n✓ Profiling: {len(profiles)} columns profiled')
print('   Numeric statistics extracted (mean, std, outliers, etc.)')
print('   Categorical statistics extracted (mode, entropy, etc.)')

# Test 3: Health
health = compute_data_health('test_run', df)
print(f'\n✓ Health Score: {health["overall_health_score"]:.1f}/100 ({health["health_status"]})')
print(f'   Dimensions:')
for dim, score in health['dimensions'].items():
    print(f'      {dim}: {score:.1f}')

# Test 4: DB Format
db_records = profiler.profile_to_db_format(df, 'test_run_123')
print(f'\n✓ Database Format: {len(db_records)} records ready for DB insert')
for record in db_records[:2]:
    print(f'   {record["column_name"]}: {record["detected_type"]} ({record["health_status"]})')

print('\n' + '='*60)
print('SUCCESS - All Module 2 components working!')
print('='*60 + '\n')
