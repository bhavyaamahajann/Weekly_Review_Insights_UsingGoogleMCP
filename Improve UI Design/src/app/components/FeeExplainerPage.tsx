import { useState, useEffect } from "react";
import { ExternalLink, AlertTriangle, BookOpen, AlertCircle } from "lucide-react";

interface FeeExplainerPageProps {
  selectedWeek: string;
  loadingWeeks: boolean;
}

export function FeeExplainerPage({ selectedWeek, loadingWeeks }: FeeExplainerPageProps) {
  const [feeData, setFeeData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!selectedWeek) return;
    setLoading(true);
    setError(null);
    fetch(`/api/fee/${selectedWeek}`)
      .then((res) => {
        if (!res.ok) throw new Error("No fee explanation found for this week.");
        return res.json();
      })
      .then((data) => {
        setFeeData(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setError(err.message);
        setLoading(false);
      });
  }, [selectedWeek]);

  if (loadingWeeks || (loading && !feeData)) {
    return (
      <div className="flex flex-col items-center justify-center h-[500px] text-gray-500 font-medium">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-500 mb-4"></div>
        <span>Loading fee explanation...</span>
      </div>
    );
  }

  if (error || !feeData) {
    return (
      <div className="flex flex-col items-center justify-center h-[500px] text-gray-500 p-8 text-center">
        <AlertCircle size={40} className="text-gray-400 mb-4" />
        <h3 className="text-lg font-semibold text-gray-700 mb-1">No Fee Explainer Available</h3>
        <p className="text-sm text-gray-500 max-w-sm mb-4">
          {error || "We couldn't load the fee explanation for this week."}
        </p>
      </div>
    );
  }

  const { scenario, bullets, sources, last_checked } = feeData;

  return (
    <div className="p-8 max-w-[960px] mx-auto">
      {/* Header */}
      <div className="flex items-start justify-between mb-2">
        <div>
          <div className="flex items-center gap-3">
            <h1 style={{ fontSize: 22, fontWeight: 600, color: "#111827", letterSpacing: "-0.02em" }}>
              {scenario}
            </h1>
            <span
              className="rounded-full px-3 py-0.5"
              style={{ fontSize: 11.5, fontWeight: 600, background: "#fff7ed", color: "#c2410c", border: "1px solid #fed7aa" }}
            >
              Last checked: {last_checked}
            </span>
          </div>
          <p style={{ fontSize: 13, color: "#6b7280", marginTop: 6 }}>
            Generated for week {selectedWeek} — Factual, neutral fee explanation for Groww users
          </p>
        </div>
      </div>

      <div className="grid gap-4 mt-6" style={{ gridTemplateColumns: "1fr 280px" }}>
        {/* Key Facts */}
        <div className="rounded-xl p-6" style={{ background: "#fff", border: "1px solid var(--border)", boxShadow: "0 1px 3px rgba(0,0,0,0.04)" }}>
          <div className="flex items-center gap-2 mb-5">
            <BookOpen size={16} style={{ color: "#00b386" }} />
            <h2 style={{ fontSize: 15, fontWeight: 600, color: "#111827" }}>Key Facts</h2>
          </div>
          <div className="flex flex-col gap-3">
            {bullets.map((fact: string, i: number) => (
              <div
                key={i}
                className="flex gap-4 rounded-lg p-4 transition-colors"
                style={{ background: "#f9fafb", border: "1px solid var(--border)" }}
              >
                <div
                  className="flex items-center justify-center rounded-full shrink-0"
                  style={{ width: 26, height: 26, background: "#f0faf6", fontSize: 12, fontWeight: 700, color: "#00b386", marginTop: 1 }}
                >
                  {i + 1}
                </div>
                <p style={{ fontSize: 13.5, color: "#374151", lineHeight: 1.6 }}>{fact}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Right column */}
        <div className="flex flex-col gap-4">
          {/* Official Sources */}
          <div className="rounded-xl p-5" style={{ background: "#fff", border: "1px solid var(--border)", boxShadow: "0 1px 3px rgba(0,0,0,0.04)" }}>
            <div className="flex items-center gap-2 mb-4">
              <div
                className="rounded-lg flex items-center justify-center"
                style={{ width: 28, height: 28, background: "#f0faf6" }}
              >
                <ExternalLink size={13} style={{ color: "#00b386" }} />
              </div>
              <h3 style={{ fontSize: 13.5, fontWeight: 600, color: "#111827" }}>Official Sources</h3>
            </div>
            <div className="flex flex-col gap-2">
              {sources.map((s: string | { name: string; url: string }, i: number) => {
                const name = typeof s === "string" ? s : s.name;
                const url = typeof s === "string" ? null : s.url;
                return (
                  <a
                    key={i}
                    href={url ?? "#"}
                    target={url ? "_blank" : undefined}
                    rel={url ? "noopener noreferrer" : undefined}
                    className="flex items-center gap-2 rounded-lg px-3 py-2.5 group"
                    style={{
                      background: "#f9fafb",
                      border: "1px solid var(--border)",
                      textDecoration: "none",
                      cursor: url ? "pointer" : "default",
                      transition: "background 0.15s, border-color 0.15s, box-shadow 0.15s",
                    }}
                    onMouseEnter={(e) => {
                      if (!url) return;
                      const el = e.currentTarget as HTMLAnchorElement;
                      el.style.background = "#f0faf6";
                      el.style.borderColor = "#6ee7c7";
                      el.style.boxShadow = "0 2px 8px rgba(0,179,134,0.10)";
                    }}
                    onMouseLeave={(e) => {
                      const el = e.currentTarget as HTMLAnchorElement;
                      el.style.background = "#f9fafb";
                      el.style.borderColor = "var(--border)";
                      el.style.boxShadow = "none";
                    }}
                  >
                    <div className="rounded-full shrink-0" style={{ width: 6, height: 6, background: "#00b386" }} />
                    <span style={{ fontSize: 12.5, color: "#00b386", fontWeight: 500, flex: 1 }}>{name}</span>
                    <ExternalLink
                      size={10}
                      style={{ color: url ? "#00b386" : "#9ca3af", opacity: url ? 0.7 : 0.4, flexShrink: 0 }}
                    />
                  </a>
                );
              })}
            </div>
          </div>

          {/* Disclaimer */}
          <div className="rounded-xl p-5" style={{ background: "#fffbeb", border: "1px solid #fde68a" }}>
            <div className="flex items-center gap-2 mb-3">
              <AlertTriangle size={14} style={{ color: "#d97706" }} />
              <h3 style={{ fontSize: 13, fontWeight: 600, color: "#92400e" }}>Disclaimer</h3>
            </div>
            <p style={{ fontSize: 12, color: "#78350f", lineHeight: 1.6 }}>
              This explanation is provided for general informational purposes only and does not constitute financial or legal advice. Fees and charges are subject to regulatory updates and fund house terms.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
