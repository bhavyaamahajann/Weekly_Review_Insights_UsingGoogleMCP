import { useState, useEffect } from "react";
import { Cloud, Clock, CheckCircle, AlertCircle } from "lucide-react";

interface Run {
  id: string;
  week: string;
  status: "success" | "failed" | "running";
  reviews: number;
  clusters: number;
  duration: string;
  time: string;
}

export function RunHistoryPage() {
  const [runs, setRuns] = useState<Run[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/history")
      .then((res) => res.json())
      .then((data) => {
        if (Array.isArray(data)) {
          setRuns(data);
        }
        setLoading(false);
      })
      .catch((err) => {
        console.error("Failed to fetch run history:", err);
        setLoading(false);
      });
  }, []);

  const hasRuns = runs.length > 0;

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-[500px] text-gray-500 font-medium">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-500 mb-4"></div>
        <span>Loading run history...</span>
      </div>
    );
  }

  const formatTimestamp = (ts: string) => {
    try {
      const d = new Date(ts);
      return d.toLocaleString("en-US", {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
        hour12: true
      });
    } catch (e) {
      return ts;
    }
  };

  return (
    <div className="p-8 max-w-[960px] mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 style={{ fontSize: 22, fontWeight: 600, color: "#111827", letterSpacing: "-0.02em" }}>
          Run History & Audits
        </h1>
        <p style={{ fontSize: 13, color: "#6b7280", marginTop: 4 }}>
          Review the historical performance and audit logs of automated pulse runs.
        </p>
      </div>

      {/* Run list / table */}
      <div
        className="rounded-xl mb-5"
        style={{ background: "#fff", border: "1px solid var(--border)", boxShadow: "0 1px 3px rgba(0,0,0,0.04)", overflow: "hidden" }}
      >
        {hasRuns ? (
          <div className="overflow-x-auto">
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ borderBottom: "1px solid var(--border)", background: "#f9fafb" }}>
                  {["Week", "Status", "Reviews", "Clusters", "Duration", "Run Time"].map(h => (
                    <th
                      key={h}
                      style={{ padding: "12px 16px", fontSize: 11, fontWeight: 600, color: "#9ca3af", textTransform: "uppercase", letterSpacing: "0.06em", textAlign: "left" }}
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {runs.map(r => (
                  <tr key={r.id} style={{ borderBottom: "1px solid var(--border)" }} className="hover:bg-slate-50 transition-colors">
                    <td style={{ padding: "14px 16px", fontSize: 13.5, fontWeight: 500, color: "#111827" }}>{r.week}</td>
                    <td style={{ padding: "14px 16px" }}>
                      <span
                        className="flex items-center gap-1.5 rounded-full px-2.5 py-0.5"
                        style={{
                          fontSize: 11.5,
                          fontWeight: 600,
                          display: "inline-flex",
                          color: r.status === "success" ? "#00b386" : r.status === "failed" ? "#ef4444" : "#f59e0b",
                          background: r.status === "success" ? "#f0faf6" : r.status === "failed" ? "#fef2f2" : "#fffbeb",
                        }}
                      >
                        {r.status === "success" ? <CheckCircle size={11} /> : r.status === "failed" ? <AlertCircle size={11} /> : <Clock size={11} />}
                        {r.status.charAt(0).toUpperCase() + r.status.slice(1)}
                      </span>
                    </td>
                    <td style={{ padding: "14px 16px", fontSize: 13, color: "#374151" }}>{r.reviews}</td>
                    <td style={{ padding: "14px 16px", fontSize: 13, color: "#374151" }}>{r.clusters}</td>
                    <td style={{ padding: "14px 16px", fontSize: 13, color: "#6b7280" }}>{r.duration}</td>
                    <td style={{ padding: "14px 16px", fontSize: 12.5, color: "#9ca3af" }}>{formatTimestamp(r.time)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-16 px-8">
            <div
              className="flex items-center justify-center rounded-full mb-4"
              style={{ width: 56, height: 56, background: "#f0f2f5" }}
            >
              <Clock size={24} style={{ color: "#9ca3af" }} />
            </div>
            <h3 style={{ fontSize: 15, fontWeight: 600, color: "#111827", marginBottom: 6 }}>No Run History</h3>
            <p style={{ fontSize: 13, color: "#9ca3af", textAlign: "center", maxWidth: 300 }}>
              Audit logs are empty. Run the weekly review pulse pipeline to generate reports.
            </p>
          </div>
        )}
      </div>

      {/* Feature cards */}
      <div className="grid grid-cols-2 gap-4">
        <div className="rounded-xl p-6" style={{ background: "#fff", border: "1px solid var(--border)", boxShadow: "0 1px 3px rgba(0,0,0,0.04)" }}>
          <div
            className="flex items-center justify-center rounded-xl mb-4"
            style={{ width: 44, height: 44, background: "#eff6ff" }}
          >
            <Cloud size={20} style={{ color: "#3b82f6" }} />
          </div>
          <h3 style={{ fontSize: 14, fontWeight: 600, color: "#111827", marginBottom: 6 }}>Cloud Automation</h3>
          <p style={{ fontSize: 13, color: "#6b7280", lineHeight: 1.6 }}>
            Every run is backed up to secure Google Doc summaries and triggers draft emails to product teams automatically.
          </p>
        </div>

        <div className="rounded-xl p-6" style={{ background: "#fff", border: "1px solid var(--border)", boxShadow: "0 1px 3px rgba(0,0,0,0.04)" }}>
          <div
            className="flex items-center justify-center rounded-xl mb-4"
            style={{ width: 44, height: 44, background: "#f0faf6" }}
          >
            <CheckCircle size={20} style={{ color: "#00b386" }} />
          </div>
          <h3 style={{ fontSize: 14, fontWeight: 600, color: "#111827", marginBottom: 6 }}>Compliance Auditing</h3>
          <p style={{ fontSize: 13, color: "#6b7280", lineHeight: 1.6 }}>
            All operations are approval-gated and logged for strict data safety, PII scrubbing, and transparent quality control.
          </p>
        </div>
      </div>
    </div>
  );
}
