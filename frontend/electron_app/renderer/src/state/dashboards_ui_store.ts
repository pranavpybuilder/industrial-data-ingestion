/**
 * Dashboards UI Store (Internal)
 *
 * Tracks dashboard availability for the active run.
 */

export interface DashboardsUIState {
  isLoaded: boolean;
  dashboardCount: number;
}

class DashboardsUIStore {
  private state: DashboardsUIState = {
    isLoaded: false,
    dashboardCount: 0,
  };

  getState(): DashboardsUIState {
    return { ...this.state };
  }

  markLoaded(dashboardCount: number): void {
    this.state.isLoaded = true;
    this.state.dashboardCount = dashboardCount;
  }

  reset(): void {
    this.state.isLoaded = false;
    this.state.dashboardCount = 0;
  }
}

const dashboardsUIStore = new DashboardsUIStore();

/**
 * Public interface for dashboards UI state.
 */
export const dashboardsUI = {
  getState: (): DashboardsUIState => dashboardsUIStore.getState(),
  markLoaded: (count: number): void =>
    dashboardsUIStore.markLoaded(count),
  reset: (): void => dashboardsUIStore.reset(),
};