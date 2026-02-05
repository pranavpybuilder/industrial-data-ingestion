# Feature Store & Normalization Layer

## Purpose

The Feature Store layer is responsible for converting raw, heterogeneous,
versioned industrial data into structured, validated, and normalized
features suitable for analytics, rule engines, and machine learning models.

This layer acts as the semantic boundary between raw data ingestion and
intelligence generation.

---

## Position in Architecture

Ingestion Layer → Feature Store & Normalization → Profiling / ML / Rules

The Feature Store does not ingest data and does not perform analytics.
Its sole responsibility is feature correctness and stability.

---

## Core Responsibilities

- Time alignment of heterogeneous data sources
- Conservative data cleaning
- Deterministic feature construction
- Configuration-driven normalization
- Feature governance and versioning
- Schema and range validation

---

## Processing Flow

1. **Time Alignment**
   - Event-time–based alignment
   - Fixed rolling windows
   - Config-driven behavior

2. **Data Cleaning**
   - Duplicate removal
   - Conservative missing value handling
   - Type enforcement without data loss

3. **Feature Building**
   - Source-specific builders (SAP, PLC, RFID, Excel)
   - Entity-scoped feature generation
   - Deterministic aggregation

4. **Normalization**
   - Min–Max scaling
   - Z-score normalization
   - No normalization for flags
   - Metadata persisted for reproducibility

5. **Validation**
   - Schema validation
   - Range validation
   - Fail-fast behavior

---

## Normalization Strategy

Normalization behavior is defined declaratively in:

- `configs/normalization.yaml`

Normalization metadata is persisted per pipeline run to enable:

- ML reproducibility
- Debugging
- Auditability

No normalization logic is hardcoded.

---

## Feature Governance

All generated features must be registered in:

- `registry/feature_registry.yaml`

The registry captures:

- Feature ownership
- Source system
- Entity mapping
- Version history
- Semantic description

This prevents uncontrolled feature drift.

---

## Design Principles

- Fully offline operation
- Configuration over code
- Deterministic outputs
- Fail fast, never silently
- Preserve real-world industrial signals

---

## Outcome

The Feature Store layer guarantees that downstream systems operate on
trusted, reproducible, and semantically correct features, enabling
safe analytics and machine learning in confidential industrial environments.
