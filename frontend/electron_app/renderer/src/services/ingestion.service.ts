import { IngestionRequest, IngestionResult } from "../contracts/ingestion.contract";
import { frontendApi } from "./frontendApi";

export async function ingestData(
  payload: IngestionRequest
): Promise<IngestionResult> {
  const filePath = (payload.file as any)?.path || "";
  if (!filePath) {
    return {
      success: false,
      message: "Desktop ingestion requires an absolute local file path.",
    };
  }

  const sourceMap: Record<string, string> = {
    SAP_PM: "sap",
    RFID: "rfid",
    PLC: "plc",
    ENERGY: "generic_tabular",
  };
  const sourceType = sourceMap[payload.ingestionType] || "generic_tabular";

  const response = await frontendApi.uploadFile(filePath, sourceType);
  if (!response.success) {
    return {
      success: false,
      message: response.message || "Ingestion failed",
    };
  }

  return {
    success: true,
    runId: response.data?.run_id,
    message: response.message || "Ingestion successful",
  };
}
