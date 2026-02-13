# INTEGRATION GUIDE: MODULE 2 - PROFILING LAYER

## Quick Start

### 1. Run Tests (Verify Module 2 Works)
```bash
python test_profiling_module.py
```

Expected output:
```
╔══════════════════════════════════════════════════════════════════════════════╗
║              MODULE 2: PROFILING LAYER - TEST SUITE                       ║
╚══════════════════════════════════════════════════════════════════════════════╝

TEST 1: Column Classifier - Numeric Detection
✅ PASS: Numeric columns detected correctly

TEST 2: Column Classifier - Categorical Detection
✅ PASS: Categorical columns detected correctly

... (18 tests total)

╔══════════════════════════════════════════════════════════════════════════════╗
║ TEST RESULTS: 18 passed, 0 failed (18 total)                             ║
╚══════════════════════════════════════════════════════════════════════════════╝
```


### 2. Usage Examples

#### Example 1: Classify Columns
```python
from profiling.column_classifier import get_classifier
import pandas as pd

# Load your data
df = pd.read_csv('data/raw/plc/sample.csv')

# Classify
classifier = get_classifier()
classifications = classifier.classify(df)

# Output:
#{
#   'temperature': {
#       'detected_type': 'numeric',
#       'confidence': 0.95,
#       'cardinality': 487,
#       'null_count': 0,
#       'sample_values': [42.5, 43.2, 41.8, ...]
#   },
#   'machine_id': {
#       'detected_type': 'identifier',
#       'confidence': 0.95,
#       'cardinality': 10,  # 10 unique machine IDs
#       ...
#   }
#}
```

#### Example 2: Profile Data
```python
from profiling.data_profiler import get_profiler

# Profile all columns
profiler = get_profiler()
profiles = profiler.profile(df)

# Access numeric statistics
temp_profile = profiles['temperature']
print(f"Mean: {temp_profile['mean']}")
print(f"Std: {temp_profile['std']}")
print(f"Outliers: {temp_profile['outlier_count']}")

# Get database-ready records
db_records = profiler.profile_to_db_format(df, run_id='run_12345')
# Output: [
#   {
#     'run_id': 'run_12345',
#     'column_name': 'temperature',
#     'missing_percentage': 0.0,
#     'outlier_count': 2,
#     'detected_type': 'numeric',
#     'health_status': 'good'
#   },
#   ...
# ]
```

#### Example 3: Compute Data Health
```python
from profiling.data_health import compute_data_health

# Get overall health score
health = compute_data_health('run_12345', df)

# Output:
#{
#   'overall_health_score': 87.5,
#   'health_status': 'good',
#   'total_rows': 1000,
#   'total_columns': 15,
#   'dimensions': {
#       'completeness': 98.0,
#       'consistency': 95.0,
#       'uniqueness': 90.0,
#       'validity': 85.0,
#       'freshness': 80.0
#   },
#   'column_issues': [
#       {
#           'column_name': 'notes',
#           'severity': 'warning',
#           'message': 'Column has 5.3% missing values'
#       }
#   ],
#   'summary': 'Dataset is in good condition. No specific issues detected.'
#}
```


### 3. Integration with Pipeline Runner

The module needs to be called after ingestion. Here's where to add it:

File: `app/pipeline_runner.py` (after ingestion)

```python
from profiling import DataProfiler
from storage.repositories.profiling_repo import ProfilingRepository

profiling_repo = ProfilingRepository()

# After ingestion:
# ... existing code ...

# NEW: Add profiling step
def run_single_file(self, file_path, source_type=None, run_name=None):
    # ... existing ingestion code ...
    
    # STEP 3: PROFILE THE DATA
    profiler = DataProfiler()
    
    # Read ingested data from Parquet
    ingested_path = f"data/raw/{source_type}/run_{run_id}.parquet"
    df = pd.read_parquet(ingested_path)
    
    # Profile it
    profiling_records = profiler.profile_to_db_format(df, run_id)
    
    # Save to database
    profiling_repo.save_profiling_results(run_id, profiling_records)
    
    logger.info(f"Profiling complete: {len(profiling_records)} columns analyzed")
```


### 4. Data Flow After Module 2

```
User Uploads File
    ↓
Module 1 (Ingestion) ✅
  └─ Parquet file saved to disk
  └─ Metadata in DB (runs, ingested_files, feature_store)
    ↓
Module 2 (Profiling) ✅ ← YOU ARE HERE
  ├─ Classifies each column
  ├─ Computes statistics
  ├─ Generates health score
  └─ Saves to profiling_results table
    ↓
Frontend: Data Health page can now show:
  ├─ Overall health score (0-100)
  ├─ Per-column statistics
  ├─ Issues and warnings
  └─ Data quality assessment
    ↓
Module 3 (Rules Engine) ⏳ NEXT
  ├─ Reads: profiling_results + feature_store
  ├─ Applies: threshold rules
  └─ Outputs: rule_findings
    ↓
Module 5 (Orchestration) ⏳ AFTER MODULE 3
  └─ Combines all findings → insights table
```


### 5. Database Integration

The profiling_results table is already defined in schema.sql:

```sql
CREATE TABLE IF NOT EXISTS profiling_results (
    run_id TEXT NOT NULL,
    column_name TEXT NOT NULL,
    missing_percentage DOUBLE,
    outlier_count INTEGER,
    detected_type TEXT,
    health_status TEXT
);
```

ProfileRepository (already exists) handles:
- `save_profiling_results(run_id, results)` → INSERT records
- `get_profiling_results(run_id)` → SELECT for frontend
- `has_profiling_data(run_id)` → Check if exists


### 6. Frontend Integration

The Data Health page will eventually look like:

```
DATA HEALTH & PROFILING

Overall Health Score: 87.5/100 ✓ GOOD

Dimensions:
  Completeness ████████████████░░ 98%
  Consistency  ░░░░░░░░░░░░░░░░░░ 95%
  Uniqueness   ████████████░░░░░░ 90%
  Validity     ██████████░░░░░░░░ 85%
  Freshness    ████████░░░░░░░░░░ 80%

Column Details:
  temperature_celsius
    • Type: Numeric
    • Missing: 0%
    • Outliers: 2 (0.2%)
    • Status: ✓ GOOD

  machine_id
    • Type: Identifier
    • Cardinality: 10 unique
    • Duplicates: 0
    • Status: ✓ GOOD

Issues (1):
  ⚠️  notes: Column has 5.3% missing values
```


### 7. Key Statistics Provided

For each column, Module 2 provides:

**Numeric Columns:**
- Mean, Median, Std Dev
- Min, Max, Range
- Q1, Q3, IQR
- Outlier count & percentage
- Skewness, Kurtosis
- Coefficient of Variation

**Categorical Columns:**
- Unique values count
- Mode & frequency
- Top 5 values
- Shannon entropy (diversity)
- Uniqueness ratio

**Temporal Columns:**
- Min/Max dates
- Date range (days)
- Mean/median interval
- Inferred frequency
- Timezone info

**Boolean Columns:**
- True/False counts
- Percentages
- Balance assessment

**All Columns:**
- Total count & non-null count
- Null percentage
- Cardinality


### 8. Troubleshooting

**Test Fails:**
```bash
# Ensure all dependencies installed
pip install pandas numpy scipy scikit-learn

# Run again
python test_profiling_module.py
```

**Import Error:**
```python
# Make sure profiling/__init__.py exports are correct
from profiling import DataProfiler, get_profiler, compute_data_health
```

**Null Handling:**
- Module handles all-null columns (classifies as 'unknown')
- Module handles mixed nulls gracefully
- Health score reduced for high null percentages


### 9. Next Steps

1. ✅ Verify tests pass
2. ⏳ Extend pipeline_runner.py to call profiler after ingestion
3. ⏳ Update Data Health page frontend to fetch profiling_results
4. ⏳ Start Module 3: Rules Engine


---

**Test Suite Location:** `test_profiling_module.py`
**Module Location:** `profiling/`
**Repository Location:** `storage/repositories/profiling_repo.py`
**IPC Handler Location:** `ipc/data_health_ipc.py`
