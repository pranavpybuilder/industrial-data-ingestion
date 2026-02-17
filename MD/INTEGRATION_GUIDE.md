# Integration Guide: Frontend + Module 4 ML Engine + Testing

## Overview

This guide covers:
1. **Frontend Integration**: Display Rule Findings (Module 3) in Insights page
2. **Module 4 ML Engine**: Anomaly detection design for full compatibility
3. **Backend Testing**: Step-by-step procedures for all layers
4. **Synthetic Data**: Test files for each data source

---

## Part 1: Frontend Integration - Rule Findings Display

### Architecture

```
Backend (Python)              IPC Layer              Frontend (React/TypeScript)
─────────────────             ─────────             ────────────────────────

Modules 1-3:      →    insights_ipc.py    →    Insights.tsx
- Rules Engine        (IPC Handler)              (Consumer)
- Profiling
- Results DB

       ↓
  InsightRepository
  (loads from insights table)
```

### Step 1: Extend InsightRepository to include Rule Findings

**File: `storage/repositories/insight_repo.py`**

```python
def save_rule_findings(self, run_id: str, rule_findings: List[Dict]) -> None:
    """Save rule findings as insights."""
    conn = get_connection()
    
    for idx, finding in enumerate(rule_findings):
        insight_id = f"{run_id}_rule_{finding['rule_id']}_{idx}"
        
        conn.execute(
            """
            INSERT INTO insights (
                insight_id, run_id, insight_type, summary, confidence, metadata
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                insight_id,
                run_id,
                "rule_finding",  # New type
                finding['message'],  # Rule message as summary
                finding['confidence'],
                json.dumps({
                    "rule_name": finding['rule_name'],
                    "rule_id": finding['rule_id'],
                    "severity": finding['severity'],
                    "remediation": finding['remediation'],
                    "affected_columns": finding.get('affected_columns', []),
                    "triggered": finding['triggered'],
                }),
            ),
        )

def get_rule_findings(self, run_id: str) -> List[Dict]:
    """Retrieve rule findings for a run."""
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT insight_id, summary, confidence, metadata
        FROM insights
        WHERE run_id = ? AND insight_type = 'rule_finding'
        ORDER BY created_at DESC
        """,
        (run_id,),
    ).fetchall()
    
    return [
        {
            "insight_id": r[0],
            "message": r[1],
            "confidence": r[2],
            **json.loads(r[3]),  # Unpack metadata
        }
        for r in rows
    ]
```

### Step 2: Update insights_ipc.py to include Rule Findings

**File: `ipc/insights_ipc.py`**

```python
from storage.repositories.insight_repo import InsightRepository
from storage.repositories.profiling_repo import ProfilingRepository
import json

insight_repo = InsightRepository()
profiling_repo = ProfilingRepository()


def get_insights_ipc(run_id: str):
    """
    Get all insights for a run: Rule Findings + Profiling Summary.
    """
    rule_findings = insight_repo.get_rule_findings(run_id)
    profiling_results = profiling_repo.get_profiling_results(run_id)
    
    # Aggregate profiling into summary
    profiling_summary = {
        "total_columns": len(profiling_results),
        "complete_columns": sum(
            1 for r in profiling_results 
            if r.get('missing_percentage', 0) < 20
        ),
        "health_status": "good" if len(profiling_results) > 0 else "unknown",
    }
    
    return {
        "success": True,
        "data": {
            "rule_findings": rule_findings,  # NEW
            "profiling_summary": profiling_summary,
            "insights": insight_repo.get_insights(run_id),
        },
    }
```

### Step 3: Update Insights.tsx to Display Rule Findings

**File: `frontend/electron_app/renderer/src/pages/Insights/Insights.tsx`**

```tsx
import { useSyncExternalStore, useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { FiBarChart2, FiArrowRight, FiDownload, FiAlertCircle, FiCheckCircle } from "react-icons/fi";
import { runUI } from "../../state/run_ui_store";

// Severity colors
const SEVERITY_COLORS = {
  critical: "#dc2626",
  warning: "#f59e0b",
  info: "#3b82f6",
};

const SEVERITY_BG = {
  critical: "#fee2e2",
  warning: "#fef3c7",
  info: "#dbeafe",
};

const Insights = () => {
  const navigate = useNavigate();
  const [ruleFindings, setRuleFindings] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const runState = useSyncExternalStore(
    runUI.subscribe,
    runUI.getSnapshot
  );

  const activeRun = runState.activeRunId;

  // Fetch rule findings when run changes
  useEffect(() => {
    if (!activeRun) return;

    setLoading(true);
    // IPC call to get insights (includes rule findings)
    window.ipcRenderer?.invoke("get_insights_ipc", activeRun)
      .then((response: any) => {
        if (response?.success && response?.data?.rule_findings) {
          setRuleFindings(response.data.rule_findings);
        }
      })
      .catch((err: any) => console.error("Failed to fetch insights:", err))
      .finally(() => setLoading(false));
  }, [activeRun]);

  if (!activeRun) {
    return (
      <section>
        <h1>Insights</h1>
        <p>No active run selected.</p>
      </section>
    );
  }

  return (
    <>
      <style>{fadeKeyframes}</style>
      <section style={styles.page}>
        {/* Header */}
        <header style={styles.header}>
          <div style={styles.headerIcon}>
            <FiBarChart2 size={22} color="#6366f1" />
          </div>
          <div>
            <h1 style={styles.title}>Insights</h1>
            <p style={styles.subtitle}>
              Generated insights for <strong>{activeRun}</strong>
            </p>
          </div>
        </header>

        {/* Rule Findings Section - NEW */}
        {ruleFindings.length > 0 && (
          <div style={styles.card}>
            <h3 style={styles.cardTitle}>
              System Findings ({ruleFindings.length})
            </h3>
            <div style={styles.findingsList}>
              {ruleFindings.map((finding, idx) => (
                <div
                  key={idx}
                  style={{
                    ...styles.findingItem,
                    borderLeftColor: SEVERITY_COLORS[finding.severity as keyof typeof SEVERITY_COLORS],
                    backgroundColor: SEVERITY_BG[finding.severity as keyof typeof SEVERITY_BG],
                  }}
                >
                  <div style={styles.findingHeader}>
                    <div style={styles.findingTitle}>
                      {finding.triggered ? (
                        <FiAlertCircle size={18} color={SEVERITY_COLORS[finding.severity as keyof typeof SEVERITY_COLORS]} />
                      ) : (
                        <FiCheckCircle size={18} color="#10b981" />
                      )}
                      <span style={{ marginLeft: "8px", fontWeight: 600 }}>
                        {finding.rule_name}
                      </span>
                    </div>
                    <span style={styles.severity}>
                      {finding.severity.toUpperCase()}
                    </span>
                  </div>
                  
                  <p style={styles.findingMessage}>
                    {finding.message}
                  </p>
                  
                  {finding.remediation && (
                    <p style={styles.remediation}>
                      <strong>Action:</strong> {finding.remediation}
                    </p>
                  )}
                  
                  {finding.affected_columns && finding.affected_columns.length > 0 && (
                    <div style={styles.affectedCols}>
                      <strong>Affected Columns:</strong>{" "}
                      {finding.affected_columns.join(", ")}
                    </div>
                  )}
                  
                  <div style={styles.confidenceBar}>
                    <div 
                      style={{
                        ...styles.confidenceFill,
                        width: `${(finding.confidence || 0) * 100}%`,
                        backgroundColor: SEVERITY_COLORS[finding.severity as keyof typeof SEVERITY_COLORS],
                      }}
                    />
                  </div>
                  <small style={styles.confidence}>
                    Confidence: {((finding.confidence || 0) * 100).toFixed(0)}%
                  </small>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div style={styles.card}>
            <p style={{ color: "#999" }}>Loading insights...</p>
          </div>
        )}

        {/* No Findings State */}
        {!loading && ruleFindings.length === 0 && (
          <div style={styles.card}>
            <p style={{ color: "#10b981" }}>✓ All system checks passed</p>
          </div>
        )}

        {/* Actions */}
        <div style={styles.actions}>
          <button
            style={styles.primaryBtn}
            onClick={() => navigate("/dashboards")}
            onMouseEnter={(e) => { (e.currentTarget.style.background) = "#4f46e5"; }}
            onMouseLeave={(e) => { (e.currentTarget.style.background) = "#6366f1"; }}
          >
            <FiArrowRight size={15} />
            Go to Dashboards
          </button>

          <button
            style={styles.secondaryBtn}
            onClick={() => navigate("/exports")}
            onMouseEnter={(e) => { e.currentTarget.style.background = "#f3f4f6"; }}
            onMouseLeave={(e) => { e.currentTarget.style.background = "#ffffff"; }}
          >
            <FiDownload size={15} />
            Export Insights
          </button>
        </div>
      </section>
    </>
  );
};

// Add these new styles
const fadeKeyframes = `
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: none; }
}
`;

const styles: Record<string, React.CSSProperties> = {
  // ... existing styles ...
  
  findingsList: {
    display: "flex",
    flexDirection: "column",
    gap: "12px",
  },

  findingItem: {
    borderLeft: "4px solid #ef4444",
    padding: "12px",
    borderRadius: "6px",
    backgroundColor: "#fee2e2",
  },

  findingHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "8px",
  },

  findingTitle: {
    display: "flex",
    alignItems: "center",
    fontSize: "14px",
  },

  severity: {
    fontSize: "11px",
    fontWeight: 600,
    padding: "4px 8px",
    borderRadius: "4px",
    backgroundColor: "rgba(0,0,0,0.1)",
  },

  findingMessage: {
    fontSize: "13px",
    margin: "6px 0",
    color: "#1f2937",
  },

  remediation: {
    fontSize: "12px",
    marginTop: "8px",
    padding: "8px",
    backgroundColor: "rgba(255,255,255,0.5)",
    borderRadius: "4px",
    color: "#374151",
  },

  affectedCols: {
    fontSize: "12px",
    marginTop: "6px",
    color: "#374151",
  },

  confidenceBar: {
    width: "100%",
    height: "4px",
    backgroundColor: "rgba(0,0,0,0.1)",
    borderRadius: "2px",
    marginTop: "8px",
    overflow: "hidden",
  },

  confidenceFill: {
    height: "100%",
    transition: "width 0.3s ease",
  },

  confidence: {
    display: "block",
    marginTop: "4px",
    color: "#666",
  },

  // ... existing styles ...
};

export default Insights;
```

---

## Part 2: Module 4 ML Engine - Anomaly Detection Design

### Architecture Overview

```
Module 2 (Profiling) ──┐
Module 3 (Rules)       ├──→ Module 5 (Orchestration) ──→ Frontend (Insights)
Module 4 (ML)          │
 ↓ Anomaly Detection ──┘
```

### Module 4: Core Components

**File: `ml_engine/anomaly_detector.py`** (NEW)

```python
"""
Module 4: Anomaly Detection Engine.

Works alongside Module 3 Rules Engine:
- Module 3: Deterministic threshold-based + domain-specific rules
- Module 4: Statistical anomaly detection (complementary)

Integration: Both feed into Module 5 Orchestration
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
import numpy as np
from scipy import stats
import json


@dataclass
class AnomalyResult:
    """Result of anomaly detection analysis."""
    anomaly_type: str  # "univariate", "multivariate", "temporal"
    column: str
    is_anomaly: bool
    anomaly_score: float  # 0-1
    confidence: float  # 0-1
    method: str  # "isolation_forest", "zscore", "seasonal_decomposition"
    message: str
    remediation: str
    severity: str  # "critical", "warning", "info"


class AnomalyDetector(ABC):
    """Base class for anomaly detection strategies."""

    @abstractmethod
    def detect(self, data: np.ndarray, column_name: str) -> AnomalyResult:
        """Detect anomalies in column data."""
        pass


class UnivariateAnomalyDetector(AnomalyDetector):
    """Z-score based univariate anomaly detection."""

    def detect(self, data: np.ndarray, column_name: str) -> AnomalyResult:
        # Remove NaN
        clean_data = data[~np.isnan(data)]
        
        if len(clean_data) < 5:
            return AnomalyResult(
                anomaly_type="univariate",
                column=column_name,
                is_anomaly=False,
                anomaly_score=0.0,
                confidence=0.0,
                method="zscore",
                message="Insufficient data for analysis",
                remediation="Collect more data points",
                severity="info",
            )

        z_scores = np.abs(stats.zscore(clean_data))
        outlier_ratio = (z_scores > 3).sum() / len(clean_data)
        
        is_anomaly = outlier_ratio > 0.15

        return AnomalyResult(
            anomaly_type="univariate",
            column=column_name,
            is_anomaly=is_anomaly,
            anomaly_score=min(outlier_ratio, 1.0),
            confidence=0.85,
            method="zscore",
            message=f"{column_name}: {(outlier_ratio*100):.1f}% values are statistical outliers",
            remediation="Review identified outliers for data quality issues" if is_anomaly else "Data within expected range",
            severity="warning" if is_anomaly else "info",
        )


class IsolationForestDetector(AnomalyDetector):
    """Isolation forest for multivariate anomaly detection."""

    def detect(self, data: np.ndarray, column_name: str) -> AnomalyResult:
        try:
            from sklearn.ensemble import IsolationForest
            
            clean_data = data[~np.isnan(data)].reshape(-1, 1)
            
            if len(clean_data) < 10:
                return AnomalyResult(
                    anomaly_type="multivariate",
                    column=column_name,
                    is_anomaly=False,
                    anomaly_score=0.0,
                    confidence=0.0,
                    method="isolation_forest",
                    message="Insufficient data for multivariate analysis",
                    remediation="Collect more data points",
                    severity="info",
                )

            iso_forest = IsolationForest(
                contamination=0.1,
                random_state=42,
                n_estimators=50,
            )
            predictions = iso_forest.fit_predict(clean_data)
            anomaly_ratio = (predictions == -1).sum() / len(clean_data)

            return AnomalyResult(
                anomaly_type="multivariate",
                column=column_name,
                is_anomaly=anomaly_ratio > 0.10,
                anomaly_score=min(anomaly_ratio, 1.0),
                confidence=0.80,
                method="isolation_forest",
                message=f"{column_name}: {(anomaly_ratio*100):.1f}% anomalous samples detected",
                remediation="Investigate isolated patterns in data distribution",
                severity="warning" if anomaly_ratio > 0.10 else "info",
            )
        except ImportError:
            return AnomalyResult(
                anomaly_type="multivariate",
                column=column_name,
                is_anomaly=False,
                anomaly_score=0.0,
                confidence=0.0,
                method="isolation_forest",
                message="Scikit-learn not available",
                remediation="Install scikit-learn for advanced anomaly detection",
                severity="info",
            )


class TemporalAnomalyDetector(AnomalyDetector):
    """Temporal/seasonal anomaly detection."""

    def detect(self, data: np.ndarray, column_name: str, timestamps: Optional[np.ndarray] = None) -> AnomalyResult:
        clean_data = data[~np.isnan(data)]
        
        if len(clean_data) < 20:
            return AnomalyResult(
                anomaly_type="temporal",
                column=column_name,
                is_anomaly=False,
                anomaly_score=0.0,
                confidence=0.0,
                method="seasonal_decomposition",
                message="Insufficient temporal data",
                remediation="Collect more time-series observations",
                severity="info",
            )

        # Simple autocorrelation check
        autocorr = np.correlate(
            clean_data - clean_data.mean(),
            clean_data - clean_data.mean(),
            mode='full'
        )
        autocorr = autocorr[len(autocorr)//2:]
        autocorr = autocorr / autocorr[0]
        
        lag_1_corr = autocorr[1] if len(autocorr) > 1 else 0
        
        has_temporal_pattern = lag_1_corr > 0.7

        return AnomalyResult(
            anomaly_type="temporal",
            column=column_name,
            is_anomaly=False,
            anomaly_score=0.0,
            confidence=0.60,
            method="seasonal_decomposition",
            message=f"{column_name}: Autocorrelation={lag_1_corr:.2f}",
            remediation="Data shows temporal patterns; suitable for time-series forecasting",
            severity="info",
        )


class MLEngine:
    """Module 4: ML Engine orchestrator."""

    def __init__(self):
        self.univariate_detector = UnivariateAnomalyDetector()
        self.multivariate_detector = IsolationForestDetector()
        self.temporal_detector = TemporalAnomalyDetector()

    def analyze_profiles(
        self,
        run_id: str,
        profiles: Dict[str, Any],
        data: Optional[Dict[str, np.ndarray]] = None,
    ) -> Dict[str, Any]:
        """
        Analyze column profiles with ML models.
        
        Parameters
        ----------
        run_id : str
            Run ID
        profiles : dict
            Column profiles from Module 2
        data : dict, optional
            Raw column data for temporal analysis
            
        Returns
        -------
        dict with keys:
            - anomaly_results: List of AnomalyResult dicts
            - summary: High-level findings
            - recommendations: Machine learning insights
        """
        anomaly_results = []

        # Univariate anomaly detection (all columns)
        for col_name, profile in profiles.items():
            if profile.get('type') in ['numeric', 'integer', 'float']:
                # Get data if available
                col_data = None
                if data and col_name in data:
                    col_data = data[col_name]
                
                if col_data is not None:
                    result = self.univariate_detector.detect(col_data, col_name)
                    anomaly_results.append(result)

        # Build summary
        critical_anomalies = [
            r for r in anomaly_results
            if r.severity == "critical"
        ]
        warning_anomalies = [
            r for r in anomaly_results
            if r.severity == "warning"
        ]

        return {
            "anomaly_results": [
                {
                    "anomaly_type": r.anomaly_type,
                    "column": r.column,
                    "is_anomaly": r.is_anomaly,
                    "anomaly_score": r.anomaly_score,
                    "confidence": r.confidence,
                    "method": r.method,
                    "message": r.message,
                    "remediation": r.remediation,
                    "severity": r.severity,
                }
                for r in anomaly_results
            ],
            "summary": {
                "total_analyzed": len(anomaly_results),
                "anomalies_detected": len([r for r in anomaly_results if r.is_anomaly]),
                "critical": len(critical_anomalies),
                "warning": len(warning_anomalies),
            },
            "recommendations": [
                "Consider seasonal decomposition for temporal patterns" if any(
                    r.anomaly_type == "temporal" for r in anomaly_results
                ) else None,
                "Multivariate outlier detection useful for feature interactions" if len(
                    [r for r in anomaly_results if r.type == "numeric"]
                ) > 5 else None,
            ],
        }
```

### Module 4 Integration with Module 5

**File: `ml_engine/__init__.py`**

```python
from ml_engine.anomaly_detector import (
    MLEngine,
    AnomalyDetector,
    AnomalyResult,
    UnivariateAnomalyDetector,
    IsolationForestDetector,
    TemporalAnomalyDetector,
)

__all__ = [
    "MLEngine",
    "AnomalyDetector",
    "AnomalyResult",
    "UnivariateAnomalyDetector",
    "IsolationForestDetector",
    "TemporalAnomalyDetector",
]
```

---

## Part 3: Backend Testing - Complete Procedures

### Test Strategy

```
Synthetic Data (5 sources) 
         ↓
Module 1: Ingestion (validation + versioning)
         ↓
Module 2: Profiling (classification + health)
         ↓
Module 3: Rules (threshold + domain-specific)
         ↓
Module 4: ML (anomaly detection) [OPTIONAL]
         ↓
Module 5: Orchestration (merge findings)
         ↓
Frontend: Display in Insights
```

### Test Execution Matrix

```
Data Source     Rows    Expected Health    Rule Findings    ML Findings
─────────────────────────────────────────────────────────────────────
PLC (sensors)    50      85-90%            2-4 findings     Outliers in temp/vibration
SAP (Orders)     30      80-85%            1-2 findings     PM overdue patterns
RFID (Scans)     100     88-92%            0-1 findings     Connectivity gaps
Report Excel     25      75-80%            2-3 findings     Missing data patterns
Operational      40      82-88%            1-2 findings     Energy anomalies
─────────────────────────────────────────────────────────────────────
```

### Layer-by-Layer Testing

#### Layer 1: Ingestion (Module 1)

```bash
# Test command
.\venv\Scripts\python -c "
from ingestion.upload_handler import handle_file_upload
result = handle_file_upload('synthetic_data/plc_sample.csv', 'plc')
print(f'✓ Ingestion: {result[\"rows\"]} rows parsed')
print(f'✓ Columns: {result[\"columns\"]}')
"

# Expected output:
# ✓ Ingestion: 50 rows parsed
# ✓ Columns: ['timestamp', 'temperature', 'pressure', 'vibration', 'energy', 'rpm']
```

#### Layer 2: Profiling (Module 2)

```bash
# Test command
.\venv\Scripts\python test_profiling_module.py

# Expected: Creates column profiles for each column
# Health score should be in 75-95 range depending on data quality
```

#### Layer 3: Rules (Module 3)

```bash
# Test command
.\venv\Scripts\python -c "
from rule_engine import ThresholdEngine
from profiling.data_profiler import DataProfiler
import pandas as pd

df = pd.read_parquet('data/raw/plc/plc.parquet')
profiler = DataProfiler(df)
profiles = profiler.profile()

engine = ThresholdEngine()
findings = engine.apply_to_all_profiles(profiles)
print(f'✓ Rules: {len(findings)} rules evaluated')
"

# Expected: Shows triggered rules and findings
```

#### Layer 4: ML (Module 4)

```bash
# Test command [OPTIONAL]
.\venv\Scripts\python -c "
from ml_engine import MLEngine
import pandas as pd

df = pd.read_parquet('data/raw/plc/plc.parquet')
engine = MLEngine()
results = engine.analyze_profiles('run_id', {}, data=df.to_dict('list'))
print(f'✓ ML: {results[\"summary\"][\"anomalies_detected\"]} anomalies detected')
"
```

#### Layer 5: Orchestration & Frontend (Modules 5+)

```bash
# Test full pipeline
.\venv\Scripts\python -c "
from app.pipeline_runner import PipelineRunner
runner = PipelineRunner()
result = runner.run_single_file('synthetic_data/plc_sample.csv', 'plc')
print(f'✓ Pipeline: {result[\"success\"]}')
print(f'✓ Health: {result[\"health_score\"]}')
print(f'✓ Rules: {result[\"triggered_rules\"]} triggered')
"
```

---

## Part 4: Synthetic Data Files

See separate section below for actual synthetic data file generation.

---

## Summary: Integration Checklist

### Frontend Integration
- [ ] Extend InsightRepository with `save_rule_findings()` and `get_rule_findings()`
- [ ] Update schema.sql to include `metadata` column in insights table
- [ ] Update insights_ipc.py to return rule findings
- [ ] Update Insights.tsx to display rule findings with severity colors
- [ ] Test IPC communication frontend ↔ backend

### Module 4 ML Engine
- [ ] Create ml_engine/anomaly_detector.py
- [ ] Create ml_engine/__init__.py
- [ ] Update requirements.txt with scikit-learn (optional)
- [ ] Design Module 5 to merge Module 3 + Module 4 findings
- [ ] Update pipeline_runner.py to call ML engine (optional)

### Testing Infrastructure
- [ ] Create synthetic_data/ folder with 5 data sources
- [ ] Create test_layers.py for step-by-step layer testing
- [ ] Create test_end_to_end.py for full pipeline
- [ ] Document expected outputs for each layer

### Deployment
- [ ] Update schema.sql in database initialization
- [ ] Run full pipeline with synthetic data
- [ ] Verify frontend displays rule findings
- [ ] Verify ML findings integrate without breaking existing rules

