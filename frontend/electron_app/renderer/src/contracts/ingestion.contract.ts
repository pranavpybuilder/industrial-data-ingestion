export type IngestionType =
  | "SAP_PM"
  | "RFID"
  | "PLC"
  | "ENERGY";

export interface IngestionRequest {
  ingestionType: IngestionType;
  metadata: Record<string, string>;
  file: File;
}

export interface IngestionResult {
  success: boolean;
  runId?: string;
  message: string;
}