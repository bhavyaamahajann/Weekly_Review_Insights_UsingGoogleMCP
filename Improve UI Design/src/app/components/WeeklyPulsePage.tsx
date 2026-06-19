import { useState, useEffect } from "react";
import { CheckCircle, Calendar, TrendingUp, TrendingDown, Minus, AlertCircle, Star, BarChart2, Zap } from "lucide-react";

interface WeeklyPulsePageProps {
  selectedWeek: string;
  weeks: string[];
  setSelectedWeek: (week: string) => void;
  loadingWeeks: boolean;
}

export function WeeklyPulsePage({ selectedWeek, weeks, setSelectedWeek, loadingWeeks }: WeeklyPulsePageProps) {
  const [pulseData, setPulseData] = useState<any>(null);
  const [feeData, setFeeData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [trendData, setTrendData] = useState<any[]>([]);
  const [hoveredPoint, setHoveredPoint] = useState<any | null>(null);
  const [showEmailSnapshot, setShowEmailSnapshot] = useState(false);

  useEffect(() => {
    if (!selectedWeek) return;
    setLoading(true);
    setError(null);
    setFeeData(null);
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

    fetch(`/api/fee/${selectedWeek}`)
      .then((res) => res.ok ? res.json() : null)
      .then(setFeeData)
      .catch(() => setFeeData(null));
  }, [selectedWeek]);

  // Fetch multi-week trend data (once on mount)
  useEffect(() => {
    fetch("/api/trend")
      .then(r => r.ok ? r.json() : [])
      .then(setTrendData)
      .catch(() => setTrendData([]));
  }, []);

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

  const sentiment = pulse.sentiment || { positive: 0, negative: 0, neutral: 0 };
  const pos = sentiment.positive || 0;
  const neg = sentiment.negative || 0;
  const neu = sentiment.neutral || 0;
  const avgRating = pos + neg + neu > 0 ? Math.round(((pos * 5 + neu * 3 + neg * 1) / (pos + neg + neu)) * 10) / 10 : 0.0;

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

    // Feature requests & conditional phrases override — "would be good if you added"
    // is a suggestion, not positive sentiment, regardless of the word "good"
    const featureRequestPhrases = [
      "would be good if", "would be great if", "it would be good",
      "please add", "if you added", "if you add", "should add",
      "would love if", "hoping for", "request", "suggestion",
      "trailing stop", "scalping", "please include", "would appreciate if"
    ];
    if (featureRequestPhrases.some(p => t.includes(p))) return "neutral";

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
              <button
                onClick={() => setShowEmailSnapshot(true)}
                className="flex items-center gap-1.5 rounded-full px-3 py-0.5 border transition-colors cursor-pointer hover:bg-emerald-50"
                style={{ background: "#fff", border: "1px solid #a7f3d0", color: "#00b386", fontSize: 12, fontWeight: 500, outline: "none" }}
              >
                ✉ View Email Snapshot
              </button>
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
      <div className="grid grid-cols-2 gap-4 mb-6">
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
      </div>

      {/* Middle section: Summary + Clusters + Avg Rating */}
      <div className="grid gap-4 mb-6" style={{ gridTemplateColumns: "1fr 340px 240px" }}>
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
            {themeClusters.slice(0, 5).map((c: any, i: number) => (
              <div key={c.name} className="flex items-center gap-3">
                <div
                  className="rounded flex items-center justify-center shrink-0"
                  style={{ width: 22, height: 22, background: "#f0f2f5", fontSize: 11, fontWeight: 600, color: "#6b7280" }}
                >
                  {i + 1}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1">
                    <span style={{ fontSize: 12.5, fontWeight: 500, color: "#374151", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }} title={c.name}>
                      {c.name}
                      {i < 3 && (
                        <span className="rounded px-1.5 py-0.25 ml-1.5" style={{ fontSize: 8.5, fontWeight: 700, background: "#e0f2fe", color: "#0284c7", textTransform: "uppercase", display: "inline-block", verticalAlign: "middle" }}>
                          TOP
                        </span>
                      )}
                    </span>
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

        {/* Avg Rating (Sentiment Score) */}
        <div className="rounded-xl p-6" style={{ background: "#fff", border: "1px solid var(--border)", boxShadow: "0 1px 3px rgba(0,0,0,0.04)", display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
          <div>
            <div style={{ fontSize: 11, fontWeight: 600, color: "#9ca3af", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 12 }}>
              Avg Rating (sentiment score)
            </div>
            <div className="flex items-end gap-2 mb-2">
              <div style={{ fontSize: 42, fontWeight: 700, color: "#111827", letterSpacing: "-0.03em", lineHeight: 1 }}>{avgRating}</div>
              <div className="flex mb-1.5 gap-0.5">
                {[1, 2, 3, 4, 5].map(s => (
                  <Star key={s} size={15} fill={s <= Math.round(avgRating) ? "#f59e0b" : "none"} style={{ color: "#f59e0b" }} />
                ))}
              </div>
            </div>
            <div style={{ fontSize: 12, color: "#6b7280" }}>Based on sentiment distribution</div>
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

      {/* ── NEW: Trend Chart + Avg Rating + Top Themes Bar + Emerging Issues ── */}
      {trendData.length >= 1 && (() => {
        const currentWeekTrend = trendData.find(d => d.week === selectedWeek);

        // All unique theme labels across all weeks (for legend)
        const allLabels = Array.from(new Set(trendData.flatMap(d => Object.keys(d.themes))));
        const CHART_COLORS = ["#00b386","#3b82f6","#f59e0b","#ef4444","#8b5cf6","#06b6d4","#f43f5e","#10b981","#ec4899"];

        // Build a persistent theme-to-color mapping
        const themeColorMap: Record<string, string> = {};
        allLabels.forEach((label, idx) => {
          themeColorMap[label] = CHART_COLORS[idx % CHART_COLORS.length];
        });

        // Emerging issues (current week)
        const emerging = (currentWeekTrend?.emerging || []).slice(0, 5);

        return (
          <>
            {/* Trend Chart */}
            <div 
              className="rounded-xl p-6 mb-6 trend-chart-container" 
              style={{ background: "#fff", border: "1px solid var(--border)", boxShadow: "0 1px 3px rgba(0,0,0,0.04)", position: "relative" }}
            >
              <div className="flex items-center gap-2 mb-1">
                <BarChart2 size={15} style={{ color: "#00b386" }} />
                <h3 style={{ fontSize: 14, fontWeight: 600, color: "#111827" }}>Theme Distribution Trend</h3>
              </div>
              <p style={{ fontSize: 12, color: "#9ca3af", marginBottom: 20 }}>Weekly theme share comparison (% of reviews). Hover segments for details.</p>
              
              <div className="flex flex-col gap-4">
                {trendData.map((d, i) => {
                  const themes = Object.entries(d.themes).sort((a: any, b: any) => b[1] - a[1]);
                  
                  return (
                    <div key={d.week} className="flex items-center gap-4">
                      {/* Week label */}
                      <span className="w-16 shrink-0 text-xs font-semibold text-gray-500 font-mono">
                        {d.week}
                      </span>
                      
                      {/* Stacked bar */}
                      <div className="flex-1 flex h-7 rounded-lg overflow-hidden bg-gray-100 shadow-inner border border-gray-100 relative">
                        {themes.map(([label, val]: any) => {
                          const pctValue = val as number;
                          if (pctValue <= 0) return null;
                          const color = themeColorMap[label] || "#cbd5e1";
                          const isHovered = hoveredPoint?.label === label && hoveredPoint?.week === d.week;
                          
                          return (
                            <div
                              key={label}
                              style={{
                                width: `${pctValue}%`,
                                backgroundColor: color,
                                cursor: "pointer",
                                transition: "all 0.15s ease",
                                opacity: hoveredPoint ? (isHovered ? 1.0 : 0.45) : 0.95,
                                borderLeft: isHovered ? "1px solid #1e293b" : "none",
                                borderRight: isHovered ? "1px solid #1e293b" : "none",
                                boxShadow: isHovered ? "inset 0 0 0 2px rgba(255,255,255,0.4)" : "none",
                              }}
                              onMouseEnter={(e) => {
                                const rect = e.currentTarget.getBoundingClientRect();
                                const container = e.currentTarget.closest(".trend-chart-container");
                                if (container) {
                                  const containerRect = container.getBoundingClientRect();
                                  setHoveredPoint({
                                    label,
                                    week: d.week,
                                    val: pctValue,
                                    x: rect.left - containerRect.left + rect.width / 2,
                                    y: rect.top - containerRect.top - 8
                                  });
                                }
                              }}
                              onMouseLeave={() => setHoveredPoint(null)}
                            />
                          );
                        })}
                      </div>
                    </div>
                  );
                })}
              </div>

              {hoveredPoint && (
                <div
                  style={{
                    position: "absolute",
                    left: hoveredPoint.x,
                    top: hoveredPoint.y,
                    transform: "translate(-50%, -100%)",
                    background: "#1e293b",
                    color: "#f8fafc",
                    padding: "8px 12px",
                    borderRadius: "8px",
                    fontSize: "11px",
                    fontFamily: "Inter, sans-serif",
                    pointerEvents: "none",
                    boxShadow: "0 10px 25px -5px rgba(0,0,0,0.15), 0 8px 10px -6px rgba(0,0,0,0.15)",
                    zIndex: 50,
                    border: "1px solid rgba(255,255,255,0.15)",
                    whiteSpace: "nowrap"
                  }}
                >
                  <div style={{ fontWeight: 600, color: "#38bdf8", marginBottom: "2px" }}>{hoveredPoint.label}</div>
                  <div>
                    Week: <span style={{ fontWeight: 600 }}>{hoveredPoint.week}</span> | Share: <span style={{ fontWeight: 700, color: "#34d399" }}>{hoveredPoint.val}%</span>
                  </div>
                </div>
              )}

              {/* Legend */}
              <div className="flex flex-wrap gap-x-4 gap-y-1.5 mt-5 pt-3 border-t border-gray-100">
                {allLabels.map((label) => (
                  <div key={label} className="flex items-center gap-1.5">
                    <div style={{ width: 8, height: 8, borderRadius: 2, background: themeColorMap[label] }} />
                    <span style={{ fontSize: 11, color: "#6b7280" }}>{label}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Bottom Row: Emerging Issues Full Width */}
            <div className="grid gap-4" style={{ gridTemplateColumns: "1fr" }}>
              {/* Emerging Issues Table */}
              <div className="rounded-xl p-6" style={{ background: "#fff", border: "1px solid var(--border)", boxShadow: "0 1px 3px rgba(0,0,0,0.04)" }}>
                <div className="flex items-center gap-2 mb-4">
                  <TrendingUp size={14} style={{ color: "#ef4444" }} />
                  <h3 style={{ fontSize: 14, fontWeight: 600, color: "#111827" }}>Emerging Issues</h3>
                  <span className="rounded-full px-2 py-0.5 ml-auto" style={{ fontSize: 11, fontWeight: 600, background: "#fef2f2", color: "#ef4444" }}>WoW change</span>
                </div>
                {emerging.length === 0 ? (
                  <div style={{ fontSize: 12.5, color: "#9ca3af", textAlign: "center", padding: "24px 0" }}>
                    Need 2+ weeks of data for comparison
                  </div>
                ) : (
                  <div>
                    <div className="grid mb-2" style={{ gridTemplateColumns: "1fr auto", gap: "0 12px" }}>
                      <span style={{ fontSize: 11, fontWeight: 600, color: "#9ca3af", textTransform: "uppercase", letterSpacing: "0.05em" }}>Theme</span>
                      <span style={{ fontSize: 11, fontWeight: 600, color: "#9ca3af", textTransform: "uppercase", letterSpacing: "0.05em" }}>Change</span>
                    </div>
                    <div className="flex flex-col gap-2">
                      {emerging.map((e: any) => (
                        <div key={e.theme} className="grid items-center rounded-lg px-3 py-2.5" style={{ gridTemplateColumns: "1fr auto", background: "#f9fafb", border: "1px solid var(--border)" }}>
                          <span style={{ fontSize: 12.5, color: "#374151", fontWeight: 500, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }} title={e.theme}>{e.theme}</span>
                          <span
                            className="flex items-center gap-1 rounded-full px-2 py-0.5"
                            style={{
                              fontSize: 11.5, fontWeight: 700,
                              color: e.change > 0 ? "#ef4444" : e.change < 0 ? "#00b386" : "#9ca3af",
                              background: e.change > 0 ? "#fef2f2" : e.change < 0 ? "#f0faf6" : "#f9fafb",
                            }}
                          >
                            {e.change > 0 ? <TrendingUp size={10}/> : e.change < 0 ? <TrendingDown size={10}/> : <Minus size={10}/>}
                            {e.change > 0 ? "+" : ""}{e.change}%
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </>
        );
      })()}

      {/* Email Snapshot Modal */}
      {showEmailSnapshot && (
        <div 
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fadeIn"
        >
          <div 
            className="w-full max-w-[650px] bg-white rounded-xl shadow-2xl overflow-hidden border border-gray-100 flex flex-col max-h-[90vh] animate-scaleUp"
          >
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 bg-gray-50">
              <div className="flex items-center gap-2">
                <span className="text-emerald-600 bg-emerald-50 rounded-full p-1.5 flex items-center justify-center">
                  <CheckCircle size={16} />
                </span>
                <span style={{ fontSize: 15, fontWeight: 600, color: "#111827" }}>
                  Email Draft Snapshot
                </span>
              </div>
              <button 
                onClick={() => setShowEmailSnapshot(false)}
                className="text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg p-1.5 transition-colors cursor-pointer"
                style={{ border: "none", outline: "none", background: "none" }}
              >
                ✕
              </button>
            </div>
            
            {/* Fields */}
            <div className="px-6 py-4 border-b border-gray-100 flex flex-col gap-2 bg-white text-sm">
              <div className="flex items-center">
                <span className="w-16 font-semibold text-gray-500">To:</span>
                <span className="text-gray-800 font-medium">team@groww.in</span>
              </div>
              <div className="flex items-start">
                <span className="w-16 font-semibold text-gray-500 shrink-0">Subject:</span>
                <span className="text-gray-800 font-medium">
                  Weekly Pulse + Fee Explainer — Groww ({selectedWeek})
                </span>
              </div>
            </div>

            {/* Email Body Area */}
            <div className="p-6 bg-gray-50 overflow-y-auto flex-1 font-mono text-[12.5px] text-gray-800 leading-relaxed whitespace-pre-wrap select-all">
{`Hi Team,

Here is the Weekly Product Review Pulse and Fee Explainer for Groww (${selectedWeek}).

WEEKLY PULSE SUMMARY:
${pulseData.pulse.weekly_summary}

FEE EXPLAINER: Mutual Fund Exit Load
${feeData && feeData.bullets ? feeData.bullets.map((b: string) => `- ${b}`).join("\n") : "- Exit load is a fee charged by mutual fund houses when you redeem your mutual fund units before a specified period.\n- It is designed to discourage short-term redemptions and protect the interests of long-term investors.\n- The fee is typically calculated as a percentage of the redemption value (e.g., 1% if redeemed within 365 days).\n- The exit load amount is directly deducted from the redemption proceeds and the remaining balance is paid out.\n- Different types of mutual funds (e.g., equity, debt, liquid) have varying exit load structures and periods.\n- Exit load details are disclosed in the scheme information document and are subject to regulatory updates by SEBI."}

The full report and historical logs have been appended to the Google Doc:
${pulseData.doc_link || `https://docs.google.com/document/d/default_doc_id/edit`}

Best regards,
Product Review Pulse Automator`}
            </div>

            {/* Footer */}
            <div className="px-6 py-3 border-t border-gray-100 bg-gray-50 flex justify-between items-center text-xs text-gray-400">
              <span>This is a read-only snapshot of the auto-generated draft.</span>
              <button 
                onClick={() => setShowEmailSnapshot(false)}
                className="bg-emerald-500 hover:bg-emerald-600 text-white font-medium px-4 py-1.5 rounded-lg transition-colors cursor-pointer"
                style={{ border: "none", outline: "none" }}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        @keyframes scaleUp {
          from { opacity: 0; transform: scale(0.95); }
          to { opacity: 1; transform: scale(1); }
        }
        .animate-fadeIn {
          animation: fadeIn 0.2s ease-out forwards;
        }
        .animate-scaleUp {
          animation: scaleUp 0.2s ease-out forwards;
        }
      `}</style>
    </div>
  );
}
