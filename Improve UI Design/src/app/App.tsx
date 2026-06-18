import { useState, useEffect } from "react";
import { WeeklyPulsePage } from "./components/WeeklyPulsePage";
import { FeeExplainerPage } from "./components/FeeExplainerPage";
import { RunHistoryPage } from "./components/RunHistoryPage";
import { SettingsPage } from "./components/SettingsPage";
import {
  BarChart2, FileText, History, Settings, ChevronLeft, ChevronRight, User
} from "lucide-react";

type Page = "pulse" | "fee" | "history" | "settings";

const navItems = [
  { id: "pulse" as Page, label: "Weekly Pulse", icon: BarChart2 },
  { id: "fee" as Page, label: "Fee Explainer", icon: FileText },
  { id: "history" as Page, label: "Run History", icon: History },
  { id: "settings" as Page, label: "Settings", icon: Settings },
];

export default function App() {
  const [page, setPage] = useState<Page>("pulse");
  const [collapsed, setCollapsed] = useState(false);
  const [weeks, setWeeks] = useState<string[]>([]);
  const [selectedWeek, setSelectedWeek] = useState<string>("");
  const [loadingWeeks, setLoadingWeeks] = useState(true);

  useEffect(() => {
    fetch("/api/weeks")
      .then((res) => res.json())
      .then((data) => {
        if (Array.isArray(data) && data.length > 0) {
          setWeeks(data);
          setSelectedWeek(data[0]);
        }
        setLoadingWeeks(false);
      })
      .catch((err) => {
        console.error("Failed to fetch weeks:", err);
        setLoadingWeeks(false);
      });
  }, []);

  return (
    <div className="flex h-screen bg-background font-[Inter,sans-serif] overflow-hidden">
      {/* Sidebar */}
      <aside
        className="flex flex-col shrink-0 transition-all duration-300 overflow-hidden"
        style={{
          width: collapsed ? 64 : 220,
          background: "var(--sidebar)",
          borderRight: "1px solid var(--sidebar-border)",
        }}
      >
        {/* Logo */}
        <div className="flex items-center gap-3 px-4 py-5 shrink-0" style={{ minHeight: 64 }}>
          <div
            className="flex items-center justify-center rounded-lg shrink-0"
            style={{ width: 34, height: 34, background: "var(--primary)", color: "#fff" }}
          >
            <span style={{ fontWeight: 700, fontSize: 16 }}>G</span>
          </div>
          {!collapsed && (
            <span style={{ color: "#f1f5f9", fontWeight: 600, fontSize: 17, letterSpacing: "-0.01em" }}>
              Groww
            </span>
          )}
        </div>

        {/* Nav */}
        <nav className="flex flex-col gap-1 px-2 flex-1 pt-2">
          {navItems.map(({ id, label, icon: Icon }) => {
            const active = page === id;
            return (
              <button
                key={id}
                onClick={() => setPage(id)}
                className="flex items-center gap-3 rounded-lg transition-all duration-150 text-left cursor-pointer"
                style={{
                  padding: collapsed ? "10px 14px" : "10px 12px",
                  background: active ? "var(--sidebar-accent)" : "transparent",
                  color: active ? "#f1f5f9" : "var(--sidebar-foreground)",
                  fontSize: 13.5,
                  fontWeight: active ? 500 : 400,
                  justifyContent: collapsed ? "center" : "flex-start",
                  border: "none",
                  outline: "none",
                  width: "100%",
                }}
              >
                <Icon
                  size={17}
                  style={{ color: active ? "var(--primary)" : "var(--sidebar-foreground)" }}
                />
                {!collapsed && <span>{label}</span>}
              </button>
            );
          })}
        </nav>

        {/* Week Selector in Sidebar */}
        {!collapsed && weeks.length > 0 && (
          <div className="px-4 py-3 border-t border-[rgba(255,255,255,0.06)] mt-auto mb-2">
            <label className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider block mb-1.5">
              Review Week
            </label>
            <select
              value={selectedWeek}
              onChange={(e) => setSelectedWeek(e.target.value)}
              className="w-full text-xs bg-slate-800 text-slate-200 border border-slate-700 rounded px-2 py-1 focus:outline-none focus:border-emerald-500 cursor-pointer"
            >
              {weeks.map((w) => (
                <option key={w} value={w}>
                  {w}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Profile + collapse */}
        <div className="px-2 pb-4 flex flex-col gap-2">
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="flex items-center justify-center rounded-lg transition-colors cursor-pointer"
            style={{
              height: 34,
              width: collapsed ? 36 : "100%",
              background: "transparent",
              color: "var(--sidebar-foreground)",
              border: "none",
              outline: "none",
              alignSelf: collapsed ? "center" : "flex-start",
              gap: 6,
              paddingLeft: collapsed ? 0 : 10,
              fontSize: 12.5,
            }}
          >
            {collapsed ? <ChevronRight size={15} /> : <><ChevronLeft size={15} /><span>Collapse</span></>}
          </button>
          <div
            className="flex items-center gap-3 rounded-lg px-2 py-2"
            style={{ cursor: "default" }}
          >
            <div
              className="flex items-center justify-center rounded-full shrink-0"
              style={{ width: 30, height: 30, background: "#1e293b", color: "#94a3b8" }}
            >
              <User size={15} />
            </div>
            {!collapsed && (
              <div>
                <div style={{ color: "#e2e8f0", fontSize: 12.5, fontWeight: 500 }}>Profile</div>
              </div>
            )}
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto">
        {page === "pulse" && (
          <WeeklyPulsePage 
            selectedWeek={selectedWeek} 
            weeks={weeks} 
            setSelectedWeek={setSelectedWeek} 
            loadingWeeks={loadingWeeks}
          />
        )}
        {page === "fee" && (
          <FeeExplainerPage 
            selectedWeek={selectedWeek} 
            loadingWeeks={loadingWeeks}
          />
        )}
        {page === "history" && <RunHistoryPage />}
        {page === "settings" && <SettingsPage />}
      </main>
    </div>
  );
}
