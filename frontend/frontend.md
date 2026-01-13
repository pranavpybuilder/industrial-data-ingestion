# Frontend Architecture Layer  
Offline Industrial Data Intelligence System

## Overview

The frontend layer is implemented as a **fully offline Electron desktop application** with a **React-based renderer**.  
It is designed strictly as a **read-only intelligence consumer**, ensuring that no analytics, feature computation, rule evaluation, or machine learning logic is executed at the UI level.

The frontend consumes only **final, validated, and versioned outputs** from backend layers through controlled interfaces, preserving determinism, auditability, and data confidentiality.

---

## Core Design Principles

- Fully offline operation with no internet dependency
- No cloud services, telemetry, or external APIs
- Strict separation between UI state and system intelligence
- Run-scoped visibility for insights and dashboards
- Explainability-first design for maintenance engineers
- Deterministic rendering based on backend outputs

---

## Frontend Responsibility Mapping

### Backend Layers Visible to Frontend

| Architecture Layer | Frontend Sees | Reason |
|-------------------|---------------|--------|
| Data Profiler | Data health, column roles, statistics | Engineers trust data only when quality is visible |
| Rule Engine | Rule results and explanations | Maintenance decisions require explainability |
| ML Engine | Anomaly flags and confidence scores | Model internals must remain hidden |
| Insight Orchestrator | Final merged insights | Single source of truth |
| Dashboard Blueprint Engine | KPIs, charts, layouts | UI rendering logic |
| Local SQLite Storage | Read-only views | Offline and auditable |

### Backend Layers Hidden from Frontend

| Backend Layer | Frontend Access |
|--------------|-----------------|
| Ingestion | ❌ Hidden |
| Feature Store | ❌ Hidden |
| Normalization | ❌ Hidden |
| Raw Data Sources | ❌ Hidden |

---

## Navigation Structure

The frontend uses a **persistent left sidebar** with a **central workspace**.  
Navigation does not reset application state and is optimized for long-running industrial usage.

### Primary Screens (Always Visible)

1. Home / System Overview  
2. Data Ingestion  
3. Insights  
4. Dashboards  
5. Exports & Reports  

### Contextual Screens

- Data Health & Profiling  
- Entity / Explorer (Machine, Order, Time, Report)

### Hidden / Advanced Screens

- System Metadata (Advanced / About)

---

## Run-Scoped Intelligence Model

- Every ingestion creates an immutable **run**
- Insights and dashboards are always scoped to a single run
- Users can switch runs via a searchable run selector
- No implicit merging of runs is allowed
- Switching runs never triggers recomputation

---

## Export Lifecycle Design

Exports are treated as **first-class system outcomes**.

### Supported Export Scopes

- Insights only  
- Dashboards only  
- Combined Insights + Dashboards  

### Supported Formats

- Excel  
- PDF  

### Export Characteristics

- Exports consume only precomputed outputs
- Exported reports are immutable
- Reports are searchable by run, file name, type, and timestamp

---

## UI Behavior Guarantees

- No blank screens under any condition
- Explicit empty-state messaging
- Human-readable error explanations
- Offline-first assumptions everywhere
- No auto-fixing, guessing, or silent failures

---

## Frontend Validation Guarantees

The frontend guarantees:

- No cross-run data leakage
- No analytics execution from UI actions
- Full auditability via run IDs and metadata
- Deterministic and reproducible rendering
- Safe deletion (soft delete for dashboards, explicit delete for reports)

---

## Next Steps

- Implement Electron main process and secure IPC layer
- Implement React renderer following defined contracts
- Validate frontend using the defined validation checklist
- Integrate frontend with backend storage and orchestration outputs
