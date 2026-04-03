// src/pages/Login.jsx
import React, { useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { BarChart2, Mail, Lock, Eye, EyeOff } from "lucide-react";
import toast from "react-hot-toast";
import { useAuth } from "../context/AuthContext";

export default function Login() {
  const { login, loginWithGoogle, isAdmin } = useAuth();
  const navigate  = useNavigate();
  const location  = useLocation();
  const from      = location.state?.from?.pathname || null;

  const [email,    setEmail]    = useState("");
  const [password, setPassword] = useState("");
  const [showPw,   setShowPw]   = useState(false);
  const [loading,  setLoading]  = useState(false);

  const redirect = (admin) => navigate(from || (admin ? "/admin" : "/home"), { replace: true });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await login(email, password);
      // isAdmin from context updates via onAuthStateChanged — check uid directly
      const { auth, ADMIN_UID } = await import("../lib/firebase");
      redirect(auth.currentUser?.uid === ADMIN_UID);
    } catch (err) {
      toast.error(err.message?.replace("Firebase: ", "").replace(/\(.*\)/, "").trim() || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  const handleGoogle = async () => {
    setLoading(true);
    try {
      await loginWithGoogle();
      const { auth, ADMIN_UID } = await import("../lib/firebase");
      redirect(auth.currentUser?.uid === ADMIN_UID);
    } catch (err) {
      toast.error("Google sign-in failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-surface-0 flex items-center justify-center px-4">
      {/* Background glow */}
      <div className="fixed top-1/3 left-1/2 -translate-x-1/2 w-[600px] h-[400px] pointer-events-none rounded-full"
           style={{ background: "radial-gradient(ellipse, rgba(14,165,233,0.08) 0%, transparent 70%)" }} />

      <div className="relative w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <Link to="/" className="inline-flex items-center gap-2 mb-6">
            <div className="w-9 h-9 rounded-xl flex items-center justify-center"
                 style={{ background: "linear-gradient(135deg,#0ea5e9,#22d3ee)" }}>
              <BarChart2 size={18} className="text-surface-0" />
            </div>
            <span className="font-display font-bold text-white text-xl">DataLens AI</span>
          </Link>
          <h1 className="font-display font-bold text-2xl text-white">Welcome back</h1>
          <p className="text-slate-400 text-sm mt-1 font-body">Sign in to your account</p>
        </div>

        <div className="glass rounded-3xl p-8">
          {/* Google */}
          <button onClick={handleGoogle} disabled={loading}
                  className="btn-secondary w-full justify-center mb-6 py-3">
            <svg width="18" height="18" viewBox="0 0 24 24">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
            Continue with Google
          </button>

          <div className="flex items-center gap-3 mb-6">
            <div className="flex-1 h-px bg-surface-3" />
            <span className="text-slate-600 text-xs font-body">or</span>
            <div className="flex-1 h-px bg-surface-3" />
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1.5">Email</label>
              <div className="relative">
                <Mail size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
                <input type="email" value={email} onChange={e => setEmail(e.target.value)}
                       className="input-field pl-10" placeholder="you@example.com" required />
              </div>
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1.5">Password</label>
              <div className="relative">
                <Lock size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
                <input type={showPw ? "text" : "password"} value={password}
                       onChange={e => setPassword(e.target.value)}
                       className="input-field pl-10 pr-10" placeholder="••••••••" required />
                <button type="button" onClick={() => setShowPw(v => !v)}
                        className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300">
                  {showPw ? <EyeOff size={15}/> : <Eye size={15}/>}
                </button>
              </div>
            </div>
            <button type="submit" disabled={loading} className="btn-primary w-full justify-center py-3 mt-2">
              {loading ? <span className="w-4 h-4 border-2 border-surface-0 border-t-transparent rounded-full animate-spin" /> : "Sign in"}
            </button>
          </form>

          <p className="text-center text-sm text-slate-500 mt-6 font-body">
            Don't have an account?{" "}
            <Link to="/signup" className="text-accent-cyan hover:underline">Create one</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
