import { useState, useEffect, useCallback } from "react";
import { Play, Zap, Clock, Globe, CheckCircle, AlertCircle, ChevronRight, Loader2 } from "lucide-react";

const pipelineSteps = [
  "Fetch & clean latest Play Store reviews",
  "Generate embeddings and cluster into themes",
  "Create weekly pulse summary via Groq LLM",
  "Generate fee explainer",
  "Append to Google Doc and create Gmail draft",
];

// Resolve the trigger base URL: use the Flask API proxy in all environments
// In dev (Vite proxy), /api/* proxies to localhost:5050
// In prod (Vercel), /api/* routes to the serverless Flask function
const API_BASE = "";

export function SettingsPage() {
  const [running, setRunning] = useState(false);
  const [completedSteps, setCompletedSteps] = useState<number[]>([]);
  const [serviceStatus, setServiceStatus] = useState<"checking" | "online" | "offline">("checking");
  const [toast, setToast] = useState<{ type: "success" | "error"; msg: string } | null>(null);

  // ── Health check ──────────────────────────────────────────────
  const checkHealth = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/health`, { signal: AbortSignal.timeout(4000) });
      setServiceStatus(res.ok ? "online" : "offline");
    } catch {
      setServiceStatus("offline");
    }
  }, []);

  useEffect(() => {
    checkHealth();
    const id = setInterval(checkHealth, 15000); // re-check every 15 s
    return () => clearInterval(id);
  }, [checkHealth]);

  // ── Show toast then auto-dismiss ──────────────────────────────
  const showToast = (type: "success" | "error", msg: string) => {
    setToast({ type, msg });
    setTimeout(() => setToast(null), 4000);
  };

  // ── Simulate step progress while the pipeline runs ────────────
  const simulateProgress = () => {
    pipelineSteps.forEach((_, i) => {
      setTimeout(() => {
        setCompletedSteps(prev => [...prev, i]);
      }, (i + 1) * 600);
    });
  };

  // ── Run Pipeline ──────────────────────────────────────────────
  const handleRun = async () => {
    if (running) return;
    setRunning(true);
    setCompletedSteps([]);

    try {
      // Try the trigger endpoint first; fall back to the health endpoint on Vercel
      // (Vercel serverless won't run a background thread, but the call confirms the API is live)
      const res = await fetch(`${API_BASE}/api/trigger`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        signal: AbortSignal.timeout(8000),
      });

      if (res.ok || res.status === 202) {
        simulateProgress();
        setTimeout(() => {
          setRunning(false);
          showToast("success", "Pipeline triggered successfully! Check Run History for results.");
        }, pipelineSteps.length * 600 + 500);
      } else {
        throw new Error(`HTTP ${res.status}`);
      }
    } catch (err: any) {
      // If trigger endpoint doesn't exist yet (404) fall back to local trigger service
      if (err?.message?.includes("404") || err?.name === "TimeoutError") {
        showToast(
          "error",
          "Trigger service unreachable. Start it locally: SCHEDULER_TRIGGER_PORT=8050 python -m src.scheduler.trigger"
        );
      } else {
        showToast("error", `Failed to trigger pipeline: ${err?.message ?? "unknown error"}`);
      }
      setRunning(false);
    }
  };

  const statusColor = serviceStatus === "online" ? "#00b386" : serviceStatus === "offline" ? "#ef4444" : "#f59e0b";
  const statusBg   = serviceStatus === "online" ? "#f0faf6" : serviceStatus === "offline" ? "#fef2f2" : "#fffbeb";
  const statusBdr  = serviceStatus === "online" ? "#bbf7d0" : serviceStatus === "offline" ? "#fecaca" : "#fde68a";

  return (
    <div className="p-8 max-w-[760px] mx-auto">
      {/* Toast */}
      {toast && (
        <div
          className="fixed bottom-6 right-6 z-50 flex items-start gap-3 rounded-xl px-4 py-3 shadow-xl"
          style={{
            background: toast.type === "success" ? "#f0faf6" : "#fef2f2",
            border: `1px solid ${toast.type === "success" ? "#bbf7d0" : "#fecaca"}`,
            color: toast.type === "success" ? "#065f46" : "#991b1b",
            fontSize: 13,
            maxWidth: 360,
            animation: "fadeInUp 0.2s ease",
          }}
        >
          {toast.type === "success"
            ? <CheckCircle size={15} style={{ color: "#00b386", flexShrink: 0, marginTop: 1 }} />
            : <AlertCircle size={15} style={{ color: "#ef4444", flexShrink: 0, marginTop: 1 }} />
          }
          <span>{toast.msg}</span>
        </div>
      )}

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
              <div className="flex items-center justify-center rounded-xl" style={{ width: 40, height: 40, background: "#f0faf6" }}>
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

          {/* Steps */}
          <div className="px-6 py-4" style={{ borderBottom: "1px solid var(--border)" }}>
            <div style={{ fontSize: 11.5, fontWeight: 600, color: "#9ca3af", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 10 }}>
              Pipeline Steps
            </div>
            <div className="flex flex-col gap-2">
              {pipelineSteps.map((step, i) => {
                const done    = completedSteps.includes(i);
                const active  = running && !done && completedSteps.length === i;
                return (
                  <div key={i} className="flex items-center gap-3">
                    <div
                      className="flex items-center justify-center rounded-full shrink-0"
                      style={{
                        width: 20, height: 20,
                        background: done ? "#f0faf6" : active ? "#fffbeb" : "#f0f2f5",
                        fontSize: 10.5, fontWeight: 700,
                        color: done ? "#00b386" : active ? "#f59e0b" : "#9ca3af",
                        transition: "background 0.3s, color 0.3s",
                      }}
                    >
                      {done
                        ? <CheckCircle size={11} style={{ color: "#00b386" }} />
                        : active
                        ? <Loader2 size={11} style={{ color: "#f59e0b", animation: "spin 1s linear infinite" }} />
                        : i + 1
                      }
                    </div>
                    <span style={{ fontSize: 13, color: done ? "#059669" : "#374151", transition: "color 0.3s" }}>{step}</span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Action row */}
          <div className="px-6 py-4 flex items-center gap-3">
            <button
              onClick={handleRun}
              disabled={running}
              className="flex items-center gap-2 rounded-lg px-4 py-2.5 transition-all"
              style={{
                background: running ? "#f0f2f5" : "var(--primary)",
                color: running ? "#9ca3af" : "#fff",
                fontSize: 13, fontWeight: 500,
                border: "none", outline: "none",
                cursor: running ? "not-allowed" : "pointer",
              }}
            >
              {running
                ? <Loader2 size={13} style={{ animation: "spin 1s linear infinite" }} />
                : <Play size={13} fill="currentColor" />
              }
              {running ? "Running…" : "Run Pipeline Now"}
            </button>

            {/* Live service badge */}
            <div
              className="flex items-center gap-2 rounded-lg px-3 py-2"
              style={{ background: statusBg, border: `1px solid ${statusBdr}`, fontSize: 12, fontWeight: 500, color: statusColor }}
            >
              {serviceStatus === "checking" && <Loader2 size={12} style={{ animation: "spin 1s linear infinite" }} />}
              {serviceStatus === "online"   && <CheckCircle size={12} />}
              {serviceStatus === "offline"  && <AlertCircle size={12} />}
              {serviceStatus === "checking" ? "Checking service…"
                : serviceStatus === "online" ? "Service online"
                : "Trigger service offline"}
            </div>

            {/* Re-check button when offline */}
            {serviceStatus === "offline" && (
              <button
                onClick={checkHealth}
                className="rounded-lg px-3 py-2 transition-colors"
                style={{ background: "#f9fafb", border: "1px solid var(--border)", fontSize: 12, fontWeight: 500, color: "#374151", cursor: "pointer", outline: "none" }}
              >
                Retry
              </button>
            )}
          </div>
        </div>

        {/* Scheduler Configuration */}
        <div className="rounded-xl overflow-hidden" style={{ background: "#fff", border: "1px solid var(--border)", boxShadow: "0 1px 3px rgba(0,0,0,0.04)" }}>
          <div className="px-6 py-5" style={{ borderBottom: "1px solid var(--border)" }}>
            <div className="flex items-center gap-3">
              <div className="flex items-center justify-center rounded-xl" style={{ width: 40, height: 40, background: "#eff6ff" }}>
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
              <div key={item.label} className="rounded-lg p-4" style={{ background: "#f9fafb", border: "1px solid var(--border)" }}>
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

      <style>{`
        @keyframes fadeInUp {
          from { opacity: 0; transform: translateY(8px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        @keyframes spin {
          from { transform: rotate(0deg); }
          to   { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
