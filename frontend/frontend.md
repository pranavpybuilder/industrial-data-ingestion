# Frontend Architecture
Offline Industrial Data Intelligence System

## Purpose
The frontend provides engineers with a fully offline, deterministic interface to ingest data, select operational runs, explore insights, create dashboards, and export reports—without exposing backend complexity.

---

## Core Design Principles
- **Offline-first**: No network APIs, no localhost dependencies.
- **Run-scoped workflows**: Every insight, dashboard, and export is tied to a specific ingestion run.
- **Explicit system state**: The UI always communicates whether the system is ready for analysis.
- **No duplicated enforcement**: UX guidance and routing protection are intentionally separated.

---

## Frontend Responsibilities
- Run selection and visibility
- Navigation and workflow guidance
- Metrics and operational overview
- Safe handling of empty and first-time states
- Desktop-grade UX consistency

---

## Key Architectural Components

### Run UI Store
- Single authoritative source of run context.
- Guarded setters prevent redundant updates.
- Stable snapshot and subscription model.

### Sidebar (Control Surface)
- Persistent branding and navigation.
- Active run visibility at all times.
- Run selection and clearing actions.
- Visual guarding of run-dependent sections.

### RunGuard
- Enforces valid navigation paths.
- Prevents access to insights, dashboards, exports without an active run.
- Keeps enforcement logic centralized and predictable.

### System Overview
- Displays operational metrics:
  - Total runs
  - Total insights
  - Total dashboards
  - Total exports
- Safe zero-state handling (first-time users).

---

## UX Safeguards
- Disabled visual states for unavailable sections.
- Tooltips explaining required actions.
- Truncation and overflow handling for long identifiers (file names).
- No surprise errors or silent failures.

---

## Current Status
- Frontend foundation is complete and stable.
- Ready for feature-level UI scaffolding.
- Fully aligned with backend ingestion and feature-store architecture.