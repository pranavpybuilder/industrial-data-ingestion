# Renderer Layer
Electron + React (Offline Desktop UI)

## Role
The renderer layer delivers a responsive, run-aware user interface inside the Electron shell while remaining completely offline and secure.

---

## Technology Stack
- React + TypeScript
- Electron (in-process APIs)
- Vite (development & bundling)
- No HTTP, no localhost APIs

---

## Architectural Responsibilities
- Render UI based on active run context.
- Maintain deterministic state updates.
- Provide visual guidance without duplicating backend logic.
- Interface safely with Electron preload APIs.

---

## State Management Strategy
- External UI stores with guarded mutations.
- `useSyncExternalStore` for stable subscriptions.
- Explicit reset behavior on run changes.
- No implicit or cascading state updates.

---

## Stability Guarantees
- No infinite render loops.
- No side effects inside render paths.
- Strict TypeScript compliance.
- Predictable behavior across navigation changes.

---

## UX–Logic Separation
- Renderer handles **what the user sees**.
- RunGuard handles **what the user is allowed to do**.
- Backend remains authoritative for data correctness.

---

## Current Status
- Renderer layer is production-ready.
- Electron integration stable.
- Prepared for Insights, Dashboards, and Export UI expansion.

Renderer (Frontend UI Layer)

Offline Industrial Data Intelligence System

This document describes the frontend renderer layer of the Offline Industrial Data Intelligence System used by the Maintenance Department of a Drive Shaft Manufacturing Plant.

The renderer is implemented using React + TypeScript and is designed to operate fully offline inside a PySide6 (Qt WebEngine) desktop shell.

1. Renderer Architecture Overview

The renderer is not a web application.
It is a desktop UI layer embedded inside a Python-based desktop executable.

There is no client–server model.

Desktop Application (.exe)
 ├── Python Runtime
 ├── PySide6 (Qt WebEngine)
 ├── In-Process API (Python QObject)
 └── React Renderer (this layer)


The renderer communicates only with an in-process API using Qt WebChannel.

2. Execution Modes

The renderer operates in two strictly separated modes.

2.1 Development Mode (Local Only)

Used only during frontend development.

React Source Code
   ↓
Vite Development Server (localhost)
   ↓
Browser / Qt WebEngine


Started using:

npm run dev


Enables hot reload and fast iteration

Uses localhost only as a dev tool

No backend server exists

No production dependency on localhost

⚠️ This mode is never used in the final application.

2.2 Production Mode (Final Desktop Application)

Used in the packaged desktop executable.

React Build (static files)
   ↓
file://index.html
   ↓
Qt WebEngine (inside .exe)


Built using:

npm run build


Outputs static files in dist/

Loaded locally by the PySide6 desktop shell

No Node.js at runtime

No dev server

No network access

✔ Fully offline
✔ Secure
✔ Deterministic

3.API Communication Model

The renderer does not use HTTP, REST, or localhost APIs.

All communication is in-process:

React Renderer
   ↓
Qt WebChannel
   ↓
Python QObject API

Key Properties

No open ports

No sockets

No HTTP endpoints

No CORS

No authentication tokens

No network surface

The API lives inside the same executable process.

This model is intentionally chosen for industrial, offline, confidential environments.

4.Renderer Responsibilities

The renderer layer is responsible for:

User navigation and layout

Displaying insights, dashboards, and reports

Run selection and UI state handling

Export interaction (UI-side only)

The renderer does not:

Perform data ingestion

Perform analytics or ML

Access files or databases

Modify backend state

Execute business rules

5.Renderer Directory Structure
renderer/
├── src/
│   ├── app/          # App bootstrap, layout, routing
│   ├── pages/        # Route-level screens
│   ├── components/   # Shared UI components
│   ├── state/        # Frontend UI state stores
│   ├── services/     # Frontend-side API adapters
│   └── styles/       # Styling resources
├── index.html
├── vite.config.ts
├── tsconfig.json
├── tsconfig.app.json
└── renderer.md

6.State Management Philosophy

The renderer uses explicit, deterministic UI state stores.

Design principles:

Single active run at a time

Run change triggers deterministic resets

No implicit state

No derived state without source

No backend coupling

State coordination is centralized using a run-change coordinator to prevent partial or inconsistent UI state.

7.Offline & Security Guarantees

The final desktop application:

Runs without internet access

Exposes no HTTP endpoints

Does not require Node.js

Loads UI only from local files

Keeps all data and logic inside the executable

This renderer is part of a true offline industrial system, not a web application.

8.Intended Audience

This document is intended for:

Project reviewers

Maintenance & operations stakeholders (technical)

Future developers

System auditors

It explains how the renderer works, why localhost appears during development, and why it does not exist in production.