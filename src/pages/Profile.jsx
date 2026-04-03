// src/pages/Profile.jsx
import React, { useEffect, useState } from "react";
import { User, Mail, Calendar, BarChart2, MessageSquare, LogOut } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import toast from "react-hot-toast";
import { useNavigate } from "react-router-dom";
import Navbar from "../components/ui/Navbar";
import { useAuth } from "../context/AuthContext";
import { getUserProfile, getUserAnalyses } from "../lib/db";

export default function Profile() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [profile,   setProfile]   = useState(null);
  const [analyses,  setAnalyses]  = useState([]);
  const [loading,   setLoading]   = useState(true);

  useEffect(() => {
    if (!user) return;
    Promise.all([getUserProfile(user.uid), getUserAnalyses(user.uid)])
      .then(([p, a]) => { setProfile(p); setAnalyses(a); })
      .finally(() => setLoading(false));
  }, [user]);

  const handleLogout = async () => {
    await logout();
    toast.success("Signed out");
    navigate("/", { replace: true });
  };

  const totalCharts = analyses.reduce((s, a) => s + (a.chartCount || 0), 0);
  const totalChats  = analyses.reduce((s, a) => s + (a.chatHistory?.length || 0), 0);
  const joinDate    = profile?.createdAt?.toDate?.() || new Date();

  const initials = user?.displayName
    ? user.displayName.split(" ").map(n => n[0]).join("").slice(0, 2).toUpperCase()
    : user?.email?.[0]?.toUpperCase() || "U";

  return (
    <div className="min-h-screen bg-surface-0">
      <Navbar />
      <main className="max-w-2xl mx-auto px-4 sm:px-6 py-8 page-enter">
        <h1 className="font-display font-bold text-2xl text-white mb-6">Profile</h1>

        {/* Avatar + info */}
        <div className="glass rounded-3xl p-8 mb-6 flex flex-col items-center text-center">
          <div className="w-20 h-20 rounded-2xl flex items-center justify-center font-display font-bold text-2xl text-white mb-4"
               style={{ background: "linear-gradient(135deg,#0ea5e9,#a78bfa)" }}>
            {initials}
          </div>
          <h2 className="font-display font-bold text-xl text-white mb-1">
            {user?.displayName || "User"}
          </h2>
          <div className="flex items-center gap-2 text-slate-400 text-sm font-body">
            <Mail size={13} /> {user?.email}
          </div>
          <div className="flex items-center gap-2 text-slate-600 text-xs font-body mt-1">
            <Calendar size={11} /> Joined {formatDistanceToNow(joinDate, { addSuffix: true })}
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-4 mb-6">
          {[
            { icon: BarChart2,     label: "Analyses",    value: analyses.length, color: "cyan"   },
            { icon: BarChart2,     label: "Charts",      value: totalCharts,     color: "violet" },
            { icon: MessageSquare, label: "AI messages", value: totalChats,      color: "green"  },
          ].map(s => (
            <div key={s.label} className="glass rounded-2xl p-4 text-center">
              <div className="font-display font-bold text-2xl text-white">{s.value}</div>
              <div className="text-xs text-slate-500 font-body mt-0.5">{s.label}</div>
            </div>
          ))}
        </div>

        {/* Account info */}
        <div className="glass rounded-2xl p-6 mb-6 space-y-4">
          <h3 className="font-display font-semibold text-white text-sm">Account</h3>
          <div className="flex items-center justify-between text-sm font-body">
            <span className="text-slate-500">Name</span>
            <span className="text-slate-200">{user?.displayName || "—"}</span>
          </div>
          <div className="h-px bg-surface-3" />
          <div className="flex items-center justify-between text-sm font-body">
            <span className="text-slate-500">Email</span>
            <span className="text-slate-200">{user?.email}</span>
          </div>
          <div className="h-px bg-surface-3" />
          <div className="flex items-center justify-between text-sm font-body">
            <span className="text-slate-500">Plan</span>
            <span className="badge badge-green">Free forever</span>
          </div>
          <div className="h-px bg-surface-3" />
          <div className="flex items-center justify-between text-sm font-body">
            <span className="text-slate-500">Provider</span>
            <span className="text-slate-200">
              {user?.providerData?.[0]?.providerId === "google.com" ? "Google" : "Email"}
            </span>
          </div>
        </div>

        {/* Logout */}
        <button onClick={handleLogout} className="btn-secondary w-full justify-center py-3">
          <LogOut size={15} /> Sign out
        </button>
      </main>
    </div>
  );
}
