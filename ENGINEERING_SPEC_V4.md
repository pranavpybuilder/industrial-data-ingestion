# Offline Industrial Intelligence — Master Engineering Specification v4.0
> **For Claude Opus 4.6 (Thinking) via Antigravity**
> Grounded in: Application_Architecture.pdf + real project codebase
> Constraint: 100% Offline — No internet, No cloud, No external APIs during runtime

---

## 0. System Mission & Architecture Overview

### What This System Does
A **fully offline** Electron + Python desktop application that transforms raw industrial data files into actionable intelligence. Every computation — ingestion, ML, rules, insights, dashboards — runs locally on the user's machine with zero internet dependency.

### Architecture Layers (from PDF — implement ALL of them)

```
┌─────────────────────────────────────────────────────────────────┐
│                    DATA SOURCES (Input Layer)                    │
│  PLC/OPC-UA │ RFID Data │ SAP ERP Exports │ Manual/Report Files │
│  CSV/XLSX/JSON/Logs — ANY schema, ANY structure                  │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│              LAYER 1: DATA INGESTION                            │
│  • Multi-format parsing (CSV/Excel/JSON/Logs)                   │
│  • Encoding auto-detection                                       │
│  • Schema-agnostic column classification                        │
│  • Versioned runs (each upload = new run_id)                    │
│  • Fully offline                                                 │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│         LAYER 2: FEATURE STORE & NORMALIZATION                  │
│  • Type normalization (all columns typed correctly)              │
│  • Time alignment (unified timestamp axis)                      │
│  • Derived metrics (MTTR, OEE, failure rate, etc.)              │
│  • Feature registry (persisted per domain)                      │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│              LAYER 3: DATA PROFILER                             │
│  • Column role detection (KPI/dimension/identifier/text)        │
│  • KPI candidate identification                                 │
│  • Statistics: mean, median, std, min, max, nulls, cardinality │
│  • Data health score (0–100)                                    │
│  • Anomaly flags per column                                      │
└──────────────┬──────────────────────────┬───────────────────────┘
               │                          │
┌──────────────▼───────────┐  ┌───────────▼─────────────────────┐
│   LAYER 4: RULE ENGINE   │  │     LAYER 5: ML ENGINE (OFFLINE)│
│  • Threshold checks      │  │  • Anomaly detection (Isolation  │
│  • Maintenance logic     │  │    Forest, DBSCAN, Z-score)      │
│  • Domain-specific rules │  │  • Forecasting (ARIMA, Prophet   │
│  • Explainability output │  │    fallback, linear regression)  │
│  • Severity scoring      │  │  • Failure pattern recognition   │
│                          │  │  • All models run offline/local  │
└──────────────┬───────────┘  └───────────┬─────────────────────┘
               │                          │
┌──────────────▼──────────────────────────▼───────────────────────┐
│            LAYER 6: INSIGHT ORCHESTRATOR                        │
│  • Merges rule findings + ML findings                           │
│  • Deduplicates overlapping signals                             │
│  • Severity scoring (Critical/High/Medium/Low)                  │
│  • Prioritization (by impact × urgency matrix)                  │
│  • Generates structured InsightReport                           │
│  • Executive narrative composition                              │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│         LAYER 7: DASHBOARD BLUEPRINT ENGINE                     │
│  • Auto-KPI selection from profiler + insights                  │
│  • Chart type selection (domain-aware)                          │
│  • Drill-down definitions                                       │
│  • Layout rules (section grouping, grid spans)                  │
│  • Outputs: DashboardBlueprint JSON                             │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│         LAYER 8: FRONTEND INTELLIGENCE LAYER (Electron)         │
│  • Power BI-style editable dashboards                           │
│  • Filter panels (machine, failure type, time range)           │
│  • Full insights report viewer                                  │
│  • Export engine (PDF/DOCX/XLSX/JSON)                           │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│              LOCAL DATABASE (DuckDB)                            │
│  • Metadata │ Profiles │ Insights │ Dashboards │ ML Models      │
│  • Single file, fully local, versioned per run                  │
└─────────────────────────────────────────────────────────────────┘
```

### Technology Stack
```
Frontend:   React 18 (TSX) + Vite 7 + Electron (Python-managed via PyInstaller)
Backend:    Python 3.11+ (frozen by PyInstaller into .exe)
Database:   DuckDB (local file: %LOCALAPPDATA%\OfflineIndustrialIntelligence\storage\)
IPC Bridge: Electron ipcMain ↔ ipcRenderer (window.electronAPI)
ML:         scikit-learn, statsmodels, scipy (all offline, bundled)
Export:     reportlab (PDF), python-docx (DOCX), openpyxl (XLSX)
Build:      PyInstaller → NSIS → .exe installer
```

---

## 1. CRITICAL: Build & Launch Issues (Fix Before Anything Else)

### 1.1 "Frontend Not Built" Error After NSIS Install

**Root cause:** `vite.config.ts` uses `base: '/'` which breaks Electron's `file://` protocol. Also, `main.py` uses a relative path that changes after NSIS installation.

**Fix `vite.config.ts`:**
```typescript
// frontend/electron_app/renderer/vite.config.ts
export default defineConfig({
  base: './',    // ← MUST be './' not '/'  — Electron loads via file:// not http://
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    assetsDir: 'assets',
  }
})
```

**Fix `frontend/electron_app/main/main.py` — renderer path detection:**
```python
import sys
from pathlib import Path

def get_renderer_path() -> Path:
    """Resolves renderer index.html for both dev and PyInstaller frozen modes."""
    if getattr(sys, 'frozen', False):
        # Frozen by PyInstaller — files are in sys._MEIPASS
        base = Path(sys._MEIPASS)
    else:
        # Development mode
        base = Path(__file__).parent.parent
    
    path = base / "renderer" / "dist" / "index.html"
    if not path.exists():
        raise FileNotFoundError(
            f"Renderer not built. Expected: {path}\n"
            f"Run: cd frontend/electron_app/renderer && npm run build"
        )
    return path
```

**Correct build sequence (every release):**
```powershell
# 1. Build React renderer
cd D:\Projects\industrial-data-ingestion\frontend\electron_app\renderer
npm run build
# Verify: dist\index.html must exist

# 2. Package Python + renderer into .exe
cd D:\Projects\industrial-data-ingestion
.\build_production.bat

# 3. Compile NSIS installer
& "C:\Program Files (x86)\NSIS\makensis.exe" OfflineIndustrialIntelligence_Installer.nsi
```

### 1.2 DuckDB File Lock / WAL Corruption (Already Fixed)
Already resolved in `storage/connection.py`:
- 3-attempt retry with 1s delay for lock errors
- WAL-only deletion on `INTERNAL Error: Failure while replaying WAL`
- Full DB+WAL delete as last resort (DB recreated fresh from schema.sql)
- `atexit.register(close_connection)` in `pipeline_runner.py`

**Emergency recovery (PowerShell):**
```powershell
Remove-Item "$env:LOCALAPPDATA\OfflineIndustrialIntelligence\storage\*.duckdb" -Force -EA 0
Remove-Item "$env:LOCALAPPDATA\OfflineIndustrialIntelligence\storage\*.wal" -Force -EA 0
```

---

## 2. Layer 1 — Data Ingestion (Schema-Agnostic, Fully Offline)

### 2.1 Core Contract
The ingestion layer must accept **any** file and succeed or return a meaningful error. It must never crash the app.

Supported inputs:
- `.csv` — any delimiter, any encoding, any header row position
- `.xlsx` / `.xls` — any sheet, merged cells, multi-row headers
- `.json` — array of objects or nested
- `.log` — structured log files (key=value or JSON-per-line)

### 2.2 Ingestion Pipeline (Ordered Steps)

```python
# ingestion/base_ingestor.py — the contract every ingestor implements

class BaseIngestor:
    def ingest(self, file_path: str, run_id: str) -> IngestionResult:
        """
        Full ingestion pipeline:
        1. detect_encoding()      → str
        2. parse_file()           → pd.DataFrame (all strings)
        3. detect_header_row()    → pd.DataFrame (correct header)
        4. classify_columns()     → ColumnProfile[]
        5. cast_types()           → pd.DataFrame (typed)
        6. compute_schema_hash()  → str
        7. detect_domain()        → str
        8. save_to_storage()      → str (output_path)
        """
```

**Robust CSV reader:**
```python
def parse_csv(file_path: str) -> pd.DataFrame:
    encodings = ['utf-8-sig', 'utf-8', 'latin-1', 'windows-1252', 'cp1252']
    delimiters = [',', ';', '\t', '|', ':']
    
    for enc in encodings:
        for delim in delimiters:
            try:
                df = pd.read_csv(
                    file_path, encoding=enc, sep=delim,
                    dtype=str, on_bad_lines='skip',
                    skip_blank_lines=True, low_memory=False
                )
                if df.shape[1] >= 2 and df.shape[0] >= 1:
                    return df.dropna(how='all').reset_index(drop=True)
            except Exception:
                continue
    raise IngestionError(f"Cannot parse CSV: {file_path}. "
                         "File may be empty, binary, or in an unsupported format.")
```

**Robust XLSX reader:**
```python
def parse_xlsx(file_path: str) -> pd.DataFrame:
    try:
        xl = pd.ExcelFile(file_path, engine='openpyxl')
    except Exception:
        xl = pd.ExcelFile(file_path, engine='xlrd')  # fallback for .xls
    
    for sheet in xl.sheet_names:
        try:
            df = pd.read_excel(
                xl, sheet_name=sheet, dtype=str,
                na_values=['', 'NA', 'N/A', 'null', 'NULL', '#N/A', '-', '--']
            )
            df = df.dropna(how='all').dropna(axis=1, how='all')
            if df.shape[0] >= 1 and df.shape[1] >= 2:
                return df.reset_index(drop=True)
        except Exception:
            continue
    raise IngestionError(f"No readable data sheets in: {file_path}")
```

### 2.3 Domain Auto-Detection (Keyword Scoring)

```python
DOMAIN_SIGNATURES = {
    "maintenance": {
        "keywords": ["breakdown", "failure", "repair", "maintenance", "equipment",
                     "notification", "malfunction", "downtime", "mttr", "mtbf",
                     "work_order", "spare_part", "preventive", "corrective",
                     "root_cause", "why", "coding", "malfunct"],
        "weight": 1.0
    },
    "production": {
        "keywords": ["production", "output", "yield", "throughput", "cycle_time",
                     "shift", "operator", "target", "actual", "oee", "efficiency",
                     "batch", "lot", "quantity_produced"],
        "weight": 1.0
    },
    "energy": {
        "keywords": ["kwh", "energy", "power", "consumption", "meter", "voltage",
                     "current", "demand", "load", "tariff", "peak", "kva", "pf"],
        "weight": 1.0
    },
    "quality": {
        "keywords": ["defect", "rejection", "rework", "inspection", "quality",
                     "tolerance", "specification", "ncr", "ppk", "cpk",
                     "scrap", "rework", "first_pass"],
        "weight": 1.0
    },
    "safety": {
        "keywords": ["incident", "accident", "near_miss", "hazard", "safety",
                     "injury", "lti", "ppe", "permit", "risk", "severity"],
        "weight": 1.0
    },
    "inventory": {
        "keywords": ["stock", "inventory", "part", "material", "quantity", "bin",
                     "warehouse", "reorder", "supplier", "purchase", "mrp"],
        "weight": 1.0
    },
    "plc": {
        "keywords": ["tag", "address", "signal", "plc", "opc", "register",
                     "coil", "alarm", "setpoint", "process_value"],
        "weight": 1.0
    },
    "rfid": {
        "keywords": ["rfid", "tag_id", "reader", "scan", "antenna",
                     "epc", "uid", "location_id"],
        "weight": 1.0
    }
}

def detect_domain(df: pd.DataFrame) -> str:
    """Score all column names + sample values against domain keywords."""
    text = " ".join(df.columns.tolist()).lower()
    # Also sample first 20 rows of string columns
    for col in df.select_dtypes(include='object').columns[:10]:
        text += " " + " ".join(df[col].dropna().head(20).astype(str).tolist()).lower()
    
    scores = {}
    for domain, config in DOMAIN_SIGNATURES.items():
        score = sum(1 for kw in config["keywords"] if kw in text)
        scores[domain] = score * config["weight"]
    
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "generic"
```

---

## 3. Layer 2 — Feature Store & Normalization

### 3.1 Purpose
Transform raw ingested data into analysis-ready features. Every column gets a role assignment and numeric features get normalized. Time columns get aligned to a common axis.

### 3.2 Column Classification

```python
class ColumnRole(Enum):
    TIMESTAMP   = "timestamp"    # datetime columns
    NUMERIC_KPI = "numeric_kpi"  # measurable values (duration, count, value)
    CATEGORY    = "category"     # low-cardinality text (machine type, shift, status)
    IDENTIFIER  = "identifier"   # IDs, codes (equipment_id, work_order)
    TEXT        = "text"         # free text (descriptions, root causes, notes)
    BOOLEAN     = "boolean"      # yes/no, true/false, 0/1 binary
    DERIVED     = "derived"      # calculated by feature store (MTTR, rate, etc.)
```

### 3.3 Domain-Specific Derived Features

```python
# For maintenance domain:
MAINTENANCE_DERIVED = {
    "mttr_hours":        "mean(breakdown_duration) per equipment",
    "mtbf_days":         "days between failures per equipment",
    "failure_rate":      "failures per 30 days per equipment",
    "mech_elec_ratio":   "count(MECH) / count(ELEC)",
    "repeat_failure_pct":"% failures on same equipment within 7 days",
    "top_failure_mode":  "most frequent root cause (Why1 column)",
    "avg_response_time": "mean(repair_start - malfunction_start)",
}

# For production domain:
PRODUCTION_DERIVED = {
    "oee":               "(availability × performance × quality) × 100",
    "avg_cycle_time":    "mean(cycle_time) per machine",
    "rejection_rate":    "defects / total_produced × 100",
    "throughput_rate":   "units per shift",
}

# For energy domain:
ENERGY_DERIVED = {
    "daily_consumption": "sum(kwh) per day",
    "peak_demand":       "max(kw) in any 15-min window",
    "load_factor":       "avg_demand / peak_demand × 100",
    "cost_per_unit":     "total_cost / total_kwh",
}
```

---

## 4. Layer 3 — Data Profiler

### 4.1 Per-Column Profile Output

```python
@dataclass
class ColumnProfile:
    column_name:       str
    detected_type:     str          # numeric/datetime/categorical/text/boolean
    role:              ColumnRole
    row_count:         int
    null_count:        int
    null_percentage:   float
    unique_count:      int
    
    # Numeric stats (None if not numeric)
    mean:              Optional[float]
    median:            Optional[float]
    std:               Optional[float]
    min:               Optional[float]
    max:               Optional[float]
    percentile_25:     Optional[float]
    percentile_75:     Optional[float]
    
    # Categorical stats (None if not categorical)
    top_values:        Optional[Dict[str, int]]   # {value: count} top 10
    
    # Health
    health_flags:      List[str]    # e.g. ["high_nulls", "constant_value", "outliers_detected"]
    kpi_candidate:     bool         # True if this column is a good KPI
```

### 4.2 Data Health Score

```python
def compute_health_score(profiles: List[ColumnProfile]) -> float:
    """
    Returns 0–100 score. Deductions:
    - Each column with >20% nulls: -5
    - Each column with >50% nulls: -10
    - Constant-value columns: -3
    - Duplicate rows > 5%: -10
    - Zero numeric variance: -5
    - No datetime column found: -5
    """
```

---

## 5. Layer 4 — Rule Engine

### 5.1 Design: Threshold + Pattern Rules

The rule engine applies domain-specific logic to profiler output and derived features. It is **fully offline** — no ML required, deterministic outputs.

```python
class RuleResult:
    rule_id:         str
    rule_name:       str
    triggered:       bool
    severity:        Severity      # CRITICAL / HIGH / MEDIUM / LOW / INFO
    confidence:      float         # 0.0–1.0
    message:         str           # Human-readable finding
    affected_columns: List[str]
    affected_rows:   Optional[List[int]]
    remediation:     str           # Specific action recommendation
    explanation:     str           # Why this rule fired (explainability)
    evidence:        Dict[str, Any] # Supporting data points
```

### 5.2 Core Rules by Domain

```python
# MAINTENANCE RULES
class HighMTTRRule:          # MTTR > 4 hours → HIGH severity
class RepeatFailureRule:     # Same equipment fails >3x in 30 days → CRITICAL
class PMOverdueRule:         # Last maintenance > threshold → HIGH
class FailureEscalationRule: # Failure rate increasing week-over-week → HIGH
class ElecMechRatioRule:     # >70% electrical failures → pattern signal

# PRODUCTION RULES  
class OEEBelowTargetRule:    # OEE < 65% → HIGH
class RejectionSpikeRule:    # Rejection rate > 5% → HIGH
class CycleTimeAnomalyRule:  # Cycle time > 2σ from mean → MEDIUM

# ENERGY RULES
class PeakDemandExceedRule:  # Peak > contract limit → CRITICAL
class LoadFactorLowRule:     # Load factor < 60% → MEDIUM (inefficiency)
class ConsumptionSpikeRule:  # Day-over-day > 20% increase → HIGH

# GENERIC RULES (all domains)
class DataQualityRule:       # Health score < 70 → MEDIUM
class OutlierRule:           # Values > 3σ → based on count
class MissingDataRule:       # Critical columns > 15% null → HIGH
```

### 5.3 Explainability Output

Every triggered rule must produce a plain-English explanation:
```
"RepeatFailureRule triggered because equipment 1000005760 (SHAFT WASHING MACHINE)
recorded 8 failures in the last 30 days, exceeding the threshold of 3.
The failures cluster on Mondays (shift start) and root cause analysis shows
'belt tension' appearing in 6 of 8 Why1 fields. This pattern indicates
a systemic issue, not random failure."
```

---

## 6. Layer 5 — ML Engine (Fully Offline)

### 6.1 Offline-Only Constraint
All ML must work with **no internet connection** and **no GPU requirement**.
- Models: scikit-learn, statsmodels, scipy — all installable offline via requirements.txt
- No transformer models, no LLMs, no cloud inference
- Models are lightweight and run in < 5 seconds on standard hardware

### 6.2 Anomaly Detection

```python
class AnomalyDetector:
    """
    Runs three methods and takes ensemble vote.
    Returns anomaly score (0–1) per row and per column.
    """
    
    def detect(self, df: pd.DataFrame, numeric_cols: List[str]) -> AnomalyResult:
        results = {}
        
        # Method 1: Z-score (fast, interpretable)
        z_scores = self._zscore_anomalies(df, numeric_cols, threshold=3.0)
        
        # Method 2: IQR-based (robust to skewed distributions)
        iqr_flags = self._iqr_anomalies(df, numeric_cols, multiplier=1.5)
        
        # Method 3: Isolation Forest (captures multivariate anomalies)
        if len(numeric_cols) >= 2 and len(df) >= 20:
            iso_scores = self._isolation_forest(df, numeric_cols)
        else:
            iso_scores = {}
        
        # Ensemble: flag row if 2+ methods agree
        return self._ensemble_vote(z_scores, iqr_flags, iso_scores)
```

### 6.3 Forecasting

```python
class Forecaster:
    """
    Forecasts numeric KPIs forward 7/14/30 days.
    Uses simplest reliable method for each series.
    """
    
    def forecast(self, series: pd.Series, periods: int = 14) -> ForecastResult:
        n = len(series.dropna())
        
        if n < 10:
            return ForecastResult(method="insufficient_data", forecast=None)
        
        if n < 30:
            # Linear regression for short series
            return self._linear_regression_forecast(series, periods)
        
        try:
            # ARIMA for longer series with trend/seasonality
            return self._arima_forecast(series, periods)
        except Exception:
            # Fallback: exponential smoothing (always works)
            return self._exp_smoothing_forecast(series, periods)
```

### 6.4 Failure Pattern Recognition

```python
class FailurePatternDetector:
    """
    Identifies recurring failure patterns using:
    - Time clustering (do failures cluster at specific times?)
    - Equipment clustering (do failures cluster on specific machines?)
    - Root cause clustering (do same root causes repeat?)
    - Sequence analysis (does failure A precede failure B?)
    """
    
    def detect_patterns(self, 
                        events: pd.DataFrame,
                        timestamp_col: str,
                        equipment_col: str,
                        cause_col: Optional[str]) -> List[FailurePattern]:
        patterns = []
        patterns.extend(self._detect_time_clustering(events, timestamp_col))
        patterns.extend(self._detect_equipment_recurrence(events, equipment_col))
        if cause_col:
            patterns.extend(self._detect_cause_patterns(events, cause_col))
        return sorted(patterns, key=lambda p: p.confidence, reverse=True)
```

---

## 7. Layer 6 — Insight Orchestrator

### 7.1 Merging Rules + ML

```python
class InsightOrchestrator:
    """
    Combines rule engine findings + ML findings into unified InsightReport.
    Deduplicates overlapping signals.
    Scores by impact × urgency.
    """
    
    def orchestrate(self,
                    run_id: str,
                    rule_findings: List[RuleResult],
                    ml_findings: List[MLFinding],
                    profiling_results: Dict[str, ColumnProfile],
                    equipment_intelligence: Dict) -> List[UnifiedInsight]:
        
        # 1. Convert all findings to common InsightSignal format
        signals = self._normalize_signals(rule_findings, ml_findings)
        
        # 2. Deduplicate (same equipment + same symptom = one insight)
        signals = self._deduplicate(signals)
        
        # 3. Enrich with profile data (add statistics to context)
        signals = self._enrich_with_profiles(signals, profiling_results)
        
        # 4. Score by severity × confidence × affected_scope
        signals = self._score_and_rank(signals)
        
        # 5. Build narrative for each insight
        signals = self._compose_narratives(signals)
        
        return signals
```

### 7.2 Insight Report Structure

```python
@dataclass
class InsightReport:
    run_id:            str
    domain:            str
    generated_at:      datetime
    
    # Top-level summary (generated by narrative composer)
    executive_summary: str          # 3-5 sentences, specific to this data
    risk_level:        str          # CRITICAL / HIGH / MEDIUM / LOW
    data_quality_score: float       # 0–100
    
    # Sections
    key_findings:      List[KeyFinding]      # Top 5–10 findings, ranked
    pattern_analysis:  List[PatternInsight]  # Temporal, frequency, trend
    root_cause_analysis: List[RCAInsight]   # Cause chains with frequency
    recommendations:   List[Recommendation] # 3 priority tiers
    predictive_signals: List[Prediction]    # Forward-looking warnings
    
    # Supporting data for frontend charts
    chart_data:        Dict[str, Any]       # Pre-computed for fast rendering
```

### 7.3 Executive Narrative Composer

```python
class ExecutiveNarrativeComposer:
    """
    Generates the executive summary paragraph.
    OFFLINE — uses templates + actual data values.
    Does NOT call any LLM or API.
    
    Output example:
    "Analysis of 57 breakdown events across Plant 1152 reveals a recurring
    failure pattern in mechanical systems, which account for 68% of all
    incidents. Equipment 1000005760 (Shaft Washing Machine) is the highest-
    frequency failure point with 8 events, averaging 40 minutes downtime each.
    Failure clustering on Monday morning shifts (06:00–08:00) suggests
    inadequate pre-shift inspection protocols. Immediate action recommended:
    implement daily lubrication checklist for top 3 recurring equipment IDs,
    estimated to reduce mechanical MTTR by 35%."
    """
    
    def compose(self, signals: List[UnifiedInsight], 
                profile: DataProfile,
                domain: str) -> str:
        # Uses actual values from signals and profile — NOT generic templates
        # References specific equipment IDs, dates, percentages, counts
        # Prioritizes highest-severity findings
        # Ends with one concrete recommended action
```

---

## 8. Layer 7 — Dashboard Blueprint Engine

### 8.1 Blueprint Generation Logic

```python
def generate_blueprint(
    insight_report: InsightReport,
    profile: DataProfile,
    domain: str
) -> DashboardBlueprint:
    """
    Builds a complete dashboard layout from insight + profile data.
    Sections are organized by insight category.
    Widget types are auto-selected based on data characteristics.
    """
```

### 8.2 Auto Widget Type Selection

```python
def auto_select_visual(column: ColumnProfile, context: dict) -> WidgetType:
    if column.role == ColumnRole.TIMESTAMP:
        return WidgetType.LINE           # Time series → line chart
    
    if column.role == ColumnRole.NUMERIC_KPI:
        if column.unique_count <= 1:
            return WidgetType.METRIC     # Single value → KPI card
        elif context.get("has_time_axis"):
            return WidgetType.AREA       # Numeric over time → area chart
        elif column.unique_count <= 20:
            return WidgetType.BAR        # Few values → bar chart
        else:
            return WidgetType.LINE       # Many values → line chart
    
    if column.role == ColumnRole.CATEGORY:
        if column.unique_count <= 5:
            return WidgetType.PIE        # Few categories → pie/donut
        elif column.unique_count <= 12:
            return WidgetType.BAR        # Medium → horizontal bar
        else:
            return WidgetType.TABLE      # Many categories → table
    
    if column.role == ColumnRole.TEXT:
        return WidgetType.TABLE          # Free text → table
    
    return WidgetType.METRIC             # Fallback
```

### 8.3 Dashboard Blueprint Schema

```typescript
// frontend contracts/dashboard_contracts.ts
interface DashboardBlueprint {
    blueprintId:   string;
    runId:         string;
    generatedAt:   string;
    domain:        string;
    title:         string;
    
    sections: DashboardBlueprintSection[];
    widgets:  WidgetBlueprint[];
}

interface WidgetBlueprint {
    widgetId:          string;
    sectionId:         string;
    widgetType:        "metric" | "line" | "bar" | "area" | "pie" | 
                       "donut" | "scatter" | "table" | "gauge" | "heatmap";
    allowedVisualTypes: string[];  // user can switch between these
    title:             string;
    subtitle?:         string;
    gridSpan:          2 | 3 | 4 | 6 | 8 | 12;  // 12-col grid
    
    // Data
    data?:             Record<string, any>[];  // chart data rows
    value?:            number | string;         // metric card value
    unit?:             string;
    
    // Styling signals
    severity?:         "critical" | "warning" | "info" | "success";
    trend?:            "up" | "down" | "flat";
    trendValue?:       string;   // e.g. "+12.3%"
    
    // Drill-down definition
    drillDown?:        DrillDownConfig;
}
```

### 8.4 Dashboard Edit & Persistence Flow

```
User opens Dashboard page for a run
    ↓
IPC: getDashboard(runId) → returns {blueprint, savedLayout}
    ↓
If savedLayout exists → apply it (widget order, hidden, chart types, slicers)
If not → use blueprint defaults
    ↓
User edits:
    - Drag widget → updates widget_order[]
    - Toggle widget visibility → updates hidden_widgets: string[]  ← NOT Set
    - Change chart type → updates widget_visuals: Record<id, type>
    - Apply filter → updates slicers{}
    ↓
User clicks Save → IPC: saveDashboardLayout(runId, blueprintId, layout)
    ↓
Backend saves to dashboard_layout table in DuckDB
    ↓
dashboardsUI.markSaved() → lastSaved = new Date().toISOString()
    ↓
Header shows: "Saved 2m ago" (green pill badge)
```

---

## 9. Layer 8 — Frontend Intelligence Layer

### 9.1 Page Structure

```
AppLayout
├── Sidebar (run selector, navigation)
├── TopBar (active run badge, global actions)
└── Pages:
    ├── /home          → Home.tsx (recent runs, quick actions)
    ├── /ingestion     → Ingestion.tsx (file upload, progress)
    ├── /insights      → Insights.tsx (full insight report viewer)
    ├── /dashboards    → Dashboards.tsx (Power BI-style canvas)
    ├── /exports       → Exports.tsx (export options + history)
    ├── /data-health   → DataHealth.tsx (profiler output)
    └── /explorer      → Explorer.tsx (raw data table browser)
```

### 9.2 Insights Page Layout

```
┌─────────────────────────────────────────────────────────────┐
│  [Run: MAINT_2025-01-03] [Risk: HIGH ●] [Score: 72/100]    │
│  [Export Insights ▾]  [View Dashboard]                      │
├─────────────────────────────────────────────────────────────┤
│  EXECUTIVE SUMMARY (full-width card, indigo gradient)       │
│  "Analysis of 57 breakdown events across Plant 1152..."     │
├───────────────────────┬─────────────────────────────────────┤
│  KEY FINDINGS (left)  │  ROOT CAUSE BREAKDOWN (right)       │
│  Ranked #1–#5 cards   │  Ranked cause list + bar chart      │
│  Each: severity badge │  Frequency × Impact visualization   │
│  + specific numbers   │                                     │
├───────────────────────┴─────────────────────────────────────┤
│  PATTERN ANALYSIS (full-width)                              │
│  Temporal chart │ Frequency chart │ Trend direction         │
├─────────────────────────────────────────────────────────────┤
│  RECOMMENDATIONS (3-column: P1 red │ P2 amber │ P3 blue)   │
│  Each card: Action | Owner | Timeline | Expected Outcome    │
├─────────────────────────────────────────────────────────────┤
│  PREDICTIVE SIGNALS                                         │
│  Forecast chart + "Equipment X likely to fail within 7d"   │
└─────────────────────────────────────────────────────────────┘
```

### 9.3 Dashboard Page Layout (Power BI Style)

```
┌─────────────────────────────────────────────────────────────┐
│  [≡ Filters] Run Name    [dashboard.metadata.title]         │
│  Saved 3m ago                                               │
│  [Refresh] [Edit Layout] [Save] [Insights] [Export]         │
├──────────┬──────────────────────────────────────────────────┤
│ SIDEBAR  │  CANVAS (12-column grid)                         │
│ Filters: │                                                   │
│ Machine  │  ── Section: KPI Overview ─────────────────────  │
│ Failure  │  [MTTR: 1.4h] [Total: 57] [MECH%: 68] [ELEC%]  │
│ TimeRange│                                                   │
│          │  ── Section: Trend Analysis ───────────────────  │
│ Hidden:  │  [Failures/Week Line Chart    ][Top Equipment]   │
│ [chip×]  │                                                   │
│          │  ── Section: Root Cause Analysis ──────────────  │
│          │  [Why1 Frequency Bar — Full Width               ]│
│          │                                                   │
│          │  ── Section: Detailed Records ─────────────────  │
│          │  [Full Data Table — Full Width                  ]│
└──────────┴──────────────────────────────────────────────────┘
```

### 9.4 TypeScript State Rules (No Exceptions)

```typescript
// dashboards_ui_store.ts
interface InteractionState {
    hiddenWidgets:    string[];                    // ← NEVER Set<string>
    visualTypes:      Record<string, string>;
    timeGranularity:  "day" | "month" | "year";
    globalFilters:    FilterMap;
    slicers:          SlicerState;
    drillContext:     FilterMap | null;
    lastSaved:        string | null;              // ISO timestamp
}

// hiddenWidgets operations — always array methods:
// Check:  hiddenWidgets.includes(id)           ← NOT .has()
// Count:  hiddenWidgets.length                  ← NOT .size
// Add:    [...hiddenWidgets, id]
// Remove: hiddenWidgets.filter(x => x !== id)
// Toggle: see toggleHiddenWidget() in store

// Chart components:
// Return type: React.ReactElement               ← NOT JSX.Element
```

---

## 10. Export Engine

### 10.1 Export Modes

| Export Type | Trigger | Output Format | Content |
|-------------|---------|---------------|---------|
| Insights Only | "Export Insights" button | `.pdf` or `.docx` | Full insight report |
| Dashboard Only | "Export Dashboard" button | `.pdf` (4K render) | Dashboard screenshot |
| Dashboard File | "Save as File" | `.json` | Blueprint + saved layout |
| Full Report | "Export Full Report" | `.pdf` ONLY | Insights + Dashboard combined |

### 10.2 PDF Export — Dashboard (4K Quality)

```typescript
// In renderer process (Electron context)
async function exportDashboardPDF(runId: string): Promise<void> {
    const dashboardEl = document.getElementById('dashboard-canvas');
    
    // Render at 4x scale for 4K-equivalent quality
    const canvas = await html2canvas(dashboardEl, {
        scale: 4,
        useCORS: true,
        backgroundColor: '#ffffff',
        logging: false,
    });
    
    const imageDataUrl = canvas.toDataURL('image/png', 1.0);
    
    // Send to Python via IPC for PDF assembly
    const result = await window.electronAPI.exportDashboardPDF(runId, imageDataUrl);
    if (result.success) {
        window.electronAPI.openFile(result.data.file_path);
    }
}
```

```python
# In export/pdf_exporter.py
def export_dashboard_pdf(run_id: str, image_data_b64: str) -> str:
    from reportlab.lib.pagesizes import landscape
    from reportlab.lib.pagesizes import A3
    from reportlab.pdfgen.canvas import Canvas
    from reportlab.lib.utils import ImageReader
    import base64, io
    from PIL import Image
    
    img_bytes = base64.b64decode(image_data_b64.split(',')[1])
    img = Image.open(io.BytesIO(img_bytes))
    
    output_path = get_export_path(run_id, "dashboard.pdf")
    page_size = landscape(A3)
    c = Canvas(str(output_path), pagesize=page_size)
    w, h = page_size
    
    # Add header
    c.setFont("Helvetica-Bold", 10)
    c.drawString(30, h - 20, f"Dashboard Report | Run: {run_id}")
    c.drawRightString(w - 30, h - 20, datetime.now().strftime("%Y-%m-%d %H:%M"))
    
    # Draw dashboard image
    c.drawImage(ImageReader(img), 0, 0, width=w, height=h - 30,
                preserveAspectRatio=True, anchor='sw')
    
    c.save()
    return str(output_path)
```

### 10.3 DOCX Export — Insights Report

```python
# export/docx_exporter.py
def export_insights_docx(run_id: str, insight_report: InsightReport) -> str:
    """
    Produces a professional Word document with:
    - Cover page (title, run ID, date, risk level)
    - Auto-generated Table of Contents
    - Section 1: Executive Summary (styled box)
    - Section 2: Data Overview (stats table)
    - Section 3: Key Findings (severity-colored cards → tables)
    - Section 4: Pattern Analysis (chart images embedded)
    - Section 5: Root Cause Analysis (ranked table)
    - Section 6: Recommendations (3-tier priority tables)
    - Section 7: Predictive Signals (forecast chart + text)
    - Footer: "Confidential | Offline Industrial Intelligence | {date}"
    """
    from docx import Document
    from docx.shared import Pt, RGBColor, Inches
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    
    doc = Document()
    _set_document_styles(doc)
    _add_cover_page(doc, run_id, insight_report)
    _add_toc(doc)
    _add_executive_summary(doc, insight_report.executive_summary, 
                           insight_report.risk_level)
    _add_data_overview(doc, insight_report)
    _add_key_findings(doc, insight_report.key_findings)
    _add_pattern_analysis(doc, insight_report.pattern_analysis)
    _add_rca_section(doc, insight_report.root_cause_analysis)
    _add_recommendations(doc, insight_report.recommendations)
    _add_predictive_signals(doc, insight_report.predictive_signals)
    _add_footer(doc)
    
    output_path = get_export_path(run_id, "insights_report.docx")
    doc.save(str(output_path))
    return str(output_path)
```

### 10.4 Combined PDF (Insights + Dashboard)

```python
def export_combined_pdf(run_id: str, insight_report: InsightReport, 
                        dashboard_image_b64: str) -> str:
    """
    Page flow:
    1. Cover page
    2. Table of Contents  
    3–N. Insights sections (converted from DOCX via reportlab)
    N+1. Divider page: "Dashboard Visualization"
    N+2 to end. Dashboard pages (one section per page if possible)
    """
    from reportlab.platypus import SimpleDocTemplate, PageBreak
    
    # Build insights pages
    insights_elements = _build_insights_elements(insight_report)
    
    # Build dashboard page
    dashboard_elements = _build_dashboard_page(dashboard_image_b64, run_id)
    
    all_elements = insights_elements + [PageBreak()] + dashboard_elements
    
    output_path = get_export_path(run_id, "full_report.pdf")
    doc = SimpleDocTemplate(str(output_path), pagesize=A4)
    doc.build(all_elements, onFirstPage=_add_header_footer,
              onLaterPages=_add_header_footer)
    return str(output_path)
```

---

## 11. IPC Contract (All Handlers)

### 11.1 Standard Response Shape

```typescript
// ALL IPC responses MUST use this — no exceptions
interface IPCResponse<T = any> {
    success: boolean;
    data?:   T;
    message?: string;    // User-friendly, shown in UI
    error?:  string;     // Technical detail, logged only
    code?:   string;     // Machine-readable error code
}
```

### 11.2 All IPC Methods

```typescript
// runs
window.electronAPI.getRuns()                          → IPCResponse<RunList>
window.electronAPI.getRunDetails(runId)               → IPCResponse<RunDetails>
window.electronAPI.setActiveRun(runId)                → IPCResponse<void>

// ingestion
window.electronAPI.ingestFile(filePath, sourceType?)  → IPCResponse<IngestionResult>
window.electronAPI.getIngestionStatus(runId)          → IPCResponse<IngestionStatus>

// insights
window.electronAPI.getInsights(runId)                 → IPCResponse<InsightReport>
window.electronAPI.exportInsights(runId, format)      → IPCResponse<{file_path: string}>

// dashboard
window.electronAPI.getDashboard(runId)                → IPCResponse<DashboardData>
window.electronAPI.saveDashboardLayout(runId, bpId, layout) → IPCResponse<void>
window.electronAPI.exportDashboardPDF(runId, imgData) → IPCResponse<{file_path: string}>

// exports
window.electronAPI.exportFullReport(runId, imgData)   → IPCResponse<{file_path: string}>
window.electronAPI.getExportHistory(runId)            → IPCResponse<ExportRecord[]>
window.electronAPI.openFile(filePath)                 → IPCResponse<void>

// data health
window.electronAPI.getDataHealth(runId)               → IPCResponse<DataHealthReport>

// explorer
window.electronAPI.getExplorerData(runId, page, pageSize) → IPCResponse<TablePage>
```

---

## 12. Database Schema

```sql
-- storage/schema.sql

CREATE TABLE IF NOT EXISTS runs (
    run_id          TEXT PRIMARY KEY,
    run_name        TEXT NOT NULL,
    source_type     TEXT,
    status          TEXT DEFAULT 'PENDING',  -- PENDING/RUNNING/COMPLETED/FAILED
    error_message   TEXT,
    failed_step     TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at    TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ingested_files (
    file_id                     TEXT PRIMARY KEY,
    run_id                      TEXT NOT NULL REFERENCES runs(run_id),
    file_name                   TEXT NOT NULL,
    source_type                 TEXT,
    source_schema_type          TEXT,
    schema_version              TEXT,
    schema_hash                 TEXT,
    schema_drift_detected       BOOLEAN DEFAULT FALSE,
    row_count                   INTEGER,
    output_path                 TEXT,
    original_column_snapshot    JSON,
    normalized_column_snapshot  JSON,
    column_mapping              JSON,
    mapping_decisions           JSON,
    unmapped_source_columns     JSON,
    ingested_at                 TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS data_profiles (
    profile_id      TEXT PRIMARY KEY,
    run_id          TEXT NOT NULL REFERENCES runs(run_id),
    domain          TEXT,
    health_score    REAL,
    column_profiles JSON,   -- List[ColumnProfile] serialized
    health_details  JSON,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS insights (
    insight_id      TEXT PRIMARY KEY,
    run_id          TEXT NOT NULL REFERENCES runs(run_id),
    domain          TEXT,
    risk_level      TEXT,
    executive_summary TEXT,
    key_findings    JSON,
    pattern_analysis JSON,
    rca_data        JSON,
    recommendations JSON,
    predictive_signals JSON,
    chart_data      JSON,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS dashboard_blueprints (
    blueprint_id    TEXT PRIMARY KEY,
    run_id          TEXT NOT NULL REFERENCES runs(run_id),
    domain          TEXT,
    blueprint_json  JSON NOT NULL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS dashboard_layout (
    layout_id       TEXT PRIMARY KEY,
    run_id          TEXT NOT NULL,
    blueprint_id    TEXT,
    user_saved_layout JSON NOT NULL,   -- {widget_order, hidden_widgets, widget_visuals, slicers}
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS exports (
    export_id       TEXT PRIMARY KEY,
    run_id          TEXT NOT NULL REFERENCES runs(run_id),
    export_type     TEXT,    -- pdf_dashboard / docx_insights / pdf_combined / json_blueprint
    file_path       TEXT,
    file_size_kb    INTEGER,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 13. Sample Data Reference — Breakdown_data.csv

**A real industrial maintenance file — use as primary test case.**

```
File: Breakdown_data.csv
Rows: 57 maintenance breakdown events
Domain: maintenance (auto-detected)
Plant: 1152

Schema (auto-detected, unknown in advance):
    Notifictn Type → categorical (M2)
    Created On     → datetime
    Coding         → categorical (MECH / ELEC) → breakdown_type
    Equipment      → identifier (e.g. 1000005774)
    Description    → text (equipment name)
    Breakdown Dur. → numeric_kpi (hours, decimal)
    Malfunct. Start→ datetime (event timestamp)
    Why1–Why5      → text (5-Why root cause chain)
    Due To 1-5     → text (contributing factors)
    Action taken   → text (resolution)
    Coding code txt→ categorical (Mechanical Breakdown / Electrical Breakdown)

Expected insights output for this file:
  Executive Summary:
    "57 breakdown events documented across Plant 1152 maintenance records.
    Mechanical failures dominate at 68% (39 events) versus electrical at 32%
    (18 events). Mean Time to Repair averages 1.4 hours, but equipment
    1000005760 (Shaft Washing Machine) records 8 incidents — 14% of all
    failures — with root cause analysis revealing belt tension and circlip
    issues in 6 of 8 events. Failure frequency shows a Monday morning cluster
    (shift start 06:00–10:00) suggesting pre-shift inspection gaps.
    Immediate action: implement daily lubrication and tension inspection
    protocol for top 3 recurrent equipment IDs."
    
  Risk Level: HIGH
  
  Rule Engine Findings:
    - RepeatFailureRule: CRITICAL — Equipment 1000005760 (8 failures in period)
    - HighMTTRRule: MEDIUM — 3 equipment IDs exceed 2-hour MTTR threshold
    - FailureEscalationRule: HIGH — ELEC failures trending +40% vs prior period
    
  ML Findings:
    - AnomalyDetector: Equipment 1000005778 (Transmission Flange CNC)
      shows breakdown_duration outlier at 3.2σ above mean
    - FailurePatternDetector: Monday 06:00–10:00 cluster (37% of events)
      confidence 0.82 — statistically significant
    - Forecaster: At current failure rate, 12–15 additional breakdowns
      predicted in next 30 days for Plant 1152
```

---

## 14. Non-Negotiable Engineering Requirements

```
ZERO TOLERANCE:
□ No TODO stubs or "implement later" comments — every function fully implemented
□ No raw Python tracebacks shown to users — all errors caught and user-friendly
□ No JSX.Element — use React.ReactElement
□ No Set<string> in any state — use string[]
□ No localStorage in Electron renderer — use IPC for all persistence
□ No internet dependency at runtime — all ML, rules, insights run offline
□ No "Frontend not built" error — vite.config base: './' enforced

PERFORMANCE:
□ Dashboard render < 3 seconds for files up to 100,000 rows
□ Full ingestion pipeline < 30 seconds for files up to 50,000 rows
□ ML anomaly detection uses sampling for files > 10,000 rows (max 5000 samples)
□ Export PDF generation < 15 seconds

RELIABILITY:
□ DuckDB auto-recovery on WAL corruption (implemented in connection.py)
□ Ingestion never crashes app — always returns {success, error} shape
□ IPC handlers always return IPCResponse<T> — never throw unhandled exceptions
□ atexit.register(close_connection) in pipeline_runner.py

BUILD:
□ npm run build → 0 TypeScript errors
□ All imports use relative paths (../../)
□ vite.config.ts: base: './'
□ PyInstaller spec includes renderer/dist/ as data files
□ NSIS .nsi file paths match actual build output

QUALITY:
□ Insights reference specific values from actual data — not generic
□ Dashboard auto-layout makes visual sense (metrics first, charts second, table last)
□ Exports open correctly — PDFs in any viewer, DOCX in Word without repair prompts
□ Saved layout restores perfectly on next run open
□ "Saved X minutes ago" badge updates immediately after save
```

---

## 15. Complete Pipeline Execution Flow

```
USER uploads file
         │
         ▼
[INGESTION] detect_encoding → parse → detect_header → classify_columns
         │                           → compute_schema_hash → detect_domain
         │                           → save parquet/feather to storage
         ▼
[FEATURE STORE] normalize_types → align_time → compute_derived_features
         │                      → register_features
         ▼
[DATA PROFILER] profile_all_columns → compute_health_score
         │                         → identify_kpi_candidates
         │                         → flag_anomaly_columns
         ▼
    ┌────┴────┐
    ▼         ▼
[RULE ENGINE]  [ML ENGINE]
 threshold      anomaly_detection
 maintenance    failure_patterns
 domain rules   forecasting
    └────┬────┘
         ▼
[INSIGHT ORCHESTRATOR] merge → deduplicate → score → rank
         │                   → compose_narratives
         │                   → save to DuckDB (insights table)
         ▼
[BLUEPRINT ENGINE] select_kpis → select_charts → layout_rules
         │                      → build_DashboardBlueprint
         │                      → save to DuckDB (dashboard_blueprints)
         ▼
[EXPORT PRE-GENERATION] generate_xlsx + generate_pdf_summary
         │                → save to DuckDB (exports table)
         ▼
[IPC NOTIFICATION] run status → COMPLETED
         │
         ▼
USER sees completed run in sidebar
    ├── Clicks Insights → InsightReport renders from DuckDB
    ├── Clicks Dashboard → Blueprint renders, saved layout applied
    └── Clicks Export →
            ├── "Insights Only" → .docx or .pdf
            ├── "Dashboard" → html2canvas → 4K PDF
            └── "Full Report" → insights + dashboard combined PDF
```

---

*Specification v4.0 | Offline Industrial Intelligence | Aligned with Application_Architecture.pdf*
*Build: PyInstaller → NSIS | Stack: React+Vite+Electron / Python+DuckDB+scikit-learn*