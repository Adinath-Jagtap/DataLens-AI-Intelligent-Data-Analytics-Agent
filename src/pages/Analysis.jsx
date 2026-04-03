// src/pages/Analysis.jsx
import React, { useEffect, useState, useCallback } from "react";
import { useParams, useSearchParams, useNavigate } from "react-router-dom";
import {
  BarChart2, MessageSquare, Table2, LayoutDashboard,
  Lightbulb, Loader2, AlertCircle, Download, RefreshCw
} from "lucide-react";
import toast from "react-hot-toast";
import Navbar from "../components/ui/Navbar";
import KPICards   from "../components/dashboard/KPICards";
import ChartCard  from "../components/charts/ChartCard";
import ChatPanel  from "../components/chat/ChatPanel";
import { useAuth } from "../context/AuthContext";
import { getAnalysis, updateAnalysis, saveChat } from "../lib/db";
import { parseDataset, cleanDataset, buildChartData } from "../lib/pyodide";
import { analyseDataset, generateChartConfigs } from "../lib/groq";

const TABS = [
  { id: "overview",   icon: LayoutDashboard, label: "Overview"  },
  { id: "charts",     icon: BarChart2,       label: "Charts"    },
  { id: "chat",       icon: MessageSquare,   label: "AI Chat"   },
  { id: "data",       icon: Table2,          label: "Data"      },
];

// ── Processing step log ──────────────────────────────────────────────────────
function ProcessingScreen({ steps, current }) {
  return (
    <div className="min-h-screen bg-surface-0 flex items-center justify-center">
      <div className="glass rounded-3xl p-10 max-w-md w-full mx-4">
        <div className="flex items-center gap-3 mb-8">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center"
               style={{ background: "linear-gradient(135deg,#0ea5e9,#22d3ee)" }}>
            <BarChart2 size={18} className="text-surface-0" />
          </div>
          <div>
            <div className="font-display font-bold text-white">Analysing your data</div>
            <div className="text-xs text-slate-500 font-body">AI is working on it…</div>
          </div>
        </div>

        <div className="space-y-3">
          {steps.map((step, i) => (
            <div key={i} className={`flex items-center gap-3 transition-opacity duration-300
              ${i > current ? "opacity-30" : "opacity-100"}`}>
              <div className={`w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 text-xs
                ${i < current  ? "bg-accent-green/20 text-accent-green" :
                  i === current ? "bg-accent-cyan/20 text-accent-cyan"  :
                                  "bg-surface-3 text-slate-600"}`}>
                {i < current ? "✓" : i === current
                  ? <Loader2 size={12} className="animate-spin" />
                  : <span>{i + 1}</span>}
              </div>
              <span className={`text-sm font-body
                ${i === current ? "text-white" : i < current ? "text-slate-400" : "text-slate-600"}`}>
                {step}
              </span>
            </div>
          ))}
        </div>

        <div className="mt-8 h-1.5 bg-surface-3 rounded-full overflow-hidden">
          <div className="h-full bg-gradient-to-r from-brand-500 to-accent-cyan rounded-full transition-all duration-500"
               style={{ width: `${Math.round((current / (steps.length - 1)) * 100)}%` }} />
        </div>
      </div>
    </div>
  );
}

// ── Data table ───────────────────────────────────────────────────────────────
function DataTable({ rows }) {
  const [page, setPage] = useState(0);
  const PER_PAGE = 50;
  if (!rows?.length) return null;
  const cols   = Object.keys(rows[0]);
  const slice  = rows.slice(page * PER_PAGE, (page + 1) * PER_PAGE);
  const pages  = Math.ceil(rows.length / PER_PAGE);

  return (
    <div>
      <div className="overflow-x-auto rounded-2xl border border-white/5">
        <table className="w-full text-xs font-body">
          <thead>
            <tr className="border-b border-white/5 bg-surface-2">
              {cols.map(c => (
                <th key={c} className="px-3 py-2.5 text-left text-slate-400 font-medium whitespace-nowrap">
                  {c}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {slice.map((row, i) => (
              <tr key={i} className="border-b border-white/5 hover:bg-surface-2/50 transition-colors">
                {cols.map(c => (
                  <td key={c} className="px-3 py-2 text-slate-300 whitespace-nowrap max-w-[180px] truncate">
                    {row[c] == null ? <span className="text-slate-600">null</span> : String(row[c])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {pages > 1 && (
        <div className="flex items-center justify-between mt-3 text-xs font-body text-slate-500">
          <span>Showing {page * PER_PAGE + 1}–{Math.min((page + 1) * PER_PAGE, rows.length)} of {rows.length}</span>
          <div className="flex gap-2">
            <button disabled={page === 0} onClick={() => setPage(p => p - 1)}
                    className="btn-secondary py-1 px-3 text-xs disabled:opacity-30">Prev</button>
            <button disabled={page >= pages - 1} onClick={() => setPage(p => p + 1)}
                    className="btn-secondary py-1 px-3 text-xs disabled:opacity-30">Next</button>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Insight cards ─────────────────────────────────────────────────────────────
function InsightCard({ text, i }) {
  const colors = ["cyan","violet","amber","green","coral"];
  const color  = colors[i % colors.length];
  return (
    <div className={`glass rounded-xl p-4 border-l-2 border-accent-${color}`}>
      <p className="text-sm font-body text-slate-300 leading-relaxed">{text}</p>
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────
export default function Analysis() {
  const { id }            = useParams();
  const [searchParams]    = useSearchParams();
  const isNew             = searchParams.get("new") === "1";
  const { user }          = useAuth();
  const navigate          = useNavigate();

  const [tab,         setTab]         = useState("overview");
  const [analysis,    setAnalysis]    = useState(null);
  const [rows,        setRows]        = useState([]);
  const [charts,      setCharts]      = useState([]);
  const [chartData,   setChartData]   = useState({});
  const [aiResult,    setAiResult]    = useState(null);
  const [processing,  setProcessing]  = useState(isNew);
  const [procStep,    setProcStep]    = useState(0);
  const [error,       setError]       = useState("");

  const STEPS = [
    "Loading Python runtime…",
    "Parsing your file…",
    "Profiling dataset…",
    "AI analysing data quality…",
    "Cleaning data…",
    "Generating chart configs…",
    "Rendering visualisations…",
    "Saving to your profile…",
  ];

  // ── Load existing analysis ────────────────────────────────────────────────
  useEffect(() => {
    if (!user || isNew) return;
    getAnalysis(user.uid, id).then(a => {
      if (!a) { navigate("/home"); return; }
      setAnalysis(a);
      setRows(a.rows || []);
      setCharts(a.charts || []);
      if (a.aiResult) setAiResult(a.aiResult);
    });
  }, [user, id, isNew, navigate]);

  // ── Run full pipeline for new uploads ─────────────────────────────────────
  const runPipeline = useCallback(async () => {
    try {
      // 1. Get file from IndexedDB
      const file = await getFileFromIDB(id);
      if (!file) { setError("File not found. Please upload again."); setProcessing(false); return; }

      // 2. Parse
      setProcStep(1);
      const { summary, rows: parsed } = await parseDataset(file, msg => {
        if (msg.includes("Python")) setProcStep(0);
        if (msg.includes("Parsing")) setProcStep(1);
      });
      setProcStep(2);

      // 3. AI analysis
      setProcStep(3);
      let aiData = null;
      try {
        const aiRaw = await analyseDataset(summary);
        aiData = JSON.parse(aiRaw.replace(/```json|```/g, "").trim());
        setAiResult(aiData);
      } catch { /* non-fatal */ }

      // 4. Clean
      setProcStep(4);
      let cleanedRows = parsed;
      if (aiData?.cleaning_steps?.length > 0) {
        try {
          const res = await cleanDataset(parsed, aiData.cleaning_steps);
          cleanedRows = res.rows;
        } catch { /* use original */ }
      }
      setRows(cleanedRows);

      // 5. Chart configs
      setProcStep(5);
      let chartConfigs = [];
      const numericCols = summary.columns.filter(c =>
        ["int64","float64","int32","float32"].some(t => c.dtype?.includes(t))
      ).map(c => c.name);
      const catCols = summary.columns.filter(c =>
        !["int64","float64","int32","float32"].some(t => c.dtype?.includes(t))
      ).map(c => c.name);

      if (aiData?.recommended_charts?.length > 0) {
        chartConfigs = aiData.recommended_charts.map((c, i) => ({
          id:    `chart_${i}`,
          type:  c.type,
          title: c.title,
          xCol:  c.x,
          yCol:  c.y,
          color: ["#22d3ee","#a78bfa","#fbbf24","#34d399","#fb7185","#38bdf8"][i % 6],
          description: c.reason,
        }));
      }

      // Fallback: auto-generate
      if (chartConfigs.length < 4) {
        const auto = [];
        if (numericCols.length >= 2)
          auto.push({ id:"ac1", type:"scatter",   title:`${numericCols[0]} vs ${numericCols[1]}`, xCol:numericCols[0], yCol:numericCols[1], color:"#22d3ee" });
        if (numericCols.length >= 1)
          auto.push({ id:"ac2", type:"histogram",  title:`${numericCols[0]} distribution`,         xCol:numericCols[0], color:"#a78bfa" });
        if (catCols.length >= 1 && numericCols.length >= 1)
          auto.push({ id:"ac3", type:"bar",        title:`${numericCols[0]} by ${catCols[0]}`,     xCol:catCols[0],     yCol:numericCols[0], color:"#fbbf24" });
        if (numericCols.length >= 2)
          auto.push({ id:"ac4", type:"heatmap",    title:"Correlation matrix",                     color:"#34d399" });
        chartConfigs = [...chartConfigs, ...auto].slice(0, 12);
      }
      setCharts(chartConfigs);

      // 6. Build chart data
      setProcStep(6);
      const cData = {};
      await Promise.all(
        chartConfigs.map(async cfg => {
          try {
            cData[cfg.id] = await buildChartData(cleanedRows, cfg);
          } catch {}
        })
      );
      setChartData(cData);

      // 7. Save
      // NOTE: chartData is intentionally NOT saved to Firestore.
      // The heatmap type produces a nested z-matrix ([[…],[…]]) which
      // Firestore forbids. chartData is rebuilt from rows+charts on load.
      setProcStep(7);
      await updateAnalysis(user.uid, id, {
        status:     "done",
        summary,
        rows:       cleanedRows.slice(0, 2000),
        charts:     chartConfigs,
        aiResult:   aiData,
        chartCount: chartConfigs.length,
        fileName:   file.name,
        fileSize:   file.size,
      });

      setAnalysis(prev => ({ ...prev, summary, fileName: file.name }));
      setProcessing(false);
      toast.success("Analysis complete!");

    } catch (err) {
      console.error(err);
      setError(err.message || "Analysis failed. Please try again.");
      setProcessing(false);
    }
  }, [id, user]);

  useEffect(() => { if (isNew && user) runPipeline(); }, [isNew, user, runPipeline]);

  // ── Rebuild chart data for existing analyses ─────────────────────────────
  // chartData is NOT persisted in Firestore (heatmap z-matrices are nested
  // arrays which Firestore rejects). We derive it from stored rows + charts.
  useEffect(() => {
    if (isNew || !analysis) return;
    const storedRows   = analysis.rows   || [];
    const storedCharts = analysis.charts || [];
    if (!storedRows.length || !storedCharts.length) return;

    let cancelled = false;
    (async () => {
      const cData = {};
      await Promise.all(
        storedCharts.map(async cfg => {
          try { cData[cfg.id] = await buildChartData(storedRows, cfg); } catch {}
        })
      );
      if (!cancelled) setChartData(cData);
    })();

    return () => { cancelled = true; };
  }, [analysis, isNew]);

  const handleSaveChat = useCallback(async (messages) => {
    if (!user) return;
    try { await saveChat(user.uid, id, messages); } catch {}
  }, [user, id]);

  const downloadCSV = () => {
    if (!rows.length) return;
    const cols = Object.keys(rows[0]);
    const csv  = [cols.join(","), ...rows.map(r =>
      cols.map(c => JSON.stringify(r[c] ?? "")).join(",")
    )].join("\n");
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
    a.download = `${analysis?.fileName?.replace(/\.[^.]+$/, "") || "data"}_cleaned.csv`;
    a.click();
  };

  if (processing) return <ProcessingScreen steps={STEPS} current={procStep} />;

  if (error) return (
    <div className="min-h-screen bg-surface-0 flex items-center justify-center px-4">
      <div className="glass rounded-3xl p-10 max-w-md text-center">
        <AlertCircle size={36} className="text-accent-coral mx-auto mb-4" />
        <h2 className="font-display font-bold text-white text-xl mb-2">Analysis failed</h2>
        <p className="text-slate-400 font-body text-sm mb-6">{error}</p>
        <button onClick={() => navigate("/upload")} className="btn-primary mx-auto">Try again</button>
      </div>
    </div>
  );

  const summary     = analysis?.summary;
  const insights    = aiResult?.key_insights || [];
  const qualScore   = aiResult?.quality_score;
  const dataContext = { summary, sample: rows.slice(0, 10), aiResult };

  return (
    <div className="min-h-screen bg-surface-0">
      <Navbar />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6 page-enter">
        {/* Header */}
        <div className="flex items-start justify-between mb-6 gap-4">
          <div>
            <h1 className="font-display font-bold text-2xl text-white truncate">
              {analysis?.fileName || "Analysis"}
            </h1>
            <div className="flex items-center gap-3 mt-1">
              {qualScore != null && (
                <span className={`badge ${qualScore >= 80 ? "badge-green" : qualScore >= 50 ? "badge-amber" : "badge-coral"}`}>
                  Data quality: {qualScore}/100
                </span>
              )}
              {aiResult?.dataset_type && (
                <span className="badge badge-violet">{aiResult.dataset_type}</span>
              )}
              {rows.length > 0 && (
                <span className="text-xs text-slate-600 font-body">{rows.length.toLocaleString()} rows</span>
              )}
            </div>
          </div>
          <div className="flex gap-2 flex-shrink-0">
            <button onClick={downloadCSV} className="btn-secondary text-xs py-2">
              <Download size={13} /> Export CSV
            </button>
          </div>
        </div>

        {/* KPI Strip */}
        <div className="mb-6"><KPICards summary={summary} /></div>

        {/* Tabs */}
        <div className="flex gap-1 mb-6 border-b border-white/5 pb-0">
          {TABS.map(t => (
            <button key={t.id} onClick={() => setTab(t.id)}
                    className={`flex items-center gap-1.5 px-4 py-2.5 text-sm font-body font-medium
                      rounded-t-lg transition-colors relative
                      ${tab === t.id
                        ? "text-white bg-surface-2"
                        : "text-slate-500 hover:text-slate-300"}`}>
              <t.icon size={14} /> {t.label}
              {tab === t.id && (
                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-accent-cyan rounded-t-full" />
              )}
            </button>
          ))}
        </div>

        {/* ── Overview tab ── */}
        {tab === "overview" && (
          <div className="space-y-6">
            {insights.length > 0 && (
              <div>
                <h2 className="font-display font-semibold text-lg text-white mb-3 flex items-center gap-2">
                  <Lightbulb size={18} className="text-accent-amber" /> AI Insights
                </h2>
                <div className="grid md:grid-cols-2 gap-3">
                  {insights.map((ins, i) => <InsightCard key={i} text={ins} i={i} />)}
                </div>
              </div>
            )}

            {/* Top 4 charts preview */}
            {charts.length > 0 && (
              <div>
                <h2 className="font-display font-semibold text-lg text-white mb-3 flex items-center gap-2">
                  <BarChart2 size={18} className="text-accent-cyan" /> Key charts
                </h2>
                <div className="grid md:grid-cols-2 gap-4">
                  {charts.slice(0, 4).map(c => (
                    <ChartCard key={c.id}
                               data={chartData[c.id]}
                               title={c.title}
                               description={c.description}
                               onExpand={() => setTab("charts")} />
                  ))}
                </div>
              </div>
            )}

            {/* Column summary */}
            {summary?.columns && (
              <div>
                <h2 className="font-display font-semibold text-lg text-white mb-3">Column summary</h2>
                <div className="glass rounded-2xl overflow-hidden">
                  <table className="w-full text-xs font-body">
                    <thead>
                      <tr className="border-b border-white/5 bg-surface-2">
                        {["Column","Type","Nulls","Unique","Range / Top values"].map(h => (
                          <th key={h} className="px-4 py-3 text-left text-slate-400 font-medium">{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {summary.columns.map((col, i) => (
                        <tr key={i} className="border-b border-white/5 hover:bg-surface-2/50">
                          <td className="px-4 py-2.5 text-white font-medium">{col.name}</td>
                          <td className="px-4 py-2.5"><span className="badge badge-violet">{col.dtype}</span></td>
                          <td className="px-4 py-2.5 text-slate-400">{col.nulls}</td>
                          <td className="px-4 py-2.5 text-slate-400">{col.unique}</td>
                          <td className="px-4 py-2.5 text-slate-500">
                            {col.min != null
                              ? `${Number(col.min).toFixed(2)} – ${Number(col.max).toFixed(2)}`
                              : col.top_values?.slice(0,3).join(", ")}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ── Charts tab ── */}
        {tab === "charts" && (
          <div>
            {charts.length === 0 ? (
              <div className="glass rounded-2xl p-12 text-center">
                <BarChart2 size={36} className="text-slate-600 mx-auto mb-3" />
                <p className="text-slate-400 font-body">No charts generated yet.</p>
              </div>
            ) : (
              <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-4">
                {charts.map(c => (
                  <ChartCard key={c.id} data={chartData[c.id]} title={c.title} description={c.description} />
                ))}
              </div>
            )}
          </div>
        )}

        {/* ── Chat tab ── */}
        {tab === "chat" && (
          <div className="glass rounded-2xl overflow-hidden" style={{ height: "70vh" }}>
            <ChatPanel
              datasetContext={dataContext}
              chatHistory={analysis?.chatHistory}
              onSave={handleSaveChat}
            />
          </div>
        )}

        {/* ── Data tab ── */}
        {tab === "data" && (
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-display font-semibold text-lg text-white">Cleaned data</h2>
              <button onClick={downloadCSV} className="btn-secondary text-xs py-2">
                <Download size={13} /> Download CSV
              </button>
            </div>
            <DataTable rows={rows} />
          </div>
        )}
      </main>
    </div>
  );
}

// IndexedDB read helper — must match DB name/version in Upload.jsx
function getFileFromIDB(id) {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open("datalens_files", 2);
    req.onupgradeneeded = (e) => {
      const db = e.target.result;
      if (!db.objectStoreNames.contains("files")) {
        db.createObjectStore("files");
      }
    };
    req.onsuccess = (e) => {
      const db = e.target.result;
      try {
        const tx  = db.transaction("files", "readonly");
        const get = tx.objectStore("files").get(id);
        get.onsuccess = () => resolve(get.result || null);
        get.onerror   = (ev) => reject(ev.target.error);
      } catch (err) {
        reject(err);
      }
    };
    req.onerror = (e) => reject(e.target.error);
  });
}