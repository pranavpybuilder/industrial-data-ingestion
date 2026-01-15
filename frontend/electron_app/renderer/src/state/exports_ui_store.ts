/**
 * Exports UI Store (Internal)
 *
 * Tracks available exported reports.
 */

export interface ExportsUIState {
  totalReports: number;
}

class ExportsUIStore {
  private state: ExportsUIState = {
    totalReports: 0,
  };

  getState(): ExportsUIState {
    return { ...this.state };
  }

  setTotalReports(count: number): void {
    this.state.totalReports = count;
  }

  reset(): void {
    this.state.totalReports = 0;
  }
}

const exportsUIStore = new ExportsUIStore();

/**
 * Public interface for exports UI state.
 */
export const exportsUI = {
  getState: (): ExportsUIState => exportsUIStore.getState(),
  setTotalReports: (count: number): void =>
    exportsUIStore.setTotalReports(count),
  reset: (): void => exportsUIStore.reset(),
};