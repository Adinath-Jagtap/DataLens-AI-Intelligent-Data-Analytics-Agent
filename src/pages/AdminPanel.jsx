// src/pages/AdminPanel.jsx
import React, { useEffect, useState } from "react";
import {
  Users, Database, BarChart2, Trash2, RefreshCw,
  Shield, TrendingUp, FileSpreadsheet, LogOut, Activity
} from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import toast from "react-hot-toast";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { getAllUsers, getAllAnalyses, deleteUser } from "../lib/db";

const TABS = [
  { id: "overview", icon: BarChart2,  label: "Overview" },
  { id: "users",    icon: Users,      label: "Users"    },
  { id: "uploads",  icon: Database,   label: "Uploads"  },
];

function StatCard({ icon: Icon, label, value, color = "cyan" }) {
  return (
    <div className="rounded-2xl p-5 flex items-center gap-4"
         style={{ background: "rgba(15,23,38,0.8)", border: "1px solid rgba(255,255,255,0.06)" }}>
      <div className={`badge-${color} w-10 h-10 rounded-xl flex items-center justify-center`}>
        <Icon size={18} />
      </div>
      <div>
        <div className="font-display font-bold text-2xl text-white">{value}</div>
        <div className="text-xs text-slate-500 font-body">{label}</div>
      </div>
    </div>
  );
}

export default function AdminPanel() {
  const { logout } = useAuth();
  const navigate   = useNavigate();
  const [tab,      setTab]      = useState("overview");
  const [users,    setUsers]    = useState([]);
  const [analyses, setAnalyses] = useState([]);
  const [loading,  setLoading]  = useState(true);
  const [deleting, setDeleting] = useState(null);

  const load = async () => {
    setLoading(true);
    try {
      const [u, a] = await Promise.all([getAllUsers(), getAllAnalyses()]);
      setUsers(u);
      setAnalyses(a);
    } catch (err) {
      toast.error("Failed to load data: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleDeleteUser = async (uid) => {
    if (!window.confirm("Delete this user and all their data? This cannot be undone.")) return;
    setDeleting(uid);
    try {
      await deleteUser(uid);
      setUsers(u => u.filter(x => x.id !== uid));
      setAnalyses(a => a.filter(x => x.uid !== uid));
      toast.success("User deleted");
    } catch {
      toast.error("Failed to delete user");
    } finally {
      setDeleting(null);
    }
  };

  const handleLogout = async () => {
    await logout();
    navigate("/", { replace: true });
  };

  const totalCharts  = analyses.reduce((s, a) => s + (a.chartCount || 0), 0);
  const totalChats   = analyses.reduce((s, a) => s + (a.chatHistory?.length || 0), 0);

  return (
    <div className="min-h-screen bg-surface-0">
      {/* Admin nav */}
      <nav className="sticky top-0 z-50 glass border-b border-white/5">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 flex items-center justify-between h-14">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg flex items-center justify-center bg-accent-coral/20">
              <Shield size={14} className="text-accent-coral" />
            </div>
            <span className="font-display font-bold text-white text-base">Admin Panel</span>
            <span className="badge badge-coral ml-1 text-xs">Admin only</span>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={load} className="btn-secondary py-1.5 px-3 text-xs">
              <RefreshCw size={12} className={loading ? "animate-spin" : ""} /> Refresh
            </button>
            <button onClick={handleLogout} className="btn-secondary py-1.5 px-3 text-xs">
              <LogOut size={12} /> Sign out
            </button>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-8 page-enter">
        {/* Header */}
        <div className="mb-8">
          <h1 className="font-display font-bold text-3xl text-white">Dashboard</h1>
          <p className="text-slate-500 font-body text-sm mt-1">Full platform overview</p>
        </div>

        {/* Top stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <StatCard icon={Users}         label="Total users"    value={users.length}    color="cyan"   />
          <StatCard icon={FileSpreadsheet}label="Total analyses" value={analyses.length} color="violet" />
          <StatCard icon={BarChart2}     label="Charts created" value={totalCharts}     color="amber"  />
          <StatCard icon={Activity}      label="AI messages"    value={totalChats}      color="green"  />
        </div>

        {/* Tabs */}
        <div className="flex gap-1 mb-6 border-b border-white/5">
          {TABS.map(t => (
            <button key={t.id} onClick={() => setTab(t.id)}
                    className={`flex items-center gap-1.5 px-4 py-2.5 text-sm font-body font-medium
                      rounded-t-lg transition-colors relative
                      ${tab === t.id ? "text-white bg-surface-2" : "text-slate-500 hover:text-slate-300"}`}>
              <t.icon size={14} /> {t.label}
              {tab === t.id && (
                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-accent-coral rounded-t-full" />
              )}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="space-y-3">
            {[1,2,3,4].map(i => <div key={i} className="skeleton h-16 rounded-xl" />)}
          </div>
        ) : (
          <>
            {/* ── Overview tab ── */}
            {tab === "overview" && (
              <div className="space-y-6">
                {/* Recent users */}
                <div>
                  <h2 className="font-display font-semibold text-lg text-white mb-3">Recent users</h2>
                  <div className="glass rounded-2xl overflow-hidden">
                    <table className="w-full text-sm font-body">
                      <thead>
                        <tr className="border-b border-white/5 bg-surface-2">
                          {["User","Email","Joined","Analyses"].map(h => (
                            <th key={h} className="px-4 py-3 text-left text-slate-400 font-medium">{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {users.slice(0, 10).map(u => {
                          const date = u.createdAt?.toDate?.() || new Date();
                          const count = analyses.filter(a => a.uid === u.id).length;
                          return (
                            <tr key={u.id} className="border-b border-white/5 hover:bg-surface-2/50">
                              <td className="px-4 py-3 text-white font-medium">{u.displayName || "—"}</td>
                              <td className="px-4 py-3 text-slate-400">{u.email}</td>
                              <td className="px-4 py-3 text-slate-500 text-xs">{formatDistanceToNow(date, { addSuffix: true })}</td>
                              <td className="px-4 py-3"><span className="badge badge-cyan">{count}</span></td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Recent uploads */}
                <div>
                  <h2 className="font-display font-semibold text-lg text-white mb-3">Recent uploads</h2>
                  <div className="glass rounded-2xl overflow-hidden">
                    <table className="w-full text-sm font-body">
                      <thead>
                        <tr className="border-b border-white/5 bg-surface-2">
                          {["File","Rows","Charts","Uploaded"].map(h => (
                            <th key={h} className="px-4 py-3 text-left text-slate-400 font-medium">{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {analyses.slice(0, 10).map(a => {
                          const date = a.createdAt?.toDate?.() || new Date();
                          return (
                            <tr key={a.id} className="border-b border-white/5 hover:bg-surface-2/50">
                              <td className="px-4 py-3 text-white font-medium max-w-[200px] truncate">{a.fileName || "—"}</td>
                              <td className="px-4 py-3 text-slate-400">{a.summary?.rows?.toLocaleString() || "—"}</td>
                              <td className="px-4 py-3"><span className="badge badge-violet">{a.chartCount || 0}</span></td>
                              <td className="px-4 py-3 text-slate-500 text-xs">{formatDistanceToNow(date, { addSuffix: true })}</td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}

            {/* ── Users tab ── */}
            {tab === "users" && (
              <div className="glass rounded-2xl overflow-hidden">
                <table className="w-full text-sm font-body">
                  <thead>
                    <tr className="border-b border-white/5 bg-surface-2">
                      {["User","Email","UID","Joined","Analyses","Action"].map(h => (
                        <th key={h} className="px-4 py-3 text-left text-slate-400 font-medium">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {users.map(u => {
                      const date  = u.createdAt?.toDate?.() || new Date();
                      const count = analyses.filter(a => a.uid === u.id).length;
                      return (
                        <tr key={u.id} className="border-b border-white/5 hover:bg-surface-2/50">
                          <td className="px-4 py-3 text-white font-medium">{u.displayName || "—"}</td>
                          <td className="px-4 py-3 text-slate-400 text-xs">{u.email}</td>
                          <td className="px-4 py-3 text-slate-600 text-xs font-mono">{u.id?.slice(0, 12)}…</td>
                          <td className="px-4 py-3 text-slate-500 text-xs">{formatDistanceToNow(date, { addSuffix: true })}</td>
                          <td className="px-4 py-3"><span className="badge badge-cyan">{count}</span></td>
                          <td className="px-4 py-3">
                            <button onClick={() => handleDeleteUser(u.id)} disabled={deleting === u.id}
                                    className="p-1.5 rounded-lg text-slate-600 hover:text-accent-coral hover:bg-accent-coral/10 transition-colors">
                              {deleting === u.id
                                ? <span className="w-3.5 h-3.5 border border-slate-500 border-t-transparent rounded-full animate-spin block" />
                                : <Trash2 size={13} />}
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
                {users.length === 0 && (
                  <div className="p-10 text-center text-slate-600 font-body">No users yet.</div>
                )}
              </div>
            )}

            {/* ── Uploads tab ── */}
            {tab === "uploads" && (
              <div className="glass rounded-2xl overflow-hidden">
                <table className="w-full text-sm font-body">
                  <thead>
                    <tr className="border-b border-white/5 bg-surface-2">
                      {["File","User UID","Rows","Cols","Charts","Status","Date"].map(h => (
                        <th key={h} className="px-4 py-3 text-left text-slate-400 font-medium">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {analyses.map(a => {
                      const date = a.createdAt?.toDate?.() || new Date();
                      return (
                        <tr key={a.id} className="border-b border-white/5 hover:bg-surface-2/50">
                          <td className="px-4 py-3 text-white font-medium max-w-[160px] truncate">{a.fileName || "—"}</td>
                          <td className="px-4 py-3 text-slate-600 text-xs font-mono">{a.uid?.slice(0, 10)}…</td>
                          <td className="px-4 py-3 text-slate-400">{a.summary?.rows?.toLocaleString() || "—"}</td>
                          <td className="px-4 py-3 text-slate-400">{a.summary?.cols || "—"}</td>
                          <td className="px-4 py-3"><span className="badge badge-violet">{a.chartCount || 0}</span></td>
                          <td className="px-4 py-3">
                            <span className={`badge ${a.status === "done" ? "badge-green" : "badge-amber"}`}>
                              {a.status}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-slate-500 text-xs">{formatDistanceToNow(date, { addSuffix: true })}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
                {analyses.length === 0 && (
                  <div className="p-10 text-center text-slate-600 font-body">No uploads yet.</div>
                )}
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}
