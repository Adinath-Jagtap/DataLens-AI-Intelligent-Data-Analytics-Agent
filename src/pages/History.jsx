// src/pages/History.jsx
import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { FileSpreadsheet, Clock, Trash2, BarChart2, ArrowRight, Search } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import toast from "react-hot-toast";
import Navbar from "../components/ui/Navbar";
import { useAuth } from "../context/AuthContext";
import { getUserAnalyses, deleteAnalysis } from "../lib/db";

export default function History() {
  const { user }  = useAuth();
  const [analyses, setAnalyses] = useState([]);
  const [loading,  setLoading]  = useState(true);
  const [search,   setSearch]   = useState("");
  const [deleting, setDeleting] = useState(null);

  useEffect(() => {
    if (!user) return;
    getUserAnalyses(user.uid)
      .then(setAnalyses)
      .finally(() => setLoading(false));
  }, [user]);

  const handleDelete = async (id, e) => {
    e.preventDefault();
    e.stopPropagation();
    if (!window.confirm("Delete this analysis? This cannot be undone.")) return;
    setDeleting(id);
    try {
      await deleteAnalysis(user.uid, id);
      setAnalyses(a => a.filter(x => x.id !== id));
      toast.success("Analysis deleted");
    } catch {
      toast.error("Failed to delete");
    } finally {
      setDeleting(null);
    }
  };

  const filtered = analyses.filter(a =>
    !search || a.fileName?.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-surface-0">
      <Navbar />
      <main className="max-w-4xl mx-auto px-4 sm:px-6 py-8 page-enter">
        <div className="flex items-center justify-between mb-6">
          <h1 className="font-display font-bold text-2xl text-white">History</h1>
          <Link to="/upload" className="btn-primary text-sm">New analysis</Link>
        </div>

        {/* Search */}
        <div className="relative mb-6">
          <Search size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
          <input type="text" value={search} onChange={e => setSearch(e.target.value)}
                 placeholder="Search by filename…"
                 className="input-field pl-10" />
        </div>

        {loading ? (
          <div className="space-y-3">
            {[1,2,3,4].map(i => <div key={i} className="skeleton h-20 rounded-2xl" />)}
          </div>
        ) : filtered.length === 0 ? (
          <div className="glass rounded-2xl p-12 text-center">
            <BarChart2 size={36} className="text-slate-600 mx-auto mb-3" />
            <p className="text-slate-400 font-body">{search ? "No matches found." : "No analyses yet."}</p>
            {!search && (
              <Link to="/upload" className="btn-primary mt-4 mx-auto text-sm">Upload your first dataset</Link>
            )}
          </div>
        ) : (
          <div className="space-y-3">
            {filtered.map(a => {
              const date = a.createdAt?.toDate?.() || new Date();
              return (
                <Link key={a.id} to={`/analysis/${a.id}`}
                      className="glass glass-hover rounded-2xl p-5 flex items-center gap-4 group">
                  <div className="w-10 h-10 rounded-xl bg-surface-3 flex items-center justify-center flex-shrink-0">
                    <FileSpreadsheet size={18} className="text-accent-cyan" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="font-display font-semibold text-white text-sm truncate group-hover:text-accent-cyan transition-colors">
                      {a.fileName || "Untitled"}
                    </div>
                    <div className="text-xs text-slate-500 font-body mt-1 flex items-center gap-3 flex-wrap">
                      <span className="flex items-center gap-1"><Clock size={11} />{formatDistanceToNow(date, { addSuffix: true })}</span>
                      {a.summary?.rows     && <span>{a.summary.rows.toLocaleString()} rows</span>}
                      {a.summary?.cols     && <span>{a.summary.cols} columns</span>}
                      {a.chartCount > 0    && <span className="badge badge-cyan">{a.chartCount} charts</span>}
                      {a.chatHistory?.length > 0 && <span className="badge badge-violet">{a.chatHistory.length} messages</span>}
                      <span className={`badge ${a.status === "done" ? "badge-green" : "badge-amber"}`}>{a.status}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <button onClick={e => handleDelete(a.id, e)}
                            disabled={deleting === a.id}
                            className="p-2 rounded-lg text-slate-600 hover:text-accent-coral hover:bg-accent-coral/10 transition-colors">
                      {deleting === a.id
                        ? <span className="w-4 h-4 border border-slate-500 border-t-transparent rounded-full animate-spin block" />
                        : <Trash2 size={14} />}
                    </button>
                    <ArrowRight size={16} className="text-slate-600 group-hover:text-accent-cyan transition-colors" />
                  </div>
                </Link>
              );
            })}
          </div>
        )}
      </main>
    </div>
  );
}
