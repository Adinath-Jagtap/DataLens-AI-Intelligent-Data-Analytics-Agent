// src/pages/Home.jsx
import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Upload, Clock, BarChart2, TrendingUp, MessageSquare, ArrowRight, FileSpreadsheet } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import Navbar from "../components/ui/Navbar";
import { useAuth } from "../context/AuthContext";
import { getUserAnalyses } from "../lib/db";

function StatCard({ icon: Icon, label, value, color }) {
  return (
    <div className="stat-card flex items-center gap-4">
      <div className={`w-10 h-10 rounded-xl flex items-center justify-center badge-${color}`}>
        <Icon size={18} />
      </div>
      <div>
        <div className="font-display font-bold text-xl text-white">{value}</div>
        <div className="text-xs text-slate-500 font-body">{label}</div>
      </div>
    </div>
  );
}

function AnalysisCard({ analysis }) {
  const date = analysis.createdAt?.toDate?.() || new Date();
  return (
    <Link to={`/analysis/${analysis.id}`}
          className="glass glass-hover rounded-2xl p-5 flex items-start gap-4 group">
      <div className="w-10 h-10 rounded-xl bg-surface-3 flex items-center justify-center flex-shrink-0">
        <FileSpreadsheet size={18} className="text-accent-cyan" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="font-display font-semibold text-white text-sm truncate group-hover:text-accent-cyan transition-colors">
          {analysis.fileName || "Untitled dataset"}
        </div>
        <div className="text-xs text-slate-500 font-body mt-1 flex items-center gap-3">
          <span className="flex items-center gap-1">
            <Clock size={11} /> {formatDistanceToNow(date, { addSuffix: true })}
          </span>
          {analysis.summary?.rows && (
            <span>{analysis.summary.rows.toLocaleString()} rows</span>
          )}
          {analysis.chartCount > 0 && (
            <span className="badge badge-cyan">{analysis.chartCount} charts</span>
          )}
        </div>
      </div>
      <ArrowRight size={16} className="text-slate-600 group-hover:text-accent-cyan transition-colors flex-shrink-0 mt-1" />
    </Link>
  );
}

export default function Home() {
  const { user } = useAuth();
  const [analyses, setAnalyses] = useState([]);
  const [loading,  setLoading]  = useState(true);

  useEffect(() => {
    if (!user) return;
    getUserAnalyses(user.uid)
      .then(setAnalyses)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [user]);

  const totalCharts = analyses.reduce((s, a) => s + (a.chartCount || 0), 0);
  const totalChats  = analyses.reduce((s, a) => s + (a.chatHistory?.length || 0), 0);

  return (
    <div className="min-h-screen bg-surface-0">
      <Navbar />

      <main className="max-w-6xl mx-auto px-4 sm:px-6 py-8 page-enter">
        {/* Greeting */}
        <div className="mb-8">
          <h1 className="font-display font-bold text-3xl text-white">
            Hey, {user?.displayName?.split(" ")[0] || "there"} 👋
          </h1>
          <p className="text-slate-400 font-body mt-1">
            {analyses.length === 0 ? "Upload your first dataset to get started." : "Here's your analytics overview."}
          </p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <StatCard icon={BarChart2}     label="Analyses"   value={analyses.length} color="cyan"   />
          <StatCard icon={TrendingUp}    label="Charts"     value={totalCharts}     color="violet" />
          <StatCard icon={MessageSquare} label="AI messages"value={totalChats}      color="green"  />
          <StatCard icon={FileSpreadsheet} label="Datasets" value={analyses.length} color="amber"  />
        </div>

        {/* Upload CTA */}
        <Link to="/upload"
              className="glass glass-hover rounded-2xl p-6 flex items-center gap-5 mb-8 group border border-dashed border-surface-4 hover:border-accent-cyan/30 transition-colors">
          <div className="w-12 h-12 rounded-2xl flex items-center justify-center"
               style={{ background: "linear-gradient(135deg,rgba(14,165,233,0.15),rgba(34,211,238,0.15))" }}>
            <Upload size={22} className="text-accent-cyan" />
          </div>
          <div>
            <div className="font-display font-semibold text-white group-hover:text-accent-cyan transition-colors">
              Upload new dataset
            </div>
            <div className="text-xs text-slate-500 font-body mt-0.5">
              CSV or Excel · up to 50 MB · AI analysis in seconds
            </div>
          </div>
          <ArrowRight size={18} className="text-slate-600 group-hover:text-accent-cyan transition-colors ml-auto" />
        </Link>

        {/* Recent analyses */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-display font-semibold text-lg text-white">Recent analyses</h2>
            {analyses.length > 5 && (
              <Link to="/history" className="text-xs text-accent-cyan hover:underline font-body">
                View all
              </Link>
            )}
          </div>

          {loading ? (
            <div className="space-y-3">
              {[1,2,3].map(i => <div key={i} className="skeleton h-20 rounded-2xl" />)}
            </div>
          ) : analyses.length === 0 ? (
            <div className="glass rounded-2xl p-12 text-center">
              <BarChart2 size={36} className="text-slate-600 mx-auto mb-3" />
              <p className="text-slate-400 font-body">No analyses yet.</p>
              <p className="text-slate-600 text-sm font-body mt-1">Upload a dataset to get started.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {analyses.slice(0, 8).map(a => <AnalysisCard key={a.id} analysis={a} />)}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
