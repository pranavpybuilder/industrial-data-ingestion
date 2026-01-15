// src/state/state_reset.ts
import { runUI } from "./run_ui_store";

/**
 * Imperative coordinator.
 * Must be called ONLY from UI events.
 */
export const onRunChange = (runId: string) => {
  if (!runId) {
    runUI.clearRun();
  } else {
    runUI.setActiveRun(runId);
  }
};