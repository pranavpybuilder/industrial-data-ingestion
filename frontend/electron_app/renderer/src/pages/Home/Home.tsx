import { Metrics } from "../../components/Metrics/Metrics";

export default function Home() {
  return (
    <div style={{ maxWidth: 900 }}>
      <h1>System Overview</h1>

      <p style={{ marginTop: 8, color: "#6b7280" }}>
        High-level view of the system state and generated outputs.
      </p>

      <Metrics />
    </div>
  );
}