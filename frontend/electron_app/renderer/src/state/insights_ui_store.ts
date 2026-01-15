/**
 * Insights UI Store (Internal)
 *
 * Tracks insight loading state for the active run.
 */

export interface InsightsUIState {
  isLoaded: boolean;
  hasData: boolean;
}

class InsightsUIStore {
  private state: InsightsUIState = {
    isLoaded: false,
    hasData: false,
  };

  getState(): InsightsUIState {
    return { ...this.state };
  }

  markLoaded(hasData: boolean): void {
    this.state.isLoaded = true;
    this.state.hasData = hasData;
  }

  reset(): void {
    this.state.isLoaded = false;
    this.state.hasData = false;
  }
}

const insightsUIStore = new InsightsUIStore();

/**
 * Public interface for insights UI state.
 */
export const insightsUI = {
  getState: (): InsightsUIState => insightsUIStore.getState(),
  markLoaded: (hasData: boolean): void =>
    insightsUIStore.markLoaded(hasData),
  reset: (): void => insightsUIStore.reset(),
};
