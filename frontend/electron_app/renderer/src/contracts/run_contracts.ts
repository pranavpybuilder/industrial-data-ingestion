/**
 * RunStatus
 *
 * Represents the lifecycle state of an ingestion run.
 * This enum mirrors backend-defined semantics.
 */
export type RunStatus =
  | "SUCCESS"
  | "FAILED"
  | "PARTIAL";

/**
 * RunSourceType
 *
 * Indicates the primary data source for the ingestion run.
 */
export type RunSourceType =
  | "SAP"
  | "RFID"
  | "PLC"
  | "REPORT_EXCEL"
  | "OPERATIONAL_EXCEL";

/**
 * IngestionRunContract
 *
 * Read-only contract representing a single ingestion run.
 * This interface must stay aligned with backend metadata.
 */
export interface IngestionRunContract {
  readonly run_id: string;
  readonly source_type: RunSourceType;
  readonly ingested_at: string; // ISO 8601 timestamp
  readonly status: RunStatus;
}