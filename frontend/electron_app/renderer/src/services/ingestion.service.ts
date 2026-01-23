import { IngestionRequest, IngestionResult } from "../contracts/ingestion.contract";

/**
 * MOCK OFFLINE INGESTION SERVICE
 * (Later replaced with IPC / backend call)
 */
export async function ingestData(
  payload: IngestionRequest
): Promise<IngestionResult> {
  console.log("Ingestion payload:", payload);

  // simulate processing delay
  await new Promise((r) => setTimeout(r, 800));

  return {
    success: true,
    runId: `${payload.ingestionType}_${Date.now()}`,
    message: "Ingestion successful",
  };
}