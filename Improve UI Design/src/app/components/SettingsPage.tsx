import { useState } from "react";
import { Play, Zap, Clock, Globe, CheckCircle, AlertCircle, ChevronRight } from "lucide-react";

const pipelineSteps = [
  "Fetch & clean latest Play Store reviews",
  "Generate embeddings and cluster into themes",
  "Create weekly pulse summary via Groq LLM",
  "Generate fee explainer",
  "Append to Google Doc and create Gmail draft",
];

export function SettingsPage() {
  const [running, setRunning] = useState(false);
  const [serviceStatus, setServiceStatus] = useState<"online" | "offline">("offline");

  const handleRun = () => {
    setRunning(true);
    setTimeout(() => setRunning(false), 3000);
  };

  return (
    <div className="p-8 max-w-[760px] mx-auto">
      <div className="mb-8">
        <h1 style={{ fontSize: 22, fontWeight: 600, color: "#111827", letterSpacing: "-0.02em" }}>Settings</h1>
        <p style={{ fontSize: 13, color: "#6b7280", marginTop: 4 }}>
          Configure pipeline settings, notification preferences, and dashboard options.
        </p>
      </div>

      <div className="flex flex-col gap-5">
        {/* Pipeline Trigger */}
        <div className="rounded-xl overflow-hidden" style={{ background: "#fff", border: "1px solid var(--border)", boxShadow: "0 1px 3px rgba(0,0,0,0.04)" }}>
          <div className="px-6 py-5" style={{ borderBottom: "1px solid var(--border)" }}>
            <div className="flex items-center gap-3">
              <div
                className="flex items-center justify-center rounded-xl"
                style={{ width: 40, height: 40, background: "#f0faf6" }}
              >
                <Zap size={18} style={{ color: "#00b386" }} />
              </div>
              <div>
                <h2 style={{ fontSize: 15, fontWeight: 600, color: "#111827" }}>Pipeline Trigger</h2>
                <p style={{ fontSize: 12.5, color: "#6b7280", marginTop: 1 }}>
                  Manually trigger a full pipeline run in the background.
                </p>
              </div>
            </div>
          </div>

          <div className="px-6 py-4" style={{ borderBottom: "1px solid var(--border)" }}>
            <div style={{ fontSize: 11.5, fontWeight: 600, color: "#9ca3af", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 10 }}>
              Pipeline Steps
            </div>
            <div className="flex flex-col gap-2">
              {pipelineSteps.map((step, i) => (
                <div key={i} className="flex items-center gap-3">
                  <div
                    className="flex items-center justify-center rounded-full shrink-0"
                    style={{ width: 20, height: 20, background: running && i < 2 ? "#f0faf6" : "#f0f2f5", fontSize: 10.5, fontWeight: 700, color: running && i < 2 ? "#00b386" : "#9ca3af" }}
                  >
                    {running && i < 2 ? <CheckCircle size={11} style={{ color: "#00b386" }} /> : i + 1}
                  </div>
                  <span style={{ fontSize: 13, color: "#374151" }}>{step}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="px-6 py-4 flex items-center gap-3">
            <button
              onClick={handleRun}
              disabled={running}
              className="flex items-center gap-2 rounded-lg px-4 py-2.5 transition-all cursor-pointer"
              style={{
                background: running ? "#f0f2f5" : "var(--primary)",
                color: running ? "#9ca3af" : "#fff",
                fontSize: 13,
                fontWeight: 500,
                border: "none",
                outline: "none",
                cursor: running ? "not-allowed" : "pointer",
              }}
            >
              <Play size={13} fill="currentColor" />
              {running ? "Running…" : "Run Pipeline Now"}
            </button>
            <div
              className="flex items-center gap-2 rounded-lg px-3 py-2"
              style={{
                background: serviceStatus === "offline" ? "#fef2f2" : "#f0faf6",
                border: `1px solid ${serviceStatus === "offline" ? "#fecaca" : "#bbf7d0"}`,
                fontSize: 12,
                fontWeight: 500,
                color: serviceStatus === "offline" ? "#ef4444" : "#00b386",
              }}
            >
              {serviceStatus === "offline"
                ? <><AlertCircle size={12} /> Trigger service offline (port 8050)</>
                : <><CheckCircle size={12} /> Service online</>}
            </div>
          </div>
        </div>

        {/* Scheduler Configuration */}
        <div className="rounded-xl overflow-hidden" style={{ background: "#fff", border: "1px solid var(--border)", boxShadow: "0 1px 3px rgba(0,0,0,0.04)" }}>
          <div className="px-6 py-5" style={{ borderBottom: "1px solid var(--border)" }}>
            <div className="flex items-center gap-3">
              <div
                className="flex items-center justify-center rounded-xl"
                style={{ width: 40, height: 40, background: "#eff6ff" }}
              >
                <Clock size={18} style={{ color: "#3b82f6" }} />
              </div>
              <div>
                <h2 style={{ fontSize: 15, fontWeight: 600, color: "#111827" }}>Scheduler Configuration</h2>
                <p style={{ fontSize: 12.5, color: "#6b7280", marginTop: 1 }}>
                  Automated run schedule and approval settings.
                </p>
              </div>
            </div>
          </div>

          <div className="px-6 py-5 grid gap-4" style={{ gridTemplateColumns: "1fr 1fr 1fr" }}>
            {[
              { label: "Schedule", value: "Every Monday at 08:00 IST", icon: <Clock size={13} style={{ color: "#3b82f6" }} /> },
              { label: "Timezone", value: "Asia/Kolkata", icon: <Globe size={13} style={{ color: "#6b7280" }} /> },
              { label: "Approval Dates", value: "Auto-approved (headless mode)", icon: <CheckCircle size={13} style={{ color: "#00b386" }} /> },
            ].map(item => (
              <div
                key={item.label}
                className="rounded-lg p-4"
                style={{ background: "#f9fafb", border: "1px solid var(--border)" }}
              >
                <div className="flex items-center gap-1.5 mb-2">
                  {item.icon}
                  <span style={{ fontSize: 11, fontWeight: 600, color: "#9ca3af", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                    {item.label}
                  </span>
                </div>
                <div style={{ fontSize: 13, fontWeight: 600, color: "#111827", lineHeight: 1.4 }}>
                  {item.value}
                </div>
              </div>
            ))}
          </div>

          <div className="px-6 pb-5">
            <button
              className="flex items-center gap-2 rounded-lg px-4 py-2.5 transition-colors cursor-pointer"
              style={{ background: "#f9fafb", border: "1px solid var(--border)", fontSize: 13, fontWeight: 500, color: "#374151", outline: "none" }}
            >
              Edit Schedule <ChevronRight size={13} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
