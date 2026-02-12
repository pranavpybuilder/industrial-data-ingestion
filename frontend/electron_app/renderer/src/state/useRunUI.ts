import { useSyncExternalStore } from "react";
import { runUI } from "./run_ui_store";

export const useRunUI = () =>
  useSyncExternalStore(runUI.subscribe, runUI.getSnapshot);