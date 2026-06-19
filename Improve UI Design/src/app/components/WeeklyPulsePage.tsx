import { useState, useEffect } from "react";
import { CheckCircle, Calendar, TrendingUp, TrendingDown, Minus, AlertCircle } from "lucide-react";

interface WeeklyPulsePageProps {
  selectedWeek: string;
  weeks: string[];
  setSelectedWeek: (week: string) => void;
  loadingWeeks: boolean;
}

export function WeeklyPulsePage({ selectedWeek, weeks, setSelectedWeek, loadingWeeks }: WeeklyPulsePageProps) {
  const [pulseData, setPulseData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!selectedWeek) return;
    setLoading(true);
    setError(null);
    fetch(`/api/pulse/${selectedWeek}`)
      .then((res) => {
        if (!res.ok) throw new Error("No data found for this week.");
        return res.json();
      })
      .then((data) => {
        setPulseData(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setError(err.message);
        setLoading(false);
      });
  }, [selectedWeek]);

  if (loadingWeeks || (loading && !pulseData)) {
    return (
      <div className="flex flex-col items-center justify-center h-[500px] text-gray-500 font-medium">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-500 mb-4"></div>
        <span>Loading week review data...</span>
      </div>
    );
  }

  if (error || !pulseData) {
    return (
      <div className="flex flex-col items-center justify-center h-[500px] text-gray-500 p-8 text-center">
        <AlertCircle size={40} className="text-gray-400 mb-4" />
        <h3 className="text-lg font-semibold text-gray-700 mb-1">No Report Available</h3>
        <p className="text-sm text-gray-500 max-w-sm mb-4">
          {error || "We couldn't load the review insights for this week."}
        </p>
      </div>
    );
  }

  const { pulse, themes, quotes } = pulseData;
  const totalReviews = themes.reduce((sum: number, t: any) => sum + t.size, 0);

  const getWeekDateRange = (isoWeek: string) => {
    try {
      const parts = isoWeek.split("-W");
      if (parts.length !== 2) return isoWeek;
      const year = parseInt(parts[0]);
      const weekNum = parseInt(parts[1]);
      
      const jan4 = new Date(year, 0, 4);
      const day = jan4.getDay();
      const start = new Date(jan4.getTime() - ((day === 0 ? 6 : day - 1) * 24 * 3600 * 1000) + ((weekNum - 1) * 7 * 24 * 3600 * 1000));
      const end = new Date(start.getTime() + (6 * 24 * 3600 * 1000));
      
      const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
      return `${months[start.getMonth()]} ${start.getDate()} – ${months[end.getMonth()]} ${end.getDate()}, ${year}`;
    } catch (e) {
      return isoWeek;
    }
  };

  const dateRange = getWeekDateRange(selectedWeek);

  const sentimentData = [
    { label: "Negative", value: pulse.sentiment?.negative || 0, color: "#ef4444" },
    { label: "Neutral", value: pulse.sentiment?.neutral || 0, color: "#f59e0b" },
    { label: "Positive", value: pulse.sentiment?.positive || 0, color: "#00b386" },
  ];

  const themeClusters = themes.map((t: any) => ({
    name: t.label,
    count: t.size,
    delta: t.delta || 0,
    priority: t.priority || (t.size > 200 ? "high" : t.size > 100 ? "medium" : "low")
  }));

  const maxThemeCount = themeClusters.length > 0 ? Math.max(...themeClusters.map((c: any) => c.count)) : 1;

  // Keyword-based sentiment fallback (used when quotes data has no sentiment field)
  const inferSentiment = (text: string): "negative" | "positive" | "neutral" => {
    const t = text.toLowerCase();
    const neg = ["unable", "can't", "cannot", "disappoint", "frustrat", "horrible", "terrible",
      "worst", "bad", "not able", "problem", "issue", "glitch", "fail", "lost", "useless",
      "broken", "bug", "error", "crash", "hate", "scam", "cheat", "fraud", "quit", "discontinue",
      "stop using", "not good", "pathetic", "slow", "not working", "no support"
    ].filter(k => t.includes(k)).length;
    const pos = ["good", "great", "love", "excellent", "amazing", "best", "nice", "superb",
      "fantastic", "helpful", "perfect", "easy", "smooth", "happy", "wonderful"
    ].filter(k => t.includes(k)).length;
    if (neg > pos) return "negative";
    if (pos > neg) return "positive";
    return "neutral";
  };

  const feedback = quotes.map((q: any, idx: number) => {
    const names = ["Ankit R.", "Priya T.", "Rahul S.", "Amit K.", "Neha P."];
    const name = names[idx % names.length];
    const initials = name.split(" ").map((n: string) => n[0]).join("");
    // Use data sentiment field; fall back to keyword inference — never hardcode by index
    const sentiment: string = q.sentiment || inferSentiment(q.quote || "");
    const isCritical = sentiment === "negative";
    const isNeutral  = sentiment === "neutral";
    return {
      initials,
      name,
      tag:      isCritical ? "CRITICAL" : isNeutral ? "NEUTRAL" : "POSITIVE",
      tagColor: isCritical ? "#ef4444"  : isNeutral ? "#f59e0b" : "#00b386",
      tagBg:    isCritical ? "#fef2f2"  : isNeutral ? "#fffbeb" : "#f0faf6",
      text: q.quote
    };
  });

  const actions = (pulse.action_ideas || []).map((text: string, idx: number) => {
    const priorities = ["HIGH", "MED", "LOW"];
    const priority = priorities[idx % 3];
    const colors: any = {
      "HIGH": { color: "#ef4444", bg: "#fef2f2" },
      "MED": { color: "#f59e0b", bg: "#fffbeb" },
      "LOW": { color: "#6b7280", bg: "#f9fafb" }
    };
    return {
      text,
      priority,
      priorityColor: colors[priority].color,
      priorityBg: colors[priority].bg
    };
  });

  return (
    <div className="p-8 max-w-[1200px] mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-4">
          <div>
            <h1 style={{ fontSize: 22, fontWeight: 600, color: "#111827", letterSpacing: "-0.02em" }}>
              Weekly review — {selectedWeek}
            </h1>
            <div className="flex items-center gap-2 mt-1">
              <span
                className="flex items-center gap-1.5 rounded-full px-3 py-0.5"
                style={{ background: "#f0faf6", color: "#00b386", fontSize: 12, fontWeight: 500 }}
              >
                <CheckCircle size={12} /> Completed
              </span>
            </div>
          </div>
        </div>
        <div
          className="flex items-center gap-2 rounded-lg px-3 py-2"
          style={{ background: "#fff", border: "1px solid var(--border)", fontSize: 12.5, color: "#6b7280" }}
        >
          <Calendar size={13} />
          {dateRange}
        </div>
      </div>

      {/* Top stats row */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        {/* Total Reviews */}
        <div className="rounded-xl p-5" style={{ background: "#fff", border: "1px solid var(--border)", boxShadow: "0 1px 3px rgba(0,0,0,0.04)" }}>
          <div style={{ fontSize: 11, fontWeight: 600, color: "#9ca3af", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 10 }}>
            Total Reviews
          </div>
          <div style={{ fontSize: 42, fontWeight: 700, color: "#111827", letterSpacing: "-0.03em", lineHeight: 1 }}>
            {totalReviews}
          </div>
          <div className="flex items-center gap-1.5 mt-2" style={{ fontSize: 12, color: "#00b386" }}>
            <TrendingUp size={13} /> Analyzed this week
          </div>
        </div>

        {/* Sentiment Analysis */}
        <div className="rounded-xl p-5" style={{ background: "#fff", border: "1px solid var(--border)", boxShadow: "0 1px 3px rgba(0,0,0,0.04)" }}>
          <div style={{ fontSize: 11, fontWeight: 600, color: "#9ca3af", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 14 }}>
            Sentiment Analysis
          </div>
          <div className="flex items-end gap-4 mb-3">
            {sentimentData.map(s => (
              <div key={s.label}>
                <div style={{ fontSize: 20, fontWeight: 700, color: s.color, letterSpacing: "-0.02em" }}>{s.value}%</div>
                <div style={{ fontSize: 11, color: "#9ca3af", marginTop: 2 }}>{s.label.slice(0, 3).toUpperCase()}</div>
              </div>
            ))}
          </div>
          {/* Bar */}
          <div className="flex rounded-full overflow-hidden" style={{ height: 6 }}>
            {sentimentData.map(s => (
              <div key={s.label} style={{ width: `${s.value}%`, background: s.color }} />
            ))}
          </div>
        </div>

        {/* Processing Pipeline */}
        <div className="rounded-xl p-5" style={{ background: "#fff", border: "1px solid var(--border)", boxShadow: "0 1px 3px rgba(0,0,0,0.04)" }}>
          <div style={{ fontSize: 11, fontWeight: 600, color: "#9ca3af", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 10 }}>
            Processing Pipeline
          </div>
          <div style={{ fontSize: 42, fontWeight: 700, color: "#111827", letterSpacing: "-0.03em", lineHeight: 1 }}>{themeClusters.length}</div>
          <div style={{ fontSize: 12, color: "#6b7280", marginTop: 6 }}>Theme clusters identified</div>
          <div className="mt-3 flex items-center gap-1.5" style={{ fontSize: 11, color: "#00b386", fontWeight: 500 }}>
            <CheckCircle size={11} /> Pipeline complete
          </div>
        </div>
      </div>

      {/* Middle section: Summary + Clusters */}
      <div className="grid gap-4 mb-6" style={{ gridTemplateColumns: "1fr 360px" }}>
        {/* Weekly Pulse Summary */}
        <div className="rounded-xl p-6" style={{ background: "#fff", border: "1px solid var(--border)", boxShadow: "0 1px 3px rgba(0,0,0,0.04)" }}>
          <div className="flex items-center gap-2 mb-4">
            <div className="rounded" style={{ width: 4, height: 18, background: "var(--primary)" }} />
            <h3 style={{ fontSize: 14, fontWeight: 600, color: "#111827" }}>Weekly Pulse Summary</h3>
          </div>
          <p style={{ fontSize: 13.5, color: "#374151", lineHeight: 1.65 }}>
            {pulse.weekly_summary}
          </p>
          {actions.length > 0 && (
            <div
              className="mt-5 rounded-lg p-4"
              style={{ background: "#fffbeb", border: "1px solid #fde68a" }}
            >
              <div className="flex items-start gap-2">
                <AlertCircle size={14} style={{ color: "#d97706", marginTop: 1, shrink: 0 }} />
                <div>
                  <span style={{ fontSize: 12.5, fontWeight: 600, color: "#92400e" }}>Strategic Recommendation: </span>
                  <span style={{ fontSize: 12.5, color: "#78350f" }}>{actions[0].text}</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Theme Clusters */}
        <div className="rounded-xl p-6" style={{ background: "#fff", border: "1px solid var(--border)", boxShadow: "0 1px 3px rgba(0,0,0,0.04)" }}>
          <div className="flex items-center justify-between mb-4">
            <h3 style={{ fontSize: 14, fontWeight: 600, color: "#111827" }}>Theme Clusters</h3>
            <span
              className="rounded-full px-2.5 py-0.5"
              style={{ fontSize: 11, fontWeight: 600, background: "#f0f2f5", color: "#6b7280" }}
            >
              Top {themeClusters.length}
            </span>
          </div>
          <div className="flex flex-col gap-3">
            {themeClusters.map((c: any, i: number) => (
              <div key={c.name} className="flex items-center gap-3">
                <div
                  className="rounded flex items-center justify-center shrink-0"
                  style={{ width: 22, height: 22, background: "#f0f2f5", fontSize: 11, fontWeight: 600, color: "#6b7280" }}
                >
                  {i + 1}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1">
                    <span style={{ fontSize: 12.5, fontWeight: 500, color: "#374151", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }} title={c.name}>{c.name}</span>
                    <span style={{ fontSize: 12.5, fontWeight: 600, color: "#111827", fontVariantNumeric: "tabular-nums" }}>{c.count}</span>
                  </div>
                  <div className="rounded-full overflow-hidden" style={{ height: 4, background: "#f0f2f5" }}>
                    <div
                      className="rounded-full"
                      style={{
                        height: "100%",
                        width: `${(c.count / maxThemeCount) * 100}%`,
                        background: c.priority === "high" ? "#ef4444" : c.priority === "medium" ? "#00b386" : "#3b82f6",
                      }}
                    />
                  </div>
                </div>
                <div className="flex items-center gap-0.5" style={{ fontSize: 11, color: c.delta > 0 ? "#00b386" : c.delta < 0 ? "#ef4444" : "#6b7280", fontWeight: 500, minWidth: 36, justifyContent: "flex-end" }}>
                  {c.delta > 0 ? <TrendingUp size={11} /> : c.delta < 0 ? <TrendingDown size={11} /> : <Minus size={11} />}
                  {Math.abs(c.delta)}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Bottom: Feedback + Actions */}
      <div className="grid gap-4" style={{ gridTemplateColumns: "1fr 1fr" }}>
        {/* Representative Feedback */}
        <div className="rounded-xl p-6" style={{ background: "#fff", border: "1px solid var(--border)", boxShadow: "0 1px 3px rgba(0,0,0,0.04)" }}>
          <h3 style={{ fontSize: 14, fontWeight: 600, color: "#111827", marginBottom: 16 }}>Representative Feedback</h3>
          <div className="flex flex-col gap-4">
            {feedback.map((f: any, i: number) => (
              <div key={i} className="flex gap-3">
                <div
                  className="flex items-center justify-center rounded-full shrink-0"
                  style={{ width: 34, height: 34, background: "#f0f2f5", fontSize: 11.5, fontWeight: 700, color: "#374151" }}
                >
                  {f.initials}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span style={{ fontSize: 12.5, fontWeight: 600, color: "#111827" }}>{f.name}</span>
                    <span
                      className="rounded-full px-2 py-0.5"
                      style={{ fontSize: 10.5, fontWeight: 600, color: f.tagColor, background: f.tagBg }}
                    >
                      {f.tag}
                    </span>
                  </div>
                  <p style={{ fontSize: 12.5, color: "#6b7280", lineHeight: 1.55 }}>"{f.text}"</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Action Recommendations */}
        <div className="rounded-xl p-6" style={{ background: "#fff", border: "1px solid var(--border)", boxShadow: "0 1px 3px rgba(0,0,0,0.04)" }}>
          <div className="flex items-center justify-between mb-4">
            <h3 style={{ fontSize: 14, fontWeight: 600, color: "#111827" }}>Action Recommendations</h3>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr auto", gap: "6px 12px", alignItems: "center", marginBottom: 8 }}>
            <div style={{ fontSize: 11, fontWeight: 600, color: "#9ca3af", textTransform: "uppercase", letterSpacing: "0.06em" }}>Action Item</div>
            <div style={{ fontSize: 11, fontWeight: 600, color: "#9ca3af", textTransform: "uppercase", letterSpacing: "0.06em" }}>Priority</div>
          </div>
          <div className="flex flex-col gap-3">
            {actions.map((a: any, i: number) => (
              <div
                key={i}
                className="flex items-start gap-3 rounded-lg p-3 transition-colors"
                style={{ background: "#f9fafb", border: "1px solid var(--border)" }}
              >
                <p className="flex-1" style={{ fontSize: 12.5, color: "#374151", lineHeight: 1.55 }}>{a.text}</p>
                <span
                  className="rounded-full px-2.5 py-0.5 shrink-0"
                  style={{ fontSize: 10.5, fontWeight: 700, color: a.priorityColor, background: a.priorityBg, marginTop: 1 }}
                >
                  {a.priority}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
